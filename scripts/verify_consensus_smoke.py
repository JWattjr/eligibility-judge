"""Read-only zero-value consensus verification; never proves a prize payout."""
import base64
import hashlib
import importlib.metadata
import json
import time
from pathlib import Path
from eth_account import Account
from genlayer_py import create_client, studionet
from genlayer_py.types import TransactionHashVariant

assert importlib.metadata.version('genlayer-py') == '0.18.0'
root = Path(__file__).resolve().parent.parent
proof = json.loads((root / 'deploy/consensus-smoke-proof.json').read_text(encoding='utf8'))
client = create_client(chain=studionet, account=Account.create())
assert proof['smokeVerified'], 'Consensus smoke is incomplete'
for name, tx_hash in proof['transactions'].items():
    response = client.provider.make_request('eth_getTransactionByHash', [tx_hash])
    assert not response.get('error'), str(response.get('error'))
    receipt = response['result']
    assert receipt.get('status_name', receipt.get('status')) == 'FINALIZED'
    assert receipt['result_name'] in ('AGREE', 'MAJORITY_AGREE', 'SUCCESS')
    assert receipt['consensus_data']['leader_receipt'][0]['execution_result'] == 'SUCCESS'
    assert receipt.get('value') in (None, 0, '0', '0x0')
    assert receipt.get('value_credited') is not True
    assert not receipt.get('triggered_transactions'), 'Smoke unexpectedly emitted a transaction'
    print(name, tx_hash, 'FINALIZED SUCCESS, ZERO VALUE')
    time.sleep(2.6)
for label, expected in proof['samples'].items():
    actual = json.loads(client.read_contract(proof['contract'], 'get_sample', [label], transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert actual['status'] == expected['expected']
    assert actual == {key: expected[key] for key in actual}
    assert len(actual['quote']) <= 600
    print(label, actual['status'], actual['path'])
    time.sleep(2.6)
local = (root / 'contracts/consensus_probe.py').read_text(encoding='utf8')
main = (root / 'contracts/eligibility_judge.py').read_text(encoding='utf8')
assert local.startswith(main.split('@gl.evm.contract_interface', 1)[0]), 'Adjudication helpers differ'
assert hashlib.sha256(main.encode()).hexdigest() == proof['candidateSourceSha256']
assert hashlib.sha256(local.encode()).hexdigest() == proof['probeSourceSha256']
response = client.provider.make_request('gen_getContractCode', [proof['contract']])
assert not response.get('error'), str(response.get('error'))
deployed = response['result']
if deployed.startswith('0x'):
    deployed = bytes.fromhex(deployed[2:]).decode()
elif not deployed.startswith('#'):
    deployed = base64.b64decode(deployed).decode()
assert deployed.replace('\r\n', '\n') == local
print('Verified', len(proof['samples']), 'finalized consensus regressions and exact source; no funding or payout proof is claimed.')
