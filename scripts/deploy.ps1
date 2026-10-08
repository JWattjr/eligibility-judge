param([ValidateSet('probe','deploy','seed','entries','judge','settle','proof','diagnose','smoke','timeout-seed','timeout-entry','timeout-settle')][string]$Step='proof')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$env:ELIGIBILITY_STEP=$Step
$previousNodeOptions=$env:NODE_OPTIONS
$generated=Join-Path (Get-Location) 'deploy\deployScript.compiled.js'
if(Test-Path -LiteralPath $generated){Remove-Item -LiteralPath $generated}
try {
 $env:NODE_OPTIONS=($previousNodeOptions+' --import=tsx --import=./scripts/explicit-fees.mjs').Trim()
 genlayer.cmd deploy
} finally {
 $env:NODE_OPTIONS=$previousNodeOptions
 $generated=Join-Path (Get-Location) 'deploy\deployScript.compiled.js'
 if(Test-Path -LiteralPath $generated){Remove-Item -LiteralPath $generated}
}
