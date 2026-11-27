# Deposit 5, addendum 1: hash record (public)

Written 2026-11-27 by a drafting agent working for the project lead (a model agent, not a person). Every SHA-256 below
was taken at **2026-11-27T17:29:25Z** (UTC, from `date -u`), before any count of any entry that deposit 5 registers.
Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**What this file holds.** The SHA-256 of every public file of this addendum and of every private file it relies on, by
file name, or by a neutral description where a file name is withheld. It holds no half membership, fold membership, count
per stratum, list form or corpus text. Private files stay private; their hashes fix them now. Paths are relative to
`deposits/deposit-5/addendum-1/`.

## Order of work (times from `date -u`)

| Time (UTC) | Step |
|---|---|
| 2026-11-27T13:13:58Z | Deposit 5 public (PR #133, `1461979`); step 0 starts |
| 2026-11-27T13:35:23Z | (C) writing of r3-P30 version 2's card begins |
| 2026-11-27T13:42:19Z | (A) the eligibility prespecification hashed, before any eligible set |
| 2026-11-27T13:43:17Z | (C) the card hashed |
| 2026-11-27T13:43:27Z | (B) its prespecification hashed, before any reproduction or table |
| 2026-11-27T13:45:21Z | (A) the first eligible set computed |
| 2026-11-27T13:54:57Z | (A) every step-0 (A) file hashed after the run |
| 2026-11-27T14:07:28Z | (B) code, outputs, logs and the first public drafts hashed after the runs |
| 2026-11-27T15:56Z | The owner's answer on the split read recorded: "Allow for these uses (Recommended)" |
| 2026-11-27T15:58:06Z | The fold-draw note hashed, before either split-read script was written or run |
| 2026-11-27T15:59:39Z | The two split-read scripts hashed |
| 2026-11-27T16:03:32Z | The fold draw run by the lead (exit 0) |
| 2026-11-27T16:03:39Z | f4-Q09 (vi)'s guard run by the lead (exit 0; "pass") |
| 2026-11-27T16:04:49Z | (A) both outputs hashed; they match the values the lead reported |
| 2026-11-27T16:14:08Z | The R1 to R11 runner's code check passed; the lead runs it |
| 2026-11-27T16:15:58Z | The runner's first start; one unit ran clean, then the runner's own tripwire stopped it at 16:19:51Z (decision 151) |
| 2026-11-27T16:20Z | The one-line tripwire fix (decision 151) |
| 2026-11-27T16:20:45Z | The runner's second start; it stopped early, and the runner then copies one shared code folder (decision 151) |
| 2026-11-27T16:24:18Z | The runner's third start; it ran clean to 16:36:51Z |
| 2026-11-27T16:45:01Z | R1's structural check, run by the lead |
| 2026-11-27T16:46Z | The comparison's verdicts (decision 154); the temporary working copy removed |
| 2026-11-27T17:23Z | The independent check of addendum 1; every fix taken (decision 155) |
| 2026-11-27T17:29:25Z | This record |

## Public files

| File | SHA-256 |
|---|---|
| `README.md` | `189d1778c9d86312be4748bea060b4e086ab0b40ec05d63a6bec1ecf03c1d63f` |
| `guard.md` | `5241354c4bd8f4ca2068757a5afa377fd69343dbd1356bf66ff750eef8d5e1b3` |
| `feasibility.md` | `40dc93f4e2fc2f3fe94c85c2c0642c99b8efb4b2dc034e5df005fe35edb66fed` |
| `r3-P30-v2-card.md` | `dcf3e7cf442b2940c335d5a42dd6a0c66936bc915b77fb1c1d98dfe51743ce4b` |
| `reproductions.md` | `19ecea815fa9a18e68f8bc3dc63beabd716a38d903ed541e5050af62af7f4f3a` |

## The split record (private; its hash is published in deposit 2)

| File | SHA-256 |
|---|---|
| deposit 2's split draw (the half memberships), read in memory only, for the uses of the lead's decision 148 | `85848e4cb78327c52163d254a16447b90581fd6e1a696c959237fc7d0ef077f2` |

## Step 0 (A): the guard (private)

| File | SHA-256 |
|---|---|
| `private/eligibility-prespec.md` (hashed 13:42:19Z, before any eligible set) | `898eee0394a6b224b195f11411059064a967b08edc46e91917004281b8d2d739` |
| `private/run-log.md` | `637e2e7e4417c68122135a4e831a61ab3b4f7db5b3b923400a6d6b740d852de2` |
| the guard's per-row sets and results | `8d74d59c6494cd76debda584246ffa4dac56f94a4c348cd874084eafb47082d0` |
| `private/code/count_scan.py` | `3646b17b3b778e3ca86627fb31345d9363bbbd0dcee6224ca6a2d003712dc45e` |
| `private/code/guard_extract.py` | `deccfa072676eb0833eb01392b088ca48a1fb992fbc76872917822cbde302e7b` |
| `private/code/guard_sets.py` | `028bf9ebcf1ca3bdfe34015a3e7cbbf6454f608cdba6a1d2f9b1dff584011e49` |
| `private/code/guard_compare.py` | `22e9e05f53d26b557b4e1a127501e75d27b3f766d14b3b41e50604ced18b54c4` |
| `private/out/count-sizes.csv` | `9e7692dd9b0a54b80d96c137a4bdfac9174d24f2665621646597dd8723db5e51` |
| the count scan's output | `ff271097b7c3df8a9cf78db6c834df201f940fccd05271c6c34ab4a5e9932e3e` |
| the label-derived eligibility extract | `2734c5afffe0b2bedd0a2a14d6845be3607ffda2d260932cf66d9fada7a499ea` |
| the eligible sets | `bc0c74caefb8fe7e404f394d7112a52f103f17fc12fb770fe67a3c03392f2048` |
| the near-pair note | `5234ff568703e1df7ac1c82708b117e910a4fbf8583f3db3538e2918bdb8d43d` |
| `private/out/extract.log` | `b72f913c360cf0d8f625b86c8392d0fcf8c627e2c018d3aff8917da25a1395cd` |
| `private/out/sets.log` | `53d87c5faea7ae2e52bf38996a13f6a83b2818c3fb0b675fc70c1b3bf3547c61` |
| `private/out/compare.log` | `e2ea581a547ee03c1f0bdc4dd04f4b51cf83b7534fe2eb1bb57ee2ad45ab94e2` |
| `private/out/extract.err`, `private/out/sets.err`, `private/out/compare.err` (each empty) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `private/hash-record.md` (step 0 (A)'s own record) | `7b52377f1588b1efc1c4036ead4510830b08722e5b582d5bd7734cfe6ab44555` |

## The split-read scripts and their outputs (private; run by the lead)

| File | SHA-256 |
|---|---|
| `private/fold-draw-note.md` (hashed before either script was written or run) | `5cfa137e043d274be91477287573bd38d829c74946dae4fc276425f1f994df07` |
| `private/code/draw_folds.py` | `8b7fa594bc6e5b32cdcfdf6e37a92f60e69335af5b5881590f5f14f339ab3280` |
| `private/code/guard_q09vi.py` | `aacfc15cdf86844685678adaf620747a6d2afd6e721544c06cfec9237478b16a` |
| the X+T folds (seed `2026112761`) | `26ace4a8955d0d2874e4dbadcc3d3192c1341acad9febae503c3c7510492c30e` |
| f4-Q09 (vi)'s guard result ("pass") | `b8af28e7bfe71df643c0e7c11bc15f2d0d1e848365e4afed1b7defd0d3100151` |

## Step 0 (B): the prespecification, the feasibility tables and R12 to R13 (private)

| File | SHA-256 |
|---|---|
| `private/step0b-prespec.md` (hashed 13:43:27Z, before any computation) | `09f063d24f58c365ef045f7f6f0eb95b59ac91ae07033b1b84236486436c4491` |
| `private/step0b/code/guard.py` | `dc347622c9b33d6ee54562ebfee09e81e979077537404f6fb11271bfcea6f0f5` |
| `private/step0b/code/keys_only.py` | `9aa698d36030c93e5e248e5d27d224c42d50a6a46084ab85f64a4cf4ad23b7e4` |
| `private/step0b/code/feas.py` | `3b7f80faaf7a91d4e8524a9461a8432e25c66a7610f1751fe2182c05ec33efbe` |
| `private/step0b/code/compare_p30.py` | `27356f056a35faef31d28b386648988d1ea5114c47dde1a7cdbcb7239f60ba37` |
| `private/step0b/code/r13_hashes.sh` | `01ef503e6fe462caa14ad075c8f42b8ab2122b396f3ec25a4b27a034dc020f7c` |
| `private/step0b/code/scan_public.py` | `8ad2529c0a2e950d1ec2462bf48b79629fe370ac6535565b1125304ea2ddf26c` |
| F1's output (f4-Q04's corrected class 3) | `4eb135f4af83dc0b3467acf4c1cb31c7b3eb8689491a318607321989431885f8` |
| F2's output (the balance; never printed) | `b7929cbc76963f04b99c378fad1b4a6da04c2418ea503999162fb2b8bcb4224b` |
| F3's output (the congruence half's feasibility) | `e92a17d63464a2f1cd415ca4924bde74b5748dd06c54a0644eeb86562b7691c9` |
| F4's output (the A8 count) | `73a13010146342f5ff0d1febfa92982a4099f00f2807bac66e489f774e2d9f65` |
| F5's output (f4-Q12's eligibility and splice census) | `e0cf6ca9b3ebc3f0ad47cb57b341ec644ecf5bfd0a136e1ecb93911cbcb62454` |
| R12's comparison | `993e691766a74359858730cd7cc6803226060cdb3277bfba1b4ff54f1ad1f2f4` |
| `private/step0b/out/r13-check.tsv` (R13's comparison table) | `24c7842078a045092f022d14cf3f5d37d56cb7d24de22c78ea89d4a7bde66f48` |
| `private/step0b/out/r13-listed.txt` | `7d558166d8e1b82b04572864500057342677519717b98f13c5f70202725ba75e` |
| `private/step0b/logs/f1.log` | `14a99f4c175a91a6d7d70ce0bf1e3c4489fc112ccad3823d125028cba15fd4b7` |
| `private/step0b/logs/f2.log` | `3384b4e1db47567d54d6531af48b69e0e311095317554b496a8c2802d0b4c333` |
| `private/step0b/logs/f45.log` | `cbf21b5b1e3c00354d218948537dd604f5a0b3eda35575da7c19347de2f90c76` |
| `private/step0b/logs/keys_only.log` | `0763ccfe7a5c4d99e5d5b8722ecc9dd39a6978e8508e3fcbcc71bade238e284c` |
| `private/step0b/logs/r12-compare.log` | `d45ab5ba0437fcc05f7d19ea17339cd3a0166e5cdf00b4ee23323c7b4c50123e` |
| `private/step0b/logs/r13.log` | `1f75748ba7b41443510019dd4dc6b9ccf827e29dac904d8b0fc778a6ce48ae64` |
| `private/step0b/logs/r3-P30-build_pools.log` | `8a8b8bb4e49031c04aa14f570f03e510aa2c6f502b78037592554e02dcbde8f6` |
| `private/step0b/logs/r3-P30-battery.log` | `9b637861852d519feccfc2e3095a74545acf9a0dc5168845beb1470057cf2b2b` |
| `private/step0b/logs/r3-P30-write_public.log` | `4ce828ef74292006be03b6f7f7ecd27ba8b82d56c049c3891baa07efec082006` |
| `private/step0b/logs/scan_public.log`, `private/step0b/logs/scan_public-2.log`, `private/step0b/logs/scan_public-3.log`, `private/step0b/logs/scan_public-4.log` (identical) | `4f65696f0139c736f1fa5ed28f329bb3196c5155dd337fdfda73398b63b6c0f0` |
| `private/step0b/repro/r3-P30/code/battery.py` | `24367d512882a2dde275ad035605a0c233eb377ce50cd10ec0e2b274bf5688cf` |
| `private/step0b/repro/r3-P30/code/build_pools.py` | `01facd62f515e6a289d62a734577a2f2182a85561497649b59c487062e339f56` |
| `private/step0b/repro/r3-P30/code/plot_p30.py` | `3a5c3d177838009db74b94efae490d492b0ee12e0377b338d055fe70048659c4` |
| `private/step0b/repro/r3-P30/code/prespec.json` | `a23e8325c14f080310c2636fadf5508a61964f6dfed6c3251371f7f33c5a5865` |
| `private/step0b/repro/r3-P30/code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `private/step0b/repro/r3-P30/code/write_public.py` | `f847f4000b2711f4e356569310be02089d3b7c9cd8f36f7815cf5da9cd135d89` |
| R12's rerun battery record | `fedc2a20cf46d74bf3659354667f5897fcd23eb8060e45ce6c75dcbd26a497be` |
| R12's rerun battery arrays | `047d9c34b21ec2b7e05244d8905e465671363c478b5d7372912052a4a984ccfc` |
| R12's rerun pools summary | `a088dd08afb7d6fd9d3f27966a8306e48c0eb8ad19222e941386eb3c58e37ab5` |
| R12's rerun pools | `094c78196092e1a272d39dab6834281225eafdaed6016b1033f0ed76317785b3` |
| R12's rerun `data-r3-P30-classes.csv` (byte-identical to main) | `314d359d6ddb8006d13ebbceab0b6dd6e5b2b8058e22243edc3a2802215cf283` |
| R12's rerun `data-r3-P30-coverage-grid.csv` (byte-identical to main) | `4a4412acd8befa4ceda22d7da63044bb197c161effe9d4d4e7534f4a3fe99930` |
| R12's rerun `data-r3-P30-readings.csv` (byte-identical to main) | `29c7583af74bda194acecebea37b88ba9fa3449069b33f8bc6874ae1d24b177e` |
| R12's rerun `data-r3-P30-size.csv` (byte-identical to main) | `f6496eab5ba96e1ac5b5af324a954829e77c219a560affd0f6064b7c46d72afc` |
| R12's rerun `interval-choice.csv` (byte-identical to main) | `fcfe22cfba84b8b5eedd059ff605afb0055761b88c4c4d96e708d24400a6e1f6` |

## Step 0 (B): the R1 to R11 reruns (private)

The runner was accepted and its code check passed at 16:14:08Z (the lead's decision 150). The lead changed it twice under
decision 151: a one-line tripwire fix, and a copy of one shared code folder that a unit's published code checks through
the run root. Its first step reruns the third panel's code check at every start. The runner is not on main; its final hash
is below. The third start ran clean from 16:24:18Z to 16:36:51Z (decision 154). Each unit's files are fixed by its
manifest, hashed here.

| File | SHA-256 |
|---|---|
| `private/step0b/repro/run_R1_R11.sh` (final, after decision 151's two changes) | `4ebf2f55283d136d48dff306284e141da503daa7a35500152194baac21eea91c` |
| `private/step0b/repro/launch.py` | `c688918f0c85c9d769379b143d0406784c770f83a050447514ad65fac03cb53e` |
| `private/step0b/repro/verify_code.py` | `671b3591a7d8bcb84c731148adb54eb1e2a16dbb7b202b68d7d83487949c7954` |
| `private/step0b/repro/cache_check_R1.py` | `2d78ea438fa02d0b6016e33899f21ddc8b87523e783d1bf6fbf121e3bab98324` |
| `private/step0b/repro/compare_R1_R11.py` | `b6594c58c2bdb34464ac439139b74df08e8217f55f9871d3cac66b9b74ed0250` |
| `private/step0b/repro/compare_detail.py` | `61f49796d73077f8658ff1bf794908aa4eaf4e40f07900d01c28d49a6a269e22` |
| `private/step0b/repro/diag_R1.py` (R1's structural check, run by the lead) | `42a106536b00cbcb7d245b9ad1938ba57b73950a9ae21e270e70cdc41f246289` |
| `private/step0b/repro/chains.md` | `62893d08a9ea53c82d14dbde810877d4af9e9a5953fe7eb82a86bca7ed074bb3` |
| `private/step0b/code/update_repro_md.py` (one-off editor of `reproductions.md` after the comparison; text only) | `7b40741b15158b9742bafc6a9ad68884ea4dac2ca17d5ccd77b447f80e8f332e` |
| `private/step0b/code/update_repro_md_2.py` (second one-off editor of `reproductions.md`, under decision 154; text only) | `b3eab90cdd56aeef197d33d76debe77b890327b5d75193cc5decd86fb2e8535b` |
| `private/step0b/repro/out/R1/manifest.sha256` (unit R1) | `3fba99d485f8d122d6ba94f5cb032700e41f48a61b10fce230f3db73760f01ed` |
| `private/step0b/repro/out/R2/manifest.sha256` (unit R2) | `2165445b87eacfb156f9a61175a4412c560767cea89d6f93081652942b8a8b4c` |
| `private/step0b/repro/out/R3-R4/manifest.sha256` (unit R3-R4) | `d82f3ff887c389ded2ec3fdd43f92e659fb182f5af9e9594bae74c43b8c2d190` |
| `private/step0b/repro/out/R5-R6/manifest.sha256` (unit R5-R6) | `ab2d82e68fc93e203ec97568ec166f1dafb4b6b1093270fca25d12d09beb5dac` |
| `private/step0b/repro/out/R7/manifest.sha256` (unit R7) | `da06267dab97bf773cc3509b88f6865934ddb22c4a8d6505116570eb825ff148` |
| `private/step0b/repro/out/R8-R9/manifest.sha256` (unit R8-R9) | `6770456c0c3fbb4f1f6f0f60a6a3cdf8ee0cd542f08c19966a6b5f82a7eb7711` |
| `private/step0b/repro/out/R10/manifest.sha256` (unit R10) | `bc1916ed41e513d035e9d9d2e2242279dbf80b5e7a0f1b996e4a6fa5da53f103` |
| `private/step0b/repro/out/R11/manifest.sha256` (unit R11) | `304edfc05a5103b8be4bd5cb553704864c21124123db0adc639f52d2280c094a` |
| `private/step0b/repro/out/compare-R1-R11.json` (the comparison) | `31d91945e87f9b02e57ee6ecdea56914916056fa0f8bd66300933e63cb47f8be` |
| `private/step0b/repro/out/compare-R1-R11.log` | `a732dc10364dc26954e9c98c0ff70cbf1fa2452e1b791d666f05ae07ea7f2373` |
| `private/step0b/repro/out/compare-detail.json` (the cell-level comparison) | `70a6a0b620d6cc3d9c18721478ec9c4ec92d58cd35d469da9a47edcd34f85e59` |
| `private/step0b/repro/out/compare-detail.log` | `f58714758b446d4aac909d4b2d46396a14013bf9957d5f43913066e375c2a77a` |
| `private/step0b/repro/out/verify-code-archive.json` (the code check's record) and its identical copy for the working copy | `607d167f9ae533e3d0b410109c53e7ff18279a9be5cd7748cb3d9b258b39f9df` |
| `private/step0b/repro/out/verify-code-archive.log` and its identical copy for the working copy | `96b32d08aa773319c43e2f7dfd86d3d83c141d77bd538f4d7f5ec13da95a94e9` |
| `private/hash-record-b.md` (step 0 (B)'s own record, final) | `2c1bfdd82daf405b3a6c8c61053f4c7b112b606e6d22cdeb3d5395e72f626d7a` |

Each unit's run logs and its list of written files (`written.txt`), added under the lead's decision 155:

| File | SHA-256 |
|---|---|
| `private/step0b/repro/out/R1/logs/analyse_p42.stderr.log` | `0b93dd9de4345bc069d801c6a84c10095bbd97067aae0697854d3986fdfabd11` |
| `private/step0b/repro/out/R1/logs/analyse_p42.stdout.log` | `bde476dc459c53c38ede0c202055ef724c9a308f54ba6d946bc2de6215c3c02b` |
| `private/step0b/repro/out/R1/logs/cache_check.log` | `94d5449a23703251b2919573afce7191e72e784a71e63710fd8a3ddf472b0f5c` |
| `private/step0b/repro/out/R1/logs/count_p42.stderr.log` | `2b93c6ffd39602f0ab3a941ddf5a5ba3cf281504bc8e709f1f1198e9c475fb72` |
| `private/step0b/repro/out/R1/logs/count_p42.stdout.log` | `02bc61817419cce3d7797d070920da3b8c3daa6e1d8e4e5d3a6e89d005cd2347` |
| `private/step0b/repro/out/R1/logs/extract_p42.stderr.log` | `3285407da19aaf92f250bccd8713eb7b82319a7311f79d45b6bb9d333702a3c4` |
| `private/step0b/repro/out/R1/logs/extract_p42.stdout.log` | `8e1ba5317e5e506b1fc4a24e6e6253037478e83fd7e84373df42559214b400ff` |
| `private/step0b/repro/out/R1/logs/gen_variants_p42.stderr.log` | `2b93c6ffd39602f0ab3a941ddf5a5ba3cf281504bc8e709f1f1198e9c475fb72` |
| `private/step0b/repro/out/R1/logs/gen_variants_p42.stdout.log` | `1fcb03ea60a0c40f1f22431bc883c1678349d9f3479f9d746369ce736b0f14cd` |
| `private/step0b/repro/out/R1/logs/publish_p42.stderr.log` | `5389136a6afb8b9e11f1f03270549dc0af037979bbb69f7f80b358e819aa7b07` |
| `private/step0b/repro/out/R1/logs/publish_p42.stdout.log` | `6c32006a11b01ac969aca9dbd879c05ed3b3f8ba4ce0313ae0ff9045334d42ab` |
| `private/step0b/repro/out/R1/written.txt` | `c33711ff066fadff685e26f3f60f0ddd9b3ead8802891830d55f16b503370f7d` |
| `private/step0b/repro/out/R2/logs/analyse_p4346.stderr.log` | `3285407da19aaf92f250bccd8713eb7b82319a7311f79d45b6bb9d333702a3c4` |
| `private/step0b/repro/out/R2/logs/analyse_p4346.stdout.log` | `5e70c85fdf53f1fb573e9618bc449f5b0feb7ed2677a27e8b58f1aa69ce3116e` |
| `private/step0b/repro/out/R2/logs/publish_p4346.stderr.log` | `cbcc0708a64b564ad3a78a4cac0554276f94f777bdd09757dcfcf1cdec413d16` |
| `private/step0b/repro/out/R2/logs/publish_p4346.stdout.log` | `7616bfd388c4fa8c881babd159afe3da803c94cf87396c03acbbadb397c0f209` |
| `private/step0b/repro/out/R2/written.txt` | `f4c7718379326e993f16fe13663303455fbe80de11d8659c3c758cf854688d7a` |
| `private/step0b/repro/out/R3-R4/logs/analyse_desc.stderr.log` | `5f837916f02a3c4039f6e31f6cf1451677e954d0bd1483619a4ce0ba0a738c15` |
| `private/step0b/repro/out/R3-R4/logs/analyse_desc.stdout.log` | `bc5a82714cd8ebd10f018ee2b3278a4ebb69f9f5d10ab34be1de70adb5c8cc2c` |
| `private/step0b/repro/out/R3-R4/logs/extract_desc.stderr.log` | `584ada48c9e1d1f3e44b4c1e28c2dca69c9e63e03a38dbe04ce7caa4cbfd7551` |
| `private/step0b/repro/out/R3-R4/logs/extract_desc.stdout.log` | `7e59fa037d13888f8e8e5e2094cc2454db3c995854142ff207861e237a3112c7` |
| `private/step0b/repro/out/R3-R4/logs/extract_page_shared.stderr.log` | `2b93c6ffd39602f0ab3a941ddf5a5ba3cf281504bc8e709f1f1198e9c475fb72` |
| `private/step0b/repro/out/R3-R4/logs/extract_page_shared.stdout.log` | `488e18936cec63f94de4f1bf1b2ee309f205056dabe41a501d0fdede7a2ae191` |
| `private/step0b/repro/out/R3-R4/logs/publish_p29.stderr.log` | `584ada48c9e1d1f3e44b4c1e28c2dca69c9e63e03a38dbe04ce7caa4cbfd7551` |
| `private/step0b/repro/out/R3-R4/logs/publish_p29.stdout.log` | `c588ee20a2fe7f854a2d8b24a9cc0efcdf4737348bfad5384161091924704c5b` |
| `private/step0b/repro/out/R3-R4/logs/publish_p48.stderr.log` | `b96894ec225285c0272086bffa9fb32d35115d910c5da1f8b7de6f63f60cf026` |
| `private/step0b/repro/out/R3-R4/logs/publish_p48.stdout.log` | `3afc8bf60cee658ba30d5473e568fe641adb58e5e560fa8e9c09fba0524a7f8f` |
| `private/step0b/repro/out/R3-R4/logs/publish_p51.stderr.log` | `5cddad228477630645fba38f85e9921c556e7c542d2eabd5839e044973d85e8e` |
| `private/step0b/repro/out/R3-R4/logs/publish_p51.stdout.log` | `9b704bb9cfee56fb3d31ee85e422f35d7588de1a112c73b399ff02e2b9ff9080` |
| `private/step0b/repro/out/R3-R4/logs/publish_p52.stderr.log` | `584ada48c9e1d1f3e44b4c1e28c2dca69c9e63e03a38dbe04ce7caa4cbfd7551` |
| `private/step0b/repro/out/R3-R4/logs/publish_p52.stdout.log` | `8ab80ddfd895584f8686f144c234232880324c12aaf5d6fc148ed3b6d364f652` |
| `private/step0b/repro/out/R3-R4/logs/publish_p53.stderr.log` | `584ada48c9e1d1f3e44b4c1e28c2dca69c9e63e03a38dbe04ce7caa4cbfd7551` |
| `private/step0b/repro/out/R3-R4/logs/publish_p53.stdout.log` | `d267fabfb48317e52b7709354e7f2381c128dffaae8adf82afed107488a33972` |
| `private/step0b/repro/out/R3-R4/logs/publish_p55.stderr.log` | `584ada48c9e1d1f3e44b4c1e28c2dca69c9e63e03a38dbe04ce7caa4cbfd7551` |
| `private/step0b/repro/out/R3-R4/logs/publish_p55.stdout.log` | `5c358807c46785ce5393948fe3bdbef02ccd8d78522aba7ca7181ee70d6e4eea` |
| `private/step0b/repro/out/R3-R4/logs/publish_p56.stderr.log` | `584ada48c9e1d1f3e44b4c1e28c2dca69c9e63e03a38dbe04ce7caa4cbfd7551` |
| `private/step0b/repro/out/R3-R4/logs/publish_p56.stdout.log` | `115d819ec43f3afa5b63c05072abfe1bc8e109cc24c6b8d28d446f835c982d4f` |
| `private/step0b/repro/out/R3-R4/written.txt` | `3f0918af8644303a58861dd159e653d944737007c095b6795b563d25e56bfb20` |
| `private/step0b/repro/out/R5-R6/logs/extract_p3840.stderr.log` | `584ada48c9e1d1f3e44b4c1e28c2dca69c9e63e03a38dbe04ce7caa4cbfd7551` |
| `private/step0b/repro/out/R5-R6/logs/extract_p3840.stdout.log` | `d5e737c692272c0599720292a1e870b97f2128d490239d05f85225bf121b1669` |
| `private/step0b/repro/out/R5-R6/logs/p38.stderr.log` | `2b93c6ffd39602f0ab3a941ddf5a5ba3cf281504bc8e709f1f1198e9c475fb72` |
| `private/step0b/repro/out/R5-R6/logs/p38.stdout.log` | `f600f7d78f1e5abc0506e3b4d3188ad88d2c3cc962be973a115e13401f4cea72` |
| `private/step0b/repro/out/R5-R6/logs/p40.stderr.log` | `2b93c6ffd39602f0ab3a941ddf5a5ba3cf281504bc8e709f1f1198e9c475fb72` |
| `private/step0b/repro/out/R5-R6/logs/p40.stdout.log` | `d45474ec60831656bbbe1100278f813aa0e51f17b63c599ed2f3676e3644e122` |
| `private/step0b/repro/out/R5-R6/logs/publish_p38.stderr.log` | `94f9355a2fac81f54dee1ab37bad4f55ee41e74e47bd9f0414793b92a1a8f9e4` |
| `private/step0b/repro/out/R5-R6/logs/publish_p38.stdout.log` | `53d973784fc973534c28179cb0d7057adeddf8998aecf9f55dfe95d2f6c9c130` |
| `private/step0b/repro/out/R5-R6/logs/publish_p40.stderr.log` | `462f01916731ba7122fbe9687d9013fdbe6c3a0e46c5842c14b63c4ce7092d4d` |
| `private/step0b/repro/out/R5-R6/logs/publish_p40.stdout.log` | `6141fdee5e828e9c4633b288673ee8d3bf30d7222c928d0ce827406df4155228` |
| `private/step0b/repro/out/R5-R6/written.txt` | `f4386eaeffb17ca016a1f849e614cef273dc426a9c26221f0a5c26c915d54842` |
| `private/step0b/repro/out/R7/logs/eligibility_s4.stderr.log` | `3285407da19aaf92f250bccd8713eb7b82319a7311f79d45b6bb9d333702a3c4` |
| `private/step0b/repro/out/R7/logs/eligibility_s4.stdout.log` | `ac7f803059cfd21003e7c980c87cde2dd460e4415d71ac24e5fc70e276f0b4c8` |
| `private/step0b/repro/out/R7/logs/p57.stderr.log` | `3285407da19aaf92f250bccd8713eb7b82319a7311f79d45b6bb9d333702a3c4` |
| `private/step0b/repro/out/R7/logs/p57.stdout.log` | `b748f11eefb05cf5b1fd84b213d7a3e451babf5d88867ac6bc3e536939578b3b` |
| `private/step0b/repro/out/R7/logs/publish_p57.stderr.log` | `94f9355a2fac81f54dee1ab37bad4f55ee41e74e47bd9f0414793b92a1a8f9e4` |
| `private/step0b/repro/out/R7/logs/publish_p57.stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `private/step0b/repro/out/R7/written.txt` | `16032bbb1fe6b6806075d7c8ebc8e2e295b7042bf1780dee43cf48c61a558ebd` |
| `private/step0b/repro/out/R8-R9/logs/analyse_p14.stderr.log` | `3285407da19aaf92f250bccd8713eb7b82319a7311f79d45b6bb9d333702a3c4` |
| `private/step0b/repro/out/R8-R9/logs/analyse_p14.stdout.log` | `f45b88f524ae9d9520baec8896dd99c0d6e9a6ad62fd9d7b95063e1e67312794` |
| `private/step0b/repro/out/R8-R9/logs/analyse_p15.stderr.log` | `3285407da19aaf92f250bccd8713eb7b82319a7311f79d45b6bb9d333702a3c4` |
| `private/step0b/repro/out/R8-R9/logs/analyse_p15.stdout.log` | `ffad6c4c8921eb86a510db414b9fa96de3bb3d90fb90ffde7aa6cc3a3902f948` |
| `private/step0b/repro/out/R8-R9/logs/analyse_p16.stderr.log` | `3285407da19aaf92f250bccd8713eb7b82319a7311f79d45b6bb9d333702a3c4` |
| `private/step0b/repro/out/R8-R9/logs/analyse_p16.stdout.log` | `ddbb9df782b44d83153224967c5e110d4706e79ee8d32b82f6984492b6a904fe` |
| `private/step0b/repro/out/R8-R9/logs/analyse_p18.stderr.log` | `3285407da19aaf92f250bccd8713eb7b82319a7311f79d45b6bb9d333702a3c4` |
| `private/step0b/repro/out/R8-R9/logs/analyse_p18.stdout.log` | `a6f8650bc3c472227c2e6906a941f455e85365c87755c208a58ba4a14198fb30` |
| `private/step0b/repro/out/R8-R9/logs/analyse_p4p14.stderr.log` | `3285407da19aaf92f250bccd8713eb7b82319a7311f79d45b6bb9d333702a3c4` |
| `private/step0b/repro/out/R8-R9/logs/analyse_p4p14.stdout.log` | `40970da2fdba0b0bc1d391f8f52a01acea8c38fb15753b309e606d1009844439` |
| `private/step0b/repro/out/R8-R9/logs/count_forms.stderr.log` | `3f2c53c40def04c494b8085ea361cd94a9379f7184724e86ae1b6a4dff805023` |
| `private/step0b/repro/out/R8-R9/logs/count_forms.stdout.log` | `583658b1f21011a10c89f811959715ba0356a98c2f5f1a7685d10688703626a7` |
| `private/step0b/repro/out/R8-R9/logs/eligibility_s5.stderr.log` | `584ada48c9e1d1f3e44b4c1e28c2dca69c9e63e03a38dbe04ce7caa4cbfd7551` |
| `private/step0b/repro/out/R8-R9/logs/eligibility_s5.stdout.log` | `4ba26f002d9698eb831bd2e9412fe673d42fbac4095729d2f60b2b7c53fe4c02` |
| `private/step0b/repro/out/R8-R9/logs/publish_p14.stderr.log` | `94f9355a2fac81f54dee1ab37bad4f55ee41e74e47bd9f0414793b92a1a8f9e4` |
| `private/step0b/repro/out/R8-R9/logs/publish_p14.stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `private/step0b/repro/out/R8-R9/logs/publish_p15.stderr.log` | `6bf6e8d8c365e6b5b797379996fd019a963f713828f73309e2fb2acc2a1ecbb4` |
| `private/step0b/repro/out/R8-R9/logs/publish_p15.stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `private/step0b/repro/out/R8-R9/logs/publish_p16.stderr.log` | `5cddad228477630645fba38f85e9921c556e7c542d2eabd5839e044973d85e8e` |
| `private/step0b/repro/out/R8-R9/logs/publish_p16.stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `private/step0b/repro/out/R8-R9/logs/publish_p18.stderr.log` | `211f825637d8b3618f411fa3aac70d5983e375710c7cdadbff80386f0c7946b6` |
| `private/step0b/repro/out/R8-R9/logs/publish_p18.stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `private/step0b/repro/out/R8-R9/logs/publish_p4p14.stderr.log` | `5cddad228477630645fba38f85e9921c556e7c542d2eabd5839e044973d85e8e` |
| `private/step0b/repro/out/R8-R9/logs/publish_p4p14.stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `private/step0b/repro/out/R8-R9/written.txt` | `351d44ee01eabba40e83af95ffa5f785845f995987bee13d8453b139732606dd` |
| `private/step0b/repro/out/R10/logs/analyse_p03.stderr.log` | `b96894ec225285c0272086bffa9fb32d35115d910c5da1f8b7de6f63f60cf026` |
| `private/step0b/repro/out/R10/logs/analyse_p03.stdout.log` | `50f08519808c72c9d97ac478f530ef987ec91d08933417740ef616188b94c830` |
| `private/step0b/repro/out/R10/written.txt` | `3ccfdd5fba7b0df4fe8c1a3372f3b89a2595b31d67d702f324b8e3bad8808107` |
| `private/step0b/repro/out/R11/logs/analyse_p09.stderr.log` | `5cddad228477630645fba38f85e9921c556e7c542d2eabd5839e044973d85e8e` |
| `private/step0b/repro/out/R11/logs/analyse_p09.stdout.log` | `16e4390719af911381c31375378eb7b491cc9df75794e5405b4695479c5bb802` |
| `private/step0b/repro/out/R11/written.txt` | `3a4445514aaf8ce00a34988e43ab3444fbc7d8b213fb5e7a559316d77b991086` |

A draft correction note for r3-P42's README is not part of this addendum; it goes in its own pull request (decision 154).

## Step 0 (C): the card (private record)

| File | SHA-256 |
|---|---|
| `private/hash-record-c.md` (step 0 (C)'s own record) | `67359825f2d5cbae15876e2005309988d7de439fd0462229081a74db2b253922` |

This file does not hash itself. Compiled Python caches written by the runs are not relied on and are not listed.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
