import {createHash} from 'node:crypto';
import {existsSync,mkdirSync,readFileSync,renameSync,writeFileSync} from 'node:fs';
import type {GenLayerClient,TransactionHash} from 'genlayer-js/types';
import {TransactionHashVariant} from 'genlayer-js/types';
import {studionet} from 'genlayer-js/chains';

const OWNER='0xdb433ff614bdd1ece21aa97221c3e0a7ecf79c92';
const JUDGE='0x03E7970E791d644B2714a457D178Edf036670bb7';
const SERIES='0x0e355b80258869F6b42016185EBc0901F87C152C';
const POOL='50000000000000000';
const proofPath='deploy/milestone-proof.json',journalPath='deploy/milestone-recovery.json';
const receiptDir='deploy/receipts/milestone-v1-clean-recovery';
const hash=(bytes:Uint8Array)=>createHash('sha256').update(bytes).digest('hex');
const requireState=(condition:unknown,message:string)=>{if(!condition)throw Error(message)};
const pause=()=>new Promise(r=>setTimeout(r,10000));

// Separate zero-deposit recovery. The failed clean-run journal is never written.
export default async function recover(client:GenLayerClient<typeof studionet>){
 const sourceBytes=readFileSync(proofPath),proof=JSON.parse(sourceBytes.toString('utf8'));
 const sourceHash=hash(sourceBytes),step=process.env.ELIGIBILITY_RECOVERY_STEP;
 requireState(step==='preview'||step==='recover','Use preview or recover');
 requireState(proof.run==='milestone-v1-clean'&&proof.stopReason&&!proof.completed,'Expected the stopped clean run');
 requireState(proof.judge===JUDGE&&proof.contracts.series.address===SERIES&&proof.seriesId==='series-1','Unexpected contracts');
 requireState(proof.organizer===OWNER&&client.account?.address.toLowerCase()===OWNER,'Frozen organizer must sign recovery');
 requireState(proof.grossDepositsWei==='50000000000000002'&&proof.failures.length===1,'Unexpected deposit or failure journal');
 requireState(proof.rounds.map((r:any)=>r.id).join(',')==='challenge-5,challenge-6','Unexpected challenges');
 const chainId=Number(BigInt(await client.request({method:'eth_chainId' as never,params:[] as never}) as string));
 requireState(chainId===61999,'Recovery is restricted to StudioNet 61999');
 const journal:any=existsSync(journalPath)?JSON.parse(readFileSync(journalPath,'utf8')):{
  run:'milestone-v1-clean-recovery',sourceProofSha256:sourceHash,sourceRun:proof.run,
  failedTransaction:proof.failures[0].hash,organizer:OWNER,judge:JUDGE,series:SERIES,chainId,
  authorization:'User explicitly approved: Recover existing deposits only.',
  grossNewDepositsWei:'0',expectedRecoveryWei:'50000000000000002',transactions:{},broadcasts:{},credits:[],completed:false
 };
 requireState(journal.sourceProofSha256===sourceHash,'Stopped proof changed; do not conceal or replace it');
 requireState(!journal.stopReason,'Recovery stopped: '+journal.stopReason);
 const save=()=>{journal.recordedAt=new Date().toISOString();writeFileSync(journalPath+'.tmp',JSON.stringify(journal,null,2)+'\n');renameSync(journalPath+'.tmp',journalPath)};
 mkdirSync(receiptDir,{recursive:true});
 const read=async(address:string,functionName:string,args:any[]=[])=>JSON.parse(String(await client.readContract({address:address as `0x${string}`,functionName,args,transactionHashVariant:TransactionHashVariant.LATEST_FINAL})));
 const successful=(r:any,native=false)=>r.statusName==='FINALIZED'&&(native?r.value_credited===true:r.result===6&&['SUCCESS','FINISHED_WITH_RETURN'].includes(r.txExecutionResultName??r.consensus_data?.leader_receipt?.[0]?.execution_result));
 async function final(txHash:string,name:string,native=false):Promise<any>{
  const path=`${receiptDir}/${name}.json`;
  if(existsSync(path)){const saved=JSON.parse(readFileSync(path,'utf8'));requireState(successful(saved,native),'Preserved failed recovery receipt '+name);return saved}
  for(let i=0;i<90;i++){
   let receipt:any;
   try{receipt=await client.getTransaction({hash:txHash as TransactionHash})}catch(error){console.log(name,'read unavailable; retaining same hash',String(error).slice(0,100));await pause();continue}
   if(receipt.statusName==='FINALIZED'){
    writeFileSync(path,JSON.stringify(receipt,(_,v)=>typeof v==='bigint'?String(v):v,2)+'\n');
    requireState(successful(receipt,native),'Recovery receipt failed; no retry: '+name+' '+txHash);
    console.log(name,txHash,native?'FINALIZED CREDITED':'FINALIZED SUCCESS');return receipt;
   }
   if(i%12===0)console.log(name,txHash,receipt.statusName);
   await pause();
  }
  throw Error('Recovery receipt timeout: retain the same saved hash '+txHash);
 }
 // The only writes in this runner are these seven fixed, zero-value calls.
 const calls:Record<string,{address:string,method:string,args:any[],nativeWei?:string}>={
  'season-close':{address:SERIES,method:'close',args:['series-1']},
  'season-refund':{address:SERIES,method:'claim_refund',args:['series-1',1],nativeWei:POOL},
  'season-verify-refund':{address:SERIES,method:'verify_claim',args:[]},
  'round-1-settle':{address:JUDGE,method:'settle',args:['challenge-5']},
  'round-1-claim':{address:JUDGE,method:'claim',args:['challenge-5'],nativeWei:'1'},
  'round-2-settle':{address:JUDGE,method:'settle',args:['challenge-6']},
  'round-2-refund':{address:JUDGE,method:'claim_refund',args:['challenge-6'],nativeWei:'1'}
 };
 async function send(name:string){
  requireState(step==='recover','Preview cannot broadcast');
  requireState(hash(readFileSync(proofPath))===sourceHash,'Stopped proof changed during recovery');
  const call=calls[name];requireState(call,'Call not allowed');
  if(name==='season-verify-refund')call.args=['series-1',OWNER,journal.transactions['season-refund']];
  if(!journal.transactions[name]){
   requireState(!journal.broadcasts[name],'Uncertain previous broadcast; reconcile before any new call: '+name);
   journal.broadcasts[name]={...call,value:'0',sender:OWNER,at:new Date().toISOString()};save();
   journal.transactions[name]=await client.writeContract({address:call.address as `0x${string}`,functionName:call.method,args:call.args,value:0n});save();
  }
  const parent=await final(journal.transactions[name],name);
  const children=parent.triggered_transactions??[];
  requireState(children.length===1,'Expected exactly one finality callback or native transfer: '+name);
  journal.transactions[name+'-child-0']=children[0];save();
  const child=await final(children[0],name+'-child-0',!!call.nativeWei);
  if(call.nativeWei){
   // SDK formatting omits the native type=0 field. Inspect the protocol record.
   const native:any=await client.request({method:'eth_getTransactionByHash' as never,params:[child.hash] as never});
   writeFileSync(`${receiptDir}/${name}-native-protocol.json`,JSON.stringify(native,null,2)+'\n');
   requireState((child.from_address??child.sender).toLowerCase()===call.address.toLowerCase()&&
    (child.to_address??child.recipient).toLowerCase()===OWNER&&String(child.value)===call.nativeWei&&
    native.type===0&&native.status==='FINALIZED'&&native.value_credited===true&&
    child.consensus_data===null&&child.triggered_on==='finalized'&&child.triggered_by===parent.hash,
    'Native credit recipient, amount or parent mismatch: '+name);
   if(!journal.credits.some((c:any)=>c.name===name))journal.credits.push({name,hash:child.hash,parent:parent.hash,recipient:OWNER,amountWei:call.nativeWei,valueCredited:true});save();
  }
 }
 try{
  const series=await read(SERIES,'get_series',['series-1']);
  const rounds=[];for(const id of ['challenge-5','challenge-6'])rounds.push(await read(JUDGE,'get_challenge',[id]));
  requireState(series.organizer===OWNER&&series.pool===POOL&&series.threshold===2,'Season changed');
  if(!journal.transactions['season-close']){
   requireState(series.status==='OPEN'&&!Object.keys(series.claims).length&&!Object.keys(series.allocations).length,'Season has unexpected claims or settlement');
   requireState(Date.now()/1000>=series.ends_at,'Wait for season end');
   requireState(rounds.every(r=>r.organizer===OWNER&&r.status==='RULES_ACCEPTED'&&r.pool==='1'),'Close season before settling either original pool');
   requireState(rounds.every(r=>Date.now()/1000>=r.closes+3600),'Original judging grace remains open');
  }
  journal.preview={at:new Date().toISOString(),seriesStatus:series.status,roundStatuses:rounds.map(r=>r.status),
   strategy:'Close the expired season while both original challenges remain unsettled: both imports VOID, zero winners, full organizer refund. Then settle and recover the original one-wei allocations.',
   grossNewDepositsWei:'0',calls:Object.entries(calls).map(([name,c])=>({name,...c,args:name==='season-verify-refund'?['series-1',OWNER,'<saved season-refund hash>']:c.args,valueWei:'0'}))};save();
  if(step==='preview'){console.log(JSON.stringify(journal.preview,null,2));return}
  if(journal.completed){console.log('Recovery already completed; no writes');return}
  await send('season-close');
  let closed=await read(SERIES,'get_series',['series-1']);
  requireState(closed.status==='CLOSED'&&closed.winners.length===0&&closed.refund===POOL&&closed.allocations[OWNER]===POOL,'Season did not produce full organizer refund');
  await send('season-refund');await send('season-verify-refund');
  closed=await read(SERIES,'get_series',['series-1']);
  requireState(closed.claims[OWNER]===POOL&&closed.claim_attempts[OWNER].status==='paid','Season refund not verified as paid');
  journal.series=closed;save();
  for(let i=0;i<2;i++){
   await send(`round-${i+1}-settle`);
   const round=await read(JUDGE,'get_challenge',[`challenge-${i+5}`]);
   requireState(round.status==='SETTLED'&&round.qualifiers.length===(i===0?1:2)&&round.share===(i===0?'1':'0')&&round.refund===(i===0?'0':'1'),'Original allocation changed');
   if(i===0)requireState(round.qualifiers[0]===OWNER,'Unexpected round-one beneficiary');
   await send(i===0?'round-1-claim':'round-2-refund');
  }
  journal.rounds=[];for(const id of ['challenge-5','challenge-6'])journal.rounds.push(await read(JUDGE,'get_challenge',[id]));
  requireState(journal.rounds[0].claims[OWNER]==='1'&&journal.rounds[1].refund_claimed===true,'Original exits not recorded');
  journal.seriesBalanceWei=String(await client.getBalance({address:SERIES}));
  requireState(journal.seriesBalanceWei==='0','Season still holds funds');
  journal.recoveredWei=journal.credits.reduce((sum:bigint,c:any)=>sum+BigInt(c.amountWei),0n).toString();
  requireState(journal.credits.length===3&&journal.recoveredWei===journal.expectedRecoveryWei,'Unexpected total recovery');
  requireState(hash(readFileSync(proofPath))===sourceHash,'Original stopped manifest changed');
  journal.completed=true;journal.status='RECOVERED';save();
  console.log('RECOVERED',journal.recoveredWei,'wei; zero new deposits; failed live case preserved');
 }catch(error){journal.status='STOPPED';journal.stopReason=String(error);save();throw error}
}
