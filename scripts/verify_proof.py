"""Read-only release verification with pinned genlayer-py 0.18.0. Never signs."""
import hashlib
import base64
import importlib.metadata
import json
import re
import sys
import time
from pathlib import Path
from genlayer_py import create_client, studionet
from genlayer_py.types import TransactionHashVariant
from eth_account import Account

assert importlib.metadata.version('genlayer-py') == '0.18.0', 'Install pinned requirements.txt'
root = Path(__file__).resolve().parent.parent
proof = json.loads((root / 'deploy/proof.json').read_text(encoding='utf8'))
# SDK 0.18 requires a caller even for gen_call. This disposable account is never
# funded, saved, or used to sign; the verifier only invokes read RPC methods.
client = create_client(chain=studionet, account=Account.create())

def read_with_retry(operation):
    for attempt in range(6):
        try:
            return operation()
        except Exception as error:
            transient = re.search(r'invalid JSON|timed out|ETIMEDOUT|ECONNRESET|Bad Gateway|\b50[234]\b', str(error), re.I)
            if not transient or attempt == 5:
                raise
            print('Temporary RPC read failure; retrying the same read.', flush=True)
            time.sleep(10)

def receipt(hash_value):
    # SDK release adapter maps status fields differently across Studio versions.
    raw = read_with_retry(lambda: client.provider.make_request('eth_getTransactionByHash', [hash_value]))
    if raw.get('error'):
        raise AssertionError(raw['error'])
    return raw['result']

def finalized_success(record, transfer=False):
    status = record.get('status_name', record.get('statusName', record.get('status')))
    assert status in ('FINALIZED', 7, '7'), 'Transaction is not finalized: ' + str(status)
    if transfer:
        assert record.get('value_credited') is True, 'Transfer is not credited'
        return
    agreement = record.get('result_name', record.get('resultName'))
    assert not agreement or agreement in ('AGREE', 'MAJORITY_AGREE', 'SUCCESS'), 'Consensus rejected the leader result: ' + str(agreement)
    consensus = record.get('consensus_data') or {}
    leader = (consensus.get('leader_receipt') or [{}])[0]
    execution = record.get('txExecutionResultName', leader.get('execution_result'))
    assert execution in ('SUCCESS', 'FINISHED_WITH_RETURN'), 'Execution failed: ' + str(execution)
    result = leader.get('result')
    if isinstance(result, dict):
        assert result.get('status') != 'rollback', 'Execution rolled back'
    elif isinstance(result, str):
        assert base64.b64decode(result)[:1] == b'\x00', 'Execution did not return successfully'

def main():
    assert proof.get('completed') and proof.get('payoutVerified'), 'Live release proof is incomplete'
    if proof.get('timeoutRequired'):
        assert proof.get('timeoutCompleted') and proof.get('timeoutRefundVerified'), 'Live timeout refund proof is incomplete'
    receipts = {}
    for name, attempt in proof.get('failedTransactions', {}).items():
        failed = receipt(attempt['hash'])
        assert failed.get('status') == 'FINALIZED', 'Failed attempt is not final: ' + name
        leader = failed['consensus_data']['leader_receipt'][0]
        rejected = failed.get('result_name') in ('DISAGREE', 'MAJORITY_DISAGREE', 'NO_MAJORITY', 'TIMEOUT', 'DETERMINISTIC_VIOLATION')
        assert rejected or leader.get('execution_result') == 'ERROR' or base64.b64decode(leader.get('result', ''))[:1] == b'\x01', 'Recorded failure was successful: ' + name
        print(name, attempt['hash'], 'FINALIZED', 'RETAINED FAILURE')
        time.sleep(2.6)
    for name, hash_value in proof['transactions'].items():
        record = receipt(hash_value)
        transfer = name.startswith(('claim-qualified-child', 'claim-refund-child', 'timeout-refund-child'))
        finalized_success(record, transfer)
        receipts[name] = record
        print(name, hash_value, 'FINALIZED', 'CREDITED' if transfer else 'SUCCESS')
        time.sleep(2.6)  # Below 30 requests/min; never poll or send a write.
    record = json.loads(read_with_retry(lambda: client.read_contract(proof['contract'], 'get_challenge', [proof['challengeId']], transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)))
    assert record == proof['challenge'], 'Recorded proof differs from finalized contract state'
    assert record['status'] == 'SETTLED'
    for name, parent in receipts.items():
        if '-child-' in name:
            parent_name = name.rsplit('-child-', 1)[0]
            assert parent['hash'] in receipts[parent_name].get('triggered_transactions', []), 'Unrelated callback: ' + name
            assert parent.get('triggered_by') == receipts[parent_name]['hash'], 'Callback origin mismatch: ' + name
    expected_hash = hashlib.sha256(json.dumps(record['rules'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert record['rulebook_hash'] == expected_hash
    for name, case in proof['cases'].items():
        entry = record['entries'][case['wallet']]
        assert entry['status'] == case['expected'], 'Wrong outcome: ' + name
        assert entry['commit'] == case['commit'] and entry['repo'] == case['repo']
        for verdict in entry['verdicts']:
            assert verdict is not None and len(verdict['quote']) <= 600, 'Unfinalized or unbounded stored citation'
        for i in range(len(record['rules'])):
            assert 'judge-' + name + '-' + str(i) in receipts
            assert 'judge-' + name + '-' + str(i) + '-child-0' in receipts
    assert len(record['qualifiers']) == 1 and record['share'] == record['pool']
    assert record['refund'] == '0', 'Single-qualifier settlement has an unexpected remainder'
    assert record['claims'].get(proof['cases']['qualified']['wallet']) == record['share'], 'Claim amount is not recorded'
    claim = receipts['claim-qualified-child-0']
    assert str(claim['value']) == record['share']
    assert claim['from_address'].lower() == proof['contract'].lower()
    assert claim['to_address'].lower() == proof['cases']['qualified']['wallet'].lower()
    if proof.get('timeoutRequired'):
        timeout = json.loads(read_with_retry(lambda: client.read_contract(proof['contract'], 'get_challenge', [proof['timeoutChallengeId']], transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)))
        assert timeout == proof['timeoutChallenge'], 'Recorded timeout differs from finalized state'
        assert timeout['status'] == 'SETTLED' and len(timeout['order']) == 1
        assert timeout['qualifiers'] == [] and timeout['pool'] == timeout['refund'] == '1' and timeout['share'] == '0'
        assert timeout['refund_claimed'] is True
        entry = timeout['entries'][timeout['order'][0]]
        assert entry['status'] == 'INSUFFICIENT_EVIDENCE' and entry['resolution_reason'] == 'Judgment did not finalize before the grace deadline.'
        assert not any(entry['verdicts']) and not any(entry['pending']), 'Timeout must not invent verdicts or leave callbacks pending'
        assert not any(name.startswith('timeout-judge') for name in receipts), 'Timeout entry was judged'
        assert proof['timeoutDeadline'] == timeout['closes'] + 3600
        settled_at = receipts['timeout-settle'].get('created_timestamp', receipts['timeout-settle'].get('created_at'))
        if isinstance(settled_at, str) and not settled_at.isdecimal():
            from datetime import datetime
            settled_at = datetime.fromisoformat(settled_at.replace('Z', '+00:00')).timestamp()
        assert int(settled_at) >= proof['timeoutDeadline'], 'Timeout settlement was sent before the real grace deadline'
        refund = receipts['timeout-refund-child-0']
        assert refund['value_credited'] is True and str(refund['value']) == '1'
        assert refund['from_address'].lower() == proof['contract'].lower()
        assert refund['to_address'].lower() == timeout['organizer'].lower()
    code = read_with_retry(lambda: client.provider.make_request('gen_getContractCode', [proof['contract']]))
    if code.get('error'):
        raise AssertionError('Cannot verify deployed source: ' + str(code['error']))
    deployed = code['result']
    local = (root / 'contracts/eligibility_judge.py').read_text(encoding='utf8')
    assert hashlib.sha256(local.encode()).hexdigest() == proof['contractSourceSha256'], 'Manifest source hash differs from the release contract'
    if isinstance(deployed, str) and deployed.startswith('0x'):
        deployed = bytes.fromhex(deployed[2:]).decode()
    elif isinstance(deployed, str) and not deployed.startswith('#'):
        deployed = base64.b64decode(deployed).decode()
    assert deployed.replace('\r\n', '\n') == local, 'Deployed source differs from the release contract'
    print('Verified finalized entries, callbacks, rulebook, settlement, exact native payout, and deployed source.' + (' Live grace settlement and exact credited organizer refund verified.' if proof.get('timeoutRequired') else ''))

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('PROOF VERIFICATION FAILED:', str(error), file=sys.stderr)
        sys.exit(1)
