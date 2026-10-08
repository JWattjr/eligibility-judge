# Eligibility Judge — fix prompt

You are fixing two contract bugs in `eligibility-judge/` (contract `contracts/eligibility_judge.py`, currently live at `0x03Dd21B241ea3e1EBB9B126Eb732d795dEE8Ae9a` on StudioNet). Work autonomously. Read AGENTS.md first. Keep the change small: fix these two bugs, prove them live, update the docs. Do not refactor, restyle the app or change the judging prompts or consensus logic.

## Bug 1: the prize pool can be locked forever

`settle` requires every entry to have a final status, and nothing ever ends that wait. If a judgment keeps failing consensus, or nobody calls `judge_rule` for an entry, settlement is blocked permanently and the pool can never be paid or refunded. The README's own funding history (6 GEN + 3 wei locked across earlier contracts) comes from this bug.

**Fix:**
1. **Add a grace constant**, `JUDGING_GRACE = 3600` seconds.
2. **Change when `settle` is allowed:**
   - If every entry is final (`QUALIFIED`, `DISQUALIFIED` or `INSUFFICIENT_EVIDENCE`), allow it from `closes`, as today.
   - Otherwise, allow it only from `closes + JUDGING_GRACE`.
3. **Unfinished entries become `INSUFFICIENT_EVIDENCE`.** At that point, set each unfinished entry (`SUBMITTED` or `JUDGING`) to `INSUFFICIENT_EVIDENCE`, and record a reason such as "judgment did not finalize before the grace deadline" so the UI can show it. Unfinished entries never qualify.
4. **`judge_rule`:** require `now() < closes + JUDGING_GRACE`, so judging can't race settlement.
5. **`finalize_judgment`:** if the challenge status is no longer `RULES_ACCEPTED`, return without changing anything. A late callback must never alter a settled challenge or raise in a way that blocks other callbacks.
6. **Re-entry:** keep the current rules. A re-entry made just before `closes` is covered by the grace path.

## Bug 2: demo links break consensus

`enter` only accepts `https://web.archive.org/web/<14 digits>/<url>`. That form serves the Wayback toolbar wrapper, whose bytes can differ between fetches. Leader and validator then compute different `evidence_hash` values and cannot agree whenever an entrant supplies a demo link.

**Fix:**
- Accept only the raw form `https://web.archive.org/web/<14 digits>id_/<url>`.
- Update the error message, the app's entry form hint and validation, and any docs or examples that show the old form.

## Tests (gltest direct mode)

Add tests for:
- `settle` before `closes`: rejected.
- `settle` at `closes` with an unjudged entry: rejected.
- `settle` after `closes + JUDGING_GRACE` with one unjudged and one qualified entry: the unjudged entry becomes `INSUFFICIENT_EVIDENCE` and the qualifier gets the full pool.
- The same, but with nobody qualified: the whole pool is refundable to the organizer.
- `settle` at `closes` when every entry is final: still works immediately.
- `judge_rule` after the grace deadline: rejected.
- A late `finalize_judgment` callback after settlement: a no-op, with the challenge unchanged.
- Demo URL: the `id_` form is accepted, while the toolbar form and other hosts are rejected.

Run the full suite, genvm-lint, the TypeScript typecheck, the app tests and a production build. All must pass.

## Live proof (StudioNet)

1. Deploy the fixed contract with the existing staged deploy script.
2. Rerun the standard demo on the new contract with a 1-wei pool (`ELIGIBILITY_DEMO_WEI=1`). It must reproduce the same four outcomes (qualified, failed, missing, injection), then settle and pay out.
3. **Prove the timeout path.** Create a second 1-wei challenge with a short window and one entry that is never judged. After `closes + JUDGING_GRACE`, call `settle` and show:
   - the entry finalized as `INSUFFICIENT_EVIDENCE`
   - the organizer refund claimed and credited

   This is the transaction that proves Bug 1 is fixed.
4. **Ask the owner before depositing.** The total extra deposit is 2 wei across the two challenges; don't deposit without the owner's approval in chat.

Respect the RPC limits: 30 requests/min and 500/hr. Poll every 10 s and resume saved stages after any timeout. Do not redeploy more than once unless a deploy fails.

## Docs and submission

- **Proof files:** update `deploy/proof.json`, `npm run verify:proof`, and the receipts table in `docs/submission/READINESS.md` for the new contract. Add the timeout-path receipts as their own section.
- **Point everything at the new address:** the app config, README, `docs/submission/portal-fields.json` contract links and the explorer links.
- **Archive the old contract.** Move it (`0x03Dd21B2…8Ae9a`) under "previous runs", the same way earlier runs are kept. Don't delete history.
- **README funding history:** keep it, and add one sentence saying the lock bug was found from those runs and fixed with the grace-period settlement, with a link to the timeout-path proof.
- **Description length:** keep the Portal description within 1,000 characters.
- **Deploy the app.** `vercel --prod --scope wattxs-projects`, with a remote build.
- **Verify the live app.** Check it shows the new contract and the completed demo on desktop and at 390×844 mobile.
- **Commit and push** in small commits. Never submit to the Portal; the owner submits.

## Completion report

End with:
- the new contract address
- finalized receipts for the four outcomes, the settlement, the payout and the timeout-path settlement and refund
- the checks that actually ran
- confirmation that the live site and Portal fields point at the new contract

Do not report it ready if the timeout path is proven only by mocked tests.
