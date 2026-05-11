# Server Setup

## What the agent sends

Each computer writes to its own local log file and uploads that log file to the server over SFTP.

By default:

- Local log:
  - `logs\<computer_name>_ip_monitor.log`
- Remote directory:
  - `/root/monitoring/ip_logs/<computer_name>/`
- Remote log file:
  - `/root/monitoring/ip_logs/<computer_name>/<computer_name>_ip_monitor.log`

If you use a different server account, edit `config\config.json`:

- `server.username`
- `server.remote_root`

## Password handling

The server password is not hardcoded in the Python script.

Default approach:

- The installer stores it in the Windows user environment variable:
  - `IPMON_SERVER_PASSWORD`

The code reads the password from the environment variable named in:

- `server.password_env_var`

If you prefer another secret storage method, keep the code unchanged and make sure that environment variable is populated before the scheduled task starts.

## Server prerequisites

1. SSH/SFTP access must be enabled on the server.
2. The configured user must have permission to create and write under `server.remote_root`.
3. Port `22` must be reachable from the Windows machines, directly or through VPN.

## Verify server logs

After install, connect to the server and check:

```bash
ls -la /root/monitoring/ip_logs
ls -la /root/monitoring/ip_logs/<computer_name>
tail -n 20 /root/monitoring/ip_logs/<computer_name>/<computer_name>_ip_monitor.log
```

If the directory or file does not appear, check the local log for `server_sync_failed` entries.
