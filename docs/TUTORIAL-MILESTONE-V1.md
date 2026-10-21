# Seasons, badges and rule disputes

Open [Seasons](https://eligibility-judge.vercel.app/series) to inspect the demonstration. Reads use finalized StudioNet state; the displayed timestamp identifies when it was observed. A recorded proof remains visible when a live read is unavailable.

## Inspect a season

Choose a season to see its frozen challenges, qualification threshold, imported rounds, counts, streaks and bonus allocations. A void round never reduces the required qualification count. Anyone can import an eligible round or close the season after its end. Pending hearings must resolve before their credentials can be imported. After the additional 24-hour season exit deadline, unavailable sources permit a full organizer refund.

Connect a StudioNet-compatible browser wallet to create a season from 2–6 challenges you organize, or claim an allocation. A signed claim reserves an attempt. Its native transfer must finalize and credit the beneficiary; select **Verify native credit** to record that payment. A failed transfer permits the next numbered attempt once the contract has recovered its funds. The transaction trail preserves hashes across reloads.

## Review a rule

Open a settled challenge in the eligibility ledger, expand an entry and inspect a rule. The review panel shows the original ruling alongside the effective ruling. During the two-hour opening window after the judge's one-hour grace period, choose an existing file from the pinned commit, provide an argument of at most 600 characters, and bond 0.01–10 simulated GEN.

Opening first persists the funded reservation. A zero-value raw-file check then confirms that the named file exists and fits within 64 KB, using the same pinned raw URL as the hearing rather than the GitHub tree API. The hearing fetches that whole file. Every validator independently decides the verdict and verifies the leader's quoted text against its own fetch. Arguments and instructions in files are untrusted evidence.

UPHELD pays the bond to the entrant, or the organizer for a self-dispute. OVERTURNED returns it to the disputant. Unreachable evidence and 24-hour expiry produce VOID and a refund. Anyone can expire an overdue pending opening or hearing, and anyone can release an allocated bond to its fixed beneficiary. These changes affect credentials and season standings; the already-settled judge prize pool remains immutable.

## Verify a badge

Open a builder's badge wall from the standings or enter a full wallet address under **Qualification badges**. Expand **Verify badge** to read the contract's verification result, pinned commit, rulebook hash, effective-verdict digest and whether an overturn contributed. The embeddable link uses the same on-chain verification. Badges are non-transferable and unique per challenge and wallet.

Anyone can mint for a qualified entrant after the opening window has closed and all pending hearings have finalized. An original qualification is not enough while a hearing can still change it.

## Read the demonstration honestly

The demonstration uses owner-operated wallets and public repositories. GEN is simulated StudioNet currency. Overturns affect credentials and season standings, not the original judge pool.

The completed `milestone-v1-release` proof independently reports **PASS**, without reported failures or mismatches. In round 1, steady qualifies, rescued receives insufficient evidence because the decisive payout implementation is beyond the fetched prefix, and control fails. A fetches the complete pinned payout file and overturns that rule to PASS. B upholds a frivolous challenge against the control's correct FAIL, awarding its bond to the entrant. In the distinct second round, both builders qualify normally and control fails again. C hears the exact prompt-injection argument against the control's README and upholds FAIL.

Four qualification badges finalized, including rescued's round-1 `via_dispute` badge. The fixed threshold remains two; steady and rescued each qualify in both rounds and each receives **0.025 GEN**, with native credit independently verified. All seven clean-demo native transfers are verified. The previous attempt's one-wei pool was recovered separately and does not count as a clean-demo transfer.

Open [Seasons](https://eligibility-judge.vercel.app/series), [Rule hearings](https://eligibility-judge.vercel.app/disputes) and [Qualification badges](https://eligibility-judge.vercel.app/badges) to inspect the resulting state. The badge wall starts with the rescued builder so the dispute-derived credential is visible. Expand Verify badge to inspect its on-chain verification and embed link. Browser validation and production release are recorded separately in [readiness](submission/MILESTONE-V1-READINESS.md).

See [the milestone manifest](../deploy/milestone-proof.json), [strict verification](../deploy/milestone-verification.json) and [architecture](MILESTONE-V1-ARCHITECTURE.md) for exact results and hashes. Historical attempts remain in separate archives and the README's historical sections. Nothing is submitted to the Portal automatically.
