import proof from '@/deploy/milestone-proof.json';
import type {MilestoneProof} from '@/lib/milestone-domain';
import DisputesApp from './disputes-app';
export default function Page(){return <DisputesApp proof={proof as unknown as MilestoneProof}/>}
