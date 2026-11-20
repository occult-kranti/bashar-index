# Restartable MiniLM runtime setup after collection

`minilm_analysis_setup.py` creates the missing local analysis runtime and model
manifest automatically. Its normal command runs only after the coordinator's
checksum-verified `text-generation-ready.json` exists and there are no active
ordinary/native resource rows. It does not run ASR or real corpus inference.
`--describe`/`--dry-run` opens no corpus, installs nothing and initializes no GPU.

```powershell
python -B -m pipeline.minilm_analysis_setup --root PRIVATE_ROOT
```

The Windows default uses the existing `vlm-vision-inference` conda Python 3.10
as its base. `--base-python` can name that interpreter explicitly. A new managed
venv uses `--system-site-packages`; its CPU Torch 2.6.0, Transformers 4.51.3,
safetensors 0.5.3, tokenizers 0.21.1 and NumPy 1.26.4 stay in the existing base.
No second Torch stack is downloaded. The worker checks these versions.

Only three reviewed Windows CPython-3.10 binary wheels are downloaded from
official PyPI hosting: CTranslate2 4.9.0, CuPy CUDA-12.x 13.6.0 and fastrlock
0.8.3. Their exact filenames, lengths and SHA-256 hashes are in `WHEELS`.
Installation is local with `--no-index --no-deps --only-binary=:all:`; unverified
or incomplete wheel bytes are never installed. Total compressed wheel bytes
are 110,311,087. The installed CUDA 12.8 toolkit is reused, not downloaded.
An incompatible DLL/runtime remains a setup error instead of switching to CPU.

The pinned local snapshot is
`sentence-transformers/all-MiniLM-L6-v2` revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. `--snapshot` can provide its local
location. Offline Hugging Face flags are set; remote model code and a model
download are not enabled. Conversion uses float32, without integer quantization.
Torch neural forwards are blocked during CPU weight conversion. Source weight
length/hash and converted artifact hashes are recorded. Incomplete attempts
are preserved under the managed setup home, and a verified final model is reused.

The genuine synthetic CUDA test uses the normal production tokenizer/window
and encoder APIs. It covers long Unicode text through the final token/character,
256-token windows, deliberately different batch lengths/padding, explicit mask
mean pooling including CLS/SEP, finite unit vectors and repeated output cosine.
A standard-library fixture arithmetic oracle checks pooling, not neural
inference. The GPU owner lock and shared rolling 70% pacer wrap actual CUDA
initialization, forwards, checks and unload. Actual telemetry and limitations
are recorded. SentenceTransformer reference parity is explicitly unverified.

The command reserves a bounded 1.5 GB future-growth envelope in the existing
resource ledger. All existing actual files and other live reservations count
against 23 GB, leaving at least 12 GB physical spare. Wheels, venv, conversion
attempts, model and compilation caches stay under
`analysis/model_runtime/minilm-py310`. The envelope releases on success/failure;
retained actual files remain charged.

Success emits
`research/project-text-agents/analysis-runtime.READY.json` with the real runtime
interpreter, generated model-manifest pin and actual CUDA smoke proof. No
handwritten model manifest is required. Then use its `python_executable` from
the repository's `et-channelers` working directory:

```powershell
ANALYSIS_PYTHON -B -m pipeline.postrun_numerical_evidence --root PRIVATE_ROOT
```

That command reads the generated runtime/model pointer automatically. It
rechecks the model and completed text generation before the real numerical run.

Only CPU fixtures were executed while authoring; installation, conversion,
actual CUDA smoke and corpus inference remain pending until the phase handoff.

```powershell
python -B -m unittest pipeline.tests.test_minilm_analysis_setup
```

Primary stack documentation:

- [CTranslate2 installation and CUDA requirements](https://opennmt.net/CTranslate2/installation.html)
- [BERT conversion and encoder support](https://opennmt.net/CTranslate2/guides/transformers.html#bert)
- [CuPy 13.6 installation compatibility](https://docs.cupy.dev/en/v13.6.0/install.html)
- [Python 3.10 venv and system-site-packages](https://docs.python.org/3.10/library/venv.html)
