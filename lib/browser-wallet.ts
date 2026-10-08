import {encodeFunctionData} from 'viem';
import {studionet} from 'genlayer-js/chains';

type WalletRequest = {method:string;params?:unknown[]};
type WalletProvider = {request:(args:WalletRequest)=>Promise<unknown>};

// SDK 1.1.8 may omit gasPrice when Studio's fee RPC fails. Its browser
// transactions use legacy type 0; pin the same explicit fee as the CLI path.
export function withStudioFees(wallet:WalletProvider,onSent?:(hash:string)=>void):WalletProvider{
 return {request:async(args)=>{
  if(!['eth_sendTransaction','eth_signTransaction'].includes(args.method))return wallet.request(args);
  const [transaction,...rest]=args.params??[];
  if(!transaction||typeof transaction!=='object'||Array.isArray(transaction))throw Error('Invalid wallet transaction.');
  const tx=transaction as Record<string,unknown>;
  if(tx.chainId!==undefined&&String(tx.chainId).toLowerCase()!=='0xf22f')throw Error('Wallet transaction must use StudioNet.');
  const result=await wallet.request({...args,params:[{...tx,value:tx.value??'0x0',chainId:'0xf22f',type:'0x0',gasPrice:'0x3b9aca00'},...rest]});
  if(args.method==='eth_sendTransaction'&&typeof result==='string'&&/^0x[0-9a-f]{64}$/i.test(result))onSent?.(result);
  return result;
 }};
}

// Use the pinned SDK's native consensus ABI and gas fallback. Avoid its three
// sequential nonce/estimate/fee reads before opening a 30-second wallet prompt.
// MetaMask signs and submits; the original transaction remains the outcome proof.
export async function requestStudioAppeal(wallet:WalletProvider,account:string,txId:string,deadline:number){
 if(!/^0x[0-9a-f]{40}$/i.test(account)||!/^0x[0-9a-f]{64}$/i.test(txId))throw Error('Connect a wallet and select a valid transaction.');
 if(await wallet.request({method:'eth_chainId'})!=='0xf22f')throw Error('Switch your selected wallet to StudioNet before appealing.');
 if(!Number.isFinite(deadline)||Date.now()/1000>=deadline)throw Error('The native appeal window has expired.');
 const consensus=studionet.consensusMainContract;
 if(!consensus?.address||!consensus.abi)throw Error('StudioNet native consensus configuration is unavailable.');
 const data=encodeFunctionData({abi:consensus.abi,functionName:'submitAppeal',args:[txId as `0x${string}`]});
 const result=await withStudioFees(wallet).request({method:'eth_sendTransaction',params:[{from:account,to:consensus.address,data,gas:'0x30d40',value:'0x0'}]});
 if(typeof result!=='string'||!/^0x[0-9a-f]{64}$/i.test(result))throw Error('Wallet returned an invalid native appeal receipt.');
 return result;
}
