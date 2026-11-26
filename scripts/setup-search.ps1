$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
if(-not(Test-Path -LiteralPath '.venv-search/Scripts/python.exe')){
  & '.venv/Scripts/python.exe' -m venv .venv-search
  if($LASTEXITCODE -ne 0){throw 'Search environment creation failed.'}
}
& '.venv-search/Scripts/python.exe' -m pip install -r server/requirements-search.txt
if($LASTEXITCODE -ne 0){throw 'Search dependency installation failed.'}
& '.venv-search/Scripts/python.exe' -m playwright install chromium
if($LASTEXITCODE -ne 0){throw 'Crawler browser installation failed.'}
& '.venv-search/Scripts/python.exe' scripts/setup_search.py
if($LASTEXITCODE -ne 0){throw 'EmbeddingGemma model download failed.'}
if(-not(Test-Path -LiteralPath 'data/search.local.json')){
  Copy-Item -LiteralPath 'server/goods/search.example.json' -Destination 'data/search.local.json'
}
Write-Output 'Search ready. Put Coupang API keys only in data/search.local.json (excluded from Git).'
