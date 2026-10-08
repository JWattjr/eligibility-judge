import 'server-only';
import {createClient} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';
import {TransactionHashVariant} from 'genlayer-js/types';
import type {TransactionHash} from 'genlayer-js/types';
import proof from '../deploy/proof.json';
import {executionState,executionError,nativeAppealReview,returnedChallengeId,studioAppealDeadline} from './domain';
const client=createClient({chain:studionet});
const cache=new Map<string,{time:number;value:unknown}>();
const inFlight=new Map<string,Promise<unknown>>();
// Per-process budget below StudioNet limits. Vercel instances and other apps may share an IP.
let calls:number[]=[];
async function limited<T>(key:string,fn:()=>Promise<T>,ttl=5000):Promise<T>{const cached=cache.get(key);const terminal=key.startsWith('tx:')&&['FINALIZED_SUCCESS','FINALIZED_ERROR'].includes(String((cached?.value as {state?:string}|undefined)?.state));if(cached&&(terminal||Date.now()-cached.time<ttl))return cached.value as T;const active=inFlight.get(key);if(active)return active as Promise<T>;calls=calls.filter(t=>Date.now()-t<3600000);const cost=key.startsWith('tx:')||key.startsWith('wallet:')||key==='studio:finality'?1:3;if(calls.length+cost>450||calls.filter(t=>Date.now()-t<60000).length+cost>24)throw Error('RPC budget reached. Pause and retry in a minute.');for(let i=0;i<cost;i++)calls.push(Date.now());const request=fn().then(value=>{cache.set(key,{time:Date.now(),value});return value}).finally(()=>inFlight.delete(key));inFlight.set(key,request);return request;}
export async function challenge(id:string){
 if(!proof.contract)throw Error('Contract deployment is not recorded yet.');
 return limited('challenge:'+id,async()=>{
  const address=proof.contract as `0x${string}`;
  const ids=await client.readContract({address,functionName:'get_challenge_ids',args:[],transactionHashVariant:TransactionHashVariant.LATEST_FINAL});
  if(!Array.isArray(ids)||ids.some(value=>typeof value!=='string'))throw Error('Invalid finalized challenge index');
  const record=ids.includes(id)?JSON.parse(String(await client.readContract({address,functionName:'get_challenge',args:[id],transactionHashVariant:TransactionHashVariant.LATEST_FINAL}))):null;
  return {challenge:record,balance:String(await client.readContract({address,functionName:'get_balance',args:[],transactionHashVariant:TransactionHashVariant.LATEST_FINAL})),readAt:new Date().toISOString()};
 },15000);
}
export async function transaction(hash:string){return limited('tx:'+hash,async()=>{const receipt=await client.getTransaction({hash:hash as TransactionHash});const r=receipt as unknown as Record<string,unknown>;const state=executionState(r);let appealable=false,appealDeadline:number|null=null;if(['ACCEPTED','UNDETERMINED','LEADER_TIMEOUT','VALIDATORS_TIMEOUT'].includes(state)){const windowSeconds=Number(await limited('studio:finality',()=>client.request({method:'sim_getFinalityWindowTime' as never}),300000));appealDeadline=studioAppealDeadline(r,windowSeconds,Number(process.env.STUDIONET_APPEAL_FAILED_REDUCTION??'0.2'));appealable=appealDeadline!==null&&Date.now()/1000<appealDeadline;}return {hash,state,appealable,appealDeadline,challengeId:returnedChallengeId(r),nativeAppealReview:nativeAppealReview(r),error:executionError(r),recipient:r.recipient??r.to_address,children:state==='FINALIZED_SUCCESS'&&Array.isArray(r.triggered_transactions)?r.triggered_transactions:[]};});}
export async function wallet(address:string){return limited('wallet:'+address,async()=>({balance:String(await client.getBalance({address:address as `0x${string}`}))}),30000);}
