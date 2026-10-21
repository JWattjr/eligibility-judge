# Milestone v1 final demo — in progress

The user authorized proceeding through the revised demo, verification and deployment. The original judge and all three corrected milestone contract sources remain unchanged. The three corrected deployments are reused after fresh source and wiring checks. No old failed transaction is replayed.

The negative control now contains a full, small GenLayer contract whose claim method explicitly raises an error instead of paying GEN. This supplies direct code evidence for FAIL. The old receipt proves validator disagreement but does not identify which validator check rejected the leader; a unique root cause is not claimed. Rounds are run sequentially to preserve each real 15-minute entry window and one-hour judging grace.

Previous gross deposits of 0.05 GEN plus 2 wei remain counted toward the 0.2-GEN ceiling despite their verified recovery. The planned final run deposits 0.08 GEN plus 2 wei, for cumulative gross deposits of 0.13 GEN plus 4 wei. The 0.05-GEN bonus is funded only after A/B/C succeed.

[The stopped clean-run archive](../../deploy/previous-runs/milestone-v1-clean-stopped/) preserves its failed receipt, manifest, exact source snapshots and [successful recovery report](../../deploy/previous-runs/milestone-v1-clean-stopped/docs/submission/MILESTONE-V1-RECOVERY.md). The first run remains in its separate archive. The active final-run manifest contains fresh cases only, plus read-only deployment provenance.

Final live verification, browser checks and production deployment are pending. The Portal draft remains blocked and will not be submitted automatically.
