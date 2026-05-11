$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Split-Path -Parent $scriptDir
$configPath = Join-Path $baseDir "config\config.json"
$logsDir = Join-Path $baseDir "logs"

if (-not (Test-Path $configPath)) {
    throw "Config file not found: $configPath"
}

$config = Get-Content -Raw -Path $configPath | ConvertFrom-Json
$computerName = $config.computer_name
if ([string]::IsNullOrWhiteSpace($computerName)) {
    throw "computer_name is missing from config.json"
}

$taskName = "IPMonitor_$computerName"

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    try {
        Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    }
    catch {
    }

    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed scheduled task: $taskName"
}
else {
    Write-Host "Scheduled task not found: $taskName"
}

$deleteLogs = Read-Host "Delete local logs from $logsDir ? Type YES to confirm"
if ($deleteLogs -eq "YES" -and (Test-Path $logsDir)) {
    Remove-Item -Path (Join-Path $logsDir "*") -Force -ErrorAction SilentlyContinue
    Write-Host "Local logs deleted."
}
else {
    Write-Host "Local logs kept."
}
