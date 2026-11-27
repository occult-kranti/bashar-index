# Deposit 2: the step-0 register files, citing deposit 1

Third-round panel programme, step 0; the lead's rulings 2 and 11. It cites deposit 1 (`../deposit-1-forecast-ledger.md`,
merged 2026-11-26T02:00:22Z as `9506c24`): forecast ledger SHA-256 `d2e8e3fd32291f3b0b0a40f5e8a54cf88819e391b6c89a536df49c80a799a80a`.
No class-a entry runs before this commit is merged. Exploratory throughout.

**Programme hashed with it:** `../programme.md` (as merged in PR 107) SHA-256 `7f34500c7fa97b3877600175b0ccca394d681b87c6ad0963b40047b5fa0138bd`. Its class-b cards are hashed through it.

**Lead's additions in this deposit:** `lead-margins-and-readings-2026-11-26.md` fixes the default margins, the readings A, B and undetermined, the interval rule and the tiers, because the programme states no margin for any of its 56 primaries. It was written before any class-a run. The novelty ledger is published as a log: no novelty sentence prints in the paper before the second attack pass (ruling 12). The development set of the split policy is the registry's development set (the pilot's 48 creators).

## Public files in this folder

| File | SHA-256 |
|---|---|
| `account-prediction-cells.csv` | `5c6b741dde0f726ca04832d30dbb753f26127def7089abb7c6391928e36c5fa6` |
| `account-prediction-cells.md` | `e6de6bd395a339080c3f3c43d5f36e8d1d89e002950e3cd5903c3bf7563af322` |
| `calibration-method-card.md` | `a8bac7543b3ad25fa361d4eb3f04cc1e4e5e5d688c87e9e5d9915ba68fd22653` |
| `data-r3-P39-ledger.csv` | `9d9188f61597e5cd89eba757b98b67173dd6f9d3cf175db5073301bce64fcf93` |
| `deposit.json` | `b7254729db8b95393bf51d63452102e4542dd9f2685c46004895073f31f0520f` |
| `fig-r3-P39-ledger.pdf` | `9bce035b736886a2cd988ce12e84b70072b615f3607ff1f928b0263da4231114` |
| `fig-r3-P39-ledger.png` | `3957d8bafb6f9e61f9aac3baa2e7f4e022253b36f64d855c2266b4445ab262aa` |
| `lead-margins-and-readings-2026-11-26.md` | `c25c8979eb272b19125a0597658295241d1d4c40a33f0a22015032f90bbf18cd` |
| `ledger-manifest.json` | `fff40453c059254de70ab0d22be86eabae610af12aacf2deea4cda015c7b6de6` |
| `margins-register.csv` | `753397e64e1407463d75ff3cf831daa370f2919e13963d3236576474ef2434f7` |
| `margins-register.md` | `78c22cb975fab19c36f38bee0d53919d691447e9c90bd2af49e5134059c389a7` |
| `novelty-ledger.md` | `605f382993e08c4bef04e3662a3692f0262e65b03bb97e2a5ee3956cdaa995ab` |
| `split-policy.md` | `efdcfae32314efc75273cac8cf44cfc20ce34bc9aef7c2f7fd4cf479b943d3e7` |

## Private files (hashes only)

| File | SHA-256 |
|---|---|
| `ledger.private.jsonl` | `d2e8e3fd32291f3b0b0a40f5e8a54cf88819e391b6c89a536df49c80a799a80a` |
| `split.private.json` | `85848e4cb78327c52163d254a16447b90581fd6e1a696c959237fc7d0ef077f2` |

## Code (private; hashes only, because the files carry local paths)

| File | SHA-256 |
|---|---|
| `code/build_ledger.py` | `004235539db98ecda1a39edfba9d6c07b5b47dbd56f32e631819035276005b27` |
| `code/build_public.py` | `fc4e55466ead6f764a832ef917c209df881a22589d485c57c2e2f8d2c5a81d36` |
| `code/draw_split.py` | `72281e90a8d21bff3ae2cefe6634b8c4ce8ef3cdd84b19584f2b4f95b1d7a300` |
| `code/plot_ledger.py` | `6e07a31880220146d123b99377c97fbf2653e4664d94d8d2bae027499f600157` |
| `code/recognizer_fields.py` | `3bd8033e89ab3c5b0d20398cec3e8b14a4937984c59f6d52a950935ab1f73a0c` |
| `code/rule_coder.py` | `4fe41740974b88f76358a99bb970bab2c1847b2ca9e907c2e1be518c575aef71` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `code/test_rule_coder.py` | `5598a1d46a7fe7f26d24b3e5d91d1375832134a280248305466b12ca52a847b5` |
| `code/write_deposit.py` | `ba5937f8ff68227ab37a70d879a3f3e699e2f0dada84ec69c4c581b585863762` |

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Note of 2026-11-27: each file's SHA-256 as main stores it

Added 2026-11-27T10:34:24Z (UTC, from `date -u`) by a drafting agent working for the project lead (a model agent, not a
person). A correction note only: no file of this deposit other than this README changes, and no reading or number of any
entry changes. The hashes in the tables above stay as they were recorded.

The table "Public files in this folder" gives each hash as it was taken at deposit time. Beside it, the table below gives
the SHA-256 of the same file as main stores it (`git show 3e141f8:<path> | sha256sum`; no file of this folder has changed
since the commit that added it). Three whole-file line-ending variants of main's bytes were checked against each recorded
hash: the bytes as stored, every LF converted to CRLF, and every CRLF converted to LF.

| File | SHA-256 as main stores it | SHA-256 recorded above | Verdict |
|---|---|---|---|
| `account-prediction-cells.csv` | `2efdf3fe26716f3f55a3d323d97d65f6bddec8e7a05f5a3ce9e4b7bba61bdf84` | `5c6b741dde0f726ca04832d30dbb753f26127def7089abb7c6391928e36c5fa6` | does not reconcile under any whole-file line-ending variant |
| `account-prediction-cells.md` | `f8e360695ddf0266b7d6fc89eb2ad852137db20307d1aca0a2d1c6f84ead1c8a` | `e6de6bd395a339080c3f3c43d5f36e8d1d89e002950e3cd5903c3bf7563af322` | agrees after converting every LF to CRLF |
| `calibration-method-card.md` | `096db5079522ce5d0a2050fe47cf87bbb2dbecef6958984caf164b878c729a57` | `a8bac7543b3ad25fa361d4eb3f04cc1e4e5e5d688c87e9e5d9915ba68fd22653` | agrees after converting every LF to CRLF |
| `data-r3-P39-ledger.csv` | `9d85183fbd06a5eb240c8117ab046bd347675d275854e42c4d5e688f13c80016` | `9d9188f61597e5cd89eba757b98b67173dd6f9d3cf175db5073301bce64fcf93` | does not reconcile under any whole-file line-ending variant |
| `deposit.json` | `4e2b7a578385678da96d2f1b7b504d0adb93e244a94aea6a75b959fbb9552976` | `b7254729db8b95393bf51d63452102e4542dd9f2685c46004895073f31f0520f` | agrees after converting every LF to CRLF |
| `fig-r3-P39-ledger.pdf` | `9bce035b736886a2cd988ce12e84b70072b615f3607ff1f928b0263da4231114` | `9bce035b736886a2cd988ce12e84b70072b615f3607ff1f928b0263da4231114` | the same bytes |
| `fig-r3-P39-ledger.png` | `3957d8bafb6f9e61f9aac3baa2e7f4e022253b36f64d855c2266b4445ab262aa` | `3957d8bafb6f9e61f9aac3baa2e7f4e022253b36f64d855c2266b4445ab262aa` | the same bytes |
| `lead-margins-and-readings-2026-11-26.md` | `c25c8979eb272b19125a0597658295241d1d4c40a33f0a22015032f90bbf18cd` | `c25c8979eb272b19125a0597658295241d1d4c40a33f0a22015032f90bbf18cd` | the same bytes |
| `ledger-manifest.json` | `741c4627bc934a620a955a360a7777b3a128a634b0fba350b12f357784970acb` | `fff40453c059254de70ab0d22be86eabae610af12aacf2deea4cda015c7b6de6` | agrees after converting every LF to CRLF |
| `margins-register.csv` | `c8062b48172bd46eff9d89e3e090ec080293ded4bb592b9b518b0a943ce0d4e0` | `753397e64e1407463d75ff3cf831daa370f2919e13963d3236576474ef2434f7` | does not reconcile under any whole-file line-ending variant |
| `margins-register.md` | `fae04fa669f7625cfd657c03fba295be6c1f7c0f290bd4aa78c08ab596d0d746` | `78c22cb975fab19c36f38bee0d53919d691447e9c90bd2af49e5134059c389a7` | agrees after converting every LF to CRLF |
| `novelty-ledger.md` | `8ca21b8819b26c2bfb63f5e8d30f30685878ed56b9cf01be8c61d5bd9ba372e9` | `605f382993e08c4bef04e3662a3692f0262e65b03bb97e2a5ee3956cdaa995ab` | agrees after converting every LF to CRLF |
| `split-policy.md` | `efdcfae32314efc75273cac8cf44cfc20ce34bc9aef7c2f7fd4cf479b943d3e7` | `efdcfae32314efc75273cac8cf44cfc20ce34bc9aef7c2f7fd4cf479b943d3e7` | the same bytes |

- For `account-prediction-cells.csv`, `data-r3-P39-ledger.csv` and `margins-register.csv`, no whole-file line-ending
  variant of main's bytes gives the recorded hash. Their recorded hashes were taken on the private bytes at deposit time,
  which stay private.
- The private files and the code listed in the two tables above are not on main; their recorded hashes stay as they are
  and cannot be checked from main.
- Entries that cite this deposit's public files cite main's bytes, as deposit 5a of the fourth panel does.
