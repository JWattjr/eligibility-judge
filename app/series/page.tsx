import proof from '@/deploy/milestone-proof.json';
import type {MilestoneProof} from '@/lib/milestone-domain';
import SeriesApp from './series-app';
export default function Page(){return <SeriesApp proof={proof as unknown as MilestoneProof}/>}
