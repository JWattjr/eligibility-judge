import test from 'node:test';
import assert from 'node:assert/strict';
import {studioAppealDeadline} from '../lib/domain';

const accepted={statusName:'ACCEPTED',leader_only:false,appealed:false,timestamp_awaiting_finalization:1000,appeal_processing_time:0,appeal_failed:0};
test('native Studio appeal deadline uses the actual window, processing time and failed appeals',()=>{
 assert.equal(studioAppealDeadline(accepted,60),1060);
 assert.equal(studioAppealDeadline({...accepted,appeal_processing_time:12,appeal_failed:1},60),1060);
 assert.equal(studioAppealDeadline({...accepted,appeal_failed:2},100),1064);
});
test('finalized, leader-only and already appealed transactions cannot offer an appeal',()=>{
 for(const change of [{statusName:'FINALIZED'},{statusName:'PENDING'},{leader_only:true},{appealed:true}])assert.equal(studioAppealDeadline({...accepted,...change},60),null);
});
test('native undecided and timeout states retain their appeal window',()=>{
 for(const state of ['UNDETERMINED','LEADER_TIMEOUT','VALIDATORS_TIMEOUT'])assert.equal(studioAppealDeadline({...accepted,statusName:state},60),1060);
});
test('missing native timestamps and invalid window configuration fail closed',()=>{
 assert.equal(studioAppealDeadline({...accepted,timestamp_awaiting_finalization:undefined},60),null);
 assert.equal(studioAppealDeadline({...accepted,appeal_failed:-1},60),null);
 assert.equal(studioAppealDeadline(accepted,NaN),null);
 assert.equal(studioAppealDeadline(accepted,60,1),null);
});
