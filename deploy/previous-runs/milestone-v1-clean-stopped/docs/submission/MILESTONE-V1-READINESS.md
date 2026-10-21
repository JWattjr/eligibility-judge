# Milestone v1 clean rerun — stopped, not submission ready

The clean one-pass run stopped at **2026-10-20 19:31:47 UTC**, during the second round's control payout-rule judgment. Completion remains approximately **55%**. The user brief explicitly requires stopping on any failed receipt or unexpected outcome, with no retries. No further demo case, deposit, production release or Portal action followed the failure. A separately authorized deposit recovery has since completed; see below.

## Failed receipt

- Case: `round-2-judge-control-1`, unchanged EligibilityJudge, `judge_rule(challenge-6, control, 1)`.
- [Transaction on StudioNet](https://explorer-studio.genlayer.com/tx/0xb1c68291e8c3211acb8755f5504709ddb6acff96d3cb9481b194c21b70ad5296).
- Lifecycle **FINALIZED**, protocol result **7 / MAJORITY_DISAGREE**; **not FINALIZED SUCCESS**. Four protocol rounds, three leader rotations, no emitted child transaction. These are protocol consensus rounds within one submitted case, not application retries.
- The final leader executed successfully and proposed FAIL with a `__TREE__` citation. Three final validator votes disagreed, one agreed, and one was idle (cancelled after quorum). The receipt identifies the failed nondeterministic block but does not identify which evidence, independent-verdict or citation-verification check each validator rejected. The precise disagreement cause is unproven; do not attribute it solely to path choice or rate limiting.
- The saved original receipt remains at `deploy/receipts/milestone-v1-clean/round-2-judge-control-1.json`. A fresh read confirmed the same outcome; public read-only state is in [clean-stop-audit.json](../../deploy/clean-stop-audit.json).

## What actually completed

The raw-file opening fix is deployed. The three new contracts have exact deployed/local/Git source identity, verified constructor wiring and separate Explorer Contract evidence:

| Contract | StudioNet Explorer |
| --- | --- |
| RulingDisputes | [0x464f3e7147d1C7e7EdeF5e4A0fcb9393a8F8A680](https://explorer-studio.genlayer.com/address/0x464f3e7147d1C7e7EdeF5e4A0fcb9393a8F8A680) |
| QualificationBadges | [0x0F278ea98EB792C616947Be2Fb4A857C1Be59543](https://explorer-studio.genlayer.com/address/0x0F278ea98EB792C616947Be2Fb4A857C1Be59543) |
| EligibilitySeries | [0x0e355b80258869F6b42016185EBc0901F87C152C](https://explorer-studio.genlayer.com/address/0x0e355b80258869F6b42016185EBc0901F87C152C) |
| Unchanged EligibilityJudge | [0x03E7970E791d644B2714a457D178Edf036670bb7](https://explorer-studio.genlayer.com/address/0x03E7970E791d644B2714a457D178Edf036670bb7) |

All four links were verified against the StudioNet Explorer API with a browser user agent and in Chrome on 2026-10-20. Evidence: `deploy/clean-contract-links.json` and `deploy/clean-contract-browser.json`.

All five candidate trees were fetched once before deposits, complete, non-truncated and below 80,000 bytes. Both rounds use distinct pins. Eight pinned raw-file access probes passed.

| Round | Steady | Rescued | Control |
| --- | --- | --- | --- |
| challenge-5 | QUALIFIED, PASS/PASS/PASS | INSUFFICIENT_EVIDENCE, PASS/INSUFFICIENT_EVIDENCE/PASS | DISQUALIFIED, FAIL/FAIL/PASS |
| challenge-6 | QUALIFIED, PASS/PASS/PASS | QUALIFIED, PASS/PASS/PASS | JUDGING, FAIL/unrecorded/unrecorded |

Rescued's first-round payout reason was **GitHub tree HTTP 403**. Machine preflight establishes that the payout implementation lies beyond the original file prefix, but this live verdict does not prove prefix truncation caused the insufficient-evidence outcome.

A/B/C did not open or reach hearings. No bonds were deposited. No badges were minted, rounds imported, series winners allocated or bonus claims sent. The original pools also remain unsettled. Their dispute opening windows have now expired; no late transaction was attempted.

## Funds snapshot before authorized recovery

The read-only audit at 2026-10-21T03:00:29.548Z confirms:

- Gross new deposits: **50,000,000,000,000,002 wei = 0.05 GEN plus 2 wei**, below the 0.2-GEN ceiling. This is deposited development currency, not proof of an irreversible loss.
- RulingDisputes balance: **0**; QualificationBadges balance: **0**; EligibilitySeries balance: **50,000,000,000,000,000 wei**.
- `series-1` remains **OPEN** with no allocations, winners or claims. Each original challenge still holds its recorded 1-wei pool pending settlement.
- The season's existing timeout-refund path becomes eligible **2026-10-21 21:57:08 UTC (22:57:08 Africa/Lagos)**. It requires transactions to close the season, claim the organizer refund and verify the native credit; it is not an automatic payment. At this snapshot no recovery transaction had been sent; the separately authorized recovery is documented below.

## Validation and release state

Phase 1 passed **110 contract tests** (97 existing plus 13 new), **22 app tests**, GenVM lint for all three new contracts, TypeScript and the production build. See [phase 1 evidence](../milestone-v1-phase1.json). Those results precede the live failure and do not establish a successful live proof.

The strict verifier rejects this stopped manifest and records **FAIL**, never PASS_WITH_REPORTED_FAILURES. Submission fields are explicitly blocked and contain current addresses, actual incomplete outcomes and separate contract evidence. Their lengths are printed by the local packaging audit. The planned success summary was not generated. No new desktop/mobile release QA, push, Vercel production deployment or Portal submission followed the failure. The live site therefore still shows the previous release.

The exact first-run proof remains preserved in [the first-run archive](../../deploy/previous-runs/milestone-v1-first-run/). This clean run's failure has not been erased or retried. Completing the original success story would require an explicitly revised live plan outside this stopped one-pass run.

## Authorized recovery completed (submission remains blocked)

**Recovery is 100% complete:** all 0.05 GEN plus 2 wei credited the organizer wallet, with zero new deposits. Both original pools are now settled, the season is CLOSED with both recorded rounds VOID and no winners, the refund is paid, and its contract balance is 0 wei. Independent verification passed all 14 receipts and three native credits at 2026-10-21T04:44:07.461135+00:00.

| Recovered allocation | Amount | Native credit evidence |
| --- | --- | --- |
| Season bonus refund | 0.05 GEN | [Finalized credited transfer](https://explorer-studio.genlayer.com/tx/0xaf7a04b90be7fc9fbdd507f7de8cd9eec4bae93af27334ed589dd7b9b2bc7cfe) |
| Round 1 qualifier share | 1 wei | [Finalized credited transfer](https://explorer-studio.genlayer.com/tx/0x9c155e4c06fff6cc54d270a3428359bc350b05dbc6378c7d50711a2b62dd121a) |
| Round 2 remainder refund | 1 wei | [Finalized credited transfer](https://explorer-studio.genlayer.com/tx/0xc0a0bc6193583cb94f50a15f309b6724e2164f37333b21df5d2d49f89fffcb7d) |

Recovery used the earlier ended-season/unsettled-rounds path, before the 24-hour timeout described in the historical snapshot. It closed the season before settling the original pools. The failed live judgment was not retried and the stopped manifest's exact bytes remain unchanged. A/B/C, badges and the planned two-winner bonus story remain uncompleted; this is **fund recovery, not a passing submission proof**. See the [recovery report](MILESTONE-V1-RECOVERY.md).
