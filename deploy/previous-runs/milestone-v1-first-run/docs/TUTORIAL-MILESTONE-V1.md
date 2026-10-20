# Seasons, badges and rule disputes

Open [Seasons](https://eligibility-judge.vercel.app/series) to inspect the demonstration. Reads use finalized StudioNet state; the displayed timestamp identifies when it was observed. A recorded proof remains visible when a live read is unavailable.

## Inspect a season

Choose a season to see its frozen challenges, qualification threshold, imported rounds, counts, streaks and bonus allocations. A void round never reduces the required qualification count. Anyone can import an eligible round or close the season after its end. Pending hearings must resolve before their credentials can be imported. After the additional 24-hour season exit deadline, unavailable sources permit a full organizer refund.

Connect a StudioNet-compatible browser wallet to create a season from 2–6 challenges you organize, or claim an allocation. A signed claim reserves an attempt. Its native transfer must finalize and credit the beneficiary; select **Verify native credit** to record that payment. A failed transfer permits the next numbered attempt once the contract has recovered its funds. The transaction trail preserves hashes across reloads.

## Review a rule

Open a settled challenge in the eligibility ledger, expand an entry and inspect a rule. The review panel shows the original ruling alongside the effective ruling. During the two-hour opening window after the judge's one-hour grace period, choose an existing file from the pinned commit, provide an argument of at most 600 characters, and bond 0.01–10 simulated GEN.

Opening first persists the funded reservation. A zero-value file check then confirms that the full named file exists and fits within 64 KB. The hearing fetches that whole file. Every validator independently decides the verdict and verifies the leader's quoted text against its own fetch. Arguments and instructions in files are untrusted evidence.

UPHELD pays the bond to the entrant, or the organizer for a self-dispute. OVERTURNED returns it to the disputant. Unreachable evidence and 24-hour expiry produce VOID and a refund. Anyone can expire an overdue pending opening or hearing, and anyone can release an allocated bond to its fixed beneficiary. These changes affect credentials and season standings; the already-settled judge prize pool remains immutable.

## Verify a badge

Open a builder's badge wall from the standings or enter a full wallet address under **Qualification badges**. Expand **Verify badge** to read the contract's verification result, pinned commit, rulebook hash, effective-verdict digest and whether an overturn contributed. The embeddable link uses the same on-chain verification. Badges are non-transferable and unique per challenge and wallet.

Anyone can mint for a qualified entrant after the opening window has closed and all pending hearings have finalized. An original qualification is not enough while a hearing can still change it.

## Read the demonstration honestly

All demonstration wallets are owner-controlled. Bullseye and Eligibility Judge are the owner's published repositories; the failing entry is an existing public negative test fixture. Its injection argument is deliberately adversarial test data. GEN is simulated StudioNet currency.

The pinned Bullseye tree exceeded the immutable judge's 96 KB inspection bound. Its original insufficient-evidence outcomes are retained; six additional full-file hearings were planned but not opened before their windows closed. A completed full-file overturn qualifies one entrant in the first round. The original threshold-two season therefore has no winner and refunds its organizer; a separately created threshold-one, 1-wei season proves a positive bonus claim without changing the original season. A separate original payout-rule call finalized with validator disagreement and is preserved without rerun. The original judge's timed settlement handles any unfinished verdict. Case C was VOID during its source check; the subsequent hearing call rolled back because the case was not open, and its bond is refunded. The live injection outcome is unproven. The manifest and read-only verifier distinguish reported failures from successful transactions.

See [the milestone manifest](../deploy/milestone-proof.json), [verification report](../deploy/milestone-verification.json) and [architecture](MILESTONE-V1-ARCHITECTURE.md) for actual results and hashes. The verification report is generated only after the live sequence completes.
