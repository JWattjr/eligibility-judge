import type {Metadata} from 'next';
import '@fontsource/dm-sans/400.css';
import '@fontsource/dm-sans/500.css';
import '@fontsource/dm-sans/600.css';
import '@fontsource/space-grotesk/500.css';
import '@fontsource/space-grotesk/700.css';
import './globals.css';
export const metadata:Metadata={title:'Eligibility Judge — every rule, on record',description:'Open hackathon judging. Every entry gets a rule-by-rule verdict anyone can verify.'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>;}
