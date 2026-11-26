# r3-P37 / r4-P20 run record

Exploratory; not a test of H1-H10. Times from `date -u`.

- Exploration stage (tier S: half A and the tuning pool) ran 2026-11-26T14:20:38Z to 14:21:34Z; `private/exploration.private.json` SHA-256 `600ce63b77c6b092127bb15733c2f65cd19622db6e7442e04b61aa10b0bc878b`, recorded at 2026-11-26T14:21:40Z, before the sealed stage. Code hashes at that run are stored inside the file and checked by the sealed stage.
- Sealed stage (half B, once) ran between 2026-11-26T14:21:40Z (the exploration record) and 14:21:51Z (`date -u` after it ended), after the code-hash check passed; `private/sealed.private.json` SHA-256 `2986cc11626aafc787ebbccc6c3f63c17c4fffd11b273b5d0a569cdefb821896`, recorded at 2026-11-26T14:22:02Z. The word-anchored row (tier L) ran inside the sealed stage.
- After the sealed stage, `../ft-common/code/ftpub.py` was edited (count-form helper only: one form per creator set, a stricter nesting check, ten-wide bands on the exploration side), at 14:25 to 14:29 UTC; it is used by `p37_publish.py` to print counts, and no stage was run again. Its final SHA-256 is in `status.json`.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
