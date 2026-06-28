# dev.ps1 — Start both JobFit servers in separate terminal windows (Windows / PowerShell)
#
# Usage: .\dev.ps1
#
# Requirements:
#   - Python 3.10+ with FastAPI and uvicorn installed (see backend/requirements.txt)
#   - Node 20+ with dependencies installed (run `npm install` once inside frontend/)

$root = $PSScriptRoot

# Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

# Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "JobFit dev servers starting:"
Write-Host "  Backend  ->  http://localhost:8000"
Write-Host "  Frontend ->  http://localhost:5173"
Write-Host ""
Write-Host "Health check: http://localhost:8000/health"
