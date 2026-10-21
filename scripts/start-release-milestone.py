"""Archive the quote-error attempt; initialize fresh cases under the same gross cap."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / 'deploy/previous-runs/milestone-v1-final-stopped'
path = ROOT / 'deploy/milestone-proof.json'
old = json.loads(path.read_text())
assert old['run'] == 'milestone-v1-final' and old['stopReason'] and old['grossDepositsWei'] == '1'
assert not ARCHIVE.exists()
files = ['deploy/milestone-proof.json', 'deploy/milestone-verification.json', 'deploy/explicit-control-fixture.json',
         'docs/submission/MILESTONE-V1-READINESS.md', 'docs/submission/milestone-v1.json',
         'scripts/milestone-runner.ts', 'scripts/run-final-demo.ps1', 'scripts/preflight-milestone.py',
         old['failures'][0]['receipt']]
checks = []
for name in files:
    data = (ROOT / name).read_bytes()
    target = ARCHIVE / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    checks.append(dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
stamp = datetime.now(timezone.utc).isoformat()
(ARCHIVE / 'archive.json').write_text(json.dumps(dict(archivedAt=stamp, files=checks,
    reason='Finalized missing-verbatim-quote error; no hearings or bonus funded.'), indent=2)+'\n')
transactions = {k:v for k,v in old['transactions'].items() if k.startswith('deploy-')}
broadcasts = {k:v for k,v in old['broadcasts'].items() if k.startswith('deploy-')}
stable_probes = {}
for index in (0, 1, 2, 5, 6, 7):
    name = 'probe-' + str(index)
    transactions[name] = old['transactions'][name]
    broadcasts[name] = old['broadcasts'][name]
    url = broadcasts[name]['args'][0]
    stable_probes[url] = old['probes'][url]
previous = str(int(old['previousGrossDepositsWei']) + int(old['grossDepositsWei']))
new = dict(version=4, run='milestone-v1-release', network='StudioNet', chainId=61999,
    judge=old['judge'], probe=old['probe'], organizer=old['organizer'],
    depositCeilingWei='200000000000000000', previousGrossDepositsWei=previous,
    grossDepositsWei='0', cumulativeGrossDepositsWei=previous,
    transactions=transactions, broadcasts=broadcasts, probes=stable_probes,
    contracts=old['contracts'], deposits=[], completed=False, stages={}, stopOnAnyFailure=True,
    previousRun=str(ARCHIVE.relative_to(ROOT)).replace('\\','/'),
    deploymentReused=True, deploymentProvenance=old['deploymentProvenance'],
    probeProvenance='Six successful immutable-URL probes reused by receipt; four revised fixture URLs checked before deposits.',
    authorization='User instructed proceed till finish; fresh cases within the cumulative 0.2-GEN ceiling, preserving failed attempts without replay.',
    priorStoppedPool=dict(challenge=old['rounds'][0]['id'], amountWei='1',
                          graceEndsAt=old['rounds'][0]['challenge']['closes']+3600), recordedAt=stamp)
path.write_text(json.dumps(new, indent=2)+'\n')
print('Archived',len(checks),'exact files. Release run initialized; previous cumulative gross',previous,'wei.')
