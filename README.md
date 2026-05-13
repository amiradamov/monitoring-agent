# Monitoring Agent

Portable Windows monitoring agent for checking public IP and local CPU/RAM usage, writing JSON-line logs locally, and uploading logs to a remote server over SFTP/SSH.

## What It Does

- Checks public IP on a configurable interval.
- Checks CPU and RAM usage on a configurable interval.
- Logs events locally per computer.
- Uploads each computer's log file to a remote server over SFTP.
- Can close configured Chromium-based browsers after repeated critical resource usage.
- Installs as a Windows Scheduled Task for startup/logon persistence.

## Quick Start

Install Python 3.11 or newer, then run PowerShell from the target Windows user account:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
cd C:\Tools\monitoring-agent\scripts
.\install.ps1
```

The installer creates `config/config.json` from `config/config.example.json`, installs Python dependencies, stores the server password in a user environment variable, creates the scheduled task, and starts the agent.

## Documentation

Read these in order:

1. [`docs/WINDOWS_SETUP.md`](docs/WINDOWS_SETUP.md)
2. [`docs/SERVER_SETUP.md`](docs/SERVER_SETUP.md)
3. [`docs/VPN_SETUP.md`](docs/VPN_SETUP.md)
4. [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)

## Security

Do not commit local runtime config, logs, passwords, SSH keys, WireGuard private keys, or Telegram bot tokens. Keep real deployment values in `config/config.json` on each machine.

`config/config.json` is intentionally ignored by git.
