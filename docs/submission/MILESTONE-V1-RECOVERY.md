# Clean-run deposit recovery — complete

The user separately authorized **recovering existing deposits only**. All **50,000,000,000,000,002 wei (0.05 StudioNet GEN plus 2 wei)** from the stopped clean run have credited the frozen organizer wallet `0xdb433ff614bdd1ece21aa97221c3e0a7ecf79c92`. **Zero new GEN was deposited.** This recovery does not make the failed clean submission run pass.

| Recovered allocation | Amount | Native credit evidence |
| --- | --- | --- |
| Season bonus refund | 0.05 GEN | [Finalized credited transfer](https://explorer-studio.genlayer.com/tx/0xaf7a04b90be7fc9fbdd507f7de8cd9eec4bae93af27334ed589dd7b9b2bc7cfe) |
| Round 1 qualifier share | 1 wei | [Finalized credited transfer](https://explorer-studio.genlayer.com/tx/0x9c155e4c06fff6cc54d270a3428359bc350b05dbc6378c7d50711a2b62dd121a) |
| Round 2 remainder refund | 1 wei | [Finalized credited transfer](https://explorer-studio.genlayer.com/tx/0xc0a0bc6193583cb94f50a15f309b6724e2164f37333b21df5d2d49f89fffcb7d) |

The recovery completed at **2026-10-21T04:40:21.786Z**. Independent read-only verification passed at **2026-10-21T04:44:07.461135+00:00**: all seven parent calls and seven triggered transactions finalized successfully or credited the expected native transfer. The three native credits have the exact intended recipient, amount and parent linkage. The season contract's balance is **0 wei** and its refund is recorded as **paid**.

## Exact recovery path

1. Close `series-1` after its end while both original challenges remain unsettled. Both imported rounds become VOID, the threshold remains 2, there are no winners, and the full 0.05-GEN bonus is allocated to the organizer.
2. Claim that refund and verify its native credit on-chain.
3. Settle `challenge-5`, then claim its sole qualifier's 1-wei share as the organizer/steady entrant.
4. Settle `challenge-6` after the judging grace. The uncompleted control entry becomes insufficient evidence under the existing deadline fallback; its failed judgment is not retried. The two qualified entrants have zero integer shares from the 1-wei pool, leaving the organizer a 1-wei remainder, which is refunded.

The previous report focused on the later 24-hour timeout. This recovery used the existing earlier refund path for an ended season with unsettled challenges. It required no contract change or new deployment.

## Separate contract evidence

| Contract | Network | Direct Explorer Contract URL |
| --- | --- | --- |
| EligibilitySeries | StudioNet 61999 | [0x0e355b80258869F6b42016185EBc0901F87C152C](https://explorer-studio.genlayer.com/address/0x0e355b80258869F6b42016185EBc0901F87C152C) |
| EligibilityJudge | StudioNet 61999 | [0x03E7970E791d644B2714a457D178Edf036670bb7](https://explorer-studio.genlayer.com/address/0x03E7970E791d644B2714a457D178Edf036670bb7) |

The contract links were verified against the StudioNet Explorer API and in Chrome on 2026-10-20; recovery verification independently confirmed chain ID 61999 and read the deployed contracts at the same addresses.

## Preserved failure and validation

The stopped clean-run manifest is byte-for-byte unchanged, SHA-256 `8371021c06a2d88ee0918cd6a6ed18b22500f57780154bd1e1632bc1ea737d1d`. Its failed MAJORITY_DISAGREE transaction, unrun A/B/C hearings and missing badges remain reported. The submission verifier still reports FAIL and the submission draft remains blocked. No failed live case was retried. No production deployment or Portal submission occurred.

The recovery runner passed TypeScript checking and its no-write preview before execution. The independent verifier checked all 14 protocol receipts and final contract state. Its first final-state read used a lowercased contract address that StudioNet rejected; correcting the read address and rerunning read-only verification did not resend any transaction. Contract sources were unchanged, so the prior 110 contract tests and 22 app tests were not rerun for this operational recovery.

Evidence: [recovery journal](../../deploy/milestone-recovery.json), [independent verification](../../deploy/milestone-recovery-verification.json), [stopped clean run](../../deploy/previous-runs/milestone-v1-clean-stopped/deploy/milestone-proof.json). Execution is limited to seven fixed zero-value calls in `scripts/recover-milestone.ts`; `scripts/recover-milestone.ps1` defaults to read-only preview. No demo keys are imported by the recovery runner.
