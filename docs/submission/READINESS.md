# Grace correction - live proof pending

The fixed contract is 0x03E7970E791d644B2714a457D178Edf036670bb7 on StudioNet. Its deployment [finalized successfully](https://explorer-studio.genlayer.com/tx/0xf8c7a73646fd56834d12178977bba4ba1e48c1cdcbd1105f40c8ff7c5c2755e9). GenVM lint, 46 direct contract tests, TypeScript, 16 app tests and a production build pass.

This correction is not submission-ready yet. The two 1-wei demo deposits require owner approval. Both the four-outcome payout and a real never-judged-entry grace settlement with credited organizer refund must complete before production promotion and readiness. Mocked timeout tests do not satisfy this requirement.

The currently published site still uses the earlier paid contract. Its complete proof, receipts, browser verification, readiness report and exact deployed source are preserved in [previous runs](../../deploy/previous-runs/pre-grace/). The new staging manifest is ignored until live proof is complete. Native appeal verification continues to use the historical paid challenge explicitly recorded in its manifest.

The owner performs the final Portal submission. Nothing is submitted automatically.
