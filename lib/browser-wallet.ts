type WalletRequest = {method:string;params?:unknown[]};
type WalletProvider = {request:(args:WalletRequest)=>Promise<unknown>};

// SDK 1.1.8 may omit gasPrice when Studio's fee RPC fails. Its browser
// transactions use legacy type 0; pin the same explicit fee as the CLI path.
export function withStudioFees(wallet:WalletProvider):WalletProvider{
 return {request:async(args)=>{
  if(!['eth_sendTransaction','eth_signTransaction'].includes(args.method))return wallet.request(args);
  const [transaction,...rest]=args.params??[];
  if(!transaction||typeof transaction!=='object'||Array.isArray(transaction))throw Error('Invalid wallet transaction.');
  return wallet.request({...args,params:[{...transaction,gasPrice:'0x3b9aca00'},...rest]});
 }};
}
