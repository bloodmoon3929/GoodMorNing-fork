$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location (Join-Path $projectRoot 'app')
& (Join-Path $projectRoot 'tools\flutter\bin\flutter.bat') pub get
if ($LASTEXITCODE -ne 0) { throw 'Flutter dependency resolution failed.' }
& (Join-Path $projectRoot 'tools\flutter\bin\flutter.bat') build web --release
if ($LASTEXITCODE -ne 0) { throw 'Flutter build failed.' }
