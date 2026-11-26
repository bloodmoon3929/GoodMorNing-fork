$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
& (Join-Path $projectRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'prepare_frontend.py')
if ($LASTEXITCODE -ne 0) { throw 'Static frontend preparation failed.' }
Set-Location (Join-Path $projectRoot 'app')
& (Join-Path $projectRoot 'tools\flutter\bin\flutter.bat') pub get
if ($LASTEXITCODE -ne 0) { throw 'Flutter dependency resolution failed.' }
& (Join-Path $projectRoot 'tools\flutter\bin\flutter.bat') build web --release
if ($LASTEXITCODE -ne 0) { throw 'Flutter build failed.' }
& (Join-Path $projectRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'finalize_web.py')
if ($LASTEXITCODE -ne 0) { throw 'Frontend versioning failed.' }
