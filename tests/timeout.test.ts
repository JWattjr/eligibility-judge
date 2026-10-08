import {test} from 'node:test';
import assert from 'node:assert/strict';
import {canSettleChallenge,RAW_ARCHIVE_PATTERN,JUDGING_GRACE} from '../lib/domain';
import type {Challenge} from '../lib/domain';
const challenge={status:'RULES_ACCEPTED',closes:100,order:['alice'],entries:{alice:{status:'SUBMITTED'}}} as unknown as Challenge;
test('settlement UI opens for final entries at close and unfinished entries only at the grace boundary',()=>{
 assert.equal(canSettleChallenge(challenge,99),false);
 assert.equal(canSettleChallenge(challenge,100),false);
 assert.equal(canSettleChallenge(challenge,100+JUDGING_GRACE-1),false);
 assert.equal(canSettleChallenge(challenge,100+JUDGING_GRACE),true);
 assert.equal(canSettleChallenge({...challenge,status:'SETTLED'},100+JUDGING_GRACE),false);
 assert.equal(canSettleChallenge({...challenge,entries:{alice:{...challenge.entries.alice,status:'QUALIFIED'}}},100),true);
});
test('entry form requires the identical raw Wayback shape accepted by the contract',()=>{
 const pattern=new RegExp(RAW_ARCHIVE_PATTERN);
 assert.equal(pattern.test('https://web.archive.org/web/20260101000000id_/https://example.com/'),true);
 assert.equal(pattern.test('https://web.archive.org/web/20260101000000/https://example.com/'),false);
 assert.equal(pattern.test('https://web.archive.org.evil/web/20260101000000id_/https://example.com/'),false);
});
