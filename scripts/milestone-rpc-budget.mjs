// Count actual SDK requests, across resumptions, below the brief's StudioNet limits.
import './explicit-fees.mjs';
import {readFileSync,writeFileSync,existsSync,mkdirSync} from 'node:fs';
const original=globalThis.fetch;
const ledger='.impeccable/review/milestone-v1/rpc-budget.json';
mkdirSync('.impeccable/review/milestone-v1',{recursive:true});
let queue=Promise.resolve();
globalThis.fetch=async(input,init)=>{
 let body;try{body=JSON.parse(typeof init?.body==='string'?init.body:'null')}catch{}
 if(!String(input).includes('studio.genlayer.com')||!body?.method)return original(input,init);
 if(['eth_gasPrice','eth_maxPriorityFeePerGas'].includes(body.method))return original(input,init);
 const reservation=queue.then(async()=>{
  for(;;){
   const now=Date.now();let times=existsSync(ledger)?JSON.parse(readFileSync(ledger,'utf8')):[];
   times=times.filter(t=>now-t<3600000);
   const minute=times.filter(t=>now-t<60000);
   const delay=Math.max(minute.length>=26?minute[0]+60050-now:0,times.length>=470?times[0]+3600050-now:0);
   if(delay>0){await new Promise(r=>setTimeout(r,Math.min(delay,10000)));continue;}
   times.push(now);writeFileSync(ledger,JSON.stringify(times));break;
  }
 });
 queue=reservation.catch(()=>{});await reservation;
 return original(input,{...init,headers:{...Object.fromEntries(new Headers(init?.headers)), 'User-Agent':'Mozilla/5.0 Eligibility Judge milestone'}});
};
