# Windows Setup

## 1. Unzip the package

1. Copy the `monitoring-agent` folder or a `.zip` created from it to the Windows 11 computer.
2. Extract it to a stable location, for example:
   - `C:\Tools\monitoring-agent`
3. Do not place it in a temporary downloads folder if you want the scheduled task to keep working.

## 2. Review or edit config

The installer creates `config\config.json` from `config\config.example.json`.

Important fields:

- `computer_name`
  - Must be unique on every computer.
  - Examples: `user_1`, `user_2`, `laptop_1`, `workstation_3`
- `cpu_critical_percent`
- `ram_critical_percent`
- `resource_check_interval_seconds`
- `critical_count_before_action`
- `monitor_edge`

You can either:

1. Let `install.ps1` generate `config.json` and then edit it later, or
2. Edit `config.example.json` before running the installer if you want different defaults for all machines.

## 3. Install Python

Install Python 3.11 or newer and make sure either `py` or `python` works in PowerShell.

## 4. Run installer

Open PowerShell as the target Windows user, then run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
cd C:\Tools\monitoring-agent\scripts
.\install.ps1
```

The installer will:

1. Ask for a unique computer/user name
2. Ask for the server password securely
3. Store the password in the user environment variable named in config, default `IPMON_SERVER_PASSWORD`
4. Create `config\config.json`
5. Install Python dependencies from `requirements.txt`
6. Create the `logs` folder
7. Create a Windows Scheduled Task named `IPMonitor_<computer_name>`
8. Configure the task to run at user logon and restart if it fails
9. If PowerShell is running as Administrator, also add a system startup trigger
9. Launch the monitoring agent silently in the background

Why this matters:

- A plain user session can usually create a per-user logon task without trouble.
- A true startup trigger often requires elevated rights.
- If you need the task to start before anyone logs in, run the installer from an elevated PowerShell window.

## 5. Confirm it is running

Check Task Scheduler:

- Open Task Scheduler
- Look for `IPMonitor_<computer_name>`
- Confirm the task exists and that the last run time updates after logon

Check local logs:

- Log path:
  - `logs\<computer_name>_ip_monitor.log`
- Example:
  - `logs\user_1_ip_monitor.log`

Each line is JSON with timestamped events such as:

- agent startup
- public IP checks
- resource checks
- server sync success/failure
- browser close actions

## 6. Change thresholds later

Edit `config\config.json` and change any of these values:

- `cpu_critical_percent`
- `ram_critical_percent`
- `resource_check_interval_seconds`
- `critical_count_before_action`
- `monitor_edge`

After saving, restart the scheduled task or reboot the PC.

## 7. Uninstall

Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
cd C:\Tools\monitoring-agent\scripts
.\uninstall.ps1
```

The uninstaller stops and removes the scheduled task and asks whether local logs should be deleted.
