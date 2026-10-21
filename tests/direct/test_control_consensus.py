"""Exercise the immutable judge's real validator closure; mocks are not live proof."""
import json
from pathlib import Path

import pytest
from test_eligibility import T, self_call, warp
from conftest import to_hex


@pytest.fixture
def negative_judgment(direct_vm, direct_deploy, direct_owner, direct_alice):
    direct_vm._chain_id = 61999
    direct_vm.sender = direct_owner
    warp(direct_vm, T)
    judge = direct_deploy('contracts/eligibility_judge.py')
    rules = ['README documents a deployed StudioNet GenLayer address',
             'A Python GenLayer intelligent contract implements a native GEN payout using emit_transfer(value=...).',
             'LICENSE declares the MIT license']
    direct_vm.value = 1
    judge.create('Negative control', 'Clearly labeled owner-operated test fixture', json.dumps(rules), T, T + 900, 3)
    direct_vm.value = 0
    accepted = {'accepted': True, 'reason': 'Publicly checkable objective rule'}
    for index in range(3):
        direct_vm.mock_llm(r'.*ELIGIBILITY_RULE_VALIDATION.*', json.dumps(accepted))
        judge.validate_rule('challenge-1', index)
        self_call(direct_vm, judge.finalize_rule, 'challenge-1', index, json.dumps(accepted))
        direct_vm.clear_mocks()
    direct_vm.sender = direct_alice
    judge.enter('challenge-1', 'https://github.com/JWattjr/eligibility-judge-injection-fixture', 'a' * 40, '')
    files = {'README.md': 'Public negative fixture. No deployed StudioNet address is published.',
             'LICENSE': 'MIT License',
             'contracts/negative_control.py': Path('docs/fixtures/negative_control.py').read_text()}
    direct_vm.mock_web(r'.*api\.github\.com.*', {'status': 200, 'body': json.dumps({'truncated': False, 'tree': [{'path': p, 'type': 'blob'} for p in files]})})
    for path, body in files.items():
        direct_vm.mock_web(r'.*raw\.githubusercontent\.com.*/' + path.replace('.', r'\.') + '$', {'status': 200, 'body': body})
    answer = {'status': 'FAIL', 'path': 'contracts/negative_control.py',
              'quote': "raise gl.vm.UserError('Native GEN payouts are not implemented in this deliberately negative fixture.')",
              'reason': 'The complete claim implementation only raises an error and cannot pay native GEN.'}
    direct_vm.mock_llm(r'.*ELIGIBILITY_RULE_JUDGMENT.*', json.dumps(answer))
    judge.judge_rule('challenge-1', to_hex(direct_alice).lower(), 1)
    return judge


def test_explicit_negative_code_is_independently_accepted(negative_judgment, direct_vm):
    direct_vm.mock_llm(r'.*ELIGIBILITY_CITATION_VERIFY.*', json.dumps({'valid': True}))
    assert direct_vm.run_validator() is True


def test_failed_citation_confirmation_rejects_without_vm_exception(negative_judgment, direct_vm):
    direct_vm.mock_llm(r'.*ELIGIBILITY_CITATION_VERIFY.*', json.dumps({'valid': False}))
    assert direct_vm.run_validator() is False


def test_validator_cannot_confirm_a_quote_after_tree_access_failure(negative_judgment, direct_vm):
    direct_vm.clear_mocks()
    direct_vm.mock_web(r'.*api\.github\.com.*', {'status': 403, 'body': 'rate limited'})
    assert direct_vm.run_validator() is False


def test_negative_control_reverts_instead_of_paying(direct_vm, direct_deploy, direct_owner):
    direct_vm.sender = direct_owner
    control = direct_deploy('docs/fixtures/negative_control.py')
    assert control.status() == 'Undeployed negative control fixture'
    with direct_vm.expect_revert('not implemented'):
        control.claim()
