import proof from '@/deploy/milestone-proof.json';
import type {MilestoneProof} from '@/lib/milestone-domain';
import BadgeApp from '../badge-app';
export default async function Page({params,searchParams}:{params:Promise<{wallet:string}>;searchParams:Promise<{challenge?:string;embed?:string}>}){const {wallet}=await params,query=await searchParams;return <BadgeApp proof={proof as unknown as MilestoneProof} wallet={wallet.toLowerCase()} challenge={query.challenge??''} embed={query.embed==='1'}/>}
