# ==========================================================
# Icebrew Windows Uninstaller
# ==========================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "          ICEBREW UNINSTALLER"
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------------
# 1. Define installation directory
# ----------------------------------------------------------

$InstallDir = Join-Path $env:LOCALAPPDATA "Icebrew"
$VenvDir = Join-Path $InstallDir "venv"
$VenvScripts = Join-Path $VenvDir "Scripts"

# ----------------------------------------------------------
# 2. Check installation
# ----------------------------------------------------------

if (-not (Test-Path $InstallDir)) {

    Write-Host "[INFO] Icebrew installation was not found."
    exit 0

}

Write-Host "[INFO] Installation detected: $InstallDir"

# ----------------------------------------------------------
# 3. Remove Icebrew from user PATH
# ----------------------------------------------------------

$UserPath = [Environment]::GetEnvironmentVariable(
    "Path",
    "User"
)

if ($UserPath) {

    $PathEntries = $UserPath -split ";"

    $FilteredPath = $PathEntries | Where-Object {
        $_.TrimEnd("\") -ne $VenvScripts.TrimEnd("\")
    }

    $NewUserPath = $FilteredPath -join ";"

    [Environment]::SetEnvironmentVariable(
        "Path",
        $NewUserPath,
        "User"
    )

    Write-Host "[OK] Icebrew PATH entry removed." -ForegroundColor Green

}
else {

    Write-Host "[INFO] User PATH was empty."

}

# ----------------------------------------------------------
# 4. Remove managed installation
# ----------------------------------------------------------

Write-Host "[INFO] Removing Icebrew installation..."

Remove-Item `
    -Path $InstallDir `
    -Recurse `
    -Force

# ----------------------------------------------------------
# 5. Verify removal
# ----------------------------------------------------------

if (Test-Path $InstallDir) {

    throw "Uninstallation verification failed."

}

Write-Host "[OK] Installation directory removed." -ForegroundColor Green

# ----------------------------------------------------------
# 6. Completion
# ----------------------------------------------------------

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "       ICEBREW UNINSTALLED"
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Icebrew has been removed from this system."
Write-Host "Your external files and datasets were not touched."
Write-Host ""
