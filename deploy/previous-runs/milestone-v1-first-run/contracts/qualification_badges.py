# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Non-transferable qualifications minted only after every hearing is final. No stake or LLM."""
import json
import hashlib
from datetime import datetime
from genlayer import *

JUDGING_GRACE = 3600
DISPUTE_WINDOW = 7200


def require(condition, message):
    if not condition:
        raise gl.vm.UserError('[EXPECTED] ' + message)


def now():
    return int(datetime.fromisoformat(str(gl.message_raw['datetime']).replace('Z', '+00:00')).timestamp())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class QualificationBadges(gl.Contract):
    judge: Address
    disputes: Address
    items: TreeMap[str, str]
    wallets: TreeMap[str, str]

    def __init__(self, judge: str, disputes: str):
        require(not gl.message.value and int(gl.message.chain_id) == 61999, 'StudioNet constructor without GEN')
        self.judge = Address(judge)
        self.disputes = Address(disputes)

    def _id(self, challenge_id, entrant):
        return 'badge-' + digest([challenge_id, entrant])

    @gl.public.write
    def mint(self, challenge_id: str, entrant: str) -> str:
        entrant = str(Address(entrant)).lower()
        key = self._id(challenge_id, entrant)
        require(key not in self.items, 'badge already minted')
        source = json.loads(gl.get_contract_at(self.judge).view().get_challenge(challenge_id))
        require(source['status'] == 'SETTLED' and entrant in source['entries'], 'settled judge entry required')
        require(now() >= source['closes'] + JUDGING_GRACE + DISPUTE_WINDOW, 'dispute window still open')
        disputes = gl.get_contract_at(self.disputes).view()
        require(json.loads(disputes.get_config())['judge'].lower() == str(self.judge).lower(), 'disputes judge mismatch')
        effective = json.loads(disputes.get_effective_verdicts(challenge_id, entrant))
        require(effective['credentials_final'], 'all disputes must finalize before minting')
        require(effective['effective_status'] == 'QUALIFIED', 'entry is not effectively qualified')
        entry = source['entries'][entrant]
        badge = {'id': key, 'challenge_id': challenge_id, 'title': source['title'], 'rulebook_hash': source['rulebook_hash'],
            'repo': entry['repo'], 'commit': entry['commit'], 'wallet': entrant, 'via_dispute': effective['via_dispute'],
            'effective_verdicts_digest': digest(effective['effective_verdicts']), 'minted_at': now(),
            'judge': str(self.judge).lower(), 'disputes': str(self.disputes).lower(), 'transferable': False}
        self.items[key] = json.dumps(badge, sort_keys=True, separators=(',', ':'))
        ids = json.loads(self.wallets.get(entrant, '[]'))
        ids.append(key)
        self.wallets[entrant] = json.dumps(ids)
        return key

    @gl.public.view
    def get_badges(self, wallet: str) -> str:
        entrant = str(Address(wallet)).lower()
        return json.dumps([json.loads(self.items[key]) for key in json.loads(self.wallets.get(entrant, '[]'))], sort_keys=True, separators=(',', ':'))

    @gl.public.view
    def verify(self, wallet: str, challenge_id: str) -> bool:
        return self._id(challenge_id, str(Address(wallet)).lower()) in self.items

    @gl.public.view
    def get_badge(self, badge_id: str) -> str:
        require(badge_id in self.items, 'unknown badge')
        return self.items[badge_id]

    @gl.public.view
    def get_config(self) -> str:
        return json.dumps({'judge': str(self.judge).lower(), 'disputes': str(self.disputes).lower()})
