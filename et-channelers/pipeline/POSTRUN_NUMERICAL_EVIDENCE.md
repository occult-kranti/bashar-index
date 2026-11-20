# Local numerical evidence after text validation

`postrun_numerical_evidence.py` consumes the coordinator's private
`research/project-text-agents/text-generation-ready.json`:

```json
{"selection_sha256":"...","generation":"analysis/candidate_runs/REVISION",
 "manifest":{"path":"analysis/candidate_runs/REVISION/manifest.json","sha256":"..."},
 "view_inventory":{"path":"analysis/candidate_runs/REVISION/view-inventory.json","sha256":"..."}}
```

Paths resolve inside the private root. The generation must pass the existing
post-run revision, selection, creator, English-view, edition, source-hash and
Unicode-offset checks. A ready document alone cannot bypass those checks.

After collection, transcription and validated generation publication, use the
reviewed analysis interpreter, whose local MiniLM manifest includes a genuine
CUDA fixture:

```powershell
python -B -m pipeline.postrun_numerical_evidence --root PRIVATE_ROOT `
  --model-manifest analysis/models/MINILM/manifest.json --model-sha256 SHA
```

The default ready path is the coordinator path above. `--ready` accepts an
explicit alternate path inside the same private root. `--describe` or
`--dry-run` reports the dormant contract without opening the corpus or a model.
There is no no-op default on valid production arguments. The command does not
install packages, convert models, fetch media or call paid APIs.
After [`minilm_analysis_setup.py`](MINILM_ANALYSIS_SETUP.md) succeeds, omit the
model arguments: the normal command reads its generated
`analysis-runtime.READY.json` pointer and revalidates the pinned model.

The fixed output is
`research/project-text-agents/numerical-evidence.json`, with exactly three
methods: `tfidf`, `cluster_sensitivity` and `passage_retrieval`. Each has a
checksum-bound private artifact, selected/observed/missing denominators,
quantitative results and limitations. The full compact report must fit 45 KB.
Term lists, passage text and full missing-ID lists stay in the bound private
artifacts. Reviewed episode-specific claimed-source assignments can be supplied
with `--entity-assignments FILE --assignments-sha256 SHA`; creator repertoire
does not assign an episode or a speaker.

TF–IDF reuses the sparse CuPy CUDA backend and reviewed-family-weighted
centroids. Cluster sensitivity reuses those saved GPU cosine scores; CPU graph
bookkeeping evaluates eight declared thresholds and excludes shared inputs.
Passage retrieval reuses the pinned float32 CTranslate2 CUDA encoder, explicit
mask pooling, source-linked Unicode chunk offsets and blockwise CuPy ranking.
Every actual GPU result retains the shared 70% rolling pacing measurements;
the target is not an instantaneous guarantee. Input indexing, output I/O and
graph summaries use CPU. There is no CPU neural-inference fallback.

A dedicated local owner lock prevents concurrent duplicate triggers. Stage
checkpoints under `numerical-runs/INPUT_AND_METHOD_HASH/` retain source-bound
output hashes. A repeat call verifies saved outputs and skips completed stages;
a changed saved artifact holds rather than silently recomputing. Each complete
run has a versioned report before the fixed coordinator path is replaced. The
existing per-method GPU lock prevents overlap with ASR. Storage checks retain
the shared 23 GB managed limit and 12 GB free-disk floor, including live
reservations. Active ordinary/native resource rows block runtime preflight.

Missing CuPy, CTranslate2, conversion or actual CUDA smoke proof is an active
setup hold, not a scientific result. Missing ready input returns exit 75.
Specific data limitations, such as zero non-stopword primary terms or no
eligible independent comparisons, may produce `not_estimable` with a measured
reason and bound artifact. Partial stage outputs never complete the panel
handoff.

At authoring, only synthetic CPU fixture math and orchestration were tested.
No package installation, conversion, GPU initialization, neural inference or
real-corpus run occurred. A separate reviewed runtime and real synthetic CUDA
model fixture remain prerequisites for production activation.

```powershell
python -B -m unittest pipeline.tests.test_postrun_numerical_evidence
```

The reused method and backend documentation is in
[`CORPUS_GROUP_LEXICAL.md`](CORPUS_GROUP_LEXICAL.md) and
[`CORPUS_SEMANTIC_RETRIEVAL.md`](CORPUS_SEMANTIC_RETRIEVAL.md).
