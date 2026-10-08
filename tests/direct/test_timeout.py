import json
import pytest
from test_eligibility import contract, accept, enter, judge_all, state, self_call, warp, T, REPO, SHA

GRACE = 3600
CLOSES = T + 100

def test_unjudged_entry_cannot_settle_before_close_or_during_grace(contract, direct_vm, direct_alice):
    accept(contract, direct_vm)
    enter(contract, direct_vm, direct_alice)
    warp(direct_vm, CLOSES - 1)
    with direct_vm.expect_revert('challenge must close'):
        contract.settle('challenge-1')
    for timestamp in (CLOSES, CLOSES + GRACE - 1):
        warp(direct_vm, timestamp)
        with direct_vm.expect_revert('judging grace must expire'):
            contract.settle('challenge-1')

@pytest.mark.parametrize('qualified', [False, True])
def test_grace_timeout_never_qualifies_unjudged_entry_and_releases_pool(contract, direct_vm, direct_alice, direct_bob, qualified):
    accept(contract, direct_vm)
    unfinished = enter(contract, direct_vm, direct_alice)
    qualifier = None
    if qualified:
        qualifier = enter(contract, direct_vm, direct_bob)
        judge_all(contract, direct_vm, qualifier)
    warp(direct_vm, CLOSES + GRACE)
    contract.settle('challenge-1')
    record = state(contract)
    entry = record['entries'][unfinished]
    assert entry['status'] == 'INSUFFICIENT_EVIDENCE'
    assert entry['resolution_reason'] == 'Judgment did not finalize before the grace deadline.'
    assert entry['verdicts'] == [None] * 4  # No invented validator verdicts.
    assert entry['pending'] == [False] * 4
    assert record['qualifiers'] == ([qualifier] if qualified else [])
    assert record['share'] == ('11' if qualified else '0')
    assert record['refund'] == ('0' if qualified else '11')
    self_call(direct_vm, contract.finalize_settlement, 'challenge-1')
    assert state(contract)['status'] == 'SETTLED'

def test_final_entries_still_settle_at_close(contract, direct_vm, direct_alice):
    accept(contract, direct_vm)
    wallet = enter(contract, direct_vm, direct_alice)
    judge_all(contract, direct_vm, wallet)
    warp(direct_vm, CLOSES)
    contract.settle('challenge-1')
    assert state(contract)['qualifiers'] == [wallet]
    assert state(contract)['share'] == '11'

@pytest.mark.parametrize('timestamp', [CLOSES + GRACE, CLOSES + GRACE + 1])
def test_new_judgment_is_rejected_at_and_after_grace_deadline(contract, direct_vm, direct_alice, timestamp):
    accept(contract, direct_vm)
    wallet = enter(contract, direct_vm, direct_alice)
    warp(direct_vm, timestamp)
    with direct_vm.expect_revert('judging grace deadline reached'):
        contract.judge_rule('challenge-1', wallet, 0)

def test_pending_judgment_late_callback_is_noop_during_and_after_settlement(contract, direct_vm, direct_alice):
    from test_eligibility import mock_evidence
    accept(contract, direct_vm)
    wallet = enter(contract, direct_vm, direct_alice)
    mock_evidence(direct_vm)
    answer = json.dumps({'status':'PASS','path':'README.md','quote':'Deploy with genlayer deploy.','reason':'Verified'})
    direct_vm.mock_llm(r'.*ELIGIBILITY_RULE_JUDGMENT.*', answer)
    contract.judge_rule('challenge-1', wallet, 0)
    assert state(contract)['entries'][wallet]['status'] == 'JUDGING'
    warp(direct_vm, CLOSES + GRACE)
    contract.settle('challenge-1')
    before = contract.get_challenge('challenge-1')
    self_call(direct_vm, contract.finalize_judgment, 'challenge-1', wallet, 1, 0, answer)
    assert contract.get_challenge('challenge-1') == before
    self_call(direct_vm, contract.finalize_settlement, 'challenge-1')
    before = contract.get_challenge('challenge-1')
    self_call(direct_vm, contract.finalize_judgment, 'challenge-1', wallet, 1, 0, 'not even JSON')
    assert contract.get_challenge('challenge-1') == before

def test_reentry_just_before_close_receives_grace_timeout(contract, direct_vm, direct_alice):
    accept(contract, direct_vm)
    wallet = enter(contract, direct_vm, direct_alice)
    judge_all(contract, direct_vm, wallet, 'FAIL')
    warp(direct_vm, CLOSES - 1)
    enter(contract, direct_vm, direct_alice, 'b' * 40)
    warp(direct_vm, CLOSES + GRACE)
    contract.settle('challenge-1')
    entry = state(contract)['entries'][wallet]
    assert entry['attempt'] == 2 and len(entry['history']) == 1
    assert entry['status'] == 'INSUFFICIENT_EVIDENCE'
    assert state(contract)['refund'] == '11'

def test_raw_wayback_demo_accepted(contract, direct_vm, direct_alice):
    accept(contract, direct_vm)
    direct_vm.sender = direct_alice
    demo = 'https://web.archive.org/web/20260101000000id_/https://example.com/'
    contract.enter('challenge-1', REPO, SHA, demo)
    assert next(iter(state(contract)['entries'].values()))['demo'] == demo

@pytest.mark.parametrize('demo', [
    'https://web.archive.org/web/20260101000000/https://example.com/',
    'https://web.archive.org.evil/web/20260101000000id_/https://example.com/',
    'https://archive.org/web/20260101000000id_/https://example.com/',
    'https://web.archive.org/web/2026010100000id_/https://example.com/',
])
def test_nonraw_demo_urls_rejected(contract, direct_vm, direct_alice, demo):
    accept(contract, direct_vm)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert('raw snapshot'):
        contract.enter('challenge-1', REPO, SHA, demo)
