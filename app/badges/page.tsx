import proof from '@/deploy/milestone-proof.json';
import type {MilestoneProof} from '@/lib/milestone-domain';
import BadgeApp from './badge-app';
export default function Page(){const data=proof as unknown as MilestoneProof;const featured=Object.values(data.badges??{}).flat().find(b=>b.via_dispute);return <BadgeApp proof={data} wallet={featured?.wallet??data.organizer} challenge="" embed={false}/>}
