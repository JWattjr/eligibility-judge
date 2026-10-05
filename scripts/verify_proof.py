"""Read-only release verification with pinned genlayer-py 0.18.0. Never signs."""
import hashlib
import base64
import importlib.metadata
import json
import sys
import time
from pathlib import Path
from genlayer_py import create_client, studionet
from genlayer_py.types import TransactionHashVariant

assert importlib.metadata.version('genlayer-py') == '0.18.0', 'Install pinned requirements.txt'
root = Path(__file__).resolve().parent.parent
proof = json.loads((root / 'deploy/proof.json').read_text(encoding='utf8'))
client = create_client(chain=studionet)

def receipt(hash_value):
    # SDK release adapter maps status fields differently across Studio versions.
    raw = client.provider.make_request('gen_getTransactionReceipt', [hash_value])
    if raw.get('error'):
        raise AssertionError(raw['error'])
    return raw['result']

def finalized_success(record, transfer=False):
    status = record.get('status_name', record.get('statusName', record.get('status')))
    assert status in ('FINALIZED', 7), 'Transaction is not finalized: ' + str(status)
    if transfer:
        assert record.get('value_credited') is True, 'Transfer is not credited'
        return
    consensus = record.get('consensus_data') or {}
    leader = (consensus.get('leader_receipt') or [{}])[0]
    execution = record.get('txExecutionResultName', leader.get('execution_result'))
    assert execution in ('SUCCESS', 'FINISHED_WITH_RETURN'), 'Execution failed: ' + str(execution)
    assert (leader.get('result') or {}).get('status') != 'rollback', 'Execution rolled back'

def main():
    assert proof.get('completed') and proof.get('payoutVerified'), 'Live release proof is incomplete'
    receipts = {}
    for name, hash_value in proof['transactions'].items():
        record = receipt(hash_value)
        transfer = name.startswith(('claim-qualified-child', 'claim-refund-child'))
        finalized_success(record, transfer)
        receipts[name] = record
        print(name, hash_value, 'FINALIZED', 'CREDITED' if transfer else 'SUCCESS')
        time.sleep(2.6)  # Below 30 requests/min; never poll or send a write.
    record = json.loads(client.read_contract(proof['contract'], 'get_challenge', [proof['challengeId']], transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert record == proof['challenge'], 'Recorded proof differs from finalized contract state'
    assert record['status'] == 'SETTLED'
    expected_hash = hashlib.sha256(json.dumps(record['rules'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert record['rulebook_hash'] == expected_hash
    for name, case in proof['cases'].items():
        entry = record['entries'][case['wallet']]
        assert entry['status'] == case['expected'], 'Wrong outcome: ' + name
        assert entry['commit'] == case['commit'] and entry['repo'] == case['repo']
        for i in range(len(record['rules'])):
            assert 'judge-' + name + '-' + str(i) in receipts
            assert 'judge-' + name + '-' + str(i) + '-child-0' in receipts
    assert len(record['qualifiers']) == 1 and record['share'] == record['pool']
    claim = receipts['claim-qualified-child-0']
    assert str(claim['value']) == record['share']
    assert claim['from_address'].lower() == proof['contract'].lower()
    assert claim['to_address'].lower() == proof['cases']['qualified']['wallet'].lower()
    code = client.provider.make_request('gen_getContractCode', [proof['contract']])
    if code.get('error'):
        raise AssertionError('Cannot verify deployed source: ' + str(code['error']))
    deployed = code['result']
    local = (root / 'contracts/eligibility_judge.py').read_text(encoding='utf8')
    if isinstance(deployed, str) and deployed.startswith('0x'):
        deployed = bytes.fromhex(deployed[2:]).decode()
    elif isinstance(deployed, str) and not deployed.startswith('#'):
        deployed = base64.b64decode(deployed).decode()
    assert deployed.replace('\r\n', '\n') == local, 'Deployed source differs from the release contract'
    print('Verified finalized entries, callbacks, rulebook, settlement, exact native payout, and deployed source.')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('PROOF VERIFICATION FAILED:', str(error), file=sys.stderr)
        sys.exit(1)
