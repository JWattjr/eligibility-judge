export type Verdict = {status:'PASS'|'FAIL'|'INSUFFICIENT_EVIDENCE';path:string;quote:string;reason:string;evidence_hash?:string};
export type Entry = {wallet:string;repo:string;commit:string;demo:string;attempt:number;status:string;verdicts:(Verdict|null)[];pending:boolean[];failing_rules:number[];history:Entry[]};
export type Challenge = {id:string;title:string;brief:string;organizer:string;rules:string[];rule_checks:({accepted:boolean;reason:string}|null)[];rule_pending:boolean[];rulebook_hash:string;status:string;validation_error?:string;opens:number;closes:number;cap:number;pool:string;entries:Record<string,Entry>;order:string[];qualifiers:string[];share:string;refund:string;claims:Record<string,string>;refund_claimed:boolean};
export type Proof = {network:string;chainId:number;contract:string;probe:string;sourceCommit:string;challengeId:string;transactions:Record<string,string>;challenge:Challenge|null;payoutVerified:boolean;completed:boolean;recordedAt?:string;probes?:Record<string,unknown>;cases?:Record<string,{wallet:string;repo:string;commit:string;expected:string}>;transfers?:Record<string,unknown>};
export const RULES=['README contains deployment instructions','Contains a Python GenLayer Intelligent Contract that makes a web request','Has an OSI-approved LICENSE file','Contains at least one test file'];
export const RULE_LABELS=['Deployment guide','Web-reading contract','Open-source license','Tests included'];
export const short=(s:string)=>s?`${s.slice(0,6)}…${s.slice(-4)}`:'—';
export function gen(wei:string){const n=BigInt(wei);return `${n/10n**18n}${n%10n**18n?'.'+String(n%10n**18n).padStart(18,'0').replace(/0+$/,''):''}`;}
export function repoParts(url:string){const match=/^https:\/\/github\.com\/([\w-]+)\/([\w.-]+)\/?$/.exec(url);if(!match)throw Error('Use a public https://github.com/owner/repo URL.');const repo=match[2].replace(/\.git$/,'');if(['','.','..'].includes(repo))throw Error('Invalid repository.');return {owner:match[1],repo};}
export function selectedFiles(paths:string[]){return paths.filter(p=>/\.(py|ts|tsx|js|jsx|rs|go|sol|md|txt|json|toml)$/i.test(p)||p.split('/').at(-1)?.toLowerCase()==='license').sort((a,b)=>{const priority=(p:string)=>['readme.md','license','license.md','license.txt'].includes(p.split('/').at(-1)!.toLowerCase())?0:/\.(py|ts|tsx|js|jsx|rs|go|sol)$/i.test(p)&&/contract|test/i.test(p)?1:2;return priority(a)-priority(b)||(a<b?-1:a>b?1:0)}).slice(0,10).filter(p=>/^[A-Za-z0-9_./ -]+$/.test(p)&&!p.split('/').includes('..'));}
export function evidenceUrl(entry:Entry,path:string){const {owner,repo}=repoParts(entry.repo);return path==='__TREE__'?`https://api.github.com/repos/${owner}/${repo}/git/trees/${entry.commit}?recursive=1`:path==='__DEMO__'?entry.demo:`https://github.com/${owner}/${repo}/blob/${entry.commit}/${path.split('/').map(encodeURIComponent).join('/')}`;}
export function executionState(receipt:Record<string,unknown>):string{const status=String(receipt.statusName??receipt.status_name??'PENDING');if(status!=='FINALIZED')return status;if(receipt.value_credited===true&&receipt.consensus_data===null)return 'FINALIZED_SUCCESS';const consensus=receipt.result_name??receipt.resultName;if(consensus&&!['AGREE','MAJORITY_AGREE','SUCCESS'].includes(String(consensus)))return 'FINALIZED_ERROR';const data=receipt.consensus_data as {leader_receipt?:{execution_result?:string;result?:{status?:string}}[]}|undefined;const leader=data?.leader_receipt?.[0];return ['SUCCESS','FINISHED_WITH_RETURN'].includes(String(receipt.txExecutionResultName??leader?.execution_result))&&leader?.result?.status!=='rollback'?'FINALIZED_SUCCESS':'FINALIZED_ERROR';}
export const txUrl=(hash:string)=>`https://explorer-studio.genlayer.com/tx/${hash}`;
export function executionError(receipt:Record<string,unknown>){
 if(executionState(receipt)!=='FINALIZED_ERROR')return '';
 const leader=(receipt.consensus_data as {leader_receipt?:{genvm_result?:{error_description?:string;stderr?:string};result?:{status?:string;payload?:unknown}}[]}|undefined)?.leader_receipt?.[0];
 const result=leader?.result;
 if(result?.status==='rollback'&&typeof result.payload==='string'&&result.payload)return result.payload;
 return leader?.genvm_result?.error_description||leader?.genvm_result?.stderr||'Contract execution or consensus rejected this transaction.';
}
export function nativeAppealReview(receipt:Record<string,unknown>){
 const timestamp=Number(receipt.timestamp_appeal),rounds=Number(receipt.num_of_rounds);
 const history=(receipt.consensus_history as {consensus_results?:{consensus_round?:string}[]}|undefined)?.consensus_results;
 if(executionState(receipt)!=='FINALIZED_ERROR'&&executionState(receipt)!=='FINALIZED_SUCCESS')return null;
 if(!Number.isFinite(timestamp)||timestamp<=0||!Number.isInteger(rounds)||rounds<2||!Array.isArray(history)||history.length<2)return null;
 return ['Validator Appeal Failed','Leader Appeal Failed'].includes(history.at(-1)?.consensus_round??'')?'Native appeal reviewed · original result upheld':'Native appeal re-evaluated';
}
// Studio uses the native finality window, extended by time spent appealing and
// shortened after failed appeals (the Studio protocol's configured reduction).
export function studioAppealDeadline(receipt:Record<string,unknown>,windowSeconds:number,reduction=0.2){
 const state=executionState(receipt);
 if(!['ACCEPTED','UNDETERMINED','LEADER_TIMEOUT','VALIDATORS_TIMEOUT'].includes(state)||receipt.leader_only!==false||receipt.appealed===true)return null;
 const started=Number(receipt.timestamp_awaiting_finalization),processing=Number(receipt.appeal_processing_time??0),failed=Number(receipt.appeal_failed??0);
 if(!Number.isFinite(started)||started<=0||!Number.isFinite(windowSeconds)||windowSeconds<=0||!Number.isFinite(processing)||processing<0||!Number.isInteger(failed)||failed<0||reduction<0||reduction>=1)return null;
 return started+processing+windowSeconds*(1-reduction)**failed;
}
export function returnedChallengeId(receipt:Record<string,unknown>){if(executionState(receipt)!=='FINALIZED_SUCCESS')return null;const data=receipt.consensus_data as {leader_receipt?:{result?:{payload?:{readable?:string}}}[]}|undefined;try{const value=JSON.parse(data?.leader_receipt?.[0]?.result?.payload?.readable??'null');return typeof value==='string'&&/^challenge-\d+$/.test(value)?value:null;}catch{return null;}}
