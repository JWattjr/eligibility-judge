import {existsSync,mkdirSync,readFileSync,renameSync,writeFileSync} from 'node:fs';
import type {GenLayerClient,TransactionHash} from 'genlayer-js/types';
import {TransactionHashVariant} from 'genlayer-js/types';
import {studionet} from 'genlayer-js/chains';

const OWNER='0xdb433ff614bdd1ece21aa97221c3e0a7ecf79c92';
const JUDGE='0x03E7970E791d644B2714a457D178Edf036670bb7';
const FILE='deploy/prior-pool-recovery.json',DIR='deploy/receipts/prior-pool-recovery';
class RecoveryInvariant extends Error {}
class RecoveryPending extends Error {}
const ensure=(ok:unknown,message:string)=>{if(!ok)throw new RecoveryInvariant(message)};
const pause=()=>new Promise(r=>setTimeout(r,10000));
async function readRetry<T>(read:()=>Promise<T>):Promise<T>{
 for(let n=0;n<6;n++){
  try{return await read()}catch(error){
   if(n===5)throw new RecoveryPending('Read unavailable; resume the same saved recovery hashes: '+String(error));
   await pause();
  }
 }
 throw new RecoveryPending('Read unavailable');
}

// Two zero-value recovery calls, separately journaled from the clean live proof.
export default async function recoverPrior(client:GenLayerClient<typeof studionet>){
 const proof=JSON.parse(readFileSync('deploy/milestone-proof.json','utf8'));
 ensure(proof.run==='milestone-v1-release'&&proof.completed&&proof.stages.complete.status==='PASS','Finish the new workflow before recovering the prior pool');
 ensure(client.account?.address.toLowerCase()===OWNER&&proof.judge===JUDGE,'Frozen organizer and judge required');
 ensure(proof.priorStoppedPool?.challenge==='challenge-7'&&proof.priorStoppedPool.amountWei==='1','Only the documented one-wei pool may be recovered');
 const archived=JSON.parse(readFileSync(proof.previousRun+'/deploy/milestone-proof.json','utf8'));
 ensure(archived.stopReason&&archived.rounds[0].id==='challenge-7'&&archived.grossDepositsWei==='1','Stopped source proof does not match');
 const mode=process.env.ELIGIBILITY_PRIOR_POOL_RECOVERY;
 ensure(mode==='preview'||mode==='recover','Use preview or recover');
 const journal:any=existsSync(FILE)?JSON.parse(readFileSync(FILE,'utf8')):{
  run:'milestone-v1-prior-pool-recovery',judge:JUDGE,challenge:'challenge-7',organizer:OWNER,
  sourceFailure:archived.failures[0].hash,grossNewDepositsWei:'0',amountWei:'1',transactions:{},broadcasts:{},completed:false
 };
 ensure(!journal.stopReason,'Prior recovery stopped: '+journal.stopReason);
 const save=()=>{journal.recordedAt=new Date().toISOString();writeFileSync(FILE+'.tmp',JSON.stringify(journal,null,2)+'\n');renameSync(FILE+'.tmp',FILE)};
 const read=async()=>JSON.parse(String(await readRetry(()=>client.readContract({address:JUDGE,functionName:'get_challenge',args:['challenge-7'],transactionHashVariant:TransactionHashVariant.LATEST_FINAL}))));
 const success=(r:any,native=false)=>r.statusName==='FINALIZED'&&(native?r.value_credited===true:r.result===6&&r.consensus_data?.leader_receipt?.[0]?.execution_result==='SUCCESS');
 mkdirSync(DIR,{recursive:true});
 async function final(hash:string,name:string,native=false):Promise<any>{
  const file=DIR+'/'+name+'.json';
  if(existsSync(file)){const r=JSON.parse(readFileSync(file,'utf8'));ensure(r.hash===hash&&success(r,native),'Preserved failed or mismatched prior recovery receipt');return r}
  for(let n=0;n<90;n++){
   let r:any;try{r=await client.getTransaction({hash:hash as TransactionHash})}catch{await pause();continue}
   if(r.statusName==='FINALIZED'){writeFileSync(file,JSON.stringify(r,(_,v)=>typeof v==='bigint'?String(v):v,2));ensure(success(r,native),'Prior recovery failed: '+name);console.log(name,hash,native?'FINALIZED CREDITED':'FINALIZED SUCCESS');return r}
   await pause();
  }
  throw new RecoveryPending('Prior recovery pending; retain saved hash '+hash);
 }
 async function send(name:string,method:'settle'|'claim',native=false){
  ensure(mode==='recover','Preview cannot broadcast');
  if(!journal.transactions[name]){
   ensure(!journal.broadcasts[name],'Uncertain prior broadcast; reconcile without resending');
   journal.broadcasts[name]={address:JUDGE,method,args:['challenge-7'],value:'0',sender:OWNER};save();
   journal.transactions[name]=await client.writeContract({address:JUDGE,functionName:method,args:['challenge-7'],value:0n});save();
  }
  const parent=await final(journal.transactions[name],name);
  ensure(parent.triggered_transactions.length===1,'Expected one prior recovery callback or transfer');
  const childHash=parent.triggered_transactions[0];journal.transactions[name+'-child-0']=childHash;save();
  const child=await final(childHash,name+'-child-0',native);
  if(native){
   const raw:any=await readRetry(()=>client.request({method:'eth_getTransactionByHash' as never,params:[childHash] as never}));
   ensure(raw.type===0&&raw.status==='FINALIZED'&&raw.value_credited===true&&String(raw.value)==='1'&&raw.from_address.toLowerCase()===JUDGE.toLowerCase()&&raw.to_address.toLowerCase()===OWNER&&raw.triggered_by===parent.hash,'Wrong native recovery credit');
   journal.transfer=childHash;save();
  }
 }
 try{
  ensure(Number(BigInt(await readRetry(()=>client.request({method:'eth_chainId' as never,params:[] as never})) as string))===61999,'StudioNet only');
  const before=await read();ensure(before.organizer===OWNER&&before.pool==='1','Unexpected original pool');
  ensure(Date.now()/1000>=before.closes+3600,'Original judging grace remains open');
  if(journal.completed){console.log('Prior one-wei recovery already complete; no writes');return}
  if(mode==='preview'){console.log('Preview: settle challenge-7, claim its one-wei organizer/qualifier share; no new deposits.');return}
  if(before.status!=='SETTLED')await send('settle','settle');
  const settled=await read();ensure(settled.status==='SETTLED'&&settled.qualifiers.length===1&&settled.qualifiers[0]===OWNER&&settled.share==='1','Unexpected prior allocation');
  ensure(!settled.claims[OWNER]||journal.transactions.claim,'A prior claim already exists; reconcile its hash without sending another claim');
  await send('claim','claim',true);
  const after=await read();ensure(after.claims[OWNER]==='1','Prior claim not recorded');
  journal.judgeBalanceWei=String(await readRetry(()=>client.getBalance({address:JUDGE})));
  ensure(journal.judgeBalanceWei==='0','Original judge still holds an unexpected balance');
  journal.completed=true;journal.recoveredWei='1';journal.status='RECOVERED';delete journal.waitReason;save();
  console.log('Prior one-wei pool recovered; stopped case untouched; original judge balance zero.');
 }catch(error){
  if(error instanceof RecoveryPending){journal.status='WAITING_READ';journal.waitReason=String(error)}
  else{journal.status='STOPPED';journal.stopReason=String(error)}
  save();throw error;
 }
}
