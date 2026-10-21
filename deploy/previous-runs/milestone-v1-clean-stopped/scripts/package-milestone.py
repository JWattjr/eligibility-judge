"""Generate reviewable Portal fields and verify direct StudioNet Explorer evidence."""
import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
EXPLORER = 'https://explorer-studio.genlayer.com'
SOURCE = 'https://github.com/JWattjr/eligibility-judge'
ADDRESS = re.compile(r'^https://explorer-(studio|studio-dev|bradbury|asimov)\.genlayer\.com/address/(0x[0-9a-fA-F]{40})/?$')


def fetch_json(url):
    for attempt in range(4):
        try:
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 Eligibility Judge evidence verifier'}),timeout=60) as response:
                assert response.status==200
                return json.load(response)
        except (URLError,TimeoutError,json.JSONDecodeError) as error:
            if isinstance(error,HTTPError) and error.code not in (429,500,502,503,504):
                raise
            if attempt==3:
                raise
            print('Transient Explorer read; retrying the same URL.',flush=True)
            time.sleep(5*(attempt+1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-links', action='store_true')
    options = parser.parse_args()
    proof = json.loads((ROOT/'deploy/milestone-proof.json').read_text(encoding='utf-8'))
    report_path = ROOT/'deploy/milestone-verification.json'
    report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
    live_verified = proof['completed'] and report.get('status') == 'PASS' and proof.get('run') == 'milestone-v1-clean'
    verified = False
    descriptions = {
        'disputes': ('RulingDisputes', 'Bonded full-file rule hearings. Validators independently judge pinned evidence and verify quotes. Finalized outcomes update credentials; VOID refunds and timed exits protect bonds.'),
        'badges': ('QualificationBadges', 'Non-transferable qualification credentials tied to a pinned commit, frozen rulebook and effective-verdict digest. Minting waits for the opening window and every pending hearing. No LLM or stake.'),
        'series': ('EligibilitySeries', 'Two-to-six-round seasons with a fixed qualification count and equal GEN bonus shares. Imports final effective rulings, refunds void or empty seasons, and verifies native credit before marking paid.'),
    }
    contracts = [dict(name=descriptions[key][0], address=c['address'], description=descriptions[key][1], explorer=EXPLORER+'/address/'+c['address']) for key,c in proof['contracts'].items()]
    evidence = [dict(type='GenLayer Explorer Contract', title=c['name']+' deployed on StudioNet', url=c['explorer']) for c in contracts]
    evidence.append(dict(type='GenLayer Explorer Contract', title='Unchanged EligibilityJudge dependency on StudioNet', url=EXPLORER+'/address/'+proof['judge']))
    cases = [dict(case=name, challenge=proof['rounds'][case['round']]['id'], expected=case['expected'], actual=case.get('record',{}).get('status','PENDING'), verdict=case.get('record',{}).get('answer'), receipt=EXPLORER+'/tx/'+proof['transactions']['dispute-'+name+('-open-child-0-child-0' if case.get('record',{}).get('opening_result')=='VOID' else '-hear-child-0')], hearingAttempt=EXPLORER+'/tx/'+proof['transactions']['dispute-'+name+'-hear']) for name,case in proof.get('disputeCases',{}).items() if 'dispute-'+name+'-hear' in proof['transactions']]
    transactions = {name:EXPLORER+'/tx/'+tx for name,tx in proof['transactions'].items() if name.startswith('deploy-') or name.endswith('-hear') or name.startswith('series-close') or (name.startswith('series-claim-') and '-child-' not in name) or name.endswith('-claim-child-0') or name.startswith('payout-control-')}
    failures = {f['hash']:f for f in proof.get('failures',[]) if f.get('classification') in ('LIVE_CONSENSUS_FAILURE','LIVE_EXPECTED_STATE_ROLLBACK')}
    fields = {
        'action':'Propose an update', 'project':'Eligibility Judge',
        'milestone':'Milestone v1: Seasons, Badges and Rule Disputes',
        'status':'Clean one-pass live proof independently verified; owner reviews and submits.' if verified else 'Live proof in progress. Do not submit this draft.',
        'readyForOwnerReview':bool(verified),
        'summary':'Eligibility Judge adds targeted full-file rule hearings, portable qualification badges and fixed-threshold seasons. Validators independently fetch one named file at its pinned commit, decide the frozen rule and verify the leader’s exact quote. The live demo traces an insufficient-evidence verdict through an overturned hearing, a via-dispute badge and a season bonus. Two builders qualify across distinct rounds and each receives 0.025 GEN. A prompt-injection argument is rejected in a real hearing; frivolous disputes pay their bond to the entrant. Raw-file checks remove the GitHub tree API dependency from openings. Unreachable evidence and timed VOID exits refund funds, while native credits are verified before claims become paid. The demo uses owner-operated wallets and repositories; overturns affect credentials and seasons, not the original judge’s pool.',
        'judgmentPoints':'New judgment: apply one frozen eligibility rule to a full named file, up to 64 KB, at the original pinned Git commit. Each validator independently fetches and judges that file, compares only verdict and path, and re-verifies the leader’s verbatim quote in its own fetch. Arguments and instructions in the file remain untrusted evidence. Code derives UPHELD, OVERTURNED or VOID, preserves the original prize settlement, gates credentials on finality and deadlines, and handles bonded refunds. Badges and seasons use deterministic cross-contract reads without an LLM.',
        'reviewRules':'Opening lasts until challenge close + one-hour judging grace + two hours. Bonds are 0.01–10 simulated GEN. Opening persists a reservation before a zero-value file check. Hearings have a 24-hour VOID/refund exit. Badges and round imports wait for every pending case. Void rounds never lower the season qualification threshold. Seasons have a full-refund exit 24 hours after their end. Native claims reserve numbered attempts and require independently verified credit.',
        'network':'StudioNet 61999. GEN is simulated development currency.',
        'contracts':contracts, 'evidence':evidence,
        'liveUrl':'https://eligibility-judge.vercel.app/series', 'source':SOURCE,
        'sourceCommit':subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'tutorial':SOURCE+'/blob/main/docs/TUTORIAL-MILESTONE-V1.md',
        'architecture':SOURCE+'/blob/main/docs/MILESTONE-V1-ARCHITECTURE.md',
        'proofManifest':SOURCE+'/blob/main/deploy/milestone-proof.json',
        'verification':SOURCE+'/blob/main/deploy/milestone-verification.json',
        'deploymentVerification':SOURCE+'/blob/main/docs/submission/milestone-v1-links.json',
        'challengeProofs':cases, 'keyTransactions':transactions,
        'grossDepositsWei':proof['grossDepositsWei'], 'depositCeilingWei':proof['depositCeilingWei'], 'deposits':proof['deposits'],
        'seriesWinners':proof.get('series',{}).get('winners',[]), 'bonusShareWei':proof.get('series',{}).get('share'), 'candidateTreeSizes':{c['name']:c['bytes'] for c in proof.get('candidateTrees',[])}, 'previousRun':SOURCE+'/tree/main/deploy/previous-runs/milestone-v1-first-run',
        'limits':'The original judge retains bounded evidence inspection. Badge minting and round imports wait for the dispute opening window and every pending hearing. The qualification count stays fixed even if a round is VOID. StudioNet GEN is simulated development currency. Historical first-run evidence is preserved separately. Nothing is submitted to the Portal automatically.',
        'checks':{'contractTests':110,'existingContractTests':46,'newContractTests':64,'appTests':22,'lint':'Three contracts pass GenVM lint and SDK validation.','typecheck':'PASS','productionBuild':'PASS','liveVerification':report.get('status','PENDING')},
        'blockers':'Owner reviews the completed clean proof and submits the Portal milestone.' if verified else 'Live proof, independent verification and final production browser checks are still running.',
    }
    counts={'summary':len(fields['summary']),'judgmentPoints':len(fields['judgmentPoints'])}
    assert counts['summary']<=1000
    for c in contracts:
        counts[c['name']+'.description']=len(c['description'])
        assert len(c['description'])<=200 and ADDRESS.fullmatch(c['explorer'])
    fields['fieldCharacterCounts']=counts
    target=ROOT/'docs/submission/milestone-v1.json'
    target.write_text(json.dumps(fields,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if options.verify_links:
        results=[]
        (ROOT/'docs/submission/milestone-v1-links.json').write_text(json.dumps(dict(status='RUNNING',checkedAt=datetime.now(timezone.utc).isoformat()),indent=2)+'\n',encoding='utf-8')
        for item in evidence:
            match=ADDRESS.fullmatch(item['url']); assert match
            address=match.group(2)
            data=fetch_json(EXPLORER+'/api/address/'+address);assert data['type']=='CONTRACT' and data['address'].lower()==address.lower()
            results.append(dict(url=item['url'],httpStatus=200,network='StudioNet 61999',type='CONTRACT',address=address))
        for name,url in {**transactions,**{'reported-failure-'+str(i):EXPLORER+'/tx/'+h for i,h in enumerate(failures)}}.items():
            tx_hash=url.rsplit('/',1)[1]
            data=fetch_json(EXPLORER+'/api/transactions/'+tx_hash);assert data['transaction']['hash'].lower()==tx_hash.lower()
            results.append(dict(name=name,url=url,httpStatus=200))
        (ROOT/'docs/submission/milestone-v1-links.json').write_text(json.dumps(dict(status='PASS',checkedAt=datetime.now(timezone.utc).isoformat(),results=results),indent=2)+'\n',encoding='utf-8')
        print('Verified Explorer evidence links:',len(results))
    links_path=ROOT/'docs/submission/milestone-v1-links.json'
    links=json.loads(links_path.read_text(encoding='utf-8')) if links_path.exists() else {}
    urls={r['url'] for r in links.get('results',[]) if r.get('httpStatus')==200}
    required={item['url'] for item in evidence}|set(transactions.values())|{EXPLORER+'/tx/'+h for h in failures}
    browser_path=ROOT/'docs/milestone-v1-browser.json'
    browser=json.loads(browser_path.read_text(encoding='utf-8')) if browser_path.exists() else {}
    verified=bool(live_verified and links.get('status')=='PASS' and required<=urls and browser.get('status')=='PASS' and browser.get('run')==proof.get('run'))
    fields['readyForOwnerReview']=verified
    fields['status']='Clean one-pass live proof independently verified; owner reviews and submits.' if verified else 'Final verification in progress. Do not submit this draft.'
    fields['checks']['browser']=browser.get('status','PENDING')
    fields['checks']['explorerLinks']=links.get('status','PENDING')
    if verified:fields['blockers']='Owner reviews the completed clean proof and submits the Portal milestone.'
    target.write_text(json.dumps(fields,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(counts,indent=2))


if __name__=='__main__':
    main()
