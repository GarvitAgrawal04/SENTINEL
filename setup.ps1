# Sentinel on Windows, one command:      .\setup.bat
# (setup.bat runs this file with the execution policy bypassed for this one process, so it works even where
#  "running scripts is disabled on this system". You can also run:  powershell -ExecutionPolicy Bypass -File setup.ps1)
#
#   .\setup.bat                 set everything up, then serve the web UI and API on http://127.0.0.1:8000
#   .\setup.bat -InstallOnly    set everything up and stop
#   .\setup.bat -Test           set everything up and run the test suite
#   .\setup.bat -Port 8001      use another port
#
# Needs only Python 3.10+ and Git. Written for Windows PowerShell 5.1 and newer (no PowerShell 7 syntax).
param([switch]$InstallOnly, [switch]$Test, [int]$Port = 0, [string]$BindHost = "")

$ErrorActionPreference = "Continue"          # native tools write progress to stderr; we check exit codes ourselves
Set-Location -Path $PSScriptRoot
function Say($m)  { Write-Host "==> $m" -ForegroundColor Cyan }
function Fail($m) { Write-Host "error: $m" -ForegroundColor Red; exit 1 }
$onWindows = ($env:OS -eq "Windows_NT")

# 1. find a Python that is new enough -----------------------------------------------------------------------------
$candidates = @()
if ($env:PYTHON) { $candidates += ,@($env:PYTHON) }
if ($onWindows)  { $candidates += ,@("py", "-3") }
$candidates += ,@("python")
$candidates += ,@("python3")
$py = $null
foreach ($c in $candidates) {
    if (-not (Get-Command $c[0] -ErrorAction SilentlyContinue)) { continue }
    $pre = @(); if ($c.Length -gt 1) { $pre = $c[1..($c.Length - 1)] }
    & $c[0] @pre -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $py = $c; break }
}
if (-not $py) { Fail "Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), open a NEW terminal, and run .\setup.bat again." }
$pyPre = @(); if ($py.Length -gt 1) { $pyPre = $py[1..($py.Length - 1)] }
$version = (& $py[0] @pyPre --version 2>&1 | Out-String).Trim()
Say "Using $version"

# 2. virtual environment ------------------------------------------------------------------------------------------
if ($onWindows) { $venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe" } else { $venvPy = Join-Path $PSScriptRoot ".venv/bin/python" }
if (-not (Test-Path $venvPy)) {
    Say "Creating the virtual environment in .venv"
    & $py[0] @pyPre -m venv .venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPy)) { Fail "could not create the virtual environment. Delete the .venv folder and try again." }
}

# 3. dependencies (pinned) ----------------------------------------------------------------------------------------
Say "Installing dependencies (first run takes a minute or two)"
& $venvPy -m pip install --quiet --disable-pip-version-check --upgrade pip
& $venvPy -m pip install --quiet --disable-pip-version-check -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { Fail "pip could not install the dependencies. Check your internet connection (or proxy) and run .\setup.bat again." }
& $venvPy -m pip install --quiet --disable-pip-version-check --no-deps -e .
if ($LASTEXITCODE -ne 0) { Fail "pip could not install Sentinel itself." }

# 4. .env ---------------------------------------------------------------------------------------------------------
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Say "Created .env from .env.example (nothing in it is required)"
}
foreach ($line in Get-Content ".env") {
    $line = $line.Trim()
    if ($line -eq "" -or $line.StartsWith("#") -or -not $line.Contains("=")) { continue }
    $key = $line.Substring(0, $line.IndexOf("=")).Trim()
    $value = $line.Substring($line.IndexOf("=") + 1).Trim()
    if ($key -notmatch '^[A-Za-z_][A-Za-z0-9_]*$' -or $value -eq "") { continue }
    if (-not [Environment]::GetEnvironmentVariable($key, "Process")) { [Environment]::SetEnvironmentVariable($key, $value, "Process") }
}

# 5. go -----------------------------------------------------------------------------------------------------------
Say "Self-test"
& $venvPy -m sentinel.cli selftest | Select-Object -Last 1
if ($LASTEXITCODE -ne 0) { Fail "the engine self-test failed." }

if ($onWindows) { $activate = ".venv\Scripts\Activate.ps1" } else { $activate = "source .venv/bin/activate" }
if ($InstallOnly) {
    Say "Done. To use the 'sentinel' command in this terminal:  $activate"
    Write-Host "    (if activation is blocked:  Set-ExecutionPolicy -Scope Process Bypass  , then activate again)"
    Write-Host "    or without activating:  .venv\Scripts\sentinel.exe scan ."
    exit 0
}
if ($Test) { & $venvPy -m pytest -q; exit $LASTEXITCODE }

if ($BindHost -eq "") { if ($env:HOST) { $BindHost = $env:HOST } else { $BindHost = "127.0.0.1" } }
if ($Port -eq 0)      { if ($env:PORT) { $Port = [int]$env:PORT } else { $Port = 8000 } }
$url = "http://${BindHost}:$Port"
Say "Open $url in your browser   (API reference: $url/docs, stop with Ctrl+C)"
Write-Host "    The 'sentinel' command: open a second terminal here and run  $activate"
& $venvPy -m uvicorn sentinel.api:app --host $BindHost --port $Port
exit $LASTEXITCODE
