$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
& (Join-Path $PSScriptRoot 'setup-security.ps1')
git submodule update --init --recursive
if($LASTEXITCODE -ne 0){throw 'Source repositories could not be initialized.'}
if(-not(Test-Path -LiteralPath 'tools\flutter\bin\flutter.bat')){
  New-Item -ItemType Directory -Path tools -Force | Out-Null
  git clone --depth 1 --branch stable https://github.com/flutter/flutter.git tools\flutter
  if($LASTEXITCODE -ne 0){throw 'Flutter SDK download failed.'}
}
& .\tools\flutter\bin\flutter.bat precache --web
if($LASTEXITCODE -ne 0){throw 'Flutter precache failed.'}
if(-not(Test-Path -LiteralPath '.venv\Scripts\python.exe')){
  python -m venv .venv
  if($LASTEXITCODE -ne 0){throw 'Python 3.12 must be installed and available as python.'}
}
& .\.venv\Scripts\python.exe -m pip install -r server\requirements-windows-lock.txt
if($LASTEXITCODE -ne 0){throw 'Python dependencies failed.'}
& .\scripts\setup-postgres.ps1
& .\.venv\Scripts\python.exe scripts\setup_models.py
if($LASTEXITCODE -ne 0){throw 'SAM 2 model download failed.'}
& .\scripts\build.ps1
