param([switch]$TunnelOnly)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$names=if($TunnelOnly){@('tunnel')}else{@('tunnel','server')}
foreach($name in $names){
  $pidPath=Join-Path $projectRoot "logs\$name.pid"
  if(-not(Test-Path -LiteralPath $pidPath)){continue}
  $ownedId=[int](Get-Content -LiteralPath $pidPath)
  $process=Get-CimInstance Win32_Process -Filter "ProcessId=$ownedId"
  if(-not $process){continue}
  if(-not $process.CommandLine.Contains($projectRoot)){throw "PID $ownedId no longer belongs to this project."}
  if($name -eq 'server' -and -not $process.CommandLine.Contains('uvicorn')){throw 'Unexpected server process.'}
  if($name -eq 'tunnel' -and -not $process.CommandLine.Contains('cloudflared')){throw 'Unexpected tunnel process.'}
  Stop-Process -Id $ownedId
  Write-Output "Stopped $name ($ownedId)"
}
