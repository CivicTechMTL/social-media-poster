# Set up the project and activate its virtual environment in the current PowerShell session.
#
#   . .\setup.ps1
#
# Safe to re-run: it reuses .venv and only installs what's missing or out of date.
# If scripts are blocked, allow them for this session first:
#   Set-ExecutionPolicy -Scope Process Bypass

function Invoke-CtmtlSetup {
    $root = $PSScriptRoot

    # 1. Find a Python 3.10+ to build the venv with.
    $py = $null
    foreach ($cand in @("py", "python", "python3")) {
        if (Get-Command $cand -ErrorAction SilentlyContinue) {
            & $cand -c "import sys; sys.exit(sys.version_info < (3, 10))" 2>$null
            if ($LASTEXITCODE -eq 0) { $py = $cand; break }
        }
    }

    # 2. Create .venv if it doesn't exist.
    $venv = Join-Path $root ".venv"
    if (-not (Test-Path $venv)) {
        if (-not $py) {
            Write-Error "Python 3.10 or newer is required (https://www.python.org/downloads/)."
            return
        }
        Write-Host "-> Creating .venv with $(& $py --version)"
        & $py -m venv $venv
        if ($LASTEXITCODE -ne 0) { return }
    }

    # 3. Activate it (Scripts\ on Windows, bin/ with PowerShell on macOS/Linux).
    $activate = @("Scripts/Activate.ps1", "bin/Activate.ps1") |
        ForEach-Object { Join-Path $venv $_ } | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $activate) {
        Write-Error "Couldn't find Activate.ps1 in .venv. Delete .venv and run this again."
        return
    }
    . $activate

    # 4. Python packages, then the headless Chromium used to render the images.
    Write-Host "-> Installing Python packages"
    python -m pip install --quiet --upgrade pip
    if ($LASTEXITCODE -ne 0) { return }
    python -m pip install --quiet -r (Join-Path $root "requirements.txt")
    if ($LASTEXITCODE -ne 0) { return }
    Write-Host "-> Installing Chromium for Playwright"
    python -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { return }

    # 5. .env for Bluesky credentials.
    $envFile = Join-Path $root ".env"
    if (-not (Test-Path $envFile)) {
        Copy-Item (Join-Path $root ".env.example") $envFile
        Write-Host "-> Created .env from .env.example. Fill in BLUESKY_HANDLE and BLUESKY_APP_PASSWORD to post."
    }

    Write-Host "Ready. The .venv is active in this session; try: poe render data/100 (or poe to list tasks)"
}

# Being run (not dot-sourced) would set up everything but leave the venv inactive afterwards.
if ($MyInvocation.InvocationName -ne ".") {
    Write-Warning "Run this as '. .\setup.ps1' so the venv stays active in your session."
}

Invoke-CtmtlSetup
Remove-Item Function:\Invoke-CtmtlSetup
