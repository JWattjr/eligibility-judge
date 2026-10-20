"""Read-only StudioNet milestone verification. Never signs, retries a case, or deposits."""
import base64
import hashlib
import importlib.metadata
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from eth_account import Account
from genlayer_py import create_client, studionet
from genlayer_py.types import TransactionHashVariant
from genlayer_py.abi.calldata.decoder import decode

ROOT = Path(__file__).resolve().parent.parent
RPC = 'https://studio.genlayer.com/api'
UA = 'Mozilla/5.0 Eligibility Judge read-only milestone verifier'
ADDRESS_URL = re.compile(r'^https://explorer-(studio|studio-dev|bradbury|asimov)\.genlayer\.com/address/(0x[0-9a-fA-F]{40})/?$')
EXPECTED_JUDGE = '0x03e7970e791d644b2714a457d178edf036670bb7'
assert importlib.metadata.version('genlayer-py') == '0.18.0'
proof = json.loads((ROOT / 'deploy/milestone-proof.json').read_text(encoding='utf-8'))
client = create_client(chain=studionet, account=Account.create())
last_call = 0.0


def rpc(method, params):
    global last_call
    time.sleep(max(0, 2.7 - (time.monotonic() - last_call)))
    request = Request(RPC, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                      headers={'Content-Type': 'application/json', 'User-Agent': UA})
    for attempt in range(4):
        last_call = time.monotonic()
        try:
            with urlopen(request, timeout=60) as response:
                assert response.status == 200
                value = json.load(response)
            break
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            if isinstance(error, HTTPError) and error.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 3:
                raise
            print('Transient read failure; retrying the same read-only request:', method, flush=True)
            time.sleep(5 * (attempt + 1))
    last_call = time.monotonic()
    assert not value.get('error'), value.get('error')
    return value


# SDK 0.18 sends a default Python UA rejected by Studio. Keep its calldata and
# LATEST_FINAL decoding, replacing only its public HTTP transport.
client.provider.make_request = rpc


def view(address, method, args):
    value = client.read_contract(address, method, args, transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
    return json.loads(value) if isinstance(value, str) and value[:1] in ('{', '[') else value


def successful(receipt):
    assert receipt['status'] == 'FINALIZED', receipt.get('hash')
    leader = receipt['consensus_data']['leader_receipt'][0]
    assert receipt.get('result') == 6 and leader['execution_result'] == 'SUCCESS', receipt.get('hash')
    result = leader['result']
    if isinstance(result, str):
        assert base64.b64decode(result)[:1] == b'\x00', 'rollback or VM error'
    else:
        assert result.get('status') == 'return', 'rollback or VM error'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def source_bytes(value):
    if value.startswith('#'):
        return value.encode()
    if value.startswith('0x'):
        return bytes.fromhex(value[2:])
    return base64.b64decode(value)


def credited_transfer(receipt, parent, source, recipient, amount):
    assert receipt['status'] == 'FINALIZED' and receipt['value_credited'] is True
    assert receipt['type'] == 0 and receipt['consensus_data'] is None
    assert receipt['triggered_on'] == 'finalized'
    assert receipt['hash'] in parent['triggered_transactions']
    assert receipt.get('triggered_by') == parent['hash']
    assert receipt['from_address'].lower() == source.lower()
    assert receipt['to_address'].lower() == recipient.lower()
    assert int(receipt['value']) == amount


def main():
    assert proof['completed'], 'Live milestone is incomplete; no pass claim is allowed'
    assert proof['judge'].lower() == EXPECTED_JUDGE and proof['chainId'] == 61999
    assert all(m.get('reported') and m.get('reason') for m in proof.get('mismatches', [])), 'Every mismatch must be disclosed'
    failures = {f['hash']: f for f in proof.get('failures', []) if f.get('classification') in ('LIVE_CONSENSUS_FAILURE','LIVE_EXPECTED_STATE_ROLLBACK') and f.get('reported')}
    assert all(f.get('classification', '').startswith('LOCAL_RECEIPT_ADAPTER_ERROR') or f['hash'] in failures for f in proof.get('failures', [])), 'Unreported live failure'
    assert proof['treeBound']['bytes'] > 96000 and proof['treeBound']['bytes'] <= 1000000
    deposits = sum(int(d['value']) for d in proof['deposits'])
    assert deposits == int(proof['grossDepositsWei']) <= 10**18
    assert deposits == 13 * 10**16 + 3, 'Unexpected milestone deposits'
    records = {}
    for name, tx_hash in proof['transactions'].items():
        record = rpc('eth_getTransactionByHash', [tx_hash])['result']
        assert record and record['hash'].lower() == tx_hash.lower()
        native = record.get('type') == 0 and record.get('consensus_data') is None
        if native:
            assert record['status'] == 'FINALIZED' and record['value_credited'] is True
        elif tx_hash in failures:
            assert record['status'] == 'FINALIZED'
            assert record.get('result') != 6 or record['consensus_data']['leader_receipt'][0]['execution_result'] != 'SUCCESS'
            assert name == failures[tx_hash]['name']
        else:
            successful(record)
        records[name] = record
        if '-child-' in name:
            parent_name = name.rsplit('-child-', 1)[0]
            assert tx_hash in records[parent_name]['triggered_transactions']
            assert record.get('triggered_by') == records[parent_name]['hash']
        intended = proof['broadcasts'].get(name)
        if intended and 'method' in intended:
            assert record['to_address'].lower() == intended['address'].lower()
            assert record['from_address'].lower() == intended['sender'].lower()
            assert int(record['value']) == int(intended['value'])
            call = decode(base64.b64decode(record['data']['calldata']))
            assert call == {'method': intended['method'], 'args': intended['args']}, name
        print(name, tx_hash, 'FINALIZED CREDITED' if native else 'FINALIZED REPORTED FAILURE' if tx_hash in failures else 'FINALIZED SUCCESS', flush=True)
    for deposit in proof['deposits']:
        assert records[deposit['name']]['hash'] == deposit['hash']
        assert int(records[deposit['name']]['value']) == int(deposit['value'])

    for name, contract in proof['contracts'].items():
        deployed = source_bytes(rpc('gen_getContractCode', [contract['address']])['result'])
        local = (ROOT / contract['source']).read_bytes()
        assert deployed == local, name + ' deployed bytes differ from the repo file'
        assert hashlib.sha256(local).hexdigest() == contract['sourceSha256']
        git_blob = subprocess.check_output(['git', '-c', 'safe.directory=' + str(ROOT), 'show', 'HEAD:' + contract['source']], cwd=ROOT)
        assert git_blob == deployed, name + ' deployed bytes differ from committed Git source'
        config = view(contract['address'], 'get_config', [])
        assert config['judge'].lower() == EXPECTED_JUDGE
        if name != 'disputes':
            assert config['disputes'].lower() == proof['contracts']['disputes']['address'].lower()

    organizer = proof['organizer']
    for index, item in enumerate(proof['rounds']):
        challenge = view(proof['judge'], 'get_challenge', [item['id']])
        assert challenge['status'] == 'SETTLED' and challenge['organizer'] == organizer
        assert challenge['rules'] == proof['rules'] and challenge['rulebook_hash'] == digest(proof['rules'])
        assert challenge['pool'] == '1' and challenge['share'] == '0' and challenge['refund'] == '1'
        assert challenge['qualifiers'] == [] and challenge['refund_claimed'] is True
        assert item['originalPoolExit'] == 'claim_refund'
        for entrant in proof['entrants']:
            entry = challenge['entries'][entrant['wallet']]
            assert entry['repo'] == entrant['repo'] and entry['commit'] == entrant['commit']
            assert entry['status'] == entrant.get('observedOriginalStatus', entrant['expected']), (index, entrant['name'], entry['status'])
            assert not any(entry['pending'])
            for rule, verdict in enumerate(entry['verdicts']):
                if verdict is None:
                    label = f"round-{index+1}-judge-{entrant['name']}-{rule}"
                    assert proof['transactions'].get(label) in failures and entry.get('resolution_reason'), 'Unexplained missing verdict'
                elif entrant['name'] == 'consistent':
                    assert verdict['status'] == 'INSUFFICIENT_EVIDENCE' and verdict['reason'] == 'tree exceeds inspection limit or is malformed'
        parent = records[f'round-{index+1}-claim']
        credited_transfer(records[f'round-{index+1}-claim-child-0'], parent, proof['judge'], organizer, 1)

    for name, case in proof['disputeCases'].items():
        record = view(proof['contracts']['disputes']['address'], 'get_dispute', [case['id']])
        if name=='C':
            assert record['status']=='VOID' and record['opening_result']=='VOID'
            assert record['reason'].startswith('VOID_SOURCES_UNREACHABLE:')
            assert any(m.get('case')=='C' and m['actual']=='VOID' and m['reported'] for m in proof['mismatches'])
        else:
            assert record['status'] == case['expected'] and record['answer']['verdict'] == case['verdict']
            assert record['status'] in ('UPHELD', 'OVERTURNED')
        assert record['claims'][record['recipient']] == str(10**16)
        pending = record['claim_attempts'][record['recipient']]
        assert pending['status'] == 'paid'
        parent = records[f'dispute-{name}-claim']
        credited_transfer(records[f'dispute-{name}-claim-child-0'], parent,
                          proof['contracts']['disputes']['address'], record['recipient'], 10**16)
        assert pending['claim_hash'] == parent['hash']
        assert pending['transfer_hash'] == records[f'dispute-{name}-claim-child-0']['hash']

    all_badges = []
    for entrant in proof['entrants']:
        badges = view(proof['contracts']['badges']['address'], 'get_badges', [entrant['wallet']])
        for badge in badges:
            assert view(proof['contracts']['badges']['address'], 'verify', [entrant['wallet'], badge['challenge_id']]) is True
            effective = view(proof['contracts']['disputes']['address'], 'get_effective_verdicts', [badge['challenge_id'], entrant['wallet']])
            assert effective['credentials_final'] and effective['effective_status'] == 'QUALIFIED'
            assert badge['effective_verdicts_digest'] == digest(effective['effective_verdicts'])
            assert badge['via_dispute'] == effective['via_dispute']
            assert badge['commit'] == entrant['commit'] and badge['transferable'] is False
        all_badges.extend(badges)
    assert len(all_badges) == 1 and sum(b['via_dispute'] for b in all_badges) == 1
    assert set(proof['disputeCases'])=={'A','B','C'} and {c['case'] for c in proof['unrunCases']}==set('DEFGHI')
    series = view(proof['contracts']['series']['address'], 'get_series', [proof['seriesId']])
    assert series == proof['series'] and series['status'] == 'CLOSED'
    assert series['threshold'] == 2 and series['winners'] == []
    assert series['pool'] == str(10**17) and series['share'] == '0' and series['refund'] == str(10**17)
    assert series['claims'][organizer] == str(10**17)
    assert all(r['status'] == 'RECORDED' for r in series['rounds'].values())
    key = 'series-claim-' + organizer[2:10]
    credited_transfer(records[key+'-child-0'], records[key], proof['contracts']['series']['address'], organizer, 10**17)
    payout_control=view(proof['contracts']['series']['address'],'get_series',[proof['payoutControl']['id']])
    target=next(e['wallet'] for e in proof['entrants'] if e['name']=='targeted')
    assert payout_control==proof['payoutControl']['record'] and payout_control['status']=='CLOSED'
    assert payout_control['threshold']==1 and payout_control['winners']==[target]
    assert payout_control['pool']=='1' and payout_control['share']=='1' and payout_control['refund']=='0'
    assert payout_control['claims'][target]=='1'
    control_key='payout-control-claim-'+target[2:10]
    credited_transfer(records[control_key+'-child-0'],records[control_key],proof['contracts']['series']['address'],target,1)
    balances = {}
    for name, contract in proof['contracts'].items():
        balances[name] = int(rpc('eth_getBalance', [contract['address'], 'latest'])['result'], 16)
        assert balances[name] == 0, (name, 'unexpected stranded balance', balances[name])
    retired_balances = {}
    for retired in proof.get('previousUnfundedDeployments', []):
        for name, contract in retired['contracts'].items():
            amount = int(rpc('eth_getBalance', [contract['address'], 'latest'])['result'], 16)
            assert amount == 0
            retired_balances[contract['address']] = amount
    report = {'status': 'PASS_WITH_REPORTED_FAILURES' if failures else 'PASS', 'allTransactionsSuccessful': not bool(failures), 'reportedFailures': list(failures.values()), 'reportedMismatches': proof.get('mismatches', []), 'retiredUnfundedBalancesWei': retired_balances, 'recordedAt': datetime.now(timezone.utc).isoformat(), 'receiptCount': len(records),
        'grossDepositsWei': str(deposits), 'allNewContractBalancesWei': balances, 'badgeCount': len(all_badges),
        'viaDisputeBadges': 1, 'payoutControlWinner': target, 'unrunCases': proof['unrunCases'], 'seriesWinners': series['winners'], 'deployedAndGitSourceByteIdentical': True,
        'disputes': {name: case['record']['status'] for name, case in proof['disputeCases'].items()}}
    (ROOT/'deploy/milestone-verification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
