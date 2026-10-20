import test from 'node:test';
import assert from 'node:assert/strict';
import {credentialReady,disputeOpen,effectiveStatus,nextAttempt,claimAvailable,fixedThresholdWinners,badgeLink} from '../lib/milestone-domain';
test('credentials wait for both the opening window and all pending hearings',()=>{assert.equal(credentialReady(100,0,10899),false);assert.equal(credentialReady(100,1,10900),false);assert.equal(credentialReady(100,0,10900),true)});
test('a settled challenge rejects disputes at the exact window boundary',()=>{assert.equal(disputeOpen('SETTLED',100,10899),true);assert.equal(disputeOpen('SETTLED',100,10900),false);assert.equal(disputeOpen('RULES_ACCEPTED',100,101),false)});
test('a void round never lowers the selected qualification count',()=>{assert.deepEqual(fixedThresholdWinners([{wallet:'a',qualification_count:1},{wallet:'b',qualification_count:2}],2),['b'])});
test('effective status retains fail precedence and never invents missing passes',()=>{assert.equal(effectiveStatus([{status:'PASS'},null]),'INSUFFICIENT_EVIDENCE');assert.equal(effectiveStatus([{status:'FAIL'},null]),'DISQUALIFIED');assert.equal(effectiveStatus([{status:'PASS'}]),'QUALIFIED')});
test('paid and pending native claims cannot be claimed again; confirmed failed transfers can retry',()=>{const failed={attempt:1,amount:'11',status:'failed',claim_hash:null,transfer_hash:null};assert.equal(nextAttempt(failed),2);assert.equal(nextAttempt({...failed,status:'pending'}),null);assert.equal(claimAvailable({a:'11'},{a:'11'},{},'a'),false);assert.equal(claimAvailable({a:'11'},{},{a:failed},'a'),true)});
test('embeddable badge link pins wallet and challenge',()=>{assert.equal(badgeLink('0xabc','challenge-3',true),'/badges/0xabc?challenge=challenge-3&embed=1')});
