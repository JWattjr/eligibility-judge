import {test} from 'node:test';
import assert from 'node:assert/strict';
import {withStudioFees,requestStudioAppeal} from '../lib/browser-wallet';
import {decodeFunctionData} from 'viem';
import {studionet} from 'genlayer-js/chains';

test('wallet receives explicit Studio fees without changing recipient, value or call data',async()=>{
 const received:{method:string;params?:unknown[]}[]=[];
 const wallet=withStudioFees({request:async(args)=>{received.push(args);return 'wallet-result';}});
 const transaction={from:'0xsender',to:'0xrecipient',value:'0x1',data:'0x1234',type:'0x0'};
 assert.equal(await wallet.request({method:'eth_sendTransaction',params:[transaction]}),'wallet-result');
 assert.deepEqual(received[0],{method:'eth_sendTransaction',params:[{...transaction,chainId:'0xf22f',gasPrice:'0x3b9aca00'}]});
 await wallet.request({method:'eth_requestAccounts'});
 assert.deepEqual(received[1],{method:'eth_requestAccounts'});
 assert.equal('gasPrice' in transaction,false);
});

test('native appeal opens the wallet without nonce, estimate or fee RPCs and encodes the pinned native ABI',async()=>{
 const txId='0x'+'b'.repeat(64),account='0x'+'c'.repeat(40);
 const requests:{method:string;params?:unknown[]}[]=[];
 const wallet={request:async(args:{method:string;params?:unknown[]})=>{requests.push(args);return args.method==='eth_chainId'?'0xf22f':txId;}};
 assert.equal(await requestStudioAppeal(wallet,account,txId,Date.now()/1000+30),txId);
 assert.deepEqual(requests.map(request=>request.method),['eth_chainId','eth_sendTransaction']);
 const tx=requests[1].params![0] as {to:string;from:string;data:`0x${string}`;gas:string;value:string;gasPrice:string};
 assert.equal(tx.to,studionet.consensusMainContract!.address);
 assert.equal(tx.from,account);assert.equal(tx.gas,'0x30d40');assert.equal(tx.value,'0x0');assert.equal(tx.gasPrice,'0x3b9aca00');
 const decoded=decodeFunctionData({abi:studionet.consensusMainContract!.abi,data:tx.data});
 assert.equal(decoded.functionName,'submitAppeal');assert.deepEqual(decoded.args,[txId]);
 requests.length=0;
 await assert.rejects(requestStudioAppeal(wallet,account,txId,Date.now()/1000-1),/expired/);
 assert.deepEqual(requests.map(request=>request.method),['eth_chainId']);
 await assert.rejects(requestStudioAppeal({request:async()=> '0x1'},account,txId,Date.now()/1000+30),/StudioNet/);
});

test('native appeal wallet request pins zero value and Studio chain, saves its returned hash, and refuses other chains',async()=>{
 const hash='0x'+'a'.repeat(64);let received:unknown;let sent='';
 const wallet=withStudioFees({request:async(args)=>{received=args;return hash;}},value=>{sent=value});
 await wallet.request({method:'eth_sendTransaction',params:[{from:'0xsender',to:'0xconsensus',data:'0xappeal'}]});
 assert.deepEqual(received,{method:'eth_sendTransaction',params:[{from:'0xsender',to:'0xconsensus',data:'0xappeal',value:'0x0',chainId:'0xf22f',type:'0x0',gasPrice:'0x3b9aca00'}]});
 assert.equal(sent,hash);
 await assert.rejects(wallet.request({method:'eth_sendTransaction',params:[{chainId:'0x1'}]}),/StudioNet/);
});
