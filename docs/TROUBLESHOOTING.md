# Troubleshooting

## The scheduled task exists but logs do not update

Check:

1. Python is installed and available as `py` or `python`
2. `config\config.json` contains a real `computer_name`
3. The password environment variable exists for the same Windows user who owns the scheduled task
4. The package folder still exists in the same location

Useful commands:

```powershell
Get-ScheduledTask -TaskName IPMonitor_<computer_name>
[Environment]::GetEnvironmentVariable("IPMON_SERVER_PASSWORD","User")
Get-Content .\logs\<computer_name>_ip_monitor.log -Tail 30
```

## Server sync keeps failing

Review the local log for `server_sync_failed`.

Common causes:

- Wrong `server.username`
- Wrong password stored in the environment variable
- SSH/SFTP service unavailable on the server
- Firewall or VPN connectivity issue
- `server.remote_root` points to a directory the user cannot write to

## Resource threshold logs are too noisy

Adjust these settings in `config\config.json`:

- `cpu_critical_percent`
- `ram_critical_percent`
- `critical_count_before_action`
- `resource_check_interval_seconds`
- `resource_top_process_count`

Example:

- `cpu_critical_percent = 95`
- `ram_critical_percent = 95`
- `critical_count_before_action = 5`
- `resource_top_process_count = 5`

This makes threshold logging less sensitive because it requires more repeated high-usage checks before the critical counter resets.

## How resource monitoring works

The agent checks resource usage on the configured interval.

It records critical resource pressure when:

1. CPU or RAM is at or above the critical threshold
2. That critical condition happens for the configured number of checks in a row

Every resource check logs:

- timestamp
- CPU usage
- RAM usage
- whether threshold was reached
- top memory-heavy processes when CPU or RAM is over a configured threshold

Public IP checks also log:

- current public IP
- whether the public IP changed since the previous check
- when the current public IP was first observed
- how long the previous public IP lasted when a change is detected

Agent startup also logs:

- Windows host name
- scheduled task name
- system boot time
- system uptime

## Reinstall after config changes

Most config changes only require restarting the scheduled task.

If you changed only thresholds:

```powershell
Stop-ScheduledTask -TaskName IPMonitor_<computer_name>
Start-ScheduledTask -TaskName IPMonitor_<computer_name>
```

If the scheduled task is broken, run `scripts\uninstall.ps1` and then `scripts\install.ps1` again.

## Register-ScheduledTask says Access is denied

This usually means the task was being created with privileges or triggers that your current PowerShell session cannot register.

Current installer behavior:

- Normal PowerShell session:
  - Creates a per-user task that runs at logon
- Elevated PowerShell session:
  - Creates the same per-user logon task and also adds an at-startup trigger

If you already saw `Access is denied`, use one of these paths:

1. Rerun `install.ps1` in a normal non-admin PowerShell window with the updated installer
2. If you require a startup trigger before logon, rerun `install.ps1` in PowerShell as Administrator

If a failed attempt left partial state behind, run `scripts\uninstall.ps1` first and then install again.
