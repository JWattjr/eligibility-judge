import {NextRequest,NextResponse} from 'next/server';
import {milestoneState} from '@/lib/server-chain';
export const dynamic='force-dynamic';
export async function GET(request:NextRequest){
 const p=request.nextUrl.searchParams,kind=p.get('kind')??'series',wallet=(p.get('wallet')??'').toLowerCase(),challenge=p.get('challenge')??'';
 try{
  if(['badges','entry','verify'].includes(kind)&&!/^0x[0-9a-f]{40}$/.test(wallet))throw Error('Enter a full wallet address.');
  if(['entry','verify'].includes(kind)&&!/^challenge-\d+$/.test(challenge))throw Error('Enter a valid challenge ID.');
  return NextResponse.json(await milestoneState(kind,wallet,challenge));
 }catch(error){return NextResponse.json({error:error instanceof Error?error.message:'Finalized milestone state unavailable. Retry in a minute.'},{status:503});}
}
