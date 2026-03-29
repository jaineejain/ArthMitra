# Run from repo root: ArthMitra\
Set-Location $PSScriptRoot\..\..
Write-Host "Starting FastAPI on http://127.0.0.1:8000 ..."
python -m uvicorn arthmitra.backend.main:app --reload --host 127.0.0.1 --port 8000
