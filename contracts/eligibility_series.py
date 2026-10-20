# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Fixed-threshold seasons; read-only judge/dispute dependencies; verified GEN claims."""
import json
import base64
from datetime import datetime
from genlayer.py import calldata
from genlayer import *

JUDGING_GRACE = 3600
DISPUTE_WINDOW = 7200
EXIT_GRACE = 86400
RECEIPT_RPC = 'https://studio.genlayer.com/api'


def require(condition, message):
    if not condition:
        raise gl.vm.UserError('[EXPECTED] ' + message)


def now():
    return int(datetime.fromisoformat(str(gl.message_raw['datetime']).replace('Z', '+00:00')).timestamp())


def wallet(value):
    return str(Address(value)).lower()


def receipt_hash(value):
    require(type(value) is str and len(value) == 66 and value.startswith('0x')
            and all(c in '0123456789abcdefABCDEF' for c in value[2:]), 'invalid receipt hash')
    return value.lower()


def protocol_receipt(tx_hash):
    response = gl.nondet.web.post(RECEIPT_RPC,
        body=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getTransactionByHash',
                         'params': [tx_hash]}).encode(),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 Eligibility Judge receipt verifier'})
    require(response.status == 200, 'protocol receipt unavailable; keep pending')
    payload = json.loads(response.body.decode('utf-8'))
    require('error' not in payload and type(payload.get('result')) is dict, 'protocol receipt unavailable; keep pending')
    tx = payload['result']
    require(receipt_hash(tx.get('hash')) == tx_hash, 'receipt hash mismatch')
    return tx


def successful_call(parent, contract, expected_call):
    require(parent.get('status') == 'FINALIZED', 'transaction is not finalized')
    require(str(parent.get('to_address', '')).lower() == contract, 'wrong receipt contract')
    leader = (parent.get('consensus_data') or {}).get('leader_receipt', [])
    require(parent.get('result') == 6 and leader and leader[0].get('execution_result') == 'SUCCESS', 'execution did not succeed')
    encoded = parent.get('data', {}).get('calldata')
    require(type(encoded) is str and calldata.decode(base64.b64decode(encoded, validate=True)) == expected_call,
            'receipt method or arguments mismatch')


def begin_claim(record, participant, attempt, balance, deposited, paid, method, args):
    previous = record['claim_attempts'].get(participant)
    require(participant not in record['claims'], 'claim already paid')
    require(previous is None or previous['status'] == 'failed', 'claim already pending')
    require(type(attempt) is int and attempt == (previous['attempt'] + 1 if previous else 1), 'use the next claim attempt')
    amount = int(record['allocations'].get(participant, '0'))
    require(amount > 0, 'no payout or refund for this wallet')
    require(balance >= amount, 'contract balance insufficient; retry after funds return')
    if previous is not None:
        require(balance >= deposited - paid, 'wait for refunds and other claim verification')
    record['claim_attempts'][participant] = {'attempt': attempt, 'amount': str(amount), 'status': 'pending',
        'claim_hash': None, 'transfer_hash': None, 'initiator': str(gl.message.sender_address).lower(),
        'call': {'method': method, 'args': args}}
    return amount


def observe_claim(record, participant, claim_hash):
    pending = record['claim_attempts'][participant]
    contract = str(gl.message.contract_address).lower()
    parent = protocol_receipt(claim_hash)
    successful_call(parent, contract, pending['call'])
    require(str(parent.get('from_address', '')).lower() == pending['initiator'], 'claim initiator mismatch')
    children = parent.get('triggered_transactions')
    require(type(children) is list and len(children) == 1, 'native transfer not available yet')
    child_hash = receipt_hash(children[0])
    child = protocol_receipt(child_hash)
    require(str(child.get('from_address', '')).lower() == contract
            and str(child.get('to_address', '')).lower() == participant
            and str(child.get('value')) == pending['amount'], 'transfer recipient or amount mismatch')
    require(child.get('type') == 0 and child.get('consensus_data') is None
            and child.get('triggered_on') == 'finalized', 'not a finalized native transfer emission')
    require(child.get('status') == 'FINALIZED', 'native transfer is still pending')
    credit = child.get('value_credited')
    require(type(credit) is bool, 'native credit is unknown; keep claim pending')
    return {'decision': 'paid' if credit else 'failed', 'transfer_hash': child_hash}


@gl.evm.contract_interface
class Recipient:
    class View:
        pass
    class Write:
        pass


class EligibilitySeries(gl.Contract):
    judge: Address
    disputes: Address
    items: TreeMap[str, str]
    ids: DynArray[str]
    counter: u256
    total_deposited: u256
    total_paid: u256

    def __init__(self, judge: str, disputes: str):
        require(not gl.message.value and int(gl.message.chain_id) == 61999, 'StudioNet constructor without GEN')
        self.judge = Address(judge)
        self.disputes = Address(disputes)
        self.counter = u256(0)
        self.total_deposited = u256(0)
        self.total_paid = u256(0)

    def _claim(self, series_id, participant, attempt, method, args):
        record = self._load(series_id)
        require(record['status'] == 'CLOSED', 'wait for finalized season settlement')
        amount = begin_claim(record, participant, attempt, int(self.balance), int(self.total_deposited), int(self.total_paid), method, args)
        self._save(series_id, record)
        Recipient(Address(participant)).emit_transfer(value=u256(amount))

    @gl.public.write
    def claim(self, series_id: str, attempt: int) -> None:
        self._claim(series_id, str(gl.message.sender_address).lower(), attempt, 'claim', [series_id, attempt])

    @gl.public.write
    def claim_refund(self, series_id: str, attempt: int) -> None:
        record = self._load(series_id)
        require(str(gl.message.sender_address).lower() == record['organizer'], 'organizer only')
        self._claim(series_id, record['organizer'], attempt, 'claim_refund', [series_id, attempt])

    @gl.public.write
    def claim_for(self, series_id: str, participant: str, attempt: int) -> None:
        self._claim(series_id, wallet(participant), attempt, 'claim_for', [series_id, participant, attempt])

    def _load(self, key):
        require(key in self.items, 'unknown series')
        return json.loads(self.items[key])

    def _save(self, key, record):
        self.items[key] = json.dumps(record, sort_keys=True, separators=(',', ':'))

    def _challenge(self, key):
        return json.loads(gl.get_contract_at(self.judge).view().get_challenge(key))

    def _round(self, record, key):
        challenge = self._challenge(key)
        if challenge['status'] != 'SETTLED':
            require(now() >= record['ends_at'], 'challenge not settled; wait for series end')
            return {'challenge_id': key, 'status': 'VOID', 'reason': 'Challenge was not SETTLED when imported at/after series end.', 'entries': {}}
        require(now() >= challenge['closes'] + JUDGING_GRACE + DISPUTE_WINDOW, 'dispute window still open')
        source = gl.get_contract_at(self.disputes).view()
        config = json.loads(source.get_config())
        require(config['judge'].lower() == str(self.judge).lower(), 'disputes judge mismatch')
        entries = {}
        for entrant in challenge['order']:
            result = json.loads(source.get_effective_verdicts(key, entrant))
            require(result['credentials_final'], 'disputes still pending; finalize or expire them')
            entries[entrant] = result['effective_status']
        return {'challenge_id': key, 'status': 'RECORDED', 'reason': '', 'entries': entries,
                'rulebook_hash': challenge['rulebook_hash']}

    @gl.public.write.payable
    def create_series(self, title: str, challenge_ids_json: str, threshold: int, ends_at: int) -> str:
        amount = int(gl.message.value)
        organizer = str(gl.message.sender_address).lower()
        self.counter = u256(int(self.counter) + 1)
        key = 'series-' + str(self.counter)
        record = {'id': key, 'title': title[:100], 'organizer': organizer, 'challenge_ids': [],
            'threshold': threshold, 'ends_at': ends_at, 'exit_deadline': now() + EXIT_GRACE,
            'created_at': now(), 'pool': str(amount), 'status': 'OPEN', 'rounds': {}, 'standings': [],
            'winners': [], 'share': '0', 'refund': '0', 'allocations': {}, 'claims': {}, 'claim_attempts': {}, 'version': 0}
        try:
            challenge_ids = json.loads(challenge_ids_json)
            require(3 <= len(title) <= 100, 'title must be 3-100 characters')
            require(type(challenge_ids) is list and 2 <= len(challenge_ids) <= 6
                    and all(type(x) is str and 1 <= len(x) <= 80 for x in challenge_ids)
                    and len(set(challenge_ids)) == len(challenge_ids), 'provide 2-6 unique judge challenges')
            require(type(threshold) is int and 1 <= threshold <= len(challenge_ids), 'invalid qualification threshold')
            require(now() < ends_at <= now() + 90 * 86400, 'series end must be within 90 days')
            require(0 < amount <= 1000 * 10**18, 'fund a positive bonus pool up to 1000 GEN')
            for cid in challenge_ids:
                source = self._challenge(cid)
                require(source['organizer'].lower() == organizer, 'all challenges must belong to the organizer')
                require(ends_at >= source['closes'] + JUDGING_GRACE + DISPUTE_WINDOW, 'series end precedes dispute window')
            record['challenge_ids'] = challenge_ids
            record['exit_deadline'] = ends_at + EXIT_GRACE
        except Exception as error:
            # StudioNet credits funded failures. Preserve every deposit with a
            # deterministic refundable record instead of reverting this write.
            record.update(status='CLOSING', reason='VOID_INVALID_INPUT: ' + str(error)[:300], refund=str(amount),
                          allocations={organizer: str(amount)}, version=1)
            record['pending_call'] = {'method': 'create_series', 'args': [title, challenge_ids_json, threshold, ends_at]}
        self.total_deposited = u256(int(self.total_deposited) + amount)
        self._save(key, record)
        self.ids.append(key)
        if record['status'] == 'CLOSING':
            gl.get_contract_at(gl.message.contract_address).emit(on='finalized').finalize_series(key, 1)
        return key

    @gl.public.write
    def record_round(self, series_id: str, challenge_id: str) -> None:
        record = self._load(series_id)
        require(record['status'] == 'OPEN', 'series not open')
        require(challenge_id in record['challenge_ids'] and challenge_id not in record['rounds'], 'unknown or already recorded round')
        record['rounds'][challenge_id] = self._round(record, challenge_id)
        self._save(series_id, record)

    @gl.public.write
    def close(self, series_id: str) -> None:
        record = self._load(series_id)
        require(record['status'] == 'OPEN', 'series not open')
        require(now() >= record['ends_at'] or len(record['rounds']) == len(record['challenge_ids']), 'series still running')
        # A hard whole-season VOID exit also covers permanently unreadable
        # dependencies and a late dispute whose finality callback never ran.
        if now() >= record['exit_deadline']:
            record.update(reason='VOID_TIMEOUT: season sources did not finalize before the exit deadline.',
                          winners=[], standings=[], share='0', refund=record['pool'],
                          allocations={record['organizer']: record['pool']})
        else:
            for cid in record['challenge_ids']:
                if cid not in record['rounds']:
                    record['rounds'][cid] = self._round(record, cid)
            wallets = sorted(set(w for r in record['rounds'].values() for w in r['entries']))
            standings = []
            for entrant in wallets:
                count, streak = 0, 0
                for cid in record['challenge_ids']:
                    round_record = record['rounds'][cid]
                    if round_record['status'] == 'VOID':
                        continue
                    if round_record['entries'].get(entrant) == 'QUALIFIED':
                        count += 1
                        streak += 1
                    else:
                        streak = 0
                standings.append({'wallet': entrant, 'qualification_count': count, 'current_streak': streak})
            winners = [s['wallet'] for s in standings if s['qualification_count'] >= record['threshold']]
            pool = int(record['pool'])
            share = pool // len(winners) if winners else 0
            refund = pool - share * len(winners)
            allocations = {w: str(share) for w in winners if share}
            if refund:
                allocations[record['organizer']] = str(int(allocations.get(record['organizer'], '0')) + refund)
            record.update(standings=standings, winners=winners, share=str(share), refund=str(refund), allocations=allocations)
        record['status'] = 'CLOSING'
        record['version'] += 1
        record['pending_call'] = {'method': 'close', 'args': [series_id]}
        self._save(series_id, record)
        gl.get_contract_at(gl.message.contract_address).emit(on='finalized').finalize_series(series_id, record['version'])

    @gl.public.write
    def finalize_series(self, series_id: str, version: int) -> None:
        require(gl.message.sender_address == gl.message.contract_address, 'self callback only')
        record = self._load(series_id)
        if record['status'] != 'CLOSING' or record['version'] != version:
            return
        record.update(status='CLOSED', finalized_at=now())
        self._save(series_id, record)

    @gl.public.write
    def verify_settlement(self, series_id: str, settlement_hash: str) -> None:
        record = self._load(series_id)
        require(record['status'] == 'CLOSING', 'no pending finality')
        tx_hash = receipt_hash(settlement_hash)
        def observe():
            successful_call(protocol_receipt(tx_hash), str(gl.message.contract_address).lower(), record['pending_call'])
            return tx_hash
        gl.eq_principle.strict_eq(observe)
        record.update(status='CLOSED', finalized_at=now())
        self._save(series_id, record)

    def _finish_claim(self, key, record, participant):
        pending = record['claim_attempts'][participant]
        if pending['status'] == 'paid_pending_finality':
            pending['status'] = 'paid'
            record['claims'][participant] = pending['amount']
            self.total_paid = u256(int(self.total_paid) + int(pending['amount']))
        elif pending['status'] == 'failed_pending_finality':
            pending['status'] = 'failed'
        self._save(key, record)

    @gl.public.write
    def verify_claim(self, series_id: str, participant: str, claim_hash: str) -> str:
        record = self._load(series_id)
        participant = wallet(participant)
        pending = record['claim_attempts'].get(participant)
        require(pending is not None, 'no claim attempt for this wallet')
        if pending['status'] in ('paid', 'failed'):
            return pending['status']
        tx_hash = receipt_hash(claim_hash)
        def inspect_native_credit():
            return observe_claim(record, participant, tx_hash)
        evidence = gl.eq_principle.strict_eq(inspect_native_credit)
        if pending['status'].endswith('_pending_finality'):
            require(pending['claim_hash'] == tx_hash and pending['transfer_hash'] == evidence['transfer_hash']
                    and pending['status'] == evidence['decision'] + '_pending_finality', 'verification evidence changed')
            self._finish_claim(series_id, record, participant)
        else:
            pending.update(status=evidence['decision'] + '_pending_finality', claim_hash=tx_hash, transfer_hash=evidence['transfer_hash'])
            self._save(series_id, record)
            gl.get_contract_at(gl.message.contract_address).emit(on='finalized').finalize_claim(series_id, participant, pending['attempt'])
        return record['claim_attempts'][participant]['status']

    @gl.public.write
    def finalize_claim(self, series_id: str, participant: str, attempt: int) -> None:
        require(gl.message.sender_address == gl.message.contract_address, 'self callback only')
        record = self._load(series_id)
        pending = record['claim_attempts'].get(participant)
        if pending is not None and pending['attempt'] == attempt:
            self._finish_claim(series_id, record, participant)

    @gl.public.view
    def get_series(self, series_id: str) -> str:
        return json.dumps(self._load(series_id), sort_keys=True, separators=(',', ':'))

    @gl.public.view
    def get_standings(self, series_id: str) -> str:
        return json.dumps(self._load(series_id)['standings'], sort_keys=True, separators=(',', ':'))

    @gl.public.view
    def get_series_ids(self) -> list[str]:
        return list(self.ids)

    @gl.public.view
    def get_balance(self) -> str:
        return str(self.balance)

    @gl.public.view
    def get_config(self) -> str:
        return json.dumps({'judge': str(self.judge).lower(), 'disputes': str(self.disputes).lower(), 'threshold_policy': 'FIXED_COUNT'})
