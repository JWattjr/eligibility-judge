$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$steps=@('deploy','prepare','probe','seed-1','judge-1','disputes-1','seed-2','judge-2','disputes-2','create-series')
foreach($stage in $steps){
 do {
  Write-Output ('Running final-demo stage: '+$stage)
  & powershell -ExecutionPolicy Bypass -File scripts/milestone.ps1 $stage
  $result=Get-Content -LiteralPath deploy/milestone-proof.json -Raw | ConvertFrom-Json
  if($result.stopReason){throw ('Final run stopped: '+$result.stopReason)}
  if($result.stages.$stage.status -eq 'WAITING_RECEIPT'){
   Write-Output 'Continuing receipt reads from the same saved hashes; no failed call is replayed.'
   Start-Sleep -Seconds 10
  } elseif($LASTEXITCODE -ne 0 -or $result.stages.$stage.status -ne 'PASS'){
   throw ('Stage did not pass: '+$stage)
  }
 } while($result.stages.$stage.status -eq 'WAITING_RECEIPT')
}
while([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() -lt $result.endsAt){
 $remaining=$result.endsAt-[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
 Write-Output ('Waiting for the real credential window: '+[Math]::Ceiling($remaining/60)+' minutes remain.')
 Start-Sleep -Seconds ([Math]::Min(30,$remaining))
}
& powershell -ExecutionPolicy Bypass -File scripts/milestone.ps1 complete
if($LASTEXITCODE -ne 0){throw 'Final completion did not pass; retain the journal and receipts.'}
