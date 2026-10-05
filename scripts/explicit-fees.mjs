// StudioNet SDK 1.1.8 uses fetch JSON-RPC; make fee fields explicit before signing.
// SDK estimates gas internally; fixed RPC gas-price replies pin the signer fee budget.
const original=globalThis.fetch;
globalThis.fetch=async (input,init)=>{
 if(init?.body&&typeof init.body==='string'){
  let body;try{body=JSON.parse(init.body)}catch{}
  if(body?.method==='eth_gasPrice')return new Response(JSON.stringify({jsonrpc:'2.0',id:body.id,result:'0x3b9aca00'}),{headers:{'content-type':'application/json'}});
  if(body?.method==='eth_maxPriorityFeePerGas')return new Response(JSON.stringify({jsonrpc:'2.0',id:body.id,result:'0x3b9aca00'}),{headers:{'content-type':'application/json'}});
 }
 return original(input,init);
};
