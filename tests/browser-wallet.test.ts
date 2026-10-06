import {test} from 'node:test';
import assert from 'node:assert/strict';
import {withStudioFees} from '../lib/browser-wallet';

test('wallet receives explicit Studio fees without changing recipient, value or call data',async()=>{
 const received:{method:string;params?:unknown[]}[]=[];
 const wallet=withStudioFees({request:async(args)=>{received.push(args);return 'wallet-result';}});
 const transaction={from:'0xsender',to:'0xrecipient',value:'0x1',data:'0x1234',type:'0x0'};
 assert.equal(await wallet.request({method:'eth_sendTransaction',params:[transaction]}),'wallet-result');
 assert.deepEqual(received[0],{method:'eth_sendTransaction',params:[{...transaction,gasPrice:'0x3b9aca00'}]});
 await wallet.request({method:'eth_requestAccounts'});
 assert.deepEqual(received[1],{method:'eth_requestAccounts'});
 assert.equal('gasPrice' in transaction,false);
});
