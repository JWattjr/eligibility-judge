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
