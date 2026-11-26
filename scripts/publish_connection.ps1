param([Parameter(Mandatory=$true)][string]$ServerAddress,[string]$Repository='niraaah/GoodMorNing')
$ErrorActionPreference='Stop'
$address=[Uri]$ServerAddress
if($address.Scheme -ne 'https' -or $address.UserInfo -or $address.Query -or $address.Fragment -or $address.AbsolutePath -ne '/'){
  throw 'Expected a public HTTPS server origin, without credentials.'
}
$publicOrigin=$address.GetLeftPart([System.UriPartial]::Authority)
& gh variable set GPU_API_URL --repo $Repository --body $publicOrigin
if($LASTEXITCODE -ne 0){throw 'Could not update the Pages GPU server address. Check gh authentication.'}
& gh workflow run pages.yml --repo $Repository --ref main
if($LASTEXITCODE -ne 0){throw 'Could not trigger the Pages configuration deployment.'}
Write-Output 'GPU server address updated. Pages redeployment is in progress.'
