param([ValidateSet('preview','recover')][string]$Step='preview')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$previousNodeOptions=$env:NODE_OPTIONS
$previousStep=$env:ELIGIBILITY_PRIOR_POOL_RECOVERY
$previousMilestone=$env:ELIGIBILITY_MILESTONE_STEP
$generated=Join-Path (Get-Location) 'deploy/deployScript.compiled.js'
if(Test-Path -LiteralPath $generated){Remove-Item -LiteralPath $generated}
try {
 $env:ELIGIBILITY_MILESTONE_STEP=$null
 $env:ELIGIBILITY_PRIOR_POOL_RECOVERY=$Step
 $env:NODE_OPTIONS=($previousNodeOptions+' --import=tsx --import=./scripts/milestone-rpc-budget.mjs').Trim()
 genlayer.cmd deploy
 if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
} finally {
 $env:NODE_OPTIONS=$previousNodeOptions
 $env:ELIGIBILITY_PRIOR_POOL_RECOVERY=$previousStep
 $env:ELIGIBILITY_MILESTONE_STEP=$previousMilestone
 if(Test-Path -LiteralPath $generated){Remove-Item -LiteralPath $generated}
}
