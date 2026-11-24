# ==========================================================
# Icebrew Windows Installer
# ==========================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "          ICEBREW INSTALLER"
Write-Host "          Brew your experiments."
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------------
# 1. Locate the project root
# ----------------------------------------------------------

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..\..\").Path

Write-Host "[INFO] Project root: $ProjectRoot"

# ----------------------------------------------------------
# 2. Check Git
# ----------------------------------------------------------

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is not installed. Install Git for Windows before continuing."
}

Write-Host "[OK] Git detected." -ForegroundColor Green

# ----------------------------------------------------------
# 3. Check Python
# ----------------------------------------------------------

$PythonCommand = Get-Command python -ErrorAction SilentlyContinue

if (-not $PythonCommand) {
    $PythonCommand = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $PythonCommand) {
    throw "Python was not found. Install a compatible Python version."
}

$PythonExecutable = $PythonCommand.Source

Write-Host "[INFO] Python executable: $PythonExecutable"

# ----------------------------------------------------------
# 4. Validate Python version
# ----------------------------------------------------------

$PythonVersion = & $PythonExecutable -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"

$VersionParts = $PythonVersion.Split(".")
$Major = [int]$VersionParts[0]
$Minor = [int]$VersionParts[1]

if ($Major -ne 3 -or $Minor -lt 12 -or $Minor -ge 15) {
    throw "Icebrew requires Python 3.12, 3.13 or 3.14."
}

Write-Host "[OK] Python $PythonVersion detected." -ForegroundColor Green

# ----------------------------------------------------------
# 5. Define installation directory
# ----------------------------------------------------------

$InstallDir = Join-Path $env:LOCALAPPDATA "Icebrew"
$VenvDir = Join-Path $InstallDir "venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvScripts = Join-Path $VenvDir "Scripts"

# ----------------------------------------------------------
# 6. Create installation directory
# ----------------------------------------------------------

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

Write-Host "[INFO] Installation directory: $InstallDir"

# ----------------------------------------------------------
# 7. Create virtual environment
# ----------------------------------------------------------

if (-not (Test-Path $VenvPython)) {

    Write-Host "[INFO] Creating virtual environment..."

    & $PythonExecutable -m venv $VenvDir

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the virtual environment."
    }

}
else {

    Write-Host "[INFO] Existing virtual environment detected."
}

# ----------------------------------------------------------
# 8. Install Icebrew
# ----------------------------------------------------------

Write-Host "[INFO] Installing Icebrew..."

& $VenvPython -m pip install --upgrade pip

if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip."
}

& $VenvPython -m pip install $ProjectRoot

if ($LASTEXITCODE -ne 0) {
    throw "Icebrew installation failed."
}

# ----------------------------------------------------------
# 9. Add Icebrew to user PATH
# ----------------------------------------------------------

$UserPath = [Environment]::GetEnvironmentVariable(
    "Path",
    "User"
)

$PathEntries = @()

if ($UserPath) {
    $PathEntries = $UserPath -split ";"
}

if ($PathEntries -notcontains $VenvScripts) {

    $NewUserPath = if ($UserPath) {
        "$UserPath;$VenvScripts"
    }
    else {
        $VenvScripts
    }

    [Environment]::SetEnvironmentVariable(
        "Path",
        $NewUserPath,
        "User"
    )

    Write-Host "[INFO] Icebrew added to user PATH."
}
else {

    Write-Host "[INFO] Icebrew PATH entry already exists."
}

# ----------------------------------------------------------
# 10. Verify installation
# ----------------------------------------------------------

$IcebrewExecutable = Join-Path $VenvScripts "icebrew.exe"

if (-not (Test-Path $IcebrewExecutable)) {
    throw "Installation verification failed. icebrew.exe was not found."
}

& $IcebrewExecutable version

if ($LASTEXITCODE -ne 0) {
    throw "Icebrew verification failed."
}

# ----------------------------------------------------------
# 11. Completion
# ----------------------------------------------------------

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "       ICEBREW INSTALLED SUCCESSFULLY"
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Installation directory: $InstallDir"
Write-Host ""

Write-Host "Restart your terminal to use the PATH entry."
Write-Host "Then run:"
Write-Host "    icebrew --help"
Write-Host ""
