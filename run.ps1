Set-Location $PSScriptRoot
docker info *> $null
if ($LASTEXITCODE -eq 0) {
    docker compose build -q
    docker compose run --rm rq2
} else {
    Write-Host "Docker not running - using local Python instead."
    if (-not (Test-Path .venv)) { python -m venv .venv }
    .\.venv\Scripts\python -m pip install -q -r requirements.txt
    .\.venv\Scripts\python src\main.py
}
Read-Host "Done"
