"""Preserve the stopped run exactly, then initialize the separately authorized run."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / 'deploy/previous-runs/milestone-v1-clean-stopped'
proof_path = ROOT / 'deploy/milestone-proof.json'
old = json.loads(proof_path.read_text())
recovery = json.loads((ROOT / 'deploy/milestone-recovery.json').read_text())
verification = json.loads((ROOT / 'deploy/milestone-recovery-verification.json').read_text())
assert old['run'] == 'milestone-v1-clean' and old['stopReason'] and not old['completed']
assert recovery['completed'] and verification['status'] == 'PASS'
assert hashlib.sha256(proof_path.read_bytes()).hexdigest() == recovery['sourceProofSha256']
assert not ARCHIVE.exists(), 'Do not replace an existing archive'
files = [
    'deploy/milestone-proof.json', 'deploy/milestone-verification.json',
    'deploy/milestone-recovery.json', 'deploy/milestone-recovery-verification.json',
    'deploy/clean-stop-audit.json', 'docs/milestone-v1-phase1.json',
    'docs/submission/MILESTONE-V1-READINESS.md', 'docs/submission/MILESTONE-V1-RECOVERY.md',
    'docs/submission/milestone-v1.json', 'scripts/milestone-runner.ts',
    'scripts/milestone.ps1', 'scripts/verify_milestone.py', 'scripts/package-milestone.py',
    'scripts/recover-milestone.ts', 'scripts/verify_milestone_recovery.py',
    old['failures'][0]['receipt'],
]
checks = []
for relative in files:
    source = ROOT / relative
    target = ARCHIVE / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    target.write_bytes(data)
    assert target.read_bytes() == data
    checks.append(dict(path=relative, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
stamp = datetime.now(timezone.utc).isoformat()
head = subprocess.check_output(['git', '-c', 'safe.directory=' + str(ROOT), 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
(ARCHIVE / 'archive.json').write_text(json.dumps(dict(archivedAt=stamp, head=head,
    note='Exact working-file snapshots; the stopped journal and credited recovery are preserved. No failure was cleared.', files=checks), indent=2)+'\n')
new = dict(version=3, run='milestone-v1-final', network='StudioNet', chainId=61999,
    judge=old['judge'], probe=old['probe'], organizer=old['organizer'],
    depositCeilingWei='200000000000000000', previousGrossDepositsWei=old['grossDepositsWei'],
    grossDepositsWei='0', cumulativeGrossDepositsWei=old['grossDepositsWei'],
    transactions={k:v for k,v in old['transactions'].items() if k.startswith('deploy-')},
    broadcasts={k:v for k,v in old['broadcasts'].items() if k.startswith('deploy-')},
    contracts=old['contracts'], deposits=[], completed=False, stages={},
    stopOnAnyFailure=True, previousRun=str(ARCHIVE.relative_to(ROOT)).replace('\\','/'),
    deploymentReused=True, deploymentProvenance='Corrected contracts deployed and source-verified in the archived clean run; no contract source changes.',
    authorization='User instructed proceed till finish after the revised-demo plan and full recovery. Separate fresh cases; no old failed transaction is replayed.',
    recordedAt=stamp)
proof_path.write_text(json.dumps(new, indent=2)+'\n')
print('Preserved', len(checks), 'exact files. Initialized final run; previous gross deposits', old['grossDepositsWei'], 'wei; zero new deposits.')
