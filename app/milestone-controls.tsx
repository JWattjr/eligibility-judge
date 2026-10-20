'use client';
import {createContext,useCallback,useContext,useEffect,useRef,useState} from 'react';
import {createClient} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';
import {ExternalLink,Gavel,Wallet} from 'lucide-react';
import {withStudioFees} from '@/lib/browser-wallet';
import {short,txUrl} from '@/lib/domain';

type Provider={request:(request:{method:string;params?:unknown[]})=>Promise<unknown>;on?:(event:string,listener:(value:unknown)=>void)=>void;removeListener?:(event:string,listener:(value:unknown)=>void)=>void};
type Discovered={info:{uuid:string;name:string;rdns:string};provider:Provider};
export type SignRequest={address:string;method:string;args:(string|number)[];value?:bigint};
export type Sign= (request:SignRequest)=>Promise<{hash:string;account:string}>;
type Tracked={hash:string;address:string;method:string;args:(string|number)[];account:string;label:string;state:string;children:string[];createdAt:number;error?:string};
const STORE='eligibility:milestone:transactions';
const UPDATED='eligibility:milestone:updated';
const WalletContext=createContext<{sign:Sign;account:string}|null>(null);
function saved():Tracked[]{try{return JSON.parse(localStorage.getItem(STORE)??'[]')}catch{return []}}
function store(list:Tracked[]){localStorage.setItem(STORE,JSON.stringify(list.slice(-40)));window.dispatchEvent(new Event(UPDATED));}

export function MilestoneWallet({children}:{children:React.ReactNode}){
 const [wallets,setWallets]=useState<Discovered[]>([]),[selected,setSelected]=useState('io.metamask'),[account,setAccount]=useState(''),[error,setError]=useState('');
 useEffect(()=>{const announce=(event:Event)=>{const value=(event as CustomEvent<Discovered>).detail;if(!value?.info?.uuid||typeof value.provider?.request!=='function')return;setWallets(list=>list.some(w=>w.info.uuid===value.info.uuid)?list:[...list,value])};window.addEventListener('eip6963:announceProvider',announce);window.dispatchEvent(new Event('eip6963:requestProvider'));return()=>window.removeEventListener('eip6963:announceProvider',announce)},[]);
 const provider=wallets.find(w=>w.info.rdns===selected)?.provider??(wallets.length===0?(typeof window==='undefined'?undefined:(window as unknown as {ethereum?:Provider}).ethereum):undefined);
 useEffect(()=>{if(!provider)return;let active=true;const changed=(value:unknown)=>{if(active)setAccount(Array.isArray(value)&&typeof value[0]==='string'?value[0].toLowerCase():'')};void provider.request({method:'eth_accounts'}).then(changed).catch(()=>{});provider.on?.('accountsChanged',changed);return()=>{active=false;provider.removeListener?.('accountsChanged',changed)}},[provider]);
 async function connect(){
  if(!provider)throw Error('Choose an available StudioNet wallet, then retry.');
  const accounts=await provider.request({method:'eth_requestAccounts'}) as string[];
  if(!accounts[0])throw Error('No wallet account was selected.');
  if(await provider.request({method:'eth_chainId'})!=='0xf22f'){
   try{await provider.request({method:'wallet_switchEthereumChain',params:[{chainId:'0xf22f'}]})}catch(error){if((error as {code?:number}).code!==4902)throw error;await provider.request({method:'wallet_addEthereumChain',params:[{chainId:'0xf22f',chainName:'GenLayer StudioNet',nativeCurrency:{name:'GEN',symbol:'GEN',decimals:18},rpcUrls:['https://studio.genlayer.com/api'],blockExplorerUrls:['https://explorer-studio.genlayer.com']}]})}
  }
  const address=accounts[0].toLowerCase();setAccount(address);return {address,client:createClient({chain:studionet,account:address as `0x${string}`,provider:withStudioFees(provider)})};
 }
 const sign:Sign=async request=>{const {address,client}=await connect();const hash=await client.writeContract({address:request.address as `0x${string}`,functionName:request.method,args:request.args,value:request.value??0n});return {hash,account:address}};
 return <WalletContext.Provider value={{sign,account}}><header className="topbar milestone-topbar"><a href="/" className="brand" aria-label="Eligibility Judge home"><span className="brand-mark"><Gavel size={21}/></span><span>eligibility<span className="brand-light">judge</span></span></a><div className="header-end"><span className="network"><span/> StudioNet</span>{wallets.length>0&&<select className="wallet-select" aria-label="Choose wallet" value={selected} onChange={e=>{setSelected(e.target.value);setAccount('')}}>{!wallets.some(w=>w.info.rdns===selected)&&<option value={selected}>Choose wallet</option>}{wallets.map(w=><option key={w.info.uuid} value={w.info.rdns}>{w.info.name}</option>)}</select>}<button className="wallet-button" onClick={()=>{setError('');void connect().catch(e=>setError(String(e.message)))}}><Wallet size={16}/>{account?short(account):'Connect wallet'}</button></div></header>{error&&<p role="alert" className="milestone-error">{error}</p>}{children}</WalletContext.Provider>;
}

export function ChainAction({address,method,args,label,value=0n,disabled=false,sign:externalSign,onSent}:{address:string;method:string;args:(string|number)[];label:string;value?:bigint;disabled?:boolean;sign?:Sign;onSent?:(hash:string)=>void}){
 const context=useContext(WalletContext),[busy,setBusy]=useState(false),[error,setError]=useState(''),[pending,setPending]=useState(false);
 const argumentKey=JSON.stringify(args);
 useEffect(()=>{const update=()=>setPending(saved().some(t=>t.address.toLowerCase()===address.toLowerCase()&&t.method===method&&JSON.stringify(t.args)===argumentKey&&!t.state.startsWith('FINALIZED')));update();window.addEventListener(UPDATED,update);return()=>window.removeEventListener(UPDATED,update)},[address,method,argumentKey]);
 async function send(){setBusy(true);setError('');try{
  const sign=externalSign??context?.sign;if(!sign)throw Error('Connect your StudioNet wallet.');
  const result=await sign({address,method,args,value});
  store([...saved(),{...result,address,method,args,label,state:'SUBMITTED',children:[],createdAt:Date.now()}]);onSent?.(result.hash);
 }catch(error){setError(error instanceof Error?error.message:'Wallet transaction failed.')}finally{setBusy(false)}}
 return <span className="chain-action"><button type="button" className="button secondary small" disabled={disabled||busy||pending} onClick={()=>void send()}>{busy?'Waiting for wallet…':pending?'Waiting for finality…':label}</button>{error&&<span role="alert" className="milestone-error">{error}</span>}</span>;
}

export function TransactionTrail({onFinalized,sign}:{onFinalized?:()=>void;sign?:Sign}){
 const [transactions,setTransactions]=useState<Tracked[]>([]),[error,setError]=useState(''),[hash,setHash]=useState('');const polling=useRef(false);
 useEffect(()=>{const update=()=>setTransactions(saved());update();window.addEventListener(UPDATED,update);return()=>window.removeEventListener(UPDATED,update)},[]);
 const refresh=useRef(onFinalized);refresh.current=onFinalized;
 useEffect(()=>{let active=true;async function tick(){if(polling.current||document.hidden)return;const item=saved().find(t=>!t.state.startsWith('FINALIZED')&&Date.now()-t.createdAt<86400000);if(!item)return;polling.current=true;try{
  const response=await fetch('/api/chain?tx='+item.hash,{cache:'no-store'}),result=await response.json();if(!response.ok)throw Error(result.error);
  let state=result.state as string;const children=result.children??item.children;
  async function callbackState(hash:string,depth=0):Promise<string>{if(depth>6)throw Error('Callback depth exceeds the tracker bound. Inspect its receipt.');const r=await fetch('/api/chain?tx='+hash,{cache:'no-store'}),v=await r.json();if(!r.ok)throw Error(v.error);if(v.state==='FINALIZED_ERROR')return 'FINALIZED_ERROR';if(v.state!=='FINALIZED_SUCCESS')return 'WAITING_FOR_FINALIZED_CALLBACK';for(const child of v.children??[]){const status=await callbackState(child,depth+1);if(status!=='FINALIZED_SUCCESS')return status}return 'FINALIZED_SUCCESS';}
  if(state==='FINALIZED_SUCCESS'){for(const child of children){const status=await callbackState(child);if(status!=='FINALIZED_SUCCESS'){state=status;break}}}
  if(!active)return;
  store(saved().map(t=>t.hash===item.hash?{...t,state,children,error:result.error}:t));setError('');if(state==='FINALIZED_SUCCESS')refresh.current?.();
 }catch(error){if(active)setError(error instanceof Error?error.message:'Chain polling paused; saved hashes remain recoverable.')}finally{polling.current=false}}
 const timer=setInterval(()=>void tick(),10000);void tick();return()=>{active=false;clearInterval(timer)}},[]);
 async function track(){if(!/^0x[0-9a-f]{64}$/i.test(hash))return setError('Enter a full transaction hash.');const response=await fetch('/api/chain?tx='+hash),result=await response.json();if(!response.ok)return setError(result.error);store([...saved().filter(t=>t.hash!==hash),{hash,address:String(result.recipient),method:'tracked',args:[],account:'',label:'Tracked milestone transaction',state:result.state,children:result.children??[],createdAt:Date.now()}]);setHash('');}
 return <section className="milestone-trail" aria-label="Milestone transaction trail"><h3>Your milestone transactions</h3><p>Saved in this browser. Accepted results remain provisional; callbacks and native credits must finalize.</p>{transactions.length===0&&<p>No milestone transactions have been signed in this browser.</p>}{transactions.slice().reverse().map(t=><div className="milestone-transaction" key={t.hash}><span>{t.label}</span><a href={txUrl(t.hash)} target="_blank" rel="noreferrer">{short(t.hash)} <ExternalLink size={12}/></a><span className="status neutral">{t.state.replaceAll('_',' ').toLowerCase()}</span>{t.error&&<p role="alert">{t.error}</p>}{t.state==='FINALIZED_SUCCESS'&&['claim','claim_for','claim_refund'].includes(t.method)&&<ChainAction address={t.address} method="verify_claim" args={[String(t.args[0]),t.method==='claim_for'?String(t.args[1]):t.account,t.hash]} label="Verify native credit" sign={sign}/>}</div>)}{error&&<p role="status" className="milestone-error">{error}</p>}<form className="milestone-track-form" onSubmit={e=>{e.preventDefault();void track()}}><label>Track a saved transaction<input value={hash} onChange={e=>setHash(e.target.value)} placeholder="0x…" pattern="0x[0-9a-fA-F]{64}" required/></label><button className="button secondary small" type="submit">Track transaction</button></form></section>;
}

export function useFinalizedRead(url:string,initial:import('@/lib/milestone-domain').MilestoneRead){
 const [data,setData]=useState(initial),[mode,setMode]=useState<'recorded'|'live'>('recorded'),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const refresh=useCallback(async()=>{setBusy(true);setError('');try{const response=await fetch(url,{cache:'no-store'}),data=await response.json();if(!response.ok)throw Error(data.error);setData(data);setMode('live')}catch(error){setError(error instanceof Error?error.message:'Finalized state unavailable.')}finally{setBusy(false)}},[url]);
 useEffect(()=>{void refresh()},[refresh]);
 return {data,mode,error,busy,refresh};
}

export function MilestoneNav({active}:{active:'series'|'badges'|'ledger'}){return <nav className="milestone-nav" aria-label="Project sections"><a href="/" aria-current={active==='ledger'?'page':undefined}>Eligibility ledger</a><a href="/series" aria-current={active==='series'?'page':undefined}>Seasons</a><a href="/badges" aria-current={active==='badges'?'page':undefined}>Qualification badges</a></nav>}
export function Provenance({mode,readAt,busy,error,onRefresh}:{mode:string;readAt:string;busy:boolean;error:string;onRefresh:()=>void}){return <div className="milestone-provenance"><span>{mode==='live'?'Finalized live state':'Recorded proof'}{readAt&&' · '+new Date(readAt).toLocaleString('en-GB',{timeZone:'Africa/Lagos',hour12:false})+' Lagos'}</span><button className="button secondary small" onClick={onRefresh} disabled={busy}>{busy?'Reading chain…':'Refresh finalized state'}</button>{error&&<p role="alert">{error} The last readable state remains visible.</p>}</div>}
export function useWalletAccount(){return useContext(WalletContext)?.account??'';}
export function useMilestoneClock(){const [clock,setClock]=useState(()=>Date.now()/1000);useEffect(()=>{const timer=setInterval(()=>setClock(Date.now()/1000),10000);return()=>clearInterval(timer)},[]);return clock;}
