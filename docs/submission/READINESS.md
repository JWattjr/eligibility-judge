# Submission verification - production check pending

The fixed contract is [0x03E7970E791d644B2714a457D178Edf036670bb7](https://explorer-studio.genlayer.com/address/0x03E7970E791d644B2714a457D178Edf036670bb7) on StudioNet 61999. Both approved one-wei live demonstrations completed. The read-only proof verifier passed all 62 finalized receipts, callback origins, frozen rulebooks, exact on-chain states, four outcomes, exact credited payout and refund, zero remaining contract balance, and exact deployed source.

GenVM lint, 46 contract tests, TypeScript, 16 app tests and the final production build pass. AST comparison confirms that evidence helpers, judging prompts and validator comparisons are unchanged. Chrome verified raw replay URL validation, disabled settlement before and during grace, enabled settlement after the real deadline, the timeout reason without invented verdicts, claim tracking and reload recovery. Production deployment and its final desktop/mobile checks are in progress; this document will be marked ready after those pass.

- Site: https://eligibility-judge.vercel.app
- Source: https://github.com/JWattjr/eligibility-judge
- Proof: [manifest](../../deploy/proof.json) and [verification](../../deploy/proof-verification.json)
- Portal fields: [portal-fields.json](portal-fields.json), 956-character description
- Browser verification: [report](../browser-verification.json)

| Case | Final outcome | Entry receipt | Final judgment callback |
|---|---|---|---|
| qualified | QUALIFIED | [entry](https://explorer-studio.genlayer.com/tx/0xc68c221d51308caf3e2cdcce1b84283b937dca37dba7bb5cc1f83e2562473313) | [final callback](https://explorer-studio.genlayer.com/tx/0xcc4472a19e02bffcadd2744d237dd62a75037b47b366b870f11bea1dd6c4d2cd) |
| failed | DISQUALIFIED | [entry](https://explorer-studio.genlayer.com/tx/0x4d77934a04b2d28c5f6606d8d505d4459be0396f2f007fe7626ce82c20173fe8) | [final callback](https://explorer-studio.genlayer.com/tx/0x79f63be21f2dec86fdf94135796ccc5490d70c320e2386d3bad3b743f699addb) |
| missing | INSUFFICIENT_EVIDENCE | [entry](https://explorer-studio.genlayer.com/tx/0xb3d0044bd56cf6b0b8e68e4560600e90a02ee030191533bcabe77141c87222e8) | [final callback](https://explorer-studio.genlayer.com/tx/0x15870cf313573cd48b26e4aebba9ff9fae162478a9264f60321fede28b99a100) |
| injection | DISQUALIFIED | [entry](https://explorer-studio.genlayer.com/tx/0xcdcf997221eaa76f3c3d6a5fa37865df8a3b4b152ec611da63888d9e1756cd7e) | [final callback](https://explorer-studio.genlayer.com/tx/0xacd2babaec9dbdb1a8606a27711374980bf8759c644c2c1696a0a19d510f1ce8) |

Standard settlement: [finalized receipt](https://explorer-studio.genlayer.com/tx/0x4f3353aa2186e8fec862993f23df8e826ffae7bd7b1ca9de2077154ce177f6ce).

Credited qualifier payout: [one wei](https://explorer-studio.genlayer.com/tx/0xfdb4eaba2d58eddb83fcfb9b3dd97d5c4d1faf8b03cbfed829e351b2242c1522).

## Timeout path

Challenge challenge-1 had one entry that was never judged. Submission closed at 17:46:45 Lagos time on October 8; the real one-hour grace deadline was 18:46:45. Settlement was sent after that deadline. The entry finalized as INSUFFICIENT_EVIDENCE with reason "Judgment did not finalize before the grace deadline." Its three verdicts remain null, pending flags are false, no entry qualified, and the entire one-wei pool was claimed and credited to the organizer.

| Proof | Receipt |
|---|---|
| Funded creation | [one-wei deposit](https://explorer-studio.genlayer.com/tx/0x75f6842c2f3c80acadf1a6a2292fbc7c449a5377169726e56f2ad6e73ed69859) |
| Never-judged entry | [entry](https://explorer-studio.genlayer.com/tx/0x9eb0b1130ef3b5ecb69c4303fd7f14c0cbd37539a05bd946151ea55527784df9) |
| Grace settlement | [finalized settlement](https://explorer-studio.genlayer.com/tx/0x4d4d76bb3e495ce0c732f81adb9f63eb660f9e84e4b8d28ccd86b829cd685171) |
| Finalized settlement callback | [callback](https://explorer-studio.genlayer.com/tx/0x57231727e2148301a95a19bf94dc7e3f3fd517668ef074f4b5164d446b88fccb) |
| Organizer refund claim | [finalized claim](https://explorer-studio.genlayer.com/tx/0x59b13ca08234edb6b043e507722eac767f277260c139f7c37d7521f0d57a6353) |
| Credited organizer refund | [one-wei native credit](https://explorer-studio.genlayer.com/tx/0x1263413bbe824d0f7ebbfa0ca046996d854b5ef6124519345f76f5e72e4a7bea) |

The previous paid contract, source, proof, browser verification and native appeal history are preserved under [previous runs](../../deploy/previous-runs/pre-grace/). Native appeal verification explicitly rechecks that historical contract and its unchanged paid challenge; it is not a claim of new-contract wallet signatures. Older locked pools remain documented in the README. No further deposit is required for this release.

The owner performs the final Portal submission. Nothing has been submitted automatically.
