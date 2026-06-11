# Ensure dependencies are installed, then run BLAKE2 known-answer self-tests.

$repoRoot = Split-Path $PSScriptRoot -Parent

# --- scoop ---
if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Write-Error "scoop is required but not installed. Install it from https://scoop.sh then re-run this script."
    exit 1
}

# --- make ---
if (-not (Get-Command make -ErrorAction SilentlyContinue)) {
    Write-Host "Installing make..."
    scoop install make
}

# --- gcc (mingw) ---
$mingwBin = "$env:USERPROFILE\scoop\apps\mingw\current\bin"
if (-not (Test-Path "$mingwBin\gcc.exe")) {
    Write-Host "Installing mingw..."
    scoop install mingw
}
$env:PATH = "$mingwBin;$env:PATH"

# --- test ---
Set-Location $repoRoot
make -C sse check
