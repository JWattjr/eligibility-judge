import 'server-only';
import {createClient} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';
import {TransactionHashVariant} from 'genlayer-js/types';
import type {TransactionHash} from 'genlayer-js/types';
import proof from '../deploy/proof.json';
import {executionState} from './domain';
const client=createClient({chain:studionet});
const cache=new Map<string,{time:number;value:unknown}>();
const inFlight=new Map<string,Promise<unknown>>();
// Per-process budget below StudioNet limits. Vercel instances and other apps may share an IP.
let calls:number[]=[];
async function limited<T>(key:string,fn:()=>Promise<T>,ttl=5000):Promise<T>{const cached=cache.get(key);if(cached&&Date.now()-cached.time<ttl)return cached.value as T;const active=inFlight.get(key);if(active)return active as Promise<T>;calls=calls.filter(t=>Date.now()-t<3600000);if(calls.length>=450||calls.filter(t=>Date.now()-t<60000).length>=24)throw Error('RPC budget reached. Pause and retry in a minute.');calls.push(Date.now());const request=fn().then(value=>{cache.set(key,{time:Date.now(),value});return value}).finally(()=>inFlight.delete(key));inFlight.set(key,request);return request;}
export async function challenge(id:string){if(!proof.contract)throw Error('Contract deployment is not recorded yet.');return limited('challenge:'+id,async()=>({challenge:JSON.parse(String(await client.readContract({address:proof.contract as `0x${string}`,functionName:'get_challenge',args:[id],transactionHashVariant:TransactionHashVariant.LATEST_FINAL}))),balance:String(await client.readContract({address:proof.contract as `0x${string}`,functionName:'get_balance',args:[],transactionHashVariant:TransactionHashVariant.LATEST_FINAL})),readAt:new Date().toISOString()}),15000);}
export async function transaction(hash:string){return limited('tx:'+hash,async()=>{const receipt=await client.getTransaction({hash:hash as TransactionHash});const r=receipt as unknown as Record<string,unknown>;const state=executionState(r);let appealable=false;if(state==='ACCEPTED')try{appealable=await client.canAppeal({txId:hash as `0x${string}`})}catch{}const data=r.consensus_data as {leader_receipt?:{genvm_result?:{stderr?:string;error_description?:string};result?:unknown}[]}|undefined;return {hash,state,appealable,error:data?.leader_receipt?.[0]?.genvm_result?.error_description??data?.leader_receipt?.[0]?.genvm_result?.stderr??'',recipient:r.recipient??r.to_address,children:state==='FINALIZED_SUCCESS'?await client.getTriggeredTransactionIds({hash:hash as TransactionHash}):[]};});}
export async function wallet(address:string){return limited('wallet:'+address,async()=>({balance:String(await client.getBalance({address:address as `0x${string}`}))}),30000);}
