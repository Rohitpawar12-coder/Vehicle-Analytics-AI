$ErrorActionPreference = "Stop"
Write-Host "Setting up Vehicle Analytics CPU prototype..." -ForegroundColor Cyan
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' not found. Install Python and select Add Python to PATH."
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js not found. Install Node.js, then reopen PowerShell."
}
if (-not (Test-Path ".venv")) {
    py -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
Push-Location frontend
npm install
Pop-Location
Write-Host "`nSetup complete." -ForegroundColor Green
Write-Host "Terminal 1: .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload"
Write-Host "Terminal 2: cd frontend ; npm run dev"
