$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$result=Get-Content -LiteralPath deploy/milestone-proof.json -Raw | ConvertFrom-Json
if($result.run -ne 'milestone-v1-release' -or $result.stopReason){throw 'Use only the unchanged, successful release journal.'}
foreach($stage in @('deploy','prepare','probe','seed-1','judge-1','disputes-1','seed-2','judge-2','disputes-2','create-series')){
 if($result.stages.$stage.status -ne 'PASS'){throw ('Prerequisite stage is incomplete: '+$stage)}
}
if($result.completed -and $result.stages.complete.status -eq 'PASS'){
 Write-Output 'Final demo already complete; no writes.'
 exit 0
}
while([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() -lt $result.endsAt){
 $remaining=$result.endsAt-[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
 Write-Output ('Waiting for the real credential window: '+[Math]::Ceiling($remaining/60)+' minutes remain.')
 Start-Sleep -Seconds ([Math]::Min(30,$remaining))
}
do {
 & powershell -ExecutionPolicy Bypass -File scripts/milestone.ps1 complete
 $stepExit=$LASTEXITCODE
 $result=Get-Content -LiteralPath deploy/milestone-proof.json -Raw | ConvertFrom-Json
 if($result.stopReason){throw ('Final run stopped: '+$result.stopReason)}
 if($result.stages.complete.status -in @('WAITING_RECEIPT','WAITING_READ')){
  Write-Output 'Continuing reads of the same saved completion hashes.'
  Start-Sleep -Seconds 10
 } elseif($stepExit -ne 0 -or $result.stages.complete.status -ne 'PASS' -or !$result.completed){
  throw 'Final completion did not pass; retain the journal and receipts.'
 }
} while($result.stages.complete.status -in @('WAITING_RECEIPT','WAITING_READ'))
Write-Output 'Final demo completion PASS.'
