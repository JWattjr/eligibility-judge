# Milestone v1 readiness

**Ready for owner review with reported live deviations. Nothing has been submitted to the Portal.**

The [live site](https://eligibility-judge.vercel.app/series) and GitHub implementation are published. The independent read-only verifier returned **PASS_WITH_REPORTED_FAILURES** across **126 saved hashes**. `allTransactionsSuccessful` is explicitly false: failed calls are retained as failures, never counted as successful evidence.

## Contracts

| Contract | Direct StudioNet Explorer evidence |
| --- | --- |
| disputes | [0x1fcF18ef9e74159900E4C7eA00F859F9132EBa5C](https://explorer-studio.genlayer.com/address/0x1fcF18ef9e74159900E4C7eA00F859F9132EBa5C) |
| badges | [0x7BCF4C1ED69F0B0dC36b590911f886bd32f24bDE](https://explorer-studio.genlayer.com/address/0x7BCF4C1ED69F0B0dC36b590911f886bd32f24bDE) |
| series | [0x03262D836d327d4b01103A2ca759BC0776414E53](https://explorer-studio.genlayer.com/address/0x03262D836d327d4b01103A2ca759BC0776414E53) |

The unchanged [EligibilityJudge dependency](https://explorer-studio.genlayer.com/address/0x03E7970E791d644B2714a457D178Edf036670bb7) is a separate GenLayer Explorer Contract evidence entry alongside the three new contracts. All four addresses were verified as CONTRACT on StudioNet. All three new deployed sources equal the working files and committed Git bytes. The original judge file remains unchanged.

## Actual live outcomes

- **A OVERTURNED**: [finalized outcome](https://explorer-studio.genlayer.com/tx/0xb007b350b6873b6332bc5b58d43bbb5391956d0ee2e4496c2e14eeda780ed63e). Full-file PASS; bond returned.
- **B UPHELD**: [finalized outcome](https://explorer-studio.genlayer.com/tx/0xe122edd31707221a109058f3b4899716434dcbfc359bd2bffbda66f84ddccb16). Original FAIL upheld; bond paid to entrant.
- **C VOID**: [finalized outcome](https://explorer-studio.genlayer.com/tx/0x586f934271a13b894f7518f5250c1ddbc06bba80add7cc04ae04274ac6bdab0a). Source check was VOID; bond returned. The later hear call correctly rolled back; no live injection judgment is claimed.

One non-transferable badge was minted and verified for the targeted entrant in challenge-3, through the finalized overturn. The original threshold-two season has zero winners and returned its **0.1 GEN** pool to the organizer. A separately created threshold-one control over the same finalized rounds paid **1 wei** to the qualified entrant; it never lowered or changed the original season's threshold.

The pinned Bullseye tree was 263,265 bytes, above the immutable judge's 96,000-byte bound. Both original insufficient-evidence results remain recorded. Six additional planned full-file hearings were not opened before their windows closed. One original payout-rule judgment failed consensus; the real grace deadline permitted settlement without fabricated verdicts. The failed injection hearing attempt followed an already-VOID file check. These two failed calls and every mismatch remain in the manifest. No failed case was replayed.

## Money and exits

| New deposit | Amount |
| --- | --- |
| Two judge challenge pools | 2 wei |
| Three dispute bonds | 0.03 GEN |
| Original season bonus | 0.1 GEN |
| Separate positive-payout control | 1 wei |
| **Gross deposits** | **0.13 GEN + 3 wei** |

All seven intended native payments were credited and independently checked. Every current new contract has zero balance. The three retired, unfunded milestone candidates also have zero balance. This milestone budget is separate from the original release's historical locked funds.

## Verification and release

- 97 direct contract tests: 46 existing plus 51 milestone tests. All three contracts pass GenVM lint and SDK validation with the pinned runner.
- 22 app tests, TypeScript and remote production build pass.
- Production UI and API checks pass at 1440×960 and 390×844: both closed seasons, verified badge/embed, minted guard, challenge/rule context, original versus effective verdict, paid native receipts and saved-hash reload recovery.
- 33 Explorer evidence links return HTTP 200. Contract evidence uses direct address links, separately typed GenLayer Explorer Contract.
- Summary: 947/1,000 characters. Contract descriptions: 180, 194 and 197/200.
- Resuming the completed dispute stage added zero transactions and zero deposits, retaining all 126 saved hashes.

The final app release is `df9786a`, Vercel production deployment `dpl_F7HSAP5scHMnina1f5eBf79xTwSk`. The production alias is eligibility-judge.vercel.app. New browser wallet signatures and pending-wallet behavior are not claimed; live calls used the authorized CLI demo accounts. Live injection resistance remains unproven because case C did not reach a hearing. Direct tests cover injection handling.

## Reviewable artifacts

- [Portal milestone fields](milestone-v1.json)
- [Live manifest](../../deploy/milestone-proof.json)
- [Independent verification](../../deploy/milestone-verification.json)
- [Explorer checks](milestone-v1-links.json)
- [Production browser/API checks](../milestone-v1-browser.json)
- [No-new-transaction resume proof](../milestone-v1-resume.json)
- [Tutorial](../TUTORIAL-MILESTONE-V1.md)
