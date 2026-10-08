"""Read-only verification of native appeal re-evaluation; never signs or funds."""
import json
from pathlib import Path
from genlayer_py import create_client, studionet
from genlayer_py.types import TransactionHashVariant
from eth_account import Account

root = Path(__file__).resolve().parent.parent
proof = json.loads((root / 'deploy/proof.json').read_text(encoding='utf8'))
appeals = json.loads((root / 'deploy/native-appeal-proof.json').read_text(encoding='utf8'))
client = create_client(chain=studionet, account=Account.create())
assert appeals['contract'] == proof['contract']
for case in appeals['verifiedCases']:
    response = client.provider.make_request('eth_getTransactionByHash', [case['hash']])
    assert not response.get('error'), response.get('error')
    record = response['result']
    assert record['status'] == 'FINALIZED'
    assert record['to_address'].lower() == proof['contract'].lower()
    assert record['value'] == 0
    assert record['timestamp_appeal'] is not None
    assert int(record['num_of_rounds']) >= 2
    assert len(record['consensus_history']['consensus_results']) >= 2
    assert record['appeal_failed'] >= 1
    assert record['consensus_data']['leader_receipt'][0]['execution_result'] == 'ERROR'
    print(case['channel'], case['hash'], 'FINALIZED: native re-evaluation upheld expected rollback')
challenge = json.loads(client.read_contract(proof['contract'], 'get_challenge', [proof['challengeId']], transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
assert challenge == proof['challenge'], 'Settled demonstration state changed'
assert int(client.read_contract(proof['contract'], 'get_balance', [], transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)) == 0
print('PASS: settled demo and zero contract balance are unchanged')
