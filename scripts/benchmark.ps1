# Ensure Python is available, then run the BLAKE2 benchmark.

$repoRoot = Split-Path $PSScriptRoot -Parent

# --- python ---
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Install it from https://www.python.org/downloads/ or via 'scoop install python', then re-run this script."
    exit 1
}

# --- benchmark ---
Set-Location $repoRoot
python run_benchmark.py
