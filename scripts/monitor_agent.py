import json
import logging
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import paramiko
import psutil
import requests


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.json"


class ConfigError(Exception):
    pass


@dataclass
class AgentConfig:
    computer_name: str
    local_log_directory: Path
    public_ip_check_interval_seconds: int
    resource_check_interval_seconds: int
    cpu_critical_percent: int
    ram_critical_percent: int
    critical_count_before_action: int
    monitor_edge: bool
    server_host: str
    server_port: int
    server_username: str
    server_password_env_var: str
    server_remote_root: str
    server_connect_timeout_seconds: int
    server_upload_retry_seconds: int
    public_ip_sources: list[str]

    @property
    def log_file(self) -> Path:
        return self.local_log_directory / f"{self.computer_name}_ip_monitor.log"

    @property
    def scheduled_task_name(self) -> str:
        return f"IPMonitor_{self.computer_name}"


def load_config() -> AgentConfig:
    if not CONFIG_PATH.exists():
        raise ConfigError(f"Config file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8-sig") as handle:
        raw = json.load(handle)

    server = raw.get("server", {})
    computer_name = str(raw.get("computer_name", "")).strip()
    if not computer_name or computer_name == "replace_me":
        raise ConfigError("config.json must contain a unique computer_name")

    local_log_directory = BASE_DIR / str(raw.get("local_log_directory", "logs"))
    public_ip_sources = raw.get("public_ip_sources") or []
    if not public_ip_sources:
        raise ConfigError("public_ip_sources must contain at least one URL")
    if int(raw.get("critical_count_before_action", 3)) < 1:
        raise ConfigError("critical_count_before_action must be 1 or greater")
    if not str(server.get("host", "")).strip():
        raise ConfigError("server.host must be set")
    if not str(server.get("username", "")).strip():
        raise ConfigError("server.username must be set")
    if not str(server.get("remote_root", "")).strip():
        raise ConfigError("server.remote_root must be set")

    return AgentConfig(
        computer_name=computer_name,
        local_log_directory=local_log_directory,
        public_ip_check_interval_seconds=int(raw.get("public_ip_check_interval_seconds", 600)),
        resource_check_interval_seconds=int(raw.get("resource_check_interval_seconds", 60)),
        cpu_critical_percent=int(raw.get("cpu_critical_percent", 90)),
        ram_critical_percent=int(raw.get("ram_critical_percent", 90)),
        critical_count_before_action=int(raw.get("critical_count_before_action", 3)),
        monitor_edge=bool(raw.get("monitor_edge", False)),
        server_host=str(server.get("host", "")).strip(),
        server_port=int(server.get("port", 22)),
        server_username=str(server.get("username", "")).strip(),
        server_password_env_var=str(server.get("password_env_var", "IPMON_SERVER_PASSWORD")).strip(),
        server_remote_root=str(server.get("remote_root", "")).rstrip("/"),
        server_connect_timeout_seconds=int(server.get("connect_timeout_seconds", 15)),
        server_upload_retry_seconds=int(server.get("upload_retry_seconds", 120)),
        public_ip_sources=[str(item).strip() for item in public_ip_sources if str(item).strip()],
    )


def setup_logging(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("monitor_agent")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(message)s")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def log_event(logger: logging.Logger, event_type: str, **details: Any) -> None:
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "event_type": event_type,
        **details,
    }
    logger.info(json.dumps(payload, ensure_ascii=True))


class ServerSync:
    def __init__(self, config: AgentConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self.next_attempt_after = 0.0

    def sync_log(self) -> bool:
        now = time.monotonic()
        if now < self.next_attempt_after:
            return False

        password = os.environ.get(self.config.server_password_env_var)
        if not password:
            log_event(
                self.logger,
                "server_sync_skipped",
                reason="missing_password_env_var",
                password_env_var=self.config.server_password_env_var,
            )
            self.next_attempt_after = now + self.config.server_upload_retry_seconds
            return False

        transport = None
        sftp = None
        try:
            transport = paramiko.Transport((self.config.server_host, self.config.server_port))
            transport.banner_timeout = self.config.server_connect_timeout_seconds
            transport.connect(username=self.config.server_username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            remote_dir = f"{self.config.server_remote_root}/{self.config.computer_name}"
            ensure_remote_dir(sftp, remote_dir)
            remote_file = f"{remote_dir}/{self.config.computer_name}_ip_monitor.log"
            sftp.put(str(self.config.log_file), remote_file)
            log_event(
                self.logger,
                "server_sync_success",
                remote_file=remote_file,
                file_size_bytes=self.config.log_file.stat().st_size,
            )
            self.next_attempt_after = 0.0
            return True
        except (OSError, paramiko.SSHException, socket.error) as exc:
            log_event(
                self.logger,
                "server_sync_failed",
                error=str(exc),
                retry_in_seconds=self.config.server_upload_retry_seconds,
            )
            self.next_attempt_after = now + self.config.server_upload_retry_seconds
            return False
        finally:
            if sftp is not None:
                sftp.close()
            if transport is not None:
                transport.close()


def ensure_remote_dir(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    current = ""
    for part in remote_dir.split("/"):
        if not part:
            current = "/"
            continue
        if current in ("", "/"):
            current = f"/{part}" if current == "/" else part
        else:
            current = f"{current}/{part}"
        try:
            sftp.stat(current)
        except OSError:
            sftp.mkdir(current)


def get_public_ip(config: AgentConfig) -> str | None:
    for source in config.public_ip_sources:
        try:
            response = requests.get(source, timeout=10)
            response.raise_for_status()
            value = response.text.strip()
            if value:
                return value
        except requests.RequestException:
            continue
    return None


def collect_resource_usage() -> tuple[float, float]:
    cpu_percent = psutil.cpu_percent(interval=1.0)
    ram_percent = psutil.virtual_memory().percent
    return cpu_percent, ram_percent


def target_process_names(monitor_edge: bool) -> list[str]:
    names = ["chrome.exe", "chromium.exe"]
    if monitor_edge:
        names.append("msedge.exe")
    return names


def close_browsers_if_needed(process_names: list[str]) -> list[str]:
    active_names: set[str] = set()
    for proc in psutil.process_iter(["name"]):
        name = (proc.info.get("name") or "").lower()
        if name in process_names:
            active_names.add(name)

    closed: list[str] = []
    for process_name in sorted(active_names):
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", process_name],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                closed.append(process_name)
        except OSError:
            continue
    return closed


def main() -> int:
    try:
        config = load_config()
    except (ConfigError, json.JSONDecodeError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    logger = setup_logging(config.log_file)
    sync = ServerSync(config, logger)

    log_event(
        logger,
        "agent_started",
        computer_name=config.computer_name,
        host_name=os.environ.get("COMPUTERNAME") or socket.gethostname(),
        scheduled_task_name=config.scheduled_task_name,
    )

    next_ip_check_at = 0.0
    next_resource_check_at = 0.0
    last_public_ip = None
    critical_count = 0

    watched_process_names = [name.lower() for name in target_process_names(config.monitor_edge)]

    while True:
        now = time.monotonic()

        if now >= next_resource_check_at:
            cpu_percent, ram_percent = collect_resource_usage()
            cpu_critical = cpu_percent >= config.cpu_critical_percent
            ram_critical = ram_percent >= config.ram_critical_percent
            threshold_reached = cpu_critical or ram_critical

            if threshold_reached:
                critical_count += 1
            else:
                critical_count = 0

            closed_processes: list[str] = []
            browser_closed = False
            critical_count_for_log = critical_count
            if threshold_reached and critical_count >= config.critical_count_before_action:
                if os.name == "nt":
                    closed_processes = close_browsers_if_needed(watched_process_names)
                    browser_closed = bool(closed_processes)
                critical_count_for_log = critical_count
                critical_count = 0

            log_event(
                logger,
                "resource_check",
                cpu_usage_percent=cpu_percent,
                ram_usage_percent=ram_percent,
                cpu_threshold_reached=cpu_critical,
                ram_threshold_reached=ram_critical,
                threshold_reached=threshold_reached,
                critical_count=critical_count_for_log,
                browser_closed=browser_closed,
                closed_process_names=closed_processes,
            )
            next_resource_check_at = now + config.resource_check_interval_seconds
            if browser_closed:
                sync.sync_log()

        if now >= next_ip_check_at:
            public_ip = get_public_ip(config)
            if public_ip:
                changed = public_ip != last_public_ip
                log_event(
                    logger,
                    "public_ip_check",
                    public_ip=public_ip,
                    changed=changed,
                    previous_public_ip=last_public_ip,
                )
                last_public_ip = public_ip
            else:
                log_event(
                    logger,
                    "public_ip_check_failed",
                    error="Unable to fetch public IP from configured sources",
                )
            next_ip_check_at = now + config.public_ip_check_interval_seconds
            sync.sync_log()

        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
