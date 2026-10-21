"""Independently verify deposit recovery without signing or altering the failed run."""
import base64
import hashlib
import json
from datetime import datetime, timezone

from genlayer_py.abi.calldata.decoder import decode
from verify_milestone import ROOT, credited_transfer, rpc, successful, view

OWNER = '0xdb433ff614bdd1ece21aa97221c3e0a7ecf79c92'
# StudioNet gen_call resolves these contracts using their deployed address case.
JUDGE = '0x03E7970E791d644B2714a457D178Edf036670bb7'
SERIES = '0x0e355b80258869F6b42016185EBc0901F87C152C'
POOL = 50_000_000_000_000_000
REPORT = ROOT / 'deploy/milestone-recovery-verification.json'


def main():
    journal = json.loads((ROOT / 'deploy/milestone-recovery.json').read_text())
    frozen_path = ROOT / 'deploy/milestone-proof.json'
    if hashlib.sha256(frozen_path.read_bytes()).hexdigest() != journal['sourceProofSha256']:
        frozen_path = ROOT / 'deploy/previous-runs/milestone-v1-clean-stopped/deploy/milestone-proof.json'
    frozen = frozen_path.read_bytes()
    proof = json.loads(frozen)
    assert journal['completed'] and journal['status'] == 'RECOVERED' and not journal.get('stopReason')
    assert hashlib.sha256(frozen).hexdigest() == journal['sourceProofSha256']
    assert proof['stopReason'] and not proof['completed'] and len(proof['failures']) == 1
    assert int(rpc('eth_chainId', [])['result'], 16) == 61999
    assert journal['organizer'] == OWNER and journal['grossNewDepositsWei'] == '0'
    calls = {
        'season-close': (SERIES, 'close', ['series-1']),
        'season-refund': (SERIES, 'claim_refund', ['series-1', 1]),
        'season-verify-refund': (SERIES, 'verify_claim', ['series-1', OWNER, journal['transactions']['season-refund']]),
        'round-1-settle': (JUDGE, 'settle', ['challenge-5']),
        'round-1-claim': (JUDGE, 'claim', ['challenge-5']),
        'round-2-settle': (JUDGE, 'settle', ['challenge-6']),
        'round-2-refund': (JUDGE, 'claim_refund', ['challenge-6']),
    }
    transfers = {'season-refund': POOL, 'round-1-claim': 1, 'round-2-refund': 1}
    expected_names = set(calls) | {name + '-child-0' for name in calls}
    assert set(journal['transactions']) == expected_names and len(set(journal['transactions'].values())) == 14
    records = {}
    for name, tx_hash in journal['transactions'].items():
        receipt = rpc('eth_getTransactionByHash', [tx_hash])['result']
        assert receipt and receipt['hash'] == tx_hash
        if name in calls:
            successful(receipt)
            address, method, args = calls[name]
            assert receipt['from_address'].lower() == OWNER and receipt['to_address'].lower() == address.lower()
            assert int(receipt['value']) == 0
            assert decode(base64.b64decode(receipt['data']['calldata'])) == {'method': method, 'args': args}
            assert receipt['triggered_transactions'] == [journal['transactions'][name + '-child-0']]
        else:
            parent_name = name.removesuffix('-child-0')
            parent = records[parent_name]
            assert receipt['triggered_by'] == parent['hash'] and receipt['triggered_on'] == 'finalized'
            if parent_name in transfers:
                credited_transfer(receipt, parent, calls[parent_name][0], OWNER, transfers[parent_name])
            else:
                successful(receipt)
                assert receipt['from_address'].lower() == receipt['to_address'].lower() == calls[parent_name][0].lower()
                assert int(receipt['value']) == 0
            assert not receipt['triggered_transactions']
        records[name] = receipt
        print(name, tx_hash, 'FINALIZED VERIFIED', flush=True)
    series = view(SERIES, 'get_series', ['series-1'])
    assert series['status'] == 'CLOSED' and series['winners'] == [] and series['threshold'] == 2
    assert all(series['rounds'][key]['status'] == 'VOID' for key in ['challenge-5', 'challenge-6'])
    assert series['refund'] == str(POOL) and series['claims'][OWNER] == str(POOL)
    assert series['claim_attempts'][OWNER]['status'] == 'paid'
    balance = int(rpc('eth_getBalance', [SERIES, 'latest'])['result'], 16)
    assert balance == 0
    first = view(JUDGE, 'get_challenge', ['challenge-5'])
    second = view(JUDGE, 'get_challenge', ['challenge-6'])
    assert first['status'] == second['status'] == 'SETTLED'
    assert first['share'] == '1' and first['claims'][OWNER] == '1'
    assert second['share'] == '0' and second['refund'] == '1' and second['refund_claimed']
    assert hashlib.sha256(frozen_path.read_bytes()).hexdigest() == journal['sourceProofSha256']
    assert sum(transfers.values()) == int(journal['recoveredWei']) == POOL + 2
    result = dict(status='PASS', scope='Existing deposit recovery only; clean submission run remains failed.',
                  checkedAt=datetime.now(timezone.utc).isoformat(), chainId=61999,
                  transactionCount=len(records), nativeCredits=3, recipient=OWNER,
                  recoveredWei=str(POOL + 2), grossNewDepositsWei='0', seriesBalanceWei=str(balance),
                  failedRunPreserved=True, sourceProofSha256=journal['sourceProofSha256'],
                  credits=[dict(name=name, parent=journal['transactions'][name],
                               transfer=journal['transactions'][name + '-child-0'], amountWei=str(amount))
                           for name, amount in transfers.items()])
    REPORT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        REPORT.write_text(json.dumps(dict(status='FAIL', scope='Existing deposit recovery only', error=str(error)), indent=2) + '\n')
        raise
