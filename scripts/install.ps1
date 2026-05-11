$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Split-Path -Parent $scriptDir
$configDir = Join-Path $baseDir "config"
$logsDir = Join-Path $baseDir "logs"
$configPath = Join-Path $configDir "config.json"
$exampleConfigPath = Join-Path $configDir "config.example.json"
$vbsPath = Join-Path $scriptDir "run_hidden.vbs"

function Test-IsAdministrator {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{
            Executable = "py"
            Arguments = @("-3")
        }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{
            Executable = "python"
            Arguments = @()
        }
    }

    throw "Python 3 was not found. Install Python 3.11+ and run this installer again."
}

function Set-JsonValue {
    param(
        [Parameter(Mandatory = $true)] [object] $Object,
        [Parameter(Mandatory = $true)] [string] $PropertyName,
        [Parameter(Mandatory = $true)] [object] $Value
    )

    if ($Object.PSObject.Properties.Name -contains $PropertyName) {
        $Object.$PropertyName = $Value
    }
    else {
        $Object | Add-Member -NotePropertyName $PropertyName -NotePropertyValue $Value
    }
}

if (-not (Test-Path $exampleConfigPath)) {
    throw "Missing config template at $exampleConfigPath"
}

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

$computerName = Read-Host "Enter a unique computer/user name (example: user_1, laptop_1, workstation_3)"
if ([string]::IsNullOrWhiteSpace($computerName)) {
    throw "Computer/user name is required."
}

$computerName = $computerName.Trim()
$taskName = "IPMonitor_$computerName"
$passwordEnvVar = "IPMON_SERVER_PASSWORD"

$serverPassword = Read-Host "Enter the server password to store in your user environment variable ($passwordEnvVar)" -AsSecureString
$passwordBstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($serverPassword)
try {
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordBstr)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordBstr)
}

if ([string]::IsNullOrWhiteSpace($plainPassword)) {
    throw "Server password is required."
}

[Environment]::SetEnvironmentVariable($passwordEnvVar, $plainPassword, "User")
Set-Item -Path "Env:$passwordEnvVar" -Value $plainPassword

$configContent = Get-Content -Raw -Path $exampleConfigPath | ConvertFrom-Json
Set-JsonValue -Object $configContent -PropertyName "computer_name" -Value $computerName
Set-JsonValue -Object $configContent.server -PropertyName "password_env_var" -Value $passwordEnvVar
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
    $configPath,
    ($configContent | ConvertTo-Json -Depth 8),
    $utf8NoBom
)

$pythonCommand = Get-PythonCommand
Write-Host "Installing Python dependencies..."
& $pythonCommand.Executable @($pythonCommand.Arguments + @("-m", "pip", "install", "--upgrade", "pip"))
& $pythonCommand.Executable @($pythonCommand.Arguments + @("-m", "pip", "install", "-r", (Join-Path $baseDir "requirements.txt")))

$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbsPath`""
$isAdministrator = Test-IsAdministrator
$triggers = @(
    New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
)
if ($isAdministrator) {
    $triggers += New-ScheduledTaskTrigger -AtStartup
}

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1)

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $triggers `
    -Principal $principal `
    -Settings $settings `
    -Description "Portable monitoring agent for public IP and Windows resource monitoring." `
    -ErrorAction Stop

$registeredTask = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
Start-ScheduledTask -TaskName $taskName -ErrorAction Stop

Write-Host ""
Write-Host "Install complete."
Write-Host "Computer name: $computerName"
Write-Host "Scheduled task: $taskName"
Write-Host "Config file: $configPath"
if ($isAdministrator) {
    Write-Host "Task triggers: At logon and at startup"
}
else {
    Write-Host "Task triggers: At logon"
    Write-Host "Note: Startup trigger was skipped because PowerShell was not running as Administrator."
}
