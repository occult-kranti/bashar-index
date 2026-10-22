# Experiment pages — build source

`experiments/frequency-of-place/index.html` is generated, not hand-written:

```
python3 src/experiments/fp_model.py            # physics model -> fp_results.json, fp_series.npz (needs numpy, scipy)
python3 src/experiments/build_graph.py         # merges data/experiments/frequency-of-place/{ai_lab_papers,literature}.md -> graph.json
python3 src/experiments/fop_page.py            # writes experiments/frequency-of-place/index.html
```

`sphere_modes.py` holds the three solvers for the hollow-sphere modes; `fop_diagrams.py` draws the inline SVG diagrams;
`fop_bench.py` is the Blender (bpy 5.0) scene for the two rendered views. `fp_model.py` writes next to itself by default;
set `FP_OUT` to point it at `experiments/frequency-of-place/` and copy `fp_series.npz` to `data/experiments/frequency-of-place/`.
