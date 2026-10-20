import proof from '@/deploy/milestone-proof.json';
import type {MilestoneProof} from '@/lib/milestone-domain';
import BadgeApp from './badge-app';
export default function Page(){const data=proof as unknown as MilestoneProof;return <BadgeApp proof={data} wallet={data.organizer} challenge="" embed={false}/>}
