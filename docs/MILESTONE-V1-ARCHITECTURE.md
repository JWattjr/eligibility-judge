# Milestone v1 implementation boundary

The immutable EligibilityJudge at `0x03E7970E791d644B2714a457D178Edf036670bb7` remains authoritative for its existing prize pools. No new contract writes to it. Constructor addresses are immutable dependencies. RulingDisputes alone runs web/LLM consensus; badges and seasons derive deterministic state from finalized source views.

Disputes freeze the judge entry, rule, original verdict, named file and pinned commit. Validators independently fetch the file, independently judge it, compare only verdict and path, and verify the leader's quote in their own full fetch. Missing, oversized or unreachable evidence produces VOID/refund, never a default loss. Expiry is permissionless after 24 hours. Pending finality can be recovered by independently checking the exact successful protocol receipt. A late callback cannot revive an expired case.

The opening check uses the same pinned `raw.githubusercontent.com` file URL as the hearing. HTTP 404 means MISSING; HTTP 200 up to 65,536 bytes means FOUND; a larger HTTP 200 body means OVERSIZED. Every other status or network exception means UNREACHABLE. No GitHub tree API call is required by the disputes contract. The immutable original judge still uses its existing bounded tree inspection.

Badges and imported rounds require both the two-hour dispute-opening window to have closed and every dispute for the entry to be terminal. Merely waiting until the opening window closes is insufficient: a last-second case can remain open for another 24 hours. No badge is minted against a provisional ruling. Disputes cannot change the original judge pool.

The owner selected a fixed season qualification count: void rounds do not lower the threshold. Two required qualifications across two rounds still require two if one round is void. The full pool refunds when no wallet reaches the threshold. Standings are calculated in the frozen challenge order, independently of the order callers import rounds.

## GEN exit audit

- Dispute OPENING/OPEN/HEARD: anyone can expire after the frozen hearing deadline; VOID refunds the disputant. The payable opening commits the funded reservation before emitting a zero-value file-check callback. Failed web consensus cannot orphan the bond. Invalid funded inputs create an explicit refundable record instead of rolling back and stranding StudioNet value.
- Dispute finality pending: self callback, or permissionless receipt-verified finality recovery. Generation guards reject stale callbacks.
- Season OPEN: anyone can close once every round is imported or the fixed end passes. An unsettled round observed at/after the end is void. If source/dispute views cannot finalize by end + 24 hours, anyone can void the whole season for an organizer refund.
- Season finality pending: self callback or receipt-verified recovery, without recomputing winners.
- All final credits: reserved nonce-bound pull claims, independent exact native-credit verification and finalized paid/failed state. A failed transfer is retryable after returned funds fully back unpaid liabilities. A permissionless claim-for path sends only to the fixed beneficiary, so a missing beneficiary cannot prevent release. Verification never uses a caller-controlled RPC URL.
- No stake in badges. No administrator selects a verdict, winner, recipient or refund amount.

The clean live runner journals the broadcast intent before sending and each returned hash before waiting. It applies a cumulative 0.2 GEN gross-deposit ceiling, including the recovered prior clean-run deposits, and runs each case once. Any failed receipt, unexpected verdict or failed phase check records a stop reason and prevents subsequent phases or replays. Read-only polling follows the original hash. Before funding, every pinned candidate tree is fetched once from the machine, saved with its hash and byte count, and must be complete and below 80,000 bytes. Each entrant uses a different repository or commit in round two. No milestone deployment or live success is claimed by direct tests. The complete first-run proof is preserved in `deploy/previous-runs/milestone-v1-first-run/`.

The final workflow seeds, judges and settles each round before starting the next. It funds the season bonus only after all three hearings and their bond credits succeed. Stopped-run and recovery evidence is also preserved in `deploy/previous-runs/milestone-v1-clean-stopped/`.
