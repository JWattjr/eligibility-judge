"""Publish two labeled fixture pins, preserving the original fixture branch/history."""
import base64
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = 'JWattjr/eligibility-judge-injection-fixture'
BRANCH = 'milestone-v1-verbatim-control'
PARENT = '5bed3a266836ddf8c06235cac1f6dc403676d94c'
RECORD = ROOT / 'deploy/verbatim-control-fixture.json'
README = (ROOT / 'docs/fixtures/negative_README.md').read_text(encoding='utf-8')


def api(path, payload=None):
    command = ['gh', 'api', 'repos/' + REPO + '/' + path]
    if payload is not None:
        command += ['--method', 'POST', '--input', '-']
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def blob(content):
    return api('git/blobs', {'content': base64.b64encode(content).decode(), 'encoding': 'base64'})['sha']


def main():
    if RECORD.exists():
        record = json.loads(RECORD.read_text())
        assert api('git/ref/heads/' + BRANCH)['object']['sha'] == record['round2']
        print(json.dumps(record, indent=2))
        return
    # A new named branch only; never overwrite an existing branch or main.
    refs = api('git/matching-refs/heads/' + BRANCH)
    assert not any(r['ref'] == 'refs/heads/' + BRANCH for r in refs), 'Existing branch must be reconciled first'
    code = (ROOT / 'docs/fixtures/negative_control.py').read_bytes()
    license_blob = blob((ROOT / 'LICENSE').read_bytes())
    code_blob = blob(code)
    commits = []
    parent = PARENT
    for index in (1, 2):
        text = README + '\nRound: ' + str(index) + '.\n'
        tree = api('git/trees', {'tree': [
            {'path': 'README.md', 'mode': '100644', 'type': 'blob', 'sha': blob(text.encode())},
            {'path': 'LICENSE', 'mode': '100644', 'type': 'blob', 'sha': license_blob},
            {'path': 'contracts/negative_control.py', 'mode': '100644', 'type': 'blob', 'sha': code_blob},
        ]})
        parent = api('git/commits', {'message': 'Add explicit undeployed negative payout control, round ' + str(index),
                                     'tree': tree['sha'], 'parents': [parent]})['sha']
        commits.append(parent)
    api('git/refs', {'ref': 'refs/heads/' + BRANCH, 'sha': parent})
    record = dict(repo='https://github.com/' + REPO, branch=BRANCH, previousMain=PARENT,
                  round1=commits[0], round2=commits[1],
                  purpose='Labeled negative fixture with direct claim-reverts code evidence; original main/history retained.')
    RECORD.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
