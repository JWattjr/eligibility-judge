"""Fetch each candidate tree once from this machine, before any demo funding."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'deploy/final-preflight'
UA = 'Mozilla/5.0 Eligibility Judge clean-run preflight'


def get(url):
    with urlopen(Request(url, headers={'User-Agent': UA}), timeout=60) as response:
        assert response.status == 200, (url, response.status)
        return response.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('qualifying_commit')
    args = parser.parse_args()
    proof_path = ROOT / 'deploy/milestone-proof.json'
    proof = json.loads(proof_path.read_text(encoding='utf-8'))
    assert not proof['deposits'] and proof['grossDepositsWei'] == '0'
    assert proof['run'] == 'milestone-v1-final'
    control = json.loads((ROOT / 'deploy/explicit-control-fixture.json').read_text())
    candidates = [
        ('slash-court', 'JWattjr/Slash-court', '18b3f691fc7fcfcc3a94a1973db1caaf1570224a'),
        ('rescued-original', 'JWattjr/eligibility-judge', '24ace69788fe86ef4e2c8326e46094882df4bf12'),
        ('qualifying-current', 'JWattjr/eligibility-judge', args.qualifying_commit),
        ('control-original', 'JWattjr/eligibility-judge-injection-fixture', control['round1']),
        ('control-second', 'JWattjr/eligibility-judge-injection-fixture', control['round2']),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    checks = []
    for name, repo, commit in candidates:
        target = OUT / (name + '-tree.json')
        url = f'https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1'
        # The saved response is the only reuse path. Never refetch a tree.
        marker = OUT / (name + '-request.json')
        if name in ('slash-court', 'rescued-original') and not target.exists():
            prior = ROOT / 'deploy/clean-preflight'
            prior_marker = json.loads((prior / marker.name).read_text())
            assert prior_marker['url'] == url
            target.write_bytes((prior / target.name).read_bytes())
            marker.write_text(json.dumps({**prior_marker, 'reusedSavedResponse': True}) + '\n')
        if not target.exists():
            assert not marker.exists(), 'Prior fetch failed; no second tree request is permitted'
            marker.write_text(json.dumps({'url': url, 'requestedAt': datetime.now(timezone.utc).isoformat()}) + '\n', encoding='utf-8')
            raw = get(url)
            target.write_bytes(raw)
        else:
            assert json.loads(marker.read_text(encoding='utf-8'))['url'] == url
            raw = target.read_bytes()
        tree = json.loads(raw)
        check = dict(name=name, repo='https://github.com/' + repo, commit=commit,
                     url=url, bytes=len(raw), truncated=tree.get('truncated', True),
                     sha256=hashlib.sha256(raw).hexdigest(), responseFile=str(target.relative_to(ROOT)).replace('\\', '/'),
                     accepted=len(raw) < 80000 and tree.get('truncated') is False)
        checks.append(check)
        proof['candidateTrees'] = checks
        proof_path.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
        print(name, len(raw), 'bytes; truncated:', check['truncated'], 'accepted:', check['accepted'], flush=True)
        assert check['accepted'], 'Candidate rejected before any deposit: ' + name
        paths = [n['path'] for n in tree['tree'] if n.get('type') == 'blob']
        def priority(path):
            base = path.rsplit('/', 1)[-1].lower()
            return (0 if base in ('readme.md', 'license', 'license.md', 'license.txt') else 1 if path.lower().endswith(('.py', '.ts', '.tsx', '.js', '.jsx', '.rs', '.go', '.sol')) and ('contract' in path.lower() or 'test' in path.lower()) else 2, path)
        selected = sorted([p for p in paths if p.lower().endswith(('.py', '.ts', '.tsx', '.js', '.jsx', '.rs', '.go', '.sol', '.md', '.txt', '.json', '.toml')) or p.rsplit('/', 1)[-1].lower() == 'license'], key=priority)[:10]
        check['judgeSelectedFiles'] = selected
        raw_files = {}
        for file in selected:
            data = get(f'https://raw.githubusercontent.com/{repo}/{commit}/{file.replace(" ", "%20")}')
            raw_files[file] = data
        check['inspection'] = {file: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'visibleNativePayout': b'emit_transfer(value=' in data[:12000]} for file, data in raw_files.items()}
        readme = raw_files.get('README.md', b'')[:12000]
        check['readmeHasExplorerAddress'] = b'https://explorer-studio.genlayer.com/address/0x' in readme
        check['visibleNativePayout'] = any(b'emit_transfer(value=' in data[:12000] for file, data in raw_files.items() if file.endswith('.py') and 'contract' in file.lower())
        check['mitLicense'] = b'MIT License' in raw_files.get('LICENSE', b'')[:12000]
        if name in ('slash-court', 'qualifying-current'):
            assert check['readmeHasExplorerAddress'] and check['visibleNativePayout'] and check['mitLicense'], 'Positive repository lacks bounded evidence'
        elif name == 'rescued-original':
            assert check['readmeHasExplorerAddress'] and not check['visibleNativePayout'] and check['mitLicense']
            decisive = get(f'https://raw.githubusercontent.com/{repo}/{commit}/contracts/eligibility_judge.py')
            assert 12000 < decisive.find(b'emit_transfer(value=') < len(decisive) <= 65536
            check['decisiveFile'] = {'path': 'contracts/eligibility_judge.py', 'bytes': len(decisive), 'payoutOffset': decisive.find(b'emit_transfer(value=')}
        else:
            assert not check['readmeHasExplorerAddress'] and not check['visibleNativePayout'], 'Negative fixture does not match the frozen rules'
            assert b'raise gl.vm.UserError' in raw_files['contracts/negative_control.py']
        proof['candidateTrees'] = checks
        proof_path.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    proof['candidatePreflightPassed'] = True
    proof['candidatePreflightAt'] = datetime.now(timezone.utc).isoformat()
    proof_path.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print('All candidate trees complete, below 80,000 bytes, and evidence checked. No deposits sent.')


if __name__ == '__main__':
    main()
