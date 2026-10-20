import {NextRequest,NextResponse} from 'next/server';
import {repoParts} from '@/lib/domain';
export async function GET(request:NextRequest){
 try{
  const {owner,repo}=repoParts(request.nextUrl.searchParams.get('repo')??''),commit=request.nextUrl.searchParams.get('commit')??'';
  if(!/^[a-f0-9]{40}$/i.test(commit))throw Error('Pinned commit required.');
  const response=await fetch(`https://api.github.com/repos/${owner}/${repo}/git/trees/${commit}?recursive=1`,{headers:{'User-Agent':'Mozilla/5.0 Eligibility Judge'},next:{revalidate:3600}});
  if(!response.ok)throw Error('Pinned tree is unavailable; no file can be selected.');
  const bytes=new Uint8Array(await response.arrayBuffer());if(bytes.byteLength>1000000)throw Error('Pinned tree exceeds the dispute inspection bound.');
  const data=JSON.parse(new TextDecoder().decode(bytes));if(data.truncated)throw Error('Pinned tree is incomplete.');
  const files=(data.tree as {type:string;path:string;size?:number}[]).filter(f=>f.type==='blob'&&(f.size??0)<=65536&&/^[A-Za-z0-9_./ -]+$/.test(f.path)&&f.path.split('/').every(p=>p&&p!=='.'&&p!=='..')).map(f=>({path:f.path,bytes:f.size??0}));
  return NextResponse.json({files,commit,limitBytes:65536});
 }catch(error){return NextResponse.json({error:error instanceof Error?error.message:'Pinned file list unavailable.'},{status:400});}
}
