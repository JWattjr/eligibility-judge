# Submission review

The live demo is settled and its one-wei pool has been claimed and credited. The read-only proof verifier passed all 54 saved receipts, callbacks, exact finalized state, rulebook hash, four outcomes, exact native payout and deployed source.

The project is submission-ready. A real Chrome / MetaMask native appeal was approved inside the 30-second window and finalized after a second consensus round. The validators upheld the intentionally rejected settled-rulebook call; this expected error proves the appeal flow without changing the paid demo. `npm run verify:appeal` independently rechecks both CLI and browser appeals plus the unchanged finalized challenge and zero contract balance. No further deposit is needed.

- Site: https://eligibility-judge.vercel.app
- Source: https://github.com/JWattjr/eligibility-judge
- Contract: `0x03Dd21B241ea3e1EBB9B126Eb732d795dEE8Ae9a`
- Submission fields: `docs/submission/portal-fields.json` (891-character description)
- Tutorial: `docs/TUTORIAL.md`
- Two-minute demo: `docs/DEMO.md`
- Proof: `deploy/proof.json` and `deploy/proof-verification.json`
- Browser checks and their exact limits: `docs/browser-verification.json`

| Entry | Final outcome | Entry receipt |
|---|---|---|
| qualified | QUALIFIED | [0xfb9926445447294b0f5b5c8ddbfad6ce101e7b2875d48b48b84af8a72411a396](https://explorer-studio.genlayer.com/tx/0xfb9926445447294b0f5b5c8ddbfad6ce101e7b2875d48b48b84af8a72411a396) |
| failed | DISQUALIFIED | [0xd3b4325d9131cb068c19fc2ff05b37633ae1c77258c6343de821cd1b907f7c8a](https://explorer-studio.genlayer.com/tx/0xd3b4325d9131cb068c19fc2ff05b37633ae1c77258c6343de821cd1b907f7c8a) |
| missing | INSUFFICIENT_EVIDENCE | [0xa63796932f97420a0ab9d4f87113309bc9255a04a94ff7fa4e6c6929aca85dab](https://explorer-studio.genlayer.com/tx/0xa63796932f97420a0ab9d4f87113309bc9255a04a94ff7fa4e6c6929aca85dab) |
| injection | DISQUALIFIED | [0xa290e75c0e7684e80324f6dcef2d4cb214fa19ee738ff946f932ff41745d8639](https://explorer-studio.genlayer.com/tx/0xa290e75c0e7684e80324f6dcef2d4cb214fa19ee738ff946f932ff41745d8639) |

Settlement: [0xd869d05d650a845a5424eec0f5c31cadf5c1b607e88dfc1aa8087238cd38fc47](https://explorer-studio.genlayer.com/tx/0xd869d05d650a845a5424eec0f5c31cadf5c1b607e88dfc1aa8087238cd38fc47).

Credited payout: [0xd5c5b7f84ec29fc2d967c88418109872d31b8301a8e1d0d1b3f6049e45e22db0](https://explorer-studio.genlayer.com/tx/0xd5c5b7f84ec29fc2d967c88418109872d31b8301a8e1d0d1b3f6049e45e22db0).

All sixteen parent judgment hashes and finalized callbacks are in the proof manifest. The source commit pinned in the qualifying entry is preserved; later app and documentation fixes do not change that entry.

The owner performs the final Portal submission. Nothing has been submitted automatically.

Native browser appeal: [0xc568eeeae18c62240c1ef86b00baa3f7a309d8e7c53716f95fb9856aa6602c2e](https://explorer-studio.genlayer.com/tx/0xc568eeeae18c62240c1ef86b00baa3f7a309d8e7c53716f95fb9856aa6602c2e). Signed 27 seconds after acceptance; two rounds; expected rollback upheld. Details: `deploy/native-appeal-proof.json`.

Validation: 33 contract tests and GenVM lint passed for the unchanged deployed contract; TypeScript, 14 app tests and a production build passed for the final app correction. Desktop and mobile checks and the exact wallet-signing limits are preserved in `docs/browser-verification.json`.

Final production result display verified on desktop and 390x844 mobile at commit `79566497dd0c20e64575e552711172c071f29439`: native appeal upheld, exact expected rollback reason, reload recovery, and no horizontal overflow. Vercel production deployment `dpl_EBnLeRWNsqSXM7Fgncx1LJJdSLuc` is Ready.
