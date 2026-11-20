# Production changes at the close of acquisition

| Change | Observed problem, implementation and check |
| --- | --- |
| [Bound the wait for a shared local observation journal](derive_observation_lock.py) | The collector and a child sometimes reached the same local writer together. The earlier writer raised immediately on contention, ending unrelated acquisition. This exact production derivation adds a bounded wait when acquiring that local lock and runs its body once. It accepts the historical source revision by SHA-256 and writes a new file. It makes no source requests. Two Windows process fixtures reproduced the failure and exercised the correction. |
| [Recognize the same completion-checking code in a new worker directory](completion-owner-portability.patch) | A relocation changed the old absolute path. The corrected installation compares the approved emitter's content and checks the actual local installation path independently. A changed file fails validation. The November 20 completion-only check read all six receipt journals, reported 30 missing, wrote no completion signal and exited. |

The registered local speech task adopted the corrected check. Its existing model and speech eligibility settings stayed in force. The [production history](../../../production-history.md), [final receipt manifest](../production-evidence.csv) and [operator handoff](../../../operations.md) document the operating context.
