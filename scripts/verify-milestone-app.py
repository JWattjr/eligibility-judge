"""Verify the deployed read-only app API against the completed StudioNet proof."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='https://eligibility-judge.vercel.app')
    options = parser.parse_args()
    base = options.base_url.rstrip('/')
    parsed = urlparse(base)
    assert parsed.scheme == 'https' and parsed.hostname.endswith('.vercel.app') and not parsed.query and not parsed.fragment
    proof = json.loads((ROOT/'deploy/milestone-proof.json').read_text(encoding='utf-8'))
    verified = json.loads((ROOT/'deploy/milestone-verification.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(json.dumps(proof, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert proof['completed'] and verified['status'] == 'PASS' and verified['proofDigest'] == digest
    report = dict(status='RUNNING', run=proof['run'], proofDigest=digest, baseUrl=base, checks=[])
    target = ROOT/'docs/milestone-v1-api.json'

    def save():
        report['checkedAt'] = datetime.now(timezone.utc).isoformat()
        target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')

    def get(**query):
        url = base+'/api/milestone?'+urlencode(query)
        for attempt in range(4):
            try:
                request = Request(url, headers={'User-Agent': 'Mozilla/5.0 Eligibility Judge deployed app verifier'})
                with urlopen(request, timeout=90) as response:
                    assert response.status == 200
                    data = json.load(response)
                assert not data.get('error') and data.get('readAt')
                report['checks'].append(dict(url=url, httpStatus=200, readAt=data['readAt']))
                save()
                return data
            except (URLError, TimeoutError, json.JSONDecodeError) as error:
                if isinstance(error, HTTPError) and error.code not in (429, 500, 502, 503, 504):
                    raise
                if attempt == 3:
                    raise
                time.sleep(20)

    try:
        save()
        seasons = get(kind='series')['series']
        season = next(s for s in seasons if s['id'] == proof['seriesId'])
        winners = sorted(proof['series']['winners'])
        assert season['status'] == 'CLOSED' and season['threshold'] == 2 and sorted(season['winners']) == winners
        assert season['share'] == '25000000000000000' and season['refund'] == '0'
        standings = {s['wallet']: s for s in season['standings']}
        for wallet in winners:
            assert standings[wallet]['qualification_count'] == standings[wallet]['current_streak'] == 2
            assert season['claims'][wallet] == '25000000000000000' and season['claim_attempts'][wallet]['status'] == 'paid'
            assert season['claim_attempts'][wallet]['transfer_hash'] == proof['series']['claim_attempts'][wallet]['transfer_hash']
        hearings = {h['id']: h for h in get(kind='disputes')['disputes']}
        for case in proof['disputeCases'].values():
            actual = hearings[case['id']]
            assert actual['status'] == case['expected'] and actual['answer']['verdict'] == case['verdict']
            assert actual['claim_attempts'][actual['recipient']]['status'] == 'paid'
        badge_count = via_count = 0
        for entrant in proof['entrants']:
            badges = get(kind='badges', wallet=entrant['wallet'])['badges']
            assert len(badges) == (0 if entrant['name'] == 'control' else 2)
            badge_count += len(badges)
            via_count += sum(bool(b['via_dispute']) for b in badges)
        assert badge_count == 4 and via_count == 1
        rescued = next(e for e in proof['entrants'] if e['name'] == 'rescued')['wallet']
        challenge = proof['rounds'][0]['id']
        assert get(kind='verify', wallet=rescued, challenge=challenge)['verified'] is True
        effective = get(kind='entry', wallet=rescued, challenge=challenge)['effective']
        assert effective['effective_status'] == 'QUALIFIED' and effective['credentials_final'] and effective['via_dispute']
        report.update(status='PASS', winners=winners, badgeCount=badge_count, viaDisputeBadges=via_count, hearingOutcomes={name: c['expected'] for name, c in proof['disputeCases'].items()})
        save()
        print(json.dumps(report, indent=2), flush=True)
    except Exception as error:
        report.update(status='FAIL', error=str(error))
        save()
        raise


if __name__ == '__main__':
    main()
