# Post-collection semantic passage candidates

`corpus_semantic_retrieval.py` adds the missing semantic retrieval step, reusing
the frozen `postrun_candidates` manifest and `corpus_group_lexical` input checks.
It does not fetch media, assign events or speakers, or infer that two accounts
describe the same occurrence. Ranked cosine scores are not probabilities or
confidence estimates. Candidates require source reading and expert review.

The pinned local model is `sentence-transformers/all-MiniLM-L6-v2`, revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Its cached metadata specifies a
**256-token sentence context** and 384 dimensions, despite the base tokenizer's
512-position setting. The adapter uses at most 254 content tokens plus CLS/SEP,
with 64-token overlap. Every token, including a long chapter's final window,
is covered; truncation is disabled. Token offsets retain original Unicode
codepoints and each alias's own cue/paragraph IDs, view hashes, recording
edition, source timebase and segment times. Untimed documents remain untimed;
segment times are not represented as verified word-level alignment.

Exact audio/text aliases share inference, while retaining distinct listing and
edition associations. Cross-creator ranking masks overlapping creator sets,
same audio/text units, exact span duplicates and reviewed recording families
**before** top-k selection. Similar language alone is neither independent
evidence nor a confirmed event. Canonical creator labels are selection owner
labels, not diarized people. No inferred event labels enter the source view.

The production backend is
`ctranslate2_cuda_float32_mean_pool_cupy_blocked_v1`. CTranslate2's BERT encoder
runs CUDA float32, with no integer quantization or CPU inference fallback.
CuPy consumes CUDA hidden states, explicitly averages all non-padding token
states (including CLS/SEP), and L2-normalizes. The BERT pooler output is **not**
used. Source and CT2 streams are synchronized before sharing a CUDA array.
The same rolling 70% target pacer wraps inference, pooling, ranking and transfer
blocks, reporting actual utilization/idle waits or unavailable telemetry.

All passage vectors remain a bounded `N×384` matrix. Exact cosine ranking uses
query blocks, never an `N×N` resident result. GPU eligibility masks and stable
sorting retain only the requested top-k. Estimated model/batch/vector/sort
workspace must fit the configured and free VRAM budgets. CPU handles verified
input I/O, tokenizer indexing, provenance and serialization, not model inference.
Final private outputs are `chunks.jsonl`, `embeddings.f32` (little-endian
float32) and `ranked-passages.jsonl`, with a checksum manifest and pacing report.
Existing generations verify all three files before reuse, avoiding inference
repetition. A failed run publishes no final generation and never deletes inputs.

The cached source is available locally, but **conversion and real CUDA tests
have not been performed in this phase**. No model install/download/init or
real-corpus inference took place while authoring. Current CPU fixtures use
invented tokenizers and numeric tensors, not CPU neural inference. Production
requires a separate, checksum-bound actual CUDA smoke/pooling report; any
SentenceTransformer-reference parity must be reported separately and cannot be
assumed from these CPU fixtures.

After collection closes and a real managed disk/compute allowance is available,
convert only from the pinned local snapshot into a **new** managed private
target. Keep `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, do not enable remote
code, and use the converter's float32 option. For example, in the reviewed setup
environment:

```powershell
ct2-transformers-converter --model PINNED_LOCAL_SNAPSHOT `
  --output_dir NEW_MANAGED_TARGET --quantization float32 `
  --copy_files tokenizer.json vocab.txt
```

Do not run that setup during acquisition. The converter needs a suitable local
Transformers/PyTorch setup, but the later inference runtime needs no torch CUDA.
Record the source weights SHA, revision, converter/environment and all converted
file hashes. Validate CUDA shape, finite/unit vectors, repeatability, 256-token
tail coverage and explicit mask pooling on fixtures before running real texts.

The model manifest lives beside its converted files and includes:

```json
{"schema_version":1,"repository":"sentence-transformers/all-MiniLM-L6-v2",
 "revision":"1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
 "conversion":"ctranslate2_transformers_float32_no_integer_quantization",
 "source_weights_sha256":"...",
 "configuration":{"architecture":"BertModel","hidden_size":384,
   "max_sequence_length":256,"pooling":"attention_mask_mean_including_cls_sep_then_l2"},
 "files":[{"path":"model.bin","bytes":123,"sha256":"..."},
          {"path":"config.json","bytes":123,"sha256":"..."},
          {"path":"tokenizer.json","bytes":123,"sha256":"..."}],
 "validation":{"cuda_fixture_verified":true,
   "fixture":{"path":"cuda-smoke.json","bytes":123,"sha256":"..."},
   "sentence_transformers_reference_parity_verified":false}}
```

The actual `cuda-smoke.json` binds `model_revision`, `device:"cuda"`,
`compute_type:"float32"`, the same pooling, `dimension:384`,
`maximum_sequence_length:256`, `finite_unit_vectors:true`,
`full_window_tail_covered:true`, `mask_mean_pooling_max_abs_error <= 1e-6`, and
`repeatability_max_cosine_error <= 1e-4`. Preserve that real evidence; do not
replace it with a declared pass. Model files and the report are verified locally
before backend initialization.

Explicit preview (no corpus/model opened):

```powershell
python -B -m pipeline.corpus_semantic_retrieval --root PRIVATE_ROOT `
  --generation PRIVATE_GENERATION --manifest-sha256 SHA `
  --model-manifest PRIVATE_MODEL/manifest.json --model-sha256 SHA --describe
```

After the phase handoff, omit `--describe` to execute verified normal inputs.
Options include `--top-k 5`, `--overlap-tokens 64`, `--batch-size 16`,
`--cosine-block-rows 32` and `--gpu-working-mb 1000`. It uses the existing GPU owner
lock and charges expected outputs against 23 GB managed/12 GB physical spare.
The output is private and no dashboards are refreshed.

CPU fixture QA only:

```powershell
python -B -m unittest pipeline.tests.test_corpus_semantic_retrieval
```

Primary method/stack sources:

- [Pinned MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/blob/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/README.md)
- [CTranslate2 BERT support and conversion](https://opennmt.net/CTranslate2/guides/transformers.html#bert)
- [Encoder API](https://opennmt.net/CTranslate2/python/ctranslate2.Encoder.html)
- [CUDA StorageView array interface](https://opennmt.net/CTranslate2/python/ctranslate2.StorageView.html)
- [CuPy stable sorting](https://docs.cupy.dev/en/stable/reference/generated/cupy.argsort.html)
