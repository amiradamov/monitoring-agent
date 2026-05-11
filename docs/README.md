# Monitoring Agent

This package is a portable Windows 11 monitoring folder that can be zipped, copied to each computer, and installed locally.

The agent handles:

- Public IP checks every 10 minutes by default
- CPU and RAM checks every 1 minute by default
- Critical resource protection by closing configured Chromium-based browsers only after repeated threshold breaches
- Local log writing per computer
- Server log upload over SFTP/SSH with retry logic
- Startup persistence through Windows Task Scheduler

Folder layout:

```text
monitoring-agent/
  config/
    config.example.json
    config.json
  docs/
    README.md
    WINDOWS_SETUP.md
    SERVER_SETUP.md
    VPN_SETUP.md
    TROUBLESHOOTING.md
  logs/
  scripts/
    install.ps1
    monitor_agent.py
    run_hidden.vbs
    uninstall.ps1
  requirements.txt
```

Read these docs in order:

1. `WINDOWS_SETUP.md` for install steps on each PC
2. `SERVER_SETUP.md` for remote log destination expectations
3. `VPN_SETUP.md` if the machines use your WireGuard VPN
4. `TROUBLESHOOTING.md` for checks and recovery steps
