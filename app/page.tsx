import JudgeApp from './judge-app';
import proof from '@/deploy/proof.json';
import type {Proof} from '@/lib/domain';
export default function Page(){return <JudgeApp proof={proof as unknown as Proof}/>;}
