# Eligibility Judge

Open hackathon judging: every entry gets a rule-by-rule verdict anyone can verify.

Organizers publish 3–6 objectively checkable rules and fund a StudioNet GEN pool. Builders submit a public GitHub repository pinned to a full commit SHA. GenLayer validators independently fetch bounded evidence, judge one rule per transaction, and confirm the leader's file path and verbatim quote. Every entry that passes every rule qualifies. Contract code splits the pool equally; the organizer receives the remainder. There is no scoring, ranking, bidding, or organizer-selected winner.

## Architecture

```mermaid
flowchart LR
  Browser[Next.js rule matrix + wallet] -->|signed writes| Contract[EligibilityJudge]
  Browser -->|read-only cached API| RPC[StudioNet finalized state]
  Contract -->|one rule per transaction| Validators[GenLayer leader + independent validators]
  Validators --> GitHub[GitHub tree + pinned raw files]
  Validators --> Archive[Optional dated archive.org snapshot]
  Validators -->|verdict + verified citation| Contract
  Contract -->|native finalized callback| Settlement[Equal integer shares + refund]
  Settlement -->|pull claim| Wallets[Native GEN credited transfers]
```

## Local setup

Requires Node.js 20.9+ and Python 3.12+. The Windows development environment uses Python 3.14. Never put a private key in the app or browser bundle.

```sh
npm ci
python -m pip install -r requirements.txt
npm run dev
```

Open http://localhost:3111. The preserved proof snapshot opens without a wallet. Live chain reads come from `/api/chain`, which always requests `LATEST_FINAL`. A browser wallet signs writes on StudioNet 61999. The browser persists transaction hashes and resumes 5-second polling after reload; accepted results stay provisional until finality and callback completion.

## Contract deployment instructions

The runner is pinned to `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`. Release dependencies pin `genlayer-py==0.18.0` and `genlayer-js==1.1.8`.

```sh
genlayer network set studionet
genlayer account list
genvm-lint check contracts/eligibility_judge.py
python -m pytest tests/direct -q
```

On Windows, use the staged, resumable deployment script with your already unlocked GenLayer CLI account:

The committed manifest resumes the existing public demonstration. For a fresh contract, first preserve that manifest and copy the empty template. This starts a separate instance; its `seed` step deposits another 3 StudioNet GEN from your selected CLI account.

```powershell
Copy-Item -LiteralPath deploy/proof.json -Destination deploy/proof.previous.json
Copy-Item -LiteralPath deploy/proof.template.json -Destination deploy/proof.json
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 probe
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 deploy
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 seed
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 entries
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 judge
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 settle
npm run verify:proof
```

Each stage records hashes before waiting. Resume the same stage after a timeout; it reuses saved transactions. Receipt reads retry up to five consecutive transient connection or invalid-JSON failures; consensus rejection and uncredited transfers still stop the stage. The `probe` stage deploys its access-probe contract when the fresh manifest has no saved deployment. The demo entrants' test-wallet keys are generated into a gitignored `.env.demo-wallets.json` solely for StudioNet. By default, `seed` funds 3 GEN, starts a twenty-minute window, and validates four rules. Set `ELIGIBILITY_DEMO_WEI=1` to use a 1-wei development demonstration instead. Publish this repository before entering its pinned source commit. The CLI polls every ten seconds to leave headroom below the hourly RPC budget. Deployment scripts save receipts locally; `deploy/proof.json` is the public, compact manifest. Vercel deploys with a remote build: `vercel --prod --scope wattxs-projects`.

## Verification

```sh
npm run typecheck
npm run build
npm test
genvm-lint check contracts/eligibility_judge.py
python -m pytest tests/direct -q
npm run verify:proof
```

Direct tests mock web and LLM responses and do not claim validator consensus. The read-only proof verifier checks finalized execution, emitted callbacks, observed contract state, exact payout credit, and deployed source. Browser verification is recorded separately in `docs/browser-verification.json`. Native Studio appeals use the actual `sim_getFinalityWindowTime` and receipt timestamps, including processing time and failed appeals. The native failed-appeal reduction defaults to Studio’s 0.2 and can be matched to a changed deployment with the server-only `STUDIONET_APPEAL_FAILED_REDUCTION`. The browser submits the native zero-value Studio appeal and resumes polling the same transaction ID. These behaviors follow the [official Studio transaction view](https://github.com/genlayerlabs/genlayer-studio/blob/main/frontend/src/components/Simulator/TransactionItem.vue) and [SDK appeal implementation](https://github.com/genlayerlabs/genlayer-js/blob/main/src/contracts/actions.ts).

## Proof and submission

- [Public proof manifest](deploy/proof.json): addresses, pinned source commit, access probes, transaction hashes, outcomes, transfers, and completion flags.
- [Contract on StudioNet](https://explorer-studio.genlayer.com/address/0x03Dd21B241ea3e1EBB9B126Eb732d795dEE8Ae9a).
- [Tutorial](docs/TUTORIAL.md), [two-minute demo](docs/DEMO.md), and [portal fields](docs/submission/portal-fields.json).
- [Official finality documentation](https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy/finality).

The latest contract verifies full source quotes before capping stored excerpts at 600 characters. It also repairs file-presence citations only when the complete metadata matches an independently fetched GitHub tree node, storing the actual verbatim path in `__TREE__`. Failures citing a truncated file become insufficient evidence; positive evidence in its fetched prefix can still pass. Fabricated metadata, hidden suffixes and judge-directed instructions remain rejected.

The correction passes 33 direct tests. Six zero-value full-consensus checks finalized with validator agreement: the fixture test file, the truncated README, the SDK test file and license, its bounded Python-contract inspection, and a fully inspected control repository. The SDK inspection correctly remained insufficient; the small control conclusively failed the Python-contract rule. The control is a separate pinned branch of the approved public fixture, preserving its injection case. [Their manifest](deploy/consensus-smoke-proof.json) can be independently rechecked with `npm run verify:smoke`. These tests verify adjudication and exact deployed probe source; they do not prove funding, settlement or payout. The corrected one-wei demo has all sixteen finalized rule verdicts: the honest entry qualified, the control and injection entries were disqualified, and the nonexistent commit produced insufficient evidence. Settlement finalized and the qualifier claimed exactly one wei through a credited native transfer. The manifest preserves both real browser judgments. Browser reload recovery passed; the final native appeal signature check remains outstanding in the separate browser verification report.

Funding history is preserved: 3 StudioNet GEN are unrecoverable at the first contract after an invalid-window rollback; another 3 GEN remain locked at the second contract because a test-file judgment failed citation verification. One wei remains locked in [the evidence-corrected run](deploy/evidence-run.json), and another in [the citation-bound run](deploy/citation-run.json), which finalized thirteen of sixteen rule verdicts. [Its exact deployed source](deploy/citation-run-contract.py) is archived. The diagnostic exposed a reconstructed tree JSON object attributed to a test file ([raw diagnostic](deploy/fixture-diagnostic-proof.json)). No additional deposit was made while developing or testing this correction. On October 7, the owner authorized the fresh one-wei demo; total deposits across attempts are now 6 StudioNet GEN plus 3 wei. Nothing is submitted to the Portal automatically.
