"""Run final local checks against the completed live snapshot; never sends transactions."""
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROOF = ROOT / 'deploy/milestone-proof.json'
REPORT = ROOT / 'docs/milestone-v1-final-checks.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def main():
    proof = json.loads(PROOF.read_text(encoding='utf-8'))
    assert proof['run'] == 'milestone-v1-release' and proof['completed'] and proof['stages']['complete']['status'] == 'PASS'
    assert not proof.get('stopReason') and not proof.get('failures') and not proof.get('mismatches')
    logs = ROOT / '.impeccable/review/milestone-v1-release' / ('final-checks-' + datetime.now(timezone.utc).strftime('%H%M%S'))
    logs.mkdir(parents=True, exist_ok=True)
    report = dict(status='RUNNING', run=proof['run'], proofDigest=digest(proof), stages={}, logs=str(logs.relative_to(ROOT)).replace('\\', '/'))

    def save():
        report['recordedAt'] = datetime.now(timezone.utc).isoformat()
        REPORT.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')

    def check(name, command):
        report['stages'][name] = 'RUNNING'
        save()
        result = subprocess.run(command, cwd=ROOT, capture_output=True)
        text = (result.stdout + b'\n' + result.stderr).decode('utf-8', errors='replace')
        (logs / (name + '.log')).write_text(text, encoding='utf-8')
        assert result.returncode == 0, name + ' failed; inspect ' + str(logs / (name + '.log'))
        report['stages'][name] = 'PASS'
        save()
        print(name, 'PASS', flush=True)
        return text

    try:
        direct = check('contract-tests', [sys.executable, '-m', 'pytest', 'tests/direct', '-q'])
        report['contractTests'] = int(re.search(r'(\d+)\s+passed', direct).group(1))
        assert report['contractTests'] >= 116, 'Expected the complete direct contract suite'
        app = check('app-tests', ['cmd.exe', '/d', '/c', 'npm.cmd', 'test'])
        report['appTests'] = int(re.search(r'\btests\s+(\d+)\b', app).group(1))
        assert report['appTests'] >= 22, 'Expected the complete app test suite'
        check('typecheck', ['cmd.exe', '/d', '/c', 'npm.cmd', 'run', 'typecheck'])
        for name in ['rule_disputes', 'qualification_badges', 'eligibility_series']:
            output = check('lint-' + name, [sys.executable, '-m', 'genvm_linter.cli', 'check', 'contracts/' + name + '.py', '--json'])
            parsed = next(json.loads(line) for line in output.splitlines() if line.startswith('{'))
            assert parsed['ok'] is True, name + ' linter did not pass'
        check('production-build', ['cmd.exe', '/d', '/c', 'npm.cmd', 'run', 'build'])
        assert digest(json.loads(PROOF.read_text(encoding='utf-8'))) == report['proofDigest'], 'Live snapshot changed during final checks'
        report['status'] = 'PASS'
        save()
        print(json.dumps(report, indent=2), flush=True)
    except Exception as error:
        report['status'] = 'FAIL'
        report['error'] = str(error)
        save()
        raise


if __name__ == '__main__':
    main()
