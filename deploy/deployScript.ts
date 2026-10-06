import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import type {GenLayerClient,TransactionHash} from 'genlayer-js/types';
import {TransactionHashVariant} from 'genlayer-js/types';
import {studionet} from 'genlayer-js/chains';
import {createClient} from 'genlayer-js';
import {generatePrivateKey,privateKeyToAccount} from 'viem/accounts';
// All writes carry explicit fees via a custom transport. SDK 1.1.8 does not expose fee fields on writeContract.
// genlayer CLI supplies the signing client; fee injection is installed in scripts/deploy.ps1.
const proofPath=process.env.ELIGIBILITY_PROOF_PATH??'deploy/proof.json';
const receiptDir=proofPath==='deploy/proof.json'?'deploy/receipts':proofPath==='deploy/repaired-proof.json'?'deploy/receipts/repaired':proofPath==='deploy/release-proof.json'?'deploy/receipts/release':proofPath==='deploy/hardened-proof.json'?'deploy/receipts/hardened':'deploy/receipts/diagnostic';
const sleep=(ms:number)=>new Promise(r=>setTimeout(r,ms));
const compact=(r:any)=>({hash:r.hash,status:r.statusName??r.status_name,execution:r.txExecutionResultName??r.consensus_data?.leader_receipt?.[0]?.execution_result,recipient:r.recipient??r.to_address,value:r.value,value_credited:r.value_credited,result:r.result_name??r.resultName,error:r.consensus_data?.leader_receipt?.[0]?.genvm_result});
export default async function main(client:GenLayerClient<typeof studionet>){
 const proof=JSON.parse(readFileSync(proofPath,'utf8'));mkdirSync(receiptDir,{recursive:true});
 const save=()=>{proof.recordedAt=new Date().toISOString();writeFileSync(proofPath,JSON.stringify(proof,null,2));};
 async function final(hash:string,name:string,transfer=false){
  let readFailures=0;
  for(let i=0;i<180;i++){
   let receipt:Awaited<ReturnType<typeof client.getTransaction>>;
   try{receipt=await client.getTransaction({hash:hash as TransactionHash});readFailures=0;}
   catch(error){
    const message=error instanceof Error?error.message:String(error);
    if(++readFailures>5||!/fetch failed|Unexpected token|ETIMEDOUT|ECONNRESET|timed out|Bad Gateway|\b50[234]\b/i.test(message))throw error;
    console.log(name,'Transient receipt read failure; retrying saved hash',readFailures);
    await sleep(10000);continue;
   }
   if((receipt.statusName??(receipt as any).status_name)==='FINALIZED'){
    writeFileSync(`${receiptDir}/${name}.json`,JSON.stringify(receipt,(_,v)=>typeof v==='bigint'?String(v):v,2));
    const c=compact(receipt);console.log(name,JSON.stringify(c,(_,v)=>typeof v==='bigint'?String(v):v));
    if(transfer){if(c.value_credited!==true)throw Error('Native transfer has no credit');}
    else if(!['SUCCESS','FINISHED_WITH_RETURN'].includes(c.execution)||(c.result&&!['AGREE','MAJORITY_AGREE','SUCCESS'].includes(c.result)))throw Error('Finalized execution failed: '+name);
    return receipt;
   }
   if(i%12===0)console.log(name,(receipt as any).status_name??receipt.statusName);
   await sleep(10000);
  }
  throw Error('Timed out; rerun to resume '+name);
 }
 async function write(name:string,method:string,args:any[],value=0n,signer=client){if(!proof.transactions[name]){proof.transactions[name]=await signer.writeContract({address:proof.contract,functionName:method,args,value});save();}await final(proof.transactions[name],name);const children=await client.getTriggeredTransactionIds({hash:proof.transactions[name]});if(['validate_rule','judge_rule','settle','claim','claim_refund'].includes(method)&&children.length!==1)throw Error('Missing finalized callback or transfer: '+name);for(let i=0;i<children.length;i++){proof.transactions[name+'-child-'+i]=children[i];save();await final(children[i],name+'-child-'+i,method==='claim'||method==='claim_refund');}return proof.transactions[name];}
 async function record(){if(proof.contract){proof.challenge=JSON.parse(String(await client.readContract({address:proof.contract,functionName:'get_challenge',args:[proof.challengeId],transactionHashVariant:TransactionHashVariant.LATEST_FINAL})));save();}}
 const step=process.env.ELIGIBILITY_STEP??'proof';
 if(step==='smoke'){
  if(!proof.transactions['smoke-deploy']){proof.transactions['smoke-deploy']=await client.deployContract({code:readFileSync('contracts/consensus_probe.py','utf8'),args:[]});save();}
  proof.contract=(await final(proof.transactions['smoke-deploy'],'smoke-deploy')).recipient;save();
  const samples=[
   {label:'fixture-tests',repo:'https://github.com/JWattjr/eligibility-judge-injection-fixture',commit:'5bed3a266836ddf8c06235cac1f6dc403676d94c',rule:'Contains at least one test file',expected:'PASS'},
   {label:'repo-readme',repo:'https://github.com/genlayerlabs/genlayer-js',commit:'1b7f50a3a3f2963ea857941b0fb386081dd5c326',rule:'README contains deployment instructions',expected:'INSUFFICIENT_EVIDENCE'},
   {label:'repo-tests',repo:'https://github.com/genlayerlabs/genlayer-js',commit:'1b7f50a3a3f2963ea857941b0fb386081dd5c326',rule:'Contains at least one test file',expected:'PASS'},
   {label:'repo-license',repo:'https://github.com/genlayerlabs/genlayer-js',commit:'1b7f50a3a3f2963ea857941b0fb386081dd5c326',rule:'Has an OSI-approved LICENSE file',expected:'PASS'},
  ];
  proof.samples??={};
  for(const sample of samples){
   if(proof.samples[sample.label]?.status===sample.expected)continue;
   await write('smoke-'+sample.label,'probe',[sample.label,sample.repo,sample.commit,sample.rule]);
   const answer=JSON.parse(String(await client.readContract({address:proof.contract,functionName:'get_sample',args:[sample.label],transactionHashVariant:TransactionHashVariant.LATEST_FINAL})));
   proof.samples[sample.label]={...sample,...answer};save();console.log('SMOKE',sample.label,answer.status);
   if(answer.status!==sample.expected)throw Error('Unexpected smoke outcome: '+sample.label);
  }
  proof.smokeVerified=true;save();
 }
 if(step==='probe'){
  if(!proof.transactions['probe-deploy']){proof.transactions['probe-deploy']=await client.deployContract({code:readFileSync('contracts/access_probe.py','utf8'),args:[]});save();}
  proof.probe=(await final(proof.transactions['probe-deploy'],'probe-deploy')).recipient;save();
  const urls=['https://raw.githubusercontent.com/genlayerlabs/genlayer-js/main/README.md','https://api.github.com/repos/genlayerlabs/genlayer-js','https://web.archive.org/web/20240101000000/https://example.com/'];
  proof.probes??={};
  for(let i=0;i<urls.length;i++){const name='probe-'+i;if(!proof.transactions[name]){proof.transactions[name]=await client.writeContract({address:proof.probe,functionName:'probe',args:[urls[i]],value:0n});save();}await final(proof.transactions[name],name);proof.probes[urls[i]]=JSON.parse(String(await client.readContract({address:proof.probe,functionName:'result',args:[urls[i]],transactionHashVariant:TransactionHashVariant.LATEST_FINAL})));save();}
 }
 if(step==='deploy'){
  if(!proof.transactions.deploy){proof.transactions.deploy=await client.deployContract({code:readFileSync('contracts/eligibility_judge.py','utf8'),args:[]});save();}
  proof.contract=(await final(proof.transactions.deploy,'deploy')).recipient;proof.contractSourceSha256=(await import('node:crypto')).createHash('sha256').update(readFileSync('contracts/eligibility_judge.py','utf8').replaceAll('\r\n','\n')).digest('hex');save();
 }
 if(step==='diagnose'){
  if(!proof.transactions['diagnostic-deploy']){proof.transactions['diagnostic-deploy']=await client.deployContract({code:readFileSync('contracts/citation_probe.py','utf8'),args:[]});save();}
  proof.contract=(await final(proof.transactions['diagnostic-deploy'],'diagnostic-deploy')).recipient;save();
  await write(process.env.ELIGIBILITY_DIAGNOSTIC_NAME??'diagnostic-license','probe',[process.env.ELIGIBILITY_DIAGNOSTIC_REPO??'https://github.com/genlayerlabs/genlayer-js',process.env.ELIGIBILITY_DIAGNOSTIC_COMMIT??'1b7f50a3a3f2963ea857941b0fb386081dd5c326',process.env.ELIGIBILITY_DIAGNOSTIC_RULE??'Has an OSI-approved LICENSE file']);
  proof.diagnostic=JSON.parse(String(await client.readContract({address:proof.contract,functionName:'result',args:[],transactionHashVariant:TransactionHashVariant.LATEST_FINAL})));save();console.log('CITATION DIAGNOSTIC',JSON.stringify(proof.diagnostic));
 }
 if(step==='seed'){
  const deposit=BigInt(process.env.ELIGIBILITY_DEMO_WEI??'3000000000000000000');
  if(Object.prototype.hasOwnProperty.call(proof,'approvedDemoDeposit')&&(proof.approvedDemoDeposit===null||deposit!==BigInt(proof.approvedDemoDeposit)))throw Error('Demo deposit must equal the authorized amount recorded in the manifest');
  proof.sourceCommit=proof.sourceCommit||execFileSync('git',['-c','safe.directory='+process.cwd(),'rev-parse','HEAD'],{encoding:'utf8'}).trim();save();
  const rules=['README contains deployment instructions','Contains a Python GenLayer Intelligent Contract that makes a web request','Has an OSI-approved LICENSE file','Contains at least one test file'];
  const time=Math.floor(Date.now()/1000);
  await write('create','create',['Ship a web-reading Intelligent Contract','Public code. Four checkable rules. Every qualifying entry shares the pool equally.',JSON.stringify(rules),time,time+1200,20],deposit);
  const created=JSON.parse(readFileSync(receiptDir+'/create.json','utf8'));
  const returnedId=JSON.parse(created.consensus_data?.leader_receipt?.[0]?.result?.payload?.readable??'null');
  if(typeof returnedId!=='string'||!/^challenge-\d+$/.test(returnedId))throw Error('Finalized creation did not return a challenge ID');
  proof.challengeId=returnedId;save();
  for(let i=0;i<rules.length;i++)await write('validate-rule-'+i,'validate_rule',[proof.challengeId,i]);
  await record();
 }
 if(step==='entries'){
  const keyPath='.env.demo-wallets.json';if(!existsSync(keyPath))writeFileSync(keyPath,JSON.stringify({failed:generatePrivateKey(),missing:generatePrivateKey(),injection:generatePrivateKey()}));
  const keys=JSON.parse(readFileSync(keyPath,'utf8'));proof.cases??={};
  const fixture=await fetch('https://api.github.com/repos/JWattjr/eligibility-judge-injection-fixture/commits/HEAD',{headers:{'User-Agent':'Eligibility-Judge'}}).then(r=>r.json()) as any;
  const failRepo=await fetch('https://api.github.com/repos/genlayerlabs/genlayer-js/commits/main',{headers:{'User-Agent':'Eligibility-Judge'}}).then(r=>r.json()) as any;
  const cases=[{name:'qualified',repo:'https://github.com/JWattjr/eligibility-judge',commit:proof.sourceCommit,expected:'QUALIFIED',signer:client},{name:'failed',repo:'https://github.com/genlayerlabs/genlayer-js',commit:failRepo.sha,expected:'DISQUALIFIED',signer:createClient({chain:studionet,account:privateKeyToAccount(keys.failed)})},{name:'missing',repo:'https://github.com/JWattjr/eligibility-judge',commit:'0'.repeat(40),expected:'INSUFFICIENT_EVIDENCE',signer:createClient({chain:studionet,account:privateKeyToAccount(keys.missing)})},{name:'injection',repo:'https://github.com/JWattjr/eligibility-judge-injection-fixture',commit:fixture.sha,expected:'DISQUALIFIED',signer:createClient({chain:studionet,account:privateKeyToAccount(keys.injection)})}];
  for(const c of cases){const wallet=c.signer.account!.address.toLowerCase();proof.cases[c.name]={wallet,repo:c.repo,commit:c.commit,expected:c.expected};save();const name='enter-'+c.name;if(!proof.transactions[name]){proof.transactions[name]=await c.signer.writeContract({address:proof.contract,functionName:'enter',args:[proof.challengeId,c.repo,c.commit,''],value:0n});save();console.log(name,proof.transactions[name]);}}
  for(const c of cases)await write('enter-'+c.name,'enter',[proof.challengeId,c.repo,c.commit,''],0n,c.signer);
  await record();
 }
 if(step==='judge'){
  for(const [name,c] of Object.entries(proof.cases) as [string,any][]){if(process.env.ELIGIBILITY_CASES&&!process.env.ELIGIBILITY_CASES.split(',').includes(name))continue;for(let i=0;i<4;i++){if(process.env.ELIGIBILITY_RULES&&!process.env.ELIGIBILITY_RULES.split(',').includes(String(i)))continue;if(proof.challenge?.entries[c.wallet]?.verdicts[i])continue;const key='judge-'+name+'-'+i;
    for(let retries=0;;retries++){
     try{await write(key,'judge_rule',[proof.challengeId,c.wallet,i]);await record();if(!proof.challenge.entries[c.wallet].verdicts[i])throw Error('No finalized rule verdict: '+key);break;}
     catch(error){
      const receiptPath=receiptDir+'/'+key+'.json';
      if(retries>=2||!existsSync(receiptPath))throw error;
      const receipt=JSON.parse(readFileSync(receiptPath,'utf8')),outcome=compact(receipt);
      if(receipt.hash!==proof.transactions[key]||outcome.status!=='FINALIZED'||(['SUCCESS','FINISHED_WITH_RETURN'].includes(outcome.execution)&&(!outcome.result||['AGREE','MAJORITY_AGREE','SUCCESS'].includes(outcome.result))))throw error;
      await record();const entry=proof.challenge.entries[c.wallet];if(entry.pending[i]||entry.verdicts[i])throw error;
      const attempt=Object.keys(proof.failedTransactions??{}).filter(k=>k.startsWith(key+'-attempt-')).length+1;
      proof.failedTransactions??={};proof.failedTransactions[key+'-attempt-'+attempt]={hash:receipt.hash,status:'FINALIZED_ERROR',leaderExecution:outcome.execution,reason:outcome.result+'; '+String(receipt.consensus_data?.leader_receipt?.[0]?.result?.payload??'rejected execution')};
      writeFileSync(receiptDir+'/'+key+'-attempt-'+attempt+'.json',JSON.stringify(receipt,null,2));delete proof.transactions[key];save();console.log('Retained failed attempt; retrying',key,attempt);await sleep(5000);
     }
    }}console.log(name,proof.challenge.entries[c.wallet].status);if(process.env.ELIGIBILITY_RULES&&!proof.challenge.entries[c.wallet].verdicts.every(Boolean))console.log('Partial rule selection; outcome remains incomplete',name);else if(proof.challenge.entries[c.wallet].status!==c.expected)throw Error('Demo outcome differs from expectation: '+name);}
 }
 if(step==='settle'){
  await record();if(Math.floor(Date.now()/1000)<proof.challenge.closes)throw Error('Window still open until '+new Date(proof.challenge.closes*1000).toISOString());
  await write('settle','settle',[proof.challengeId]);await record();
  const before=await client.getBalance({address:client.account!.address});
  await write('claim-qualified','claim',[proof.challengeId]);await record();
  const child=JSON.parse(readFileSync(receiptDir+'/claim-qualified-child-0.json','utf8'));
  if(child.value_credited!==true||String(child.value)!==proof.challenge.share||String(child.to_address).toLowerCase()!==client.account!.address.toLowerCase())throw Error('Payout credit mismatch');
  proof.transfers={qualified:{recipient:child.to_address,value:child.value,hash:child.hash,balanceBefore:String(before),balanceAfter:String(await client.getBalance({address:client.account!.address}))}};
  proof.payoutVerified=true;proof.completed=true;save();
 }
 if(step==='proof')await record();
}
