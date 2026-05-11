# AGENTS.md

Guidance for coding agents working in this repository. The closest `AGENTS.md` wins if nested files are added later.

## Project Overview

This repo contains a portable Windows monitoring agent. It checks public IP and local CPU/RAM usage, writes JSON-line logs locally, and uploads logs to a remote server over SFTP/SSH. Installation and persistence are handled by PowerShell scripts and Windows Task Scheduler.

This is not currently a pnpm/Turbo monorepo. No `package.json`, `pnpm-workspace.yaml`, `turbo.json`, TypeScript config, ESLint/Prettier config, or GitHub Actions workflow was found during setup.

## Repo Structure

- `scripts/monitor_agent.py`: main Python monitoring process.
- `scripts/install.ps1`: Windows installer; creates config, installs Python deps, stores server password in a user env var, registers the scheduled task, and starts it.
- `scripts/uninstall.ps1`: removes the scheduled task and optionally local logs.
- `scripts/run_hidden.vbs`: launches the Python agent without a visible console.
- `config/config.example.json`: default runtime config template.
- `config/config.json`: local runtime config; may contain deployment-specific host/user settings.
- `docs/`: setup, server, VPN, and troubleshooting notes.
- `requirements.txt`: Python runtime dependencies.

## Setup

Use Windows PowerShell with Python 3.11 or newer available as `py` or `python`.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
cd C:\Tools\monitoring-agent\scripts
.\install.ps1
```

For local dependency installation without registering the scheduled task:

```powershell
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
```

No JavaScript dependencies are currently present. Do not run `pnpm install` unless a future package is added.

## Build, Dev, And Run Commands

- Install agent on a Windows machine: `.\scripts\install.ps1`
- Uninstall agent: `.\scripts\uninstall.ps1`
- Run the agent directly for debugging: `py -3 .\scripts\monitor_agent.py`
- Tail local logs: `Get-Content .\logs\<computer_name>_ip_monitor.log -Tail 30`
- Restart scheduled task after config changes:

```powershell
Stop-ScheduledTask -TaskName IPMonitor_<computer_name>
Start-ScheduledTask -TaskName IPMonitor_<computer_name>
```

There is no build step at present.

## Monorepo And Package Navigation

Current repo shape is a single package/folder, not a monorepo.

If this repo later becomes a pnpm/Turbo monorepo:

- Confirm package names from each package's own `package.json` `name` field.
- Use `pnpm dlx turbo run where <project_name>` to locate packages.
- Install root deps with `pnpm install`.
- Install package-specific deps with `pnpm install --filter <project_name>`.
- Create a new React + Vite TS package with `pnpm create vite@latest <project_name> -- --template react-ts`.
- Run package tests with `pnpm turbo run test --filter <project_name>`.
- Run package lint after moving files/imports with `pnpm lint --filter <project_name>`.

Nested `AGENTS.md` files are not needed yet. Consider adding them only if future packages develop distinct setup, test, or style rules.

## Code Style

- Keep changes small and operationally conservative; this agent runs on Windows machines at startup/logon.
- Preserve the existing Python style: type hints, dataclasses, `pathlib`, explicit config validation, and JSON-line logging.
- Prefer functional patterns and small pure helpers where practical.
- Avoid hardcoding secrets; read secrets from environment variables or config indirection.
- For any future TypeScript code: use strict mode, single quotes, no semicolons, and functional patterns where possible.
- For PowerShell, keep scripts idempotent where possible and fail fast with `$ErrorActionPreference = "Stop"`.

## Testing

No automated test suite was found.

Recommended manual checks after changes:

```powershell
py -3 -m py_compile .\scripts\monitor_agent.py
py -3 .\scripts\monitor_agent.py
```

The direct run requires a valid `config/config.json` and may attempt public IP lookups and SFTP upload. For safer changes, prefer adding unit tests around pure functions before changing runtime behavior.

If a future pnpm package is added:

- From package root: `pnpm test`
- Focus one Vitest test: `pnpm vitest run -t "<test name>"`
- Before commit: `pnpm lint` and `pnpm test`

## CI Notes

No `.github/workflows` directory was found. There is no known CI gate today.

Recommended future CI:

- Python syntax check with `py_compile`.
- Unit tests once a test suite exists.
- Secret scanning for config and docs.
- Optional PowerShell script analysis for installer changes.

## Security Considerations

- Never commit server passwords or private keys.
- The installer stores the server password in the Windows user environment variable named by `server.password_env_var`, default `IPMON_SERVER_PASSWORD`.
- Treat `config/config.json` as deployment-specific; avoid adding sensitive hostnames, usernames, or internal IPs unless required.
- Be careful editing `docs/VPN_SETUP.md`, server addresses, SSH usernames, remote paths, and WireGuard details.
- `monitor_agent.py` can close browser processes under configured resource pressure; review threshold and process-name changes carefully.
- SFTP upload paths are built from config and `computer_name`; preserve validation when changing config handling.

## PR Rules

- Title format: `[<project_name>] <Title>`. For the current repo, use `[monitoring-agent] <Title>`.
- Always run lint and tests before committing when those commands exist.
- Today, at minimum run `py -3 -m py_compile .\scripts\monitor_agent.py` before committing Python changes.
- Update docs when installer behavior, config fields, scheduled task behavior, server upload paths, or troubleshooting steps change.

## Known Issues And Missing Info

- No automated tests are present.
- No lint, formatter, `pyproject.toml`, or PowerShell analyzer config was found.
- No CI workflow was found.
- No package manager lockfile is present for Python dependencies.
- `config/config.json` exists in the repo and may contain environment-specific values.

## Recommended Next Steps

- Add focused unit tests for config loading, target process selection, remote path construction, and retry behavior.
- Add a lightweight Python lint/format config.
- Add CI for syntax checks and future tests.
- Consider documenting which config values are safe defaults versus per-machine deployment values.
