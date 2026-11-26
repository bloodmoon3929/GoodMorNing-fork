$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$target=Join-Path $projectRoot 'tools/gitleaks'
New-Item -ItemType Directory -Path $target -Force | Out-Null
$archive=Join-Path $target 'gitleaks.zip'
Invoke-WebRequest 'https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_windows_x64.zip' -OutFile $archive
if((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLower() -ne 'd29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e'){
  throw 'Gitleaks checksum mismatch. Hook installation stopped.'
}
Expand-Archive -LiteralPath $archive -DestinationPath $target -Force
& git -C $projectRoot config --local core.hooksPath .githooks
if($LASTEXITCODE -ne 0){throw 'Could not install the repository pre-commit hook.'}
Write-Output 'Local credential and Gitleaks checks are enabled before each commit.'
