# Dormant creator and claimed-source lexical comparison

`corpus_group_lexical.py` consumes a **completed, frozen** `postrun_candidates.py`
generation: `manifest.json` plus its `view-inventory.json`. It rechecks the pinned
manifest, roster revision, exact video/creator identity, selected English view,
source hashes and the existing codepoint/timebase contract. It uses only the
selected primary view, retaining missing text as unknown. It does not retrieve
media, run ASR, download a model, infer speakers, or refresh dashboards.

The Atlas describes a creator's repertoire. It cannot assign a recording to an
entity. An optional private assignment file must bind the exact selection and
inventory hashes, and contain episode-specific reviewed claims:

```json
{"schema_version":1,"selection_sha256":"...","view_inventory_sha256":"...",
 "assignments":[{"video_id":"abcdefghijk","channel_dir":"example",
   "text_version_id":"...","claimed_entity_id":"reviewed-source-label",
   "review_state":"episode_specific_reviewed","scope":"whole_recording_claimed_source",
   "evidence":{"path":"reviews/episode.json","bytes":123,"sha256":"..."}}]}
```

The evidence is a nonempty, checksum-bound private artifact. This first version
supports one reviewed whole-recording claim, not diarization or assigning a
multi-speaker episode to several entities. Missing reviews remain explicitly
unassigned. Contradictory reviews of the exact same audio/text unit stop. Labels
describe reviewed claims and do not verify an external entity or human speaker.

The tokenizer and stopwords come from `keywords.py`. Episode TF uses
`1 + ln(count)`, IDF uses `ln((1+N)/(1+df)) + 1`, and episode vectors have L2 norm
one. No title/date cutoff is applied. Exact audio/edition **and text** aliases
collapse to one unit; unproved recording equivalence is not invented. Group
centroids give equal weight to reviewed work families and then their text units;
unresolved recordings are separate units. This keeps long texts and repeated
listings from receiving raw-token-count weight. Source-kind mixtures, missing
denominators, hashes and view associations remain in the private result.

Cosine compares those centroids in one shared episode vocabulary. Creator versus
claimed-source tables explicitly disclose shared inputs. Exploratory clusters
are within-kind cosine-threshold graph components, excluding shared-source
edges. Components can be transitive; they are not topic-model discoveries,
independent replications, significance tests, or evidence for the claims.

Production uses lazy **`cupy_cuda12x_csr_v1`**, float64, with sparse episode and
group matrices. TF/DF/IDF, norms, centroids and blocked cosine run on CUDA.
Verified I/O, tokenization, sparse indexing, output ordering and graph bookkeeping
run on CPU. No dense vocabulary×vocabulary or episode×episode matrix is formed;
only a configurable group-score block is dense. A conservative working-memory
estimate must fit both the configured GPU budget and current free VRAM. Every
result records the actual backend/package/runtime, block size and GPU/CPU work.
Each bounded CUDA stage and score block uses the shared
`gpu_workload_pacing.pace_cuda` rolling controller, with target 0.70 where
measurable. The result includes actual sampled utilization, waits and missing
telemetry from its summary. Short blocks do not promise an instantaneous 70%.
CUDA failures do not silently fall back to CPU. The standard-library CPU path is
an explicit **fixture-only** oracle, reusing `keywords.tfidf`.

CuPy is not installed by this module. The ordinary environment currently has no
CuPy; the ASR environment has CTranslate2/NumPy but no CuPy. Provision a separate
reviewed analysis environment after collection closes. Official CuPy documents
`cupy-cuda12x` wheels for CUDA 12.x; confirm the installed driver/runtime and lock
the selected package before that later setup. No GPU initialization, install or
real-corpus analysis was performed while authoring this adapter. Cached MiniLM
embedding inference is a separate future method and is not claimed here.

An explicit preview prints a dormant plan without opening corpus inputs:

```powershell
python -B -m pipeline.corpus_group_lexical --root PRIVATE_ROOT `
  --generation PRIVATE_ROOT/analysis/candidate_runs/REVISION --manifest-sha256 SHA --describe
```

After collection and environment setup, omit `--describe` to execute CUDA math
against the verified completed generation. There is no silent no-op default. Optional arguments include
`--entity-assignments FILE --assignments-sha256 SHA`, `--cosine-threshold 0.35`,
`--cosine-block-rows 32`, and `--gpu-working-mb 1000`. The existing GPU owner lock
prevents competing ASR. Private immutable outputs appear under
`analysis/group_lexical/REVISION/`; actual output bytes plus live reservations
must fit the shared 23 GB project limit and leave 12 GB disk spare. The output
does not publish terms or text.

## Review the effect of the similarity threshold

The second panel can use the same saved GPU cosine scores to examine which groups become connected when the threshold changes. Run this export in the plotting environment after the lexical generation exists.

```powershell
python -m pipeline.lexical_cluster_figures --generation $lexicalGeneration --out $privateFigures --thresholds .25 .35 .45 .55 .65 .75 .85 .95
```

The PNG and SVG plot the share of assessed groups in the largest connected component across the chosen thresholds. Separate lines represent creators and reviewed claimed sources. A line needs at least one eligible pair. Connections can pass through an intermediate group. A flat curve over several thresholds describes this sample and its shared vocabulary.

The export includes every within-kind pair in a CSV, with text coverage for both groups and counts of shared texts and recording families. Pairs sharing either are excluded from the graph. A second CSV gives eligible groups, eligible comparisons, edges, isolated groups and components at every threshold. An absent cosine remains missing. The panel can trace a change in the curve back to the affected recording groups. [Figure exporter](lexical_cluster_figures.py)

Fixture QA only:

```powershell
python -B -m unittest pipeline.tests.test_corpus_group_lexical
```

Primary method documentation:

- [scikit-learn TF-IDF weighting](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting)
- [Cosine as normalized dot product](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html)
- [CuPy CUDA package compatibility](https://docs.cupy.dev/en/stable/install.html)
- [CuPy sparse GPU linear algebra](https://docs.cupy.dev/en/stable/reference/scipy_sparse.html)
