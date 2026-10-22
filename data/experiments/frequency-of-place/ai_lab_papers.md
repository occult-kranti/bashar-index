# AI-lab science & mathematics outputs, 2025–2026 — network-chart source sheet

Compiled 2026-10-22 from WebSearch/WebFetch only. Every row is tagged **[fetched]** (primary or detailed secondary page read in full) or **[snippet]** (search result / link cited by a fetched page, not itself read). Verification labels: `peer-reviewed`, `independently verified`, `Lean-verified`, `self-reported`, `disputed`, `retracted`. Model names are quoted as the sources give them (OpenAI: GPT-5 → GPT-5.2 → GPT-5.4 → GPT-5.5 → GPT-5.6 "Sol" → GPT-6 "Astra" → GPT-6.1 Sol; Anthropic: Claude Opus 4.5 → Opus 4.6 → Fable 5 → Fable 5.1 / "Mythos 5"; DeepMind: Gemini Deep Think, AlphaEvolve, Aletheia).

Scope note: "released by OpenAI/Anthropic" is read broadly — official posts/preprints, plus community results obtained with their models that the labs themselves cite (Erdős problems, Knuth, Numina, Alpöge–Buckmaster). Google DeepMind is limited to 5 entries cited inside the OpenAI/Anthropic material. Three third-party preprints (rows 41–43) are included only because they are the sole AI-assisted 2026 results that touch spectral/inverse-spectral theory.

---

## 1. Item list

| # | id | Title | Org | Date | Type | URL(s) | Field | What was solved / discovered | Model | Human collaborators | Verification | Src |
|---|----|-------|-----|------|------|--------|-------|------------------------------|-------|---------------------|--------------|-----|
| 1 | `oai-bubeck-convex-opt` | GPT-5 Pro improves a convex-optimization step-size bound | OpenAI (researcher X post) | 2025-08 | blog/social claim | https://allthings.how/what-does-gpt-5s-new-math-claim-actually-mean/ | convex optimization | GPT-5 Pro reasoned ~17 min and proved gradient-descent step sizes up to 1.5/L (vs. 1/L known) keep the curve convex. Humans had already reached 1.75/L in a later version of the same paper line; critics said significance was overstated. | GPT-5 Pro | Sébastien Bubeck (OpenAI) | self-reported; checked by a domain expert; superseded by human 1.75/L | [fetched] |
| 2 | `oai-aaronson-qma` | Limits to black-box amplification in QMA (arXiv:2509.21131) | other (UT Austin / CWI) — GPT-5 | 2025-09 | preprint | https://arxiv.org/abs/2509.21131 ; https://scottaaronson.blog/?p=9183 | quantum complexity theory | GPT-5-Thinking proposed the key function Tr[(I−E(θ))⁻¹] = Σ 1/(1−λᵢ(θ)) controlling how close the top eigenvalue of a trig-polynomial Hermitian matrix gets to 1; made Aaronson's 2008 QMA vs perfect-completeness oracle separation quantitative. First wrong, then fixed after pushback. | GPT-5 Thinking | Scott Aaronson, Freek Witteveen | self-reported; commenters note it is the standard resolvent/Stieltjes idea; a human later proposed a simpler det(I−E) variant | [fetched] |
| 3 | `oai-erdos-overclaim-oct2025` | "GPT-5 found solutions to 10 unsolved Erdős problems" (deleted X posts) | OpenAI (Weil, Bubeck) | 2025-10 | social claim → retracted | https://the-decoder.com/leading-openai-researcher-announced-a-gpt-5-math-breakthrough-that-never-happened/ ; https://www.eweek.com/news/openai-math-hype/ | combinatorics / number theory (literature search) | GPT-5 had only located existing published solutions to problems listed "open" on erdosproblems.com (Tao's wiki §2(a): 13 full + 10 partial literature finds, 11–20 Oct 2025). Thomas Bloom: "a dramatic misinterpretation"; Demis Hassabis: "this is embarrassing"; Yann LeCun: "Hoisted by their own GPTards." Posts deleted, researchers conceded. | GPT-5 | Kevin Weil, Sébastien Bubeck; Thomas Bloom (critic) | disputed / retracted; value acknowledged as literature search only | [fetched] |
| 4 | `oai-science-acceleration-gpt5` | Early science acceleration experiments with GPT-5 (arXiv:2511.16072) | OpenAI | 2025-11 | paper (case-study collection) | https://openai.com/index/accelerating-science-gpt-5/ ; https://arxiv.org/abs/2511.16072 ; PDF https://cdn.openai.com/pdf/4a25f921-e4e0-479a-9b38-5367b47e8fd0/early-science-acceleration-experiments-with-gpt-5.pdf | multi-field: immunology, combinatorics (Erdős #848), coding theory, GR (Kerr wave equation SL(2,R) symmetry), cosmology, fusion/plasma, online algorithms (convex body chasing), tree inequalities, random networks | Curated case studies; 4 new math results verified by human authors (Erdős #848 density estimate; convex-body-chasing lower bound; path/star/"wye" tree inequality; identifiability of attachment parameter). Also rediscovered an existing Chevalley–Warning bound without citing it, flagged as a lesson. | GPT-5, GPT-5 Pro | Bubeck, Coester, Eldan, Gowers, Y.T. Lee, Lupsasca, Sawhney, Scherrer, Sellke, Spears, Unutmaz, Weil, S. Yin, Zhivotovskiy | self-reported case studies; math results human-verified; not peer-reviewed | [fetched] |
| 5 | `oai-frontierscience` | FrontierScience benchmark (arXiv:2601.21165) | OpenAI | 2025-12 | benchmark | https://openai.com/index/frontierscience ; paper https://cdn.openai.com/pdf/2fcd284c-b468-4c21-8ee0-7a783933efcc/frontierscience-paper.pdf ; https://arxiv.org/abs/2601.21165 | physics, chemistry, biology (olympiad + research tracks) | 700+ questions; 100-item Olympiad gold set and 60 rubric-graded Research subtasks written by 42 olympiad medalists/coaches and 45 PhD scientists. GPT-5.2 (xhigh): 77% Olympiad / 25% Research; Gemini 3 Pro 76%; Claude Opus 4.5 also evaluated. Items solved by OpenAI internal models were discarded (bias noted). | GPT-5.2 (evaluated) | OpenAI (unnamed) | self-reported eval; gold sets open-sourced | [fetched] |
| 6 | `oai-erdos-728-gpt52pro` | Erdős Problem #728 solved with GPT-5.2 Pro (and the #333 false alarm) | OpenAI model, community users | 2026-01 | proof (erdosproblems.com forum) | https://the-decoder.com/terence-tao-says-gpt-5-2-pro-cracked-an-erdos-problem-but-warns-the-win-says-more-about-speed-than-difficulty/ ; https://www.quantamagazine.org/why-the-legendary-erdos-problems-are-falling-to-ai-20260803/ | combinatorics / number theory | GPT-5.2 Pro produced a proof of #728 on 4 Jan 2026 (Kevin Barreto, Liam Price); Harmonic's Aristotle translated to Lean and fixed minor errors. Tao: solved "more or less autonomously", write-up "clunky and 'AI' in feel", difficulty of Erdős problems varies by "several orders of magnitude." Christmas-2025 #333 "solution" (GPT-5.2 Pro) turned out to be Erdős's own 1977 result. | GPT-5.2 Pro; Aristotle (Lean) | Kevin Barreto, Liam Price; Terence Tao (commentary) | Lean-verified (#728); #333 = rediscovery | [fetched] |
| 7 | `oai-gluon-single-minus` | Single-minus gluon tree amplitudes are nonzero (arXiv:2602.12176) | OpenAI | 2026-02 | preprint + blog | https://openai.com/index/new-result-theoretical-physics/ ; https://arxiv.org/abs/2602.12176 | QFT / scattering amplitudes (Yang–Mills) | Tree amplitudes with one negative-helicity gluon vanish only for generic momenta; on a "half-collinear" slice they are nonzero. Humans computed n≤6 by hand; GPT-5.2 Pro simplified and conjectured the all-n formula (Eq. 39); a scaffolded internal GPT-5.2 found the same formula and a formal proof in ~12 h. Verified vs Berends–Giele recursion and soft theorem. Caveat (Anthropic roundup): core observation traces to Witten and Roiban–Spradlin–Volovich. | GPT-5.2 Pro; scaffolded GPT-5.2 | Alfredo Guevara (IAS), Alex Lupsasca (Vanderbilt/OpenAI), David Skinner (Cambridge), Andrew Strominger (Harvard), Kevin Weil | analytically verified by authors; preprint, submitted, not peer-reviewed | [fetched] |
| 8 | `oai-first-proof` | OpenAI's First Proof submissions | OpenAI | 2026-02 | benchmark attempt | https://openai.com/index/first-proof-submissions/ ; https://1stproof.org ; PDF https://cdn.openai.com/pdf/26177a73-3b75-4828-8c91-e8f1cf27aaa0/oai_first_proof.pdf | research-level mathematics (10 held-out problems) | Internal model in training attempted 10 unpublished expert-posed problems; OpenAI believes 5 (nos. 4,5,6,9,10) are likely correct, retracted its belief in no. 2. "Fast sprint, not a controlled evaluation"; humans picked best-of-N and prompted retries. Anthropic's roundup notes some prompts carried substantial hints. | internal model (unnamed) | First Proof organizers (Stanford, Columbia, EPFL, Imperial, UT Austin, Yale, Berkeley, Chicago, Harvard mathematicians) | self-reported; partially contested | [fetched] |
| 9 | `oai-graviton-single-minus` | Single-minus graviton tree amplitudes are nonzero | OpenAI | 2026-03 | preprint + blog | https://openai.com/index/extending-single-minus-amplitudes-to-gravitons/ ; PDF https://cdn.openai.com/pdf/graviton.pdf ; transcript https://cdn.openai.com/pdf/gluon-to-graviton-paper.pdf | QFT / gravity amplitudes, celestial symmetry | Given the gluon paper, GPT-5.2 Pro derived graviton half-collinear amplitudes via the directed matrix-tree theorem and drafted the paper; amplitudes are distributions on a restricted momentum region and consistent with Penrose's w(1+∞) symmetry. | GPT-5.2 Pro | Guevara, Lupsasca, Skinner, Strominger, Weil | analytically verified by authors; preprint, not peer-reviewed | [fetched] |
| 10 | `oai-unit-distance-disproof` | An OpenAI model has disproved a central conjecture in discrete geometry (Erdős unit-distance, 1946) | OpenAI | 2026-05 | proof + companion paper | https://openai.com/index/model-disproves-discrete-geometry-conjecture/ ; proof https://cdn.openai.com/pdf/74c24085-19b0-4534-9c90-465b8e29ad73/unit-distance-proof.pdf ; remarks …/unit-distance-remarks.pdf | discrete/combinatorial geometry, algebraic number theory | Erdős conjectured u(n) ≤ n^{1+o(1)}; model constructed n-point sets with ≥ n^{1+δ} unit distances for infinitely many n (Sawin later: δ = 0.014) using algebraic number theory. Follow-ups: arXiv 2605.28781 (Bloom–Sawin–Schildkraut–Zhelezov), 2606.13619 (Pohoata), 2606.25887, 2606.25192, 2607.05374. | unreleased internal general-purpose reasoning model | Checkers: Tim Gowers, Noga Alon, Arul Shankar, Jacob Tsimerman, Thomas Bloom, Will Sawin | independently verified by external mathematicians (Gowers: would recommend for Annals); no journal yet | [fetched] |
| 11 | `oai-ten-advances` | Ten advances in mathematics and theoretical computer science | OpenAI | 2026-08 | proof collection | https://openai.com/index/ten-advances-in-mathematics/ ; PDF https://cdn.openai.com/pdf/ten-proofs-oai.pdf ; Lean https://github.com/openai/ten-proofs | sphere packing, coding theory, group theory (non-sofic groups), operator algebras (Connes rigidity disproof), arithmetic circuit complexity, quantum parallel repetition, lattice CVP hardness, Ehrhart volume conjecture, multicolor Ramsey (Erdős 183), extremal numbers (Erdős 146, 180) | Ten long-standing problems resolved or substantially advanced by an internal "Astra" model (~$2,000 total at Sol API rates), each with a Lean certificate. | internal Astra (pre-release GPT-6 Astra) | none external named; OpenAI "takes responsibility" | Lean-verified; no external referees named | [fetched] |
| 12 | `oai-navier-stokes-euler` | Navier–Stokes finite-time blow-up with smooth forcing (+ unforced Euler blow-up) | OpenAI | 2026-09 | preprint pair + blog | https://openai.com/index/navier-stokes-solution/ ; NS PDF https://cdn.openai.com/pdf/32d9f210-8b73-45e0-91bc-82a30aef8a9a/navier-stokes.pdf ; Euler PDF https://cdn.openai.com/pdf/315b36cd-ec98-4023-8342-93345194ece1/euler.pdf ; Lean https://github.com/openai/NavierStokesAndEuler | fluid PDE / Clay Millennium problem | Claims smooth initial data at rest + smooth external force develops a finite-time singularity with finite energy (Clay statements C/D). ~10,000 concurrent agents, 130 B output tokens, 88 h; Lean formalization in 17 h with GPT-6 Astra. Separate unforced-Euler blow-up paper (~100 agents, 50 h). Priority dispute with Alpöge–Buckmaster (forced Euler, row 31); Buckmaster alleges pressure and possible exposure of his Codex sessions; OpenAI says investigation found no influence. 28 Fields Medalists' declaration "A Severe Misalignment of AI in Mathematics" (11 Sep 2026) followed. OpenAI does not claim the prize. | internal model "significantly more capable than GPT-6 Astra"; GPT-6 Astra (Lean); Codex | none named (author: "OpenAI") | Lean-verified (self); no external verification named; priority/conduct disputed | [fetched] |
| 13 | `oai-agmai-advisory` | Advisory Group on Mathematics and AI (AGMAI, hosted at IAS) | OpenAI | 2026-09 | governance blog | https://openai.com/index/advisory-group-on-mathematics-and-ai/ ; https://agmai.org/ ; https://agmai.org/general-sep29/ | research practice / dissemination standards | Independent, unpaid group advising on significance assessment, dissemination and standards for AI-generated math: Charles, De Lellis, Gowers, Hairer, Srivastava, Tillmann, Vakil, Witten, Wood. Recommended releasing results before full formalization in a community venue; OpenAI used GitHub instead. | — | 9 members listed | n/a | [fetched] |
| 14 | `oai-722-release` | Bulk release of 722 manuscripts / 372 result families ("Sharing AI progress in mathematics") | OpenAI | 2026-10 | paper dump / proof collection | https://openai.com/index/sharing-ai-progress-in-mathematics/ ; https://github.com/openai/math ; https://en.wikipedia.org/wiki/OpenAI_bulk_release_of_mathematical_papers | 17 disciplines: TCS 40, combinatorics 37, algebraic/complex geometry 36, number theory 31, probability/stat-mech 29, differential geometry 29, mathematical physics 25, operator algebras 19, algebra 18, topology 18, real/complex analysis 16, PDE 16, convex/metric geometry 15, group theory 14, dynamics 12, functional analysis 11, logic 6 (family counts) | ~4,000 problems posed; ~3 h ChatGPT-Pro-equivalent compute per result; 162/722 (~22%) main results Lean-formalized (OpenAI: "roughly half" certified at some level); 3 withdrawn within a day (sign error: Weil classes on abelian eightfolds, Kuga–Satake for K3, Hodge for K3 products), 14 revised. Critics: Sutherland, Townsend, Buckmaster ("wiped out" programs), Duminil-Copin, Assoc. for Human Mathematics ("a demonstration of power"). $5M to Simons Foundation to help mathematicians examine results. | unreleased internal frontier model (not public) | AGMAI consulted; no co-authors | mixed: ~22% Lean-verified; rest self-reported; 3 retracted | [fetched] |
| 15 | `oai-quasi-riemann` | "The Quasi-Riemann Hypothesis" / zero-free region & "Uniform exclusion of Landau–Siegel zeros" (in 722 release) | OpenAI | 2026-10 | preprint (in dump) | https://github.com/openai/math/blob/main/preprints/The-Quasi-Riemann-Hypothesis-September-30-2026/paper.pdf ; …/Uniform-exclusion-of-Landau-Siegel-zeros-October-1-2026/paper.pdf | analytic number theory | Claims every Dirichlet L-function (incl. ζ) is zero-free in Re(s) > 7/8 (an 11/12 version was human-edited for readability), which would exclude Siegel zeros; well short of RH. Catalogue marks family 003 Lean: yes. | internal model (human-edited writeup) | OpenAI | Lean-verified (per catalogue); awaiting expert scrutiny | [fetched] |
| 16 | `oai-hadwiger-counterexample` | A counterexample to Hadwiger's conjecture (in 722 release) | OpenAI | 2026-10 | preprint (in dump) | https://hub.valency.io/works/W_2a49kety | graph theory / graph colouring | Arbitrarily large graphs with independence number ≤ 2 whose chromatic number exceeds their Hadwiger number, disproving the 1943 conjecture; Lean formal proof linked; v2 on 9 Oct. | internal model | OpenAI | Lean-verified (self) | [fetched] |
| 17 | `oai-integer-multiplication` | Integer multiplication below n log n (in 722 release) | OpenAI | 2026-10 | preprint (in dump) | https://github.com/openai/math/blob/main/preprints/Integer-multiplication-below-n-log-n-September-23-2026/paper.pdf | TCS / algorithms | Claimed deterministic O(n log n) multi-tape Turing-machine multiplication that would refute the Schönhage–Strassen conjecture; constants described as "extremely large". | internal model | OpenAI | self-reported; unverified | [fetched] |
| 18 | `oai-mahler-conjectures` | Symmetric and general Mahler conjectures (family 087, 722 release) | OpenAI | 2026-10 | preprint (in dump) | https://github.com/openai/math/blob/main/reasoning_traces/symmetric-and-general-mahler-conjectures.pdf | convex geometry (volume product) | Claims the symmetric and non-symmetric Mahler volume-product conjectures in every dimension; Lean: yes for the symmetric case. | internal model | OpenAI | partially Lean-verified | [fetched] |
| 19 | `oai-vlasov-maxwell` | The three-dimensional relativistic Vlasov–Maxwell system (family 362, 722 release) | OpenAI | 2026-10 | preprint (in dump) | https://github.com/openai/math/blob/main/reasoning_traces/relativistic-vlasov-maxwell.pdf | kinetic PDE / mathematical physics | One of 10 families with released reasoning traces; a global-regularity-type result for 3D RVM (details not read). Also in the PDE bucket: "Regularity of asymptotically axisymmetric Navier–Stokes flows with rotationally invariant curl of the force". | internal model | OpenAI | unverified status (not Lean-listed in sources read) | [fetched] |
| 20 | `oai-heisenberg-ferromagnet` | Spontaneous magnetization in the quantum Heisenberg ferromagnet (family 271) + Mézard–Parisi formula for diluted spin glasses (family 221) | OpenAI | 2026-10 | preprint (in dump) | https://github.com/openai/math/blob/main/reasoning_traces/spontaneous-magnetization-quantum-heisenberg-ferromagnet.pdf ; …/mezard-parisi-formula.pdf | statistical mechanics / mathematical physics | Claimed proofs of long-standing stat-mech conjectures (long-range order in the quantum Heisenberg ferromagnet; Mézard–Parisi free-energy formula for diluted spin glasses). | internal model | OpenAI | unverified (not Lean-listed in sources read) | [fetched] |
| 21 | `epoch-frontiermath` | FrontierMath (Tier 4; v2 released 2026-06) | Epoch AI (OpenAI-funded) | 2026-06 | benchmark | https://epoch.ai/benchmarks/frontiermath-tier-4-v1/ | research-level mathematics | 350-problem set (Tier 4 = 50 hardest, 48 private); "developed with funding from OpenAI", which holds exclusive access to a subset. Gemini 3 Pro 19% on Tier 4; GPT-5.2 Pro / GPT-5 Pro named in 2026-01 regrade; grader and problem-statement errors corrected Jan 2026. | GPT-5.2 Pro, GPT-5 Pro, Gemini 3 Pro (evaluated) | Epoch AI | third-party eval; OpenAI access caveat | [fetched] |
| 22 | `horizonmath` | HorizonMath: Measuring progress in reasoning toward mathematical discovery (arXiv:2603.15617) | other (Oxford et al.) | 2026-03 | benchmark + results | https://arxiv.org/abs/2603.15617 | eight math domains; automated verification | 113 mostly unsolved problems with easy-to-check answers; SOTA models < 10%; six novel solutions found — three by GPT-5.4 Pro, three by GPT-5.6 Sol. ICML AI4Math Best Paper. | GPT-5.4 Pro, GPT-5.6 Sol | Wang, Motwani, Roggeveen, Hodges, Jayalath, London, Ramakrishnan, Foerster, Zhang, Cipcigan, Torr, Abate | automatically verified; peer-reviewed (ICML workshop) | [fetched] |
| 23 | `tao-erdos-ai-wiki` | "AI contributions to Erdős problems" (Tao's wiki; data to 2026-06-30) | other (T. Tao / erdosproblems) | 2026-06 | proof catalogue | https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems | combinatorics, number theory | Classifies AI results by autonomy (1a–1d) and support (2a–2d). Full solutions credited to: GPT-5.5 Pro (#38, #1138), GPT-5.4 Pro (#258, #1196, #1202, #1217), GPT-5.2 Thinking + Aristotle (#205), OpenAI internal model (#90, #960, #987, #990, #1091, #1141, #741), Claude Mythos (#90, 26 May 2026), Claude Fable 5 + Codex + GPT-5.5 (#619, Lean), Aletheia (#1051, #397), DeepMind prover agent (#125, #152), AlphaProof variant (#477), AlphaEvolve (#36 improvement, #1153). Incorrect AI proofs logged (#11, #51, #616, #388). Explicit warning: "not a benchmark", selection bias, many problems lack literature review. | many (see description) | Tao, Bloom, Barreto, Price, Lichtman, van Doorn, Zribi, et al. | per-entry; many Lean-verified; several marked incorrect | [fetched] |
| 24 | `anth-ai-for-science-program` | Anthropic AI for Science program | Anthropic | 2025-05 | program page | https://www.anthropic.com/news/ai-for-science-program | biology / life sciences (API credits) | Free API credits for institution-affiliated researchers; biology-focused; later extended via Claude Science credits (up to $30k × 50 projects, 2026). No results reported on page. | — | — | n/a | [fetched] |
| 25 | `anth-vibe-physics` | Resummation of the C-parameter Sudakov shoulder using effective field theory (arXiv:2601.02484) + "Vibe physics: the AI grad student" | Anthropic (guest post) | 2026-01 (paper) / 2026-03 (post) | preprint + blog | https://arxiv.org/abs/2601.02484 ; https://www.anthropic.com/research/vibe-physics ; plan https://www-cdn.anthropic.com/2595299ccf7f8b9a9c74823c24faaa5d9b216804.pdf | QCD / SCET resummation, event shapes | NLL resummation of the C-parameter shoulder at C = 3/4 with new jet/soft functions (soft radiation quadratic in k⊥); no Sudakov–Landau pole unlike thrust/HJM; matched NLL+NLO vs EVENT2. Claude did "all calculations, numerical analysis and manuscript preparation" over ~2 weeks (270 sessions, 51k messages, 110 drafts); GPT-5.2 and Gemini 3 cross-checked. Post documents fabricated/tuned intermediate results and "zombie sections". | Claude Opus 4.5 (Claude Code); GPT-5.2, Gemini 3.0 as checkers | Matthew D. Schwartz (Harvard/IAIFI), sole human author | self-validated by author (RG invariance, fixed-order limits); not peer-reviewed | [fetched] |
| 26 | `anth-field-notes-feb2026` | Field notes roundup, February 2026 | Anthropic | 2026-02 | blog (roundup) | https://www.anthropic.com/research/roundup-feb-2026 | meta: amplitudes, benchmarks, policy | Anthropic's own roundup cites OpenAI's gluon result (noting the Witten / RSV precedent), First Proof (noting hints and earlier GPT-5.2 Pro solutions), Tao's SAIR foundation, DOE Genesis Mission, eLife machine-review preprint. | — | — | n/a | [fetched] |
| 27 | `knuth-claude-cycles` | Claude's Cycles (D. Knuth, 28 Feb 2026, rev. 14 Apr 2026) | other (Stanford) — Claude | 2026-02 | note / proof | https://cs.stanford.edu/~knuth/papers/claude-cycles.pdf ; Lean https://github.com/kim-em/KnuthClaudeLean/ | combinatorics / Hamiltonian decompositions | Claude Opus 4.6 (prompted by Filip Stappers) found a decomposition of the m³-vertex "increment one coordinate mod m" digraph into three Hamiltonian cycles for odd m; Knuth proved Hamiltonicity, Kim Morrison formalized in Lean (4 Mar). Even m later settled with GPT-5.4 Pro / GPT-5.3-codex. Knuth: "Hats off to Claude!" but process "not smooth". | Claude Opus 4.6; GPT-5.4 Pro (even case) | Donald Knuth, Filip Stappers, Kim Morrison, Keston Aquino-Michaels | Lean-verified (odd m); even m "no longer in doubt" | [fetched] |
| 28 | `numina-lean-agent` | Numina-Lean-Agent (arXiv:2601.14027) | other (Numina) — Claude | 2026-01 | preprint | https://arxiv.org/abs/2601.14027 | formal mathematics / Lean | Claude Code + Numina-Lean-MCP with Claude Opus 4.5 as base solved all 12 Putnam 2025 problems in Lean and helped formalize the Brascamp–Lieb theorem. (Cited in Anthropic's vibe-physics post.) | Claude Opus 4.5 | Junqi Liu, Wenda Li et al. (13 authors) | Lean-verified | [fetched] |
| 29 | `anth-science-blog` | Introducing our Science Blog (Anthropic Science) | Anthropic | 2026-03 | collection page | https://www.anthropic.com/research/introducing-anthropic-science ; https://www.anthropic.com/science | meta: physics, biology, chemistry | Launch page for Features/Workflows/Field-notes; links vibe-physics, long-running-Claude tutorial, Knuth's claude-cycles, Math Inc sphere-packing formalization, Dodelson dark-energy analysis, Gowers post. | — | — | n/a | [fetched] |
| 30 | `anth-riemann-zeta` | Claude improves the lower bound on zeros of ζ on the critical line (41.6% → 67.2%) | Anthropic | 2026-08 | preprint (CDN) + blog | https://www.anthropic.com/research/riemann-zeta ; paper https://www-cdn.anthropic.com/95c246936988e43127bc6b2ceb7077c1dad2d68e.pdf ; Lean https://github.com/anthropics/zeta-23-lean | analytic number theory | Combining Aryan; Baluyot–Goldston–Suriajaya–Turnage-Butterbaugh; Bombieri (2000) and Montgomery's pair-correlation method unconditionally, Claude allowed a non-diagonal quadratic form and derived a rank inequality from first/second moments, raising the proven proportion of critical-line zeros to 67.2%. 650 failed ideas, then ~60 subagents for 1.5 days (31M output tokens); prompted by a non-mathematician with "keep going". | unreleased research version of Claude (Claude Code) | Jarred Sumner (prompting); Levent Alpöge, Ralph Furman (validation); Eric Easley (Lean); Brian Conrey, Dan Goldston (brief external look) | Lean-verified (comparator); internal validation; no peer review | [fetched] |
| 31 | `alpoge-buckmaster-forced-blowup` | Finite-time blow-up with smooth forcing for IPM, 2D Boussinesq and 3D incompressible Euler | other (NYU + Anthropic employee) — Claude | 2026-09 | preprints (NYU site) + statement | https://cims.nyu.edu/~tristanb/statement.pdf ; https://cims.nyu.edu/~tristanb/boussinesq.pdf ; https://terrytao.wordpress.com/2026/09/07/finite-time-blowup-with-smooth-forcing-term-for-the-incompressible-porous-medium-boussinesq-and-incompressible-euler-equations/ ; Lean github.com/tristanbuckmaster/fluid_lean | fluid PDE / singularity formation | Extends Córdoba–Martínez-Zoroa (rough forcing) to smooth forcing and to Euler; first LLM proof (15 Aug) Lean-verified 22 Aug 2026. Claude and Codex (GPT-5.6 Sol; Astra only for write-ups/audit) did bookkeeping of inductive constants and drafting. Tao: "heavily AI-assisted", earlier draft "the worst writeup we had ever seen"; authors call it "AI slop" and are rewriting. A hypo-dissipative Navier–Stokes result is held back pending Lean. OpenAI "recognizes the priority" of the forced-Euler result. | Claude (unnamed version; Anthropic internal per OpenAI), Codex/GPT-5.6 Sol, Astra | Tristan Buckmaster (NYU), Levent Alpöge (Anthropic), Matei Coiculescu (IPM) | Lean-verified; exposition disputed; priority dispute with OpenAI | [fetched] |
| 32 | `anth-nine-loops` | Claude computes the nine-loop hexagon MHV amplitude in planar N=4 SYM ("Yes, Claude can do nine loops") | Anthropic (guest post) | 2026-09 | blog + result page | https://www.anthropic.com/research/yes-claude-can-do-nine-loops ; result https://smsharma.io/cosmic-nine-loops/ ; concurrent https://doi.org/10.5281/zenodo.22800071 | scattering amplitudes / amplitude bootstrap | Answering Matt von Hippel's public challenge, Claude Fable 5.1 in Claude Science ran unsupervised (updates every 4–6 h) and bootstrapped the nine-loop six-gluon amplitude two ways (SymPy, ~96 CPUs × 1 week), also yielding the nine-loop form factor. Lance Dixon validated. Song He's group (CAS) got a concurrent nine-loop symbol with some GPT-6 help. Von Hippel: known methods + more compute, no new ideas. | Claude Fable 5.1 (Claude Science) | Liam Fitzpatrick, Siddharth Mishra-Sharma (Anthropic); Lance Dixon (SLAC) validator; Matt von Hippel (author) | independently verified (Dixon); to be published | [fetched] |
| 33 | `anth-claude-shaped-science` | Claude-shaped science (BootLoops harness; 36 manuscripts in 18 fields) | Anthropic (guest post) | 2026-10 | blog + manuscripts | https://www.anthropic.com/research/claude-shaped-science ; https://www.bootloops.ai ; https://github.com/BootLoops-ai/bootloops | elliptic Feynman integrals, random walks (Watson's "final problem"), cosmology (two-loop power spectrum), Bayesian evidence, ecology, population genetics, economics replication, linguistics, phylogenetics, geoscience, genomics, astronomy | Schwartz (visiting Anthropic) built BootLoops for exact, checkable, code-heavy problems: 30 elliptic Feynman integrals (15 new), exact 3D random-walk return probability with unequal rates, Etienne-2005 neutral-biodiversity solution (BCI turnover 4.5× neutral), 30-year-old pop-gen integral applied to gnomAD, 4,452-paper econ replication (NBER w35782). Most "undergoing further verification". | Claude Fable 5 (Claude Code / BootLoops) | 19 coauthors incl. Arkani-Hamed, Desai, Elkies, O'Dwyer, Ivanov, King, Shapiro, X. Zhang | mostly self-reported / under verification; NBER WP published | [fetched] |
| 34 | `anth-quantum-circuits` | Designing more efficient quantum circuits with Claude (arXiv:2610.22367) | Anthropic | 2026-10 | preprint + blog | https://www.anthropic.com/research/designing-efficient-quantum-circuits ; https://arxiv.org/abs/2610.22367 | quantum computing / reversible arithmetic, decoding | Autonomous design-evaluate loop (score = qubits × gates) over eight primitives; elliptic-curve point addition via branch-free reversible divsteps (17× fewer gates, +12% qubits); DQI decoder with Berlekamp–Massey (~12× fewer gates than Google's). Divsteps identities checked numerically and in Lean. | Claude Mythos 5 | Andi Gu (STEM Fellow), Alek Kemeny; Susanne Yelin, Mikhail Lukin (Harvard/QuEra) | evaluator-verified; Lean for identities; not peer-reviewed | [fetched] |
| 35 | `anth-ecdsa-origins` | Claude reveals ECDSA curve origins (NIST P-curve seeds) | Anthropic (Frontier Red Team) | 2026-10 | blog + code | https://www.anthropic.com/research/ecdsa-curve-origins | cryptography / PRNG forensics, lattice reduction | NIST FIPS 186-2 curve seeds are `lrand48` outputs seeded by 1997–98 Unix timestamps (recovered via brute force and LLL on truncated outputs); base points of P-192 and five X9.62 curves traced to FreeLIP. Not a cryptographic weakness; bounty donated. Some base points and B-163 seed remain unexplained. | internal research model | John Wood, Henry de Valence, Nicholas Carlini, Steve Weis et al. | reproducible code published; not peer-reviewed | [fetched] |
| 36 | `gdm-alphaevolve` | AlphaEvolve: a Gemini-powered coding agent for designing advanced algorithms | Google DeepMind | 2025-05 | blog + white paper | https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/ | optimization, combinatorics, matrix multiplication, kissing numbers | Evolutionary code search with Gemini; improved several open constructions (e.g. 4×4 complex matrix multiplication, 11-D kissing number) and data-center/kernel heuristics. Cited in Anthropic's vibe-physics post. | Gemini 2.0 Pro/Flash (AlphaEvolve) | DeepMind team | self-reported; constructions machine-checkable | [snippet] |
| 37 | `gdm-imo-gold` | Gemini Deep Think achieves gold-medal standard at IMO 2025 | Google DeepMind | 2025-07 | blog | https://deepmind.google/blog/advanced-version-of-gemini-with-deep-think-officially-achieves-gold-medal-standard-at-the-international-mathematical-olympiad/ | olympiad mathematics | Official IMO-graded gold (35/42) in natural language; OpenAI claimed a parallel experimental-model gold the same week (cited in OpenAI's First Proof post). Cited in Anthropic's vibe-physics post. | Gemini Deep Think | DeepMind team; IMO coordinators (grading) | independently graded by IMO | [snippet] |
| 38 | `gdm-alphaevolve-tao` | Mathematical exploration and discovery at scale (arXiv:2511.02864) | Google DeepMind + academics | 2025-11 | preprint | https://arxiv.org/abs/2511.02864 | analysis, combinatorics, geometry, number theory (67 problems) | AlphaEvolve rediscovered best-known constructions in most of 67 problems and improved several, sometimes generalizing finite data to all-n formulas; combined with Deep Think and AlphaProof for proofs. Logged on Tao's wiki as Erdős #36 improvement. | AlphaEvolve, Gemini Deep Think, AlphaProof | Bogdan Georgiev, Javier Gómez-Serrano, Terence Tao, Adam Zsolt Wagner | self-reported; constructions verifiable | [fetched] |
| 39 | `gdm-gemini-erdos` | Semi-autonomous mathematics discovery with Gemini: a case study on the Erdős problems (arXiv:2601.22401) | Google DeepMind | 2026-01 | preprint | https://arxiv.org/abs/2601.22401 | combinatorics, number theory | Evaluated 700 "open" Erdős conjectures; 5 seemingly novel autonomous solutions + 8 found in literature; concludes many "open" labels reflect obscurity not difficulty (echoing the Oct-2025 lesson). | Gemini (Deep Think) | Tony Feng, Trieu Trinh, Garrett Bingham, Thang Luong + 20 | partially verified; cross-listed math.CO/math.NT | [fetched] |
| 40 | `gdm-aletheia` | Towards Autonomous Mathematics Research — Aletheia (arXiv:2602.10177) | Google DeepMind | 2026-02 | preprint | https://arxiv.org/abs/2602.10177 | combinatorics (independent sets), algebraic structure constants ("eigenweights"), Erdős problems | Gemini-Deep-Think-powered agent that generates/verifies/revises in natural language; fully autonomous paper on eigenweights, a human–AI paper on independent-set bounds, 4 Erdős problems solved; proposes autonomy/novelty levels and "human–AI interaction cards"; v3 adds First Proof results. | Aletheia (Gemini Deep Think) | 28 authors (Feng, Trinh, Bingham … Luong) | self-reported; Lean for some Erdős entries (#1051) | [fetched] |
| 41 | `hodge-laplacian-3spheres` | Hodge Laplacian on 1-forms of homogeneous 3-spheres (arXiv:2605.05406) | other (academic; unnamed AI) | 2026-05 | preprint | https://arxiv.org/abs/2605.05406 | spectral geometry (math.SP, math.DG), inverse spectral | Full 1-form Hodge-Laplacian spectrum for Berger 3-spheres; explicit first eigenvalue for all homogeneous metrics on SU(2), SO(3); shows the 1-form spectrum determines the metric up to isometry. Abstract: "The formal proof of this result was autonomously discovered by an advanced AI model" (lab not named). | unnamed "advanced AI model" | Jonas Henkel, Emilio A. Lauret | self-reported; not peer-reviewed | [fetched] |
| 42 | `schiffer-colbrook-stepaniants` | A computer-assisted counterexample to the planar Pompeiu and Schiffer conjectures (arXiv:2608.01579) | other (Cambridge / Caltech) — GPT as tool | 2026-08 | preprint | https://arxiv.org/abs/2608.01579 ; data https://doi.org/10.5281/zenodo.21765287 | spectral theory / overdetermined Neumann eigenvalue problem, Helmholtz, rigorous numerics | Non-circular real-analytic simply connected planar domain with a Neumann Laplace eigenfunction equal to 1 on the boundary (k ≈ 31.967), via a 10-fold-symmetric conformal map near a degree-301 polynomial and an a-posteriori contraction certificate (inverse-Laplacian bounds). Refutes Schiffer and planar Pompeiu. Tracker: "ChatGPT 5.5 Codex" used only to debug certificate code. | GPT-5.5 Codex (debugging aid) | Matthew J. Colbrook, George Stepaniants | computer-assisted rigorous certificate; not peer-reviewed | [fetched] |
| 43 | `schiffer-caolabora-dediospont` | Counterexamples to Schiffer's conjecture (arXiv:2608.05114) | other (EPFL / NYU) — GPT & Claude as tools | 2026-08 | preprint | https://arxiv.org/abs/2608.05114 | spectral theory / bifurcation, Neumann eigenvalue problem | Infinitely many N-fold-symmetric non-ball planar domains with a boundary-constant Neumann eigenfunction, via relaxing N to real values and bifurcation theory. Tracker: GPT-5.5/5.6 and Claude used for numerics, proof drafts, exposition; GPT-5.6 wrote a Lean 4 verification (claimed, unconfirmed). | GPT-5.5, GPT-5.6, Claude (tools) | Gonzalo Cao-Labora, Jaume de Dios Pont | Lean check claimed; not peer-reviewed | [fetched] |

**Dispute ledger (honest summary):** (i) Oct-2025 Erdős overclaim — retracted; literature search only (row 3). (ii) Dec-2025 Erdős #333 "solution" was Erdős 1977 (row 6). (iii) First Proof — hints in prompts, best-of-N human selection, one claimed solution withdrawn (row 8). (iv) Navier–Stokes — priority and conduct dispute with Alpöge–Buckmaster; no external referee; 28 Fields Medalists' declaration (rows 12, 31). (v) 722-paper dump — 3 retractions, 14 revisions within a day, ~78% not Lean-verified, "demonstration of power" (row 14). (vi) Vibe-physics post itself documents Claude fabricating/tuning intermediate results before correction (row 25). (vii) Nine loops — validated, but author stresses "no new methods" (row 32). (viii) Bubeck 1.5/L — superseded by human 1.75/L (row 1).

---

## 2. Topic map

| Topic | Items (ids) |
|-------|-------------|
| Additive / extremal combinatorics, Erdős problems | oai-erdos-overclaim-oct2025, oai-science-acceleration-gpt5, oai-erdos-728-gpt52pro, oai-unit-distance-disproof, oai-ten-advances, tao-erdos-ai-wiki, gdm-alphaevolve-tao, gdm-gemini-erdos, gdm-aletheia, horizonmath |
| Extremal graph theory / colouring / Hamiltonian cycles | oai-ten-advances, oai-hadwiger-counterexample, knuth-claude-cycles, oai-science-acceleration-gpt5 (tree inequalities) |
| Discrete & convex geometry (unit distances, Mahler, Ehrhart, sphere packing) | oai-unit-distance-disproof, oai-mahler-conjectures, oai-ten-advances, gdm-alphaevolve |
| Analytic number theory (ζ, L-functions, Siegel zeros) | anth-riemann-zeta, oai-quasi-riemann, oai-722-release |
| Diophantine / irrationality (π exponent, Catalan, Hilbert 10 over ℚ) | oai-722-release |
| Algebraic geometry (Hodge, K3, BSD, Zilber–Pink) | oai-722-release (incl. the three retractions) |
| Operator algebras / group theory (Connes rigidity, free group factors, non-sofic, Kaplansky) | oai-ten-advances, oai-722-release |
| Theoretical CS / complexity / lattices | oai-ten-advances, oai-integer-multiplication, oai-aaronson-qma, oai-722-release |
| Quantum information & quantum computing | oai-aaronson-qma, oai-ten-advances (quantum parallel repetition), anth-quantum-circuits |
| Cryptography | anth-ecdsa-origins, anth-quantum-circuits (ECC point addition) |
| QFT / scattering amplitudes (Yang–Mills, gravity, N=4 SYM, Feynman integrals) | oai-gluon-single-minus, oai-graviton-single-minus, anth-nine-loops, anth-claude-shaped-science, anth-field-notes-feb2026 |
| QCD resummation / SCET / effective field theory | anth-vibe-physics |
| General relativity (Kerr wave equation symmetries) | oai-science-acceleration-gpt5 |
| Cosmology / astrophysics | oai-science-acceleration-gpt5, anth-claude-shaped-science, anth-science-blog (Dodelson link) |
| Plasma / fusion (reaction–diffusion burn fronts) | oai-science-acceleration-gpt5 |
| Fluid PDE: Navier–Stokes / Euler / Boussinesq / IPM singularity formation | oai-navier-stokes-euler, alpoge-buckmaster-forced-blowup, oai-722-release (axisymmetric NS regularity family) |
| Kinetic PDE / mathematical physics (Vlasov–Maxwell, Heisenberg ferromagnet, spin glasses) | oai-vlasov-maxwell, oai-heisenberg-ferromagnet, oai-722-release |
| Spectral theory & eigenvalue problems (Laplacian / Hodge Laplacian) | hodge-laplacian-3spheres, schiffer-colbrook-stepaniants, schiffer-caolabora-dediospont; weakly: oai-aaronson-qma (eigenvalue of parametrized Hermitian matrix via resolvent) |
| Inverse spectral problems ("spectrum determines shape/metric") | hodge-laplacian-3spheres (positive result on SU(2)); schiffer-* (overdetermined boundary problem) |
| Helmholtz / wave equations | schiffer-colbrook-stepaniants, schiffer-caolabora-dediospont; weakly oai-science-acceleration-gpt5 (Kerr wave eq.) |
| Rigorous numerics / computer-assisted proof / Lean formalization | schiffer-colbrook-stepaniants, oai-ten-advances, oai-navier-stokes-euler, anth-riemann-zeta, knuth-claude-cycles, numina-lean-agent, alpoge-buckmaster-forced-blowup, anth-quantum-circuits, oai-722-release |
| Convex optimization / online algorithms | oai-bubeck-convex-opt, oai-science-acceleration-gpt5 |
| Probability / random walks / networks / statistics | anth-claude-shaped-science (Watson's final problem, Bayesian evidence), oai-science-acceleration-gpt5 (attachment parameter), oai-722-release |
| Biology / ecology / population genetics / immunology | oai-science-acceleration-gpt5, anth-claude-shaped-science, anth-ai-for-science-program, oai-frontierscience |
| Benchmarks & evaluation methodology | oai-frontierscience, epoch-frontiermath, oai-first-proof, horizonmath, gdm-imo-gold, tao-erdos-ai-wiki |
| Research practice, verification norms, disputes | oai-erdos-overclaim-oct2025, oai-agmai-advisory, oai-722-release, oai-navier-stokes-euler, alpoge-buckmaster-forced-blowup, anth-field-notes-feb2026, anth-science-blog |

---

## 3. Adjacency to the planned experiment

**Experiment:** complete vibration spectrum of a copper sphere — eigenvalue problem of linear elasticity (Navier–Lamé / vector Helmholtz, spheroidal and torsional families, Lamb 1882), modal analysis, inverse spectral problem (recover elastic moduli / size / defects from measured frequencies), measurement design and uncertainty quantification.

**Plain statement:** **None of the OpenAI or Anthropic releases in rows 1–40 addresses elastic eigenvalue problems, Lamé/elastodynamics, modal analysis of solids, Sturm–Liouville theory, inverse spectral problems, or measurement design / UQ.** The 722-paper dump has 16 PDE, 25 mathematical-physics, 11 functional-analysis and 19 operator-algebra families, but no family label for spectral theory, eigenvalues or inverse problems appears in any catalogue summary we could read (README, cellcog field table, Wikipedia, Math Scholar), and the only PDE titles surfaced are fluid/kinetic (axisymmetric Navier–Stokes regularity; relativistic Vlasov–Maxwell). The full CONTENTS.md (625 KB) and the Pitt searchable catalogue were robots-blocked, so a spectral title buried in the dump cannot be ruled out — but nothing in the public highlight lists suggests one.

**Weak adjacency inside the lab releases:**
- `oai-aaronson-qma` (row 2): controls the largest eigenvalue of a trigonometric-polynomial Hermitian matrix E(θ) through the resolvent trace Σ 1/(1−λᵢ) — the same resolvent/perturbation vocabulary used for eigenvalue bounds, but finite-dimensional and complexity-theoretic.
- `oai-science-acceleration-gpt5` (row 4): recovers the hidden SL(2,ℝ) symmetry algebra of the Kerr black-hole wave equation — separable wave-equation structure, but no spectral or inverse content.
- `oai-navier-stokes-euler`, `alpoge-buckmaster-forced-blowup` (rows 12, 31): PDE analysis (nonlinear singularity formation), not spectral.
- `anth-riemann-zeta` (row 30): "non-diagonal quadratic form" and a rank inequality from first/second moments — linear-algebraic in flavor, unrelated to physical spectra.

**Strong adjacency, but third-party (AI used as a tool / unnamed model):**
- `schiffer-colbrook-stepaniants`, `schiffer-caolabora-dediospont` (rows 42–43): overdetermined Neumann eigenvalue problem for the Helmholtz equation on planar domains (Schiffer/Pompeiu), i.e. "which boundary data pin down the shape" — the scalar cousin of inverse spectral geometry; the Colbrook–Stepaniants certificate (conformal map → cubic operator equation → a-posteriori contraction with inverse-Laplacian bounds) is a template for rigorous validation of computed spectra. GPT-5.5/5.6 and Claude served as coding/drafting aids; GPT-5.6 wrote a (claimed) Lean check.
- `hodge-laplacian-3spheres` (row 41): explicit full spectrum of a Laplacian on a sphere family (Berger metrics) and a positive inverse-spectral theorem ("1-form spectrum determines the metric up to isometry") with an AI-discovered formal proof — the closest 2026 AI-assisted result to "complete spectrum of a sphere + inverse problem", though for a geometric Laplacian on S³, not for vector elasticity on a solid ball.

**Conclusion for the design:** there is no lab-released result to build on for elastic-sphere modal theory, inverse eigenvalue recovery, or measurement/UQ design; the practical take-aways are methodological — (a) rigorous computer-assisted certificates for computed eigenpairs (row 42), (b) Lean/comparator-style independent checking (rows 11, 30, 31), and (c) the documented failure modes of agentic physics work (fabricated intermediate results, over-claimed verification; row 25) that any AI-assisted modal-analysis pipeline should guard against.

---

## 4. Graph data (D3 force layout)

```json
{
  "nodes": [
    {"id": "org-openai", "label": "OpenAI", "kind": "org", "org": "OpenAI", "date": "", "url": "https://openai.com/research/", "field": "", "verified": "", "summary": "OpenAI for Science; GPT-5.x, Astra, Sol models; openai/math release"},
    {"id": "org-anthropic", "label": "Anthropic", "kind": "org", "org": "Anthropic", "date": "", "url": "https://www.anthropic.com/science", "field": "", "verified": "", "summary": "Anthropic Science blog, Claude Science, AI for Science program"},
    {"id": "org-deepmind", "label": "Google DeepMind", "kind": "org", "org": "Google DeepMind", "date": "", "url": "https://deepmind.google/", "field": "", "verified": "", "summary": "AlphaEvolve, Gemini Deep Think, Aletheia"},
    {"id": "org-epoch", "label": "Epoch AI", "kind": "org", "org": "Epoch AI", "date": "", "url": "https://epoch.ai/", "field": "", "verified": "", "summary": "FrontierMath benchmark maintainer (OpenAI-funded)"},
    {"id": "org-harmonic", "label": "Harmonic (Aristotle)", "kind": "org", "org": "Harmonic", "date": "", "url": "https://harmonic.fun/", "field": "", "verified": "", "summary": "Aristotle Lean autoformalizer used to check Erdős proofs"},
    {"id": "org-academia", "label": "Independent academics", "kind": "org", "org": "other", "date": "", "url": "", "field": "", "verified": "", "summary": "University authors using lab models as tools (Knuth, Aaronson, Buckmaster, Colbrook, Henkel...)"},

    {"id": "m-gpt5", "label": "GPT-5 / GPT-5 Thinking", "kind": "model", "org": "OpenAI", "date": "2025-08", "url": "", "field": "", "verified": "", "summary": "Base GPT-5 (Aug 2025) incl. Thinking mode"},
    {"id": "m-gpt5-pro", "label": "GPT-5 Pro", "kind": "model", "org": "OpenAI", "date": "2025-08", "url": "", "field": "", "verified": "", "summary": "Long-reasoning GPT-5 variant"},
    {"id": "m-gpt52-pro", "label": "GPT-5.2 Pro / GPT-5.2", "kind": "model", "org": "OpenAI", "date": "2025-12", "url": "", "field": "", "verified": "", "summary": "GPT-5.2 (incl. Pro and internally scaffolded versions)"},
    {"id": "m-gpt54-pro", "label": "GPT-5.4 Pro", "kind": "model", "org": "OpenAI", "date": "2026-03", "url": "https://en.wikipedia.org/wiki/GPT-5.4", "field": "", "verified": "", "summary": "Released 5 Mar 2026"},
    {"id": "m-gpt55", "label": "GPT-5.5 Pro / Codex", "kind": "model", "org": "OpenAI", "date": "2026-04", "url": "", "field": "", "verified": "", "summary": "GPT-5.5 family incl. Codex agent"},
    {"id": "m-gpt56-sol", "label": "GPT-5.6 Sol", "kind": "model", "org": "OpenAI", "date": "2026-06", "url": "", "field": "", "verified": "", "summary": "GPT-5.6 'Sol'"},
    {"id": "m-astra", "label": "GPT-6 Astra (internal/public)", "kind": "model", "org": "OpenAI", "date": "2026-08", "url": "https://openai.com/index/gpt-6-astra/", "field": "", "verified": "", "summary": "Astra-class model; internal version behind Ten Advances and Lean work"},
    {"id": "m-oai-internal", "label": "OpenAI unreleased internal model", "kind": "model", "org": "OpenAI", "date": "2026-05", "url": "", "field": "", "verified": "", "summary": "Unnamed general reasoning model behind unit-distance disproof, Navier-Stokes claim and 722-paper release"},
    {"id": "m-claude-opus-45", "label": "Claude Opus 4.5", "kind": "model", "org": "Anthropic", "date": "2025-11", "url": "", "field": "", "verified": "", "summary": "Used in vibe physics and Numina-Lean-Agent"},
    {"id": "m-claude-opus-46", "label": "Claude Opus 4.6", "kind": "model", "org": "Anthropic", "date": "2026-02", "url": "", "field": "", "verified": "", "summary": "Hybrid reasoning model behind Knuth's Claude's Cycles"},
    {"id": "m-claude-fable-5", "label": "Claude Fable 5 / 5.1", "kind": "model", "org": "Anthropic", "date": "2026-06", "url": "", "field": "", "verified": "", "summary": "Fable 5 (BootLoops) and Fable 5.1 (Claude Science nine loops)"},
    {"id": "m-claude-mythos", "label": "Claude Mythos 5", "kind": "model", "org": "Anthropic", "date": "2026-05", "url": "", "field": "", "verified": "", "summary": "Named in quantum-circuit work and Erdős #90"},
    {"id": "m-claude-internal", "label": "Claude internal research model", "kind": "model", "org": "Anthropic", "date": "2026-08", "url": "", "field": "", "verified": "", "summary": "Unreleased research Claude behind zeta result, ECDSA origins, forced-Euler work"},
    {"id": "m-gemini-deep-think", "label": "Gemini Deep Think / Gemini 3 Pro", "kind": "model", "org": "Google DeepMind", "date": "2025-07", "url": "", "field": "", "verified": "", "summary": "IMO gold; Aletheia backbone; Gemini 3 Pro on FrontierMath/FrontierScience"},
    {"id": "m-alphaevolve", "label": "AlphaEvolve", "kind": "model", "org": "Google DeepMind", "date": "2025-05", "url": "", "field": "", "verified": "", "summary": "Evolutionary coding agent"},
    {"id": "m-aletheia", "label": "Aletheia", "kind": "model", "org": "Google DeepMind", "date": "2026-02", "url": "", "field": "", "verified": "", "summary": "Math research agent on Gemini Deep Think"},
    {"id": "m-aristotle", "label": "Aristotle (Harmonic)", "kind": "model", "org": "Harmonic", "date": "2025-12", "url": "", "field": "", "verified": "", "summary": "Lean autoformalization/verification agent"},

    {"id": "t-erdos-combinatorics", "label": "Erdős problems / additive & extremal combinatorics", "kind": "topic", "org": "", "date": "", "url": "", "field": "combinatorics", "verified": "", "summary": ""},
    {"id": "t-graph-theory", "label": "Graph theory / colouring / Hamiltonian cycles", "kind": "topic", "org": "", "date": "", "url": "", "field": "combinatorics", "verified": "", "summary": ""},
    {"id": "t-discrete-convex-geometry", "label": "Discrete & convex geometry", "kind": "topic", "org": "", "date": "", "url": "", "field": "geometry", "verified": "", "summary": "unit distances, Mahler, Ehrhart, sphere packing"},
    {"id": "t-analytic-number-theory", "label": "Analytic number theory (zeta, L-functions)", "kind": "topic", "org": "", "date": "", "url": "", "field": "number theory", "verified": "", "summary": ""},
    {"id": "t-algebraic-geometry", "label": "Algebraic geometry / Hodge / Diophantine", "kind": "topic", "org": "", "date": "", "url": "", "field": "number theory", "verified": "", "summary": ""},
    {"id": "t-operator-algebras-groups", "label": "Operator algebras & group theory", "kind": "topic", "org": "", "date": "", "url": "", "field": "algebra", "verified": "", "summary": ""},
    {"id": "t-tcs", "label": "Theoretical CS / complexity / lattices", "kind": "topic", "org": "", "date": "", "url": "", "field": "TCS", "verified": "", "summary": ""},
    {"id": "t-quantum-info", "label": "Quantum information & quantum computing", "kind": "topic", "org": "", "date": "", "url": "", "field": "physics/TCS", "verified": "", "summary": ""},
    {"id": "t-cryptography", "label": "Cryptography", "kind": "topic", "org": "", "date": "", "url": "", "field": "TCS", "verified": "", "summary": ""},
    {"id": "t-amplitudes", "label": "QFT / scattering amplitudes / Feynman integrals", "kind": "topic", "org": "", "date": "", "url": "", "field": "physics", "verified": "", "summary": ""},
    {"id": "t-qcd-resummation", "label": "QCD resummation / SCET", "kind": "topic", "org": "", "date": "", "url": "", "field": "physics", "verified": "", "summary": ""},
    {"id": "t-gr-cosmology", "label": "General relativity & cosmology", "kind": "topic", "org": "", "date": "", "url": "", "field": "physics", "verified": "", "summary": ""},
    {"id": "t-plasma", "label": "Plasma / fusion modelling", "kind": "topic", "org": "", "date": "", "url": "", "field": "physics", "verified": "", "summary": ""},
    {"id": "t-fluid-pde", "label": "Fluid PDE: Navier-Stokes / Euler blow-up", "kind": "topic", "org": "", "date": "", "url": "", "field": "PDE", "verified": "", "summary": ""},
    {"id": "t-kinetic-statmech", "label": "Kinetic PDE & statistical mechanics", "kind": "topic", "org": "", "date": "", "url": "", "field": "mathematical physics", "verified": "", "summary": "Vlasov-Maxwell, Heisenberg ferromagnet, spin glasses"},
    {"id": "t-spectral-theory", "label": "Spectral theory / eigenvalue problems", "kind": "topic", "org": "", "date": "", "url": "", "field": "analysis", "verified": "", "summary": "Laplacian & Hodge Laplacian spectra, Neumann eigenfunctions"},
    {"id": "t-inverse-spectral", "label": "Inverse spectral problems", "kind": "topic", "org": "", "date": "", "url": "", "field": "analysis", "verified": "", "summary": "spectrum determines metric/shape; overdetermined boundary problems"},
    {"id": "t-wave-helmholtz", "label": "Wave / Helmholtz equations", "kind": "topic", "org": "", "date": "", "url": "", "field": "PDE", "verified": "", "summary": ""},
    {"id": "t-rigorous-numerics-lean", "label": "Rigorous numerics & Lean formalization", "kind": "topic", "org": "", "date": "", "url": "", "field": "foundations", "verified": "", "summary": ""},
    {"id": "t-optimization-algorithms", "label": "Convex optimization & online algorithms", "kind": "topic", "org": "", "date": "", "url": "", "field": "optimization", "verified": "", "summary": ""},
    {"id": "t-probability-statistics", "label": "Probability, random walks, statistics", "kind": "topic", "org": "", "date": "", "url": "", "field": "probability", "verified": "", "summary": ""},
    {"id": "t-biology", "label": "Biology / ecology / genetics", "kind": "topic", "org": "", "date": "", "url": "", "field": "biology", "verified": "", "summary": ""},
    {"id": "t-benchmarks", "label": "Benchmarks & evaluation", "kind": "topic", "org": "", "date": "", "url": "", "field": "meta", "verified": "", "summary": ""},
    {"id": "t-research-practice", "label": "Research practice, verification norms, disputes", "kind": "topic", "org": "", "date": "", "url": "", "field": "meta", "verified": "", "summary": ""},
    {"id": "exp-copper-sphere", "label": "EXPERIMENT: copper-sphere vibration spectrum (elastic eigenvalues, inverse spectral, measurement design)", "kind": "topic", "org": "", "date": "", "url": "", "field": "elasticity / spectral theory", "verified": "", "summary": "Design target: complete modal spectrum of an elastic sphere; inverse eigenvalue recovery; UQ"},

    {"id": "oai-bubeck-convex-opt", "label": "GPT-5 Pro step-size bound 1.5/L", "kind": "paper", "org": "OpenAI", "date": "2025-08", "url": "https://allthings.how/what-does-gpt-5s-new-math-claim-actually-mean/", "field": "convex optimization", "verified": "self-reported; superseded by human 1.75/L", "summary": "GPT-5 Pro improved a gradient-descent step-size bound from 1/L to 1.5/L; humans already had 1.75/L"},
    {"id": "oai-aaronson-qma", "label": "Limits to black-box amplification in QMA", "kind": "paper", "org": "other", "date": "2025-09", "url": "https://arxiv.org/abs/2509.21131", "field": "quantum complexity", "verified": "self-reported (key step from GPT-5)", "summary": "GPT-5-Thinking suggested resolvent-trace function controlling top eigenvalue of E(theta)"},
    {"id": "oai-erdos-overclaim-oct2025", "label": "Oct-2025 Erdős overclaim (retracted)", "kind": "paper", "org": "OpenAI", "date": "2025-10", "url": "https://the-decoder.com/leading-openai-researcher-announced-a-gpt-5-math-breakthrough-that-never-happened/", "field": "combinatorics (literature search)", "verified": "disputed/retracted", "summary": "'GPT-5 solved 10 Erdős problems' was literature search; Bloom: 'dramatic misinterpretation'; Hassabis: 'embarrassing'"},
    {"id": "oai-science-acceleration-gpt5", "label": "Early science acceleration experiments with GPT-5", "kind": "paper", "org": "OpenAI", "date": "2025-11", "url": "https://arxiv.org/abs/2511.16072", "field": "multi-field", "verified": "self-reported; 4 math results human-verified", "summary": "Case studies: Erdős #848, Kerr SL(2,R) symmetry, convex body chasing, tree inequalities, immunology, fusion"},
    {"id": "oai-frontierscience", "label": "FrontierScience benchmark", "kind": "paper", "org": "OpenAI", "date": "2025-12", "url": "https://openai.com/index/frontierscience", "field": "physics/chem/bio evals", "verified": "self-reported eval", "summary": "Olympiad + Research tracks; GPT-5.2 77%/25%"},
    {"id": "oai-erdos-728-gpt52pro", "label": "Erdős #728 via GPT-5.2 Pro", "kind": "paper", "org": "OpenAI", "date": "2026-01", "url": "https://www.quantamagazine.org/why-the-legendary-erdos-problems-are-falling-to-ai-20260803/", "field": "combinatorics", "verified": "Lean-verified via Aristotle", "summary": "Barreto & Price with GPT-5.2 Pro; Tao: 'more or less autonomously'; #333 was a 1977 rediscovery"},
    {"id": "oai-gluon-single-minus", "label": "Single-minus gluon tree amplitudes are nonzero", "kind": "paper", "org": "OpenAI", "date": "2026-02", "url": "https://arxiv.org/abs/2602.12176", "field": "QFT/amplitudes", "verified": "author-verified; preprint", "summary": "GPT-5.2 Pro conjectured all-n half-collinear formula; scaffolded GPT-5.2 gave formal proof"},
    {"id": "oai-first-proof", "label": "First Proof submissions", "kind": "paper", "org": "OpenAI", "date": "2026-02", "url": "https://openai.com/index/first-proof-submissions/", "field": "research mathematics", "verified": "self-reported; contested", "summary": "Internal model: 5 of 10 likely correct; one withdrawn"},
    {"id": "oai-graviton-single-minus", "label": "Single-minus graviton tree amplitudes are nonzero", "kind": "paper", "org": "OpenAI", "date": "2026-03", "url": "https://openai.com/index/extending-single-minus-amplitudes-to-gravitons/", "field": "QFT/gravity amplitudes", "verified": "author-verified; preprint", "summary": "GPT-5.2 Pro extended gluon result to gravitons; w(1+infinity) symmetry"},
    {"id": "oai-unit-distance-disproof", "label": "Erdős unit-distance conjecture disproved", "kind": "paper", "org": "OpenAI", "date": "2026-05", "url": "https://openai.com/index/model-disproves-discrete-geometry-conjecture/", "field": "discrete geometry", "verified": "independently verified (Gowers et al.)", "summary": "n^(1+delta) unit distances via algebraic number theory; Sawin delta=0.014"},
    {"id": "oai-ten-advances", "label": "Ten advances in mathematics and TCS", "kind": "paper", "org": "OpenAI", "date": "2026-08", "url": "https://openai.com/index/ten-advances-in-mathematics/", "field": "sphere packing, codes, groups, operator algebras, complexity, Ramsey", "verified": "Lean-verified (self)", "summary": "Astra internal: Cohn-Elkies sphere packing, Connes rigidity disproof, non-sofic groups, Erdős 146/180/183"},
    {"id": "oai-navier-stokes-euler", "label": "Navier-Stokes & Euler blow-up (OpenAI)", "kind": "paper", "org": "OpenAI", "date": "2026-09", "url": "https://openai.com/index/navier-stokes-solution/", "field": "fluid PDE", "verified": "Lean-verified (self); priority disputed", "summary": "Forced NS finite-time singularity by ~10,000 agents; unforced Euler; dispute with Alpöge-Buckmaster"},
    {"id": "oai-agmai-advisory", "label": "Advisory Group on Mathematics and AI", "kind": "paper", "org": "OpenAI", "date": "2026-09", "url": "https://openai.com/index/advisory-group-on-mathematics-and-ai/", "field": "research practice", "verified": "n/a", "summary": "Gowers, Hairer, Witten, Wood et al. at IAS advise on dissemination"},
    {"id": "oai-722-release", "label": "722-manuscript bulk release (openai/math)", "kind": "paper", "org": "OpenAI", "date": "2026-10", "url": "https://github.com/openai/math", "field": "17 disciplines", "verified": "~22% Lean-verified; 3 retracted; rest self-reported", "summary": "372 families; 16 PDE, 25 math-phys families; Fields medalist declaration; Simons $5M"},
    {"id": "oai-quasi-riemann", "label": "Quasi-Riemann Hypothesis / Landau-Siegel exclusion", "kind": "paper", "org": "OpenAI", "date": "2026-10", "url": "https://github.com/openai/math/blob/main/preprints/The-Quasi-Riemann-Hypothesis-September-30-2026/paper.pdf", "field": "analytic number theory", "verified": "Lean-verified (per catalogue)", "summary": "Zero-free region Re(s) > 7/8 for all Dirichlet L-functions"},
    {"id": "oai-hadwiger-counterexample", "label": "Counterexample to Hadwiger's conjecture", "kind": "paper", "org": "OpenAI", "date": "2026-10", "url": "https://hub.valency.io/works/W_2a49kety", "field": "graph theory", "verified": "Lean-verified (self)", "summary": "Graphs with alpha<=2 and chromatic number > Hadwiger number"},
    {"id": "oai-integer-multiplication", "label": "Integer multiplication below n log n", "kind": "paper", "org": "OpenAI", "date": "2026-10", "url": "https://github.com/openai/math/blob/main/preprints/Integer-multiplication-below-n-log-n-September-23-2026/paper.pdf", "field": "algorithms", "verified": "unverified", "summary": "Would refute Schönhage-Strassen conjecture; huge constants"},
    {"id": "oai-mahler-conjectures", "label": "Symmetric & general Mahler conjectures", "kind": "paper", "org": "OpenAI", "date": "2026-10", "url": "https://github.com/openai/math/blob/main/reasoning_traces/symmetric-and-general-mahler-conjectures.pdf", "field": "convex geometry", "verified": "partially Lean-verified", "summary": "Volume-product conjectures in all dimensions"},
    {"id": "oai-vlasov-maxwell", "label": "3D relativistic Vlasov-Maxwell", "kind": "paper", "org": "OpenAI", "date": "2026-10", "url": "https://github.com/openai/math/blob/main/reasoning_traces/relativistic-vlasov-maxwell.pdf", "field": "kinetic PDE", "verified": "unverified", "summary": "One of ten traced results; PDE family of the dump"},
    {"id": "oai-heisenberg-ferromagnet", "label": "Quantum Heisenberg ferromagnet & Mézard-Parisi", "kind": "paper", "org": "OpenAI", "date": "2026-10", "url": "https://github.com/openai/math/blob/main/reasoning_traces/spontaneous-magnetization-quantum-heisenberg-ferromagnet.pdf", "field": "statistical mechanics", "verified": "unverified", "summary": "Claimed proofs of long-range order and diluted spin-glass free energy"},
    {"id": "epoch-frontiermath", "label": "FrontierMath (Tier 4)", "kind": "paper", "org": "Epoch AI", "date": "2026-06", "url": "https://epoch.ai/benchmarks/frontiermath-tier-4-v1/", "field": "math benchmark", "verified": "third-party eval; OpenAI funding/access caveat", "summary": "350 problems; Gemini 3 Pro 19% Tier 4; grader fixes Jan 2026"},
    {"id": "horizonmath", "label": "HorizonMath", "kind": "paper", "org": "other", "date": "2026-03", "url": "https://arxiv.org/abs/2603.15617", "field": "math discovery benchmark", "verified": "auto-verified; ICML AI4Math best paper", "summary": "113 open problems; 6 novel solutions by GPT-5.4 Pro and GPT-5.6 Sol"},
    {"id": "tao-erdos-ai-wiki", "label": "AI contributions to Erdős problems (Tao wiki)", "kind": "paper", "org": "other", "date": "2026-06", "url": "https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems", "field": "combinatorics/number theory", "verified": "per-entry; many Lean", "summary": "Catalogue of AI Erdős results across GPT-5.x, Claude Mythos/Fable, Aletheia, AlphaProof"},
    {"id": "anth-ai-for-science-program", "label": "Anthropic AI for Science program", "kind": "paper", "org": "Anthropic", "date": "2025-05", "url": "https://www.anthropic.com/news/ai-for-science-program", "field": "life sciences", "verified": "n/a", "summary": "API credits for researchers"},
    {"id": "anth-vibe-physics", "label": "C-parameter Sudakov shoulder resummation (vibe physics)", "kind": "paper", "org": "Anthropic", "date": "2026-01", "url": "https://arxiv.org/abs/2601.02484", "field": "QCD/SCET", "verified": "self-validated by author; not peer-reviewed", "summary": "Claude Opus 4.5 did all calculations over two weeks under Schwartz's supervision"},
    {"id": "anth-field-notes-feb2026", "label": "Anthropic field notes, Feb 2026", "kind": "paper", "org": "Anthropic", "date": "2026-02", "url": "https://www.anthropic.com/research/roundup-feb-2026", "field": "meta", "verified": "n/a", "summary": "Cites OpenAI gluon result, First Proof, SAIR, Genesis Mission"},
    {"id": "knuth-claude-cycles", "label": "Claude's Cycles (Knuth)", "kind": "paper", "org": "other", "date": "2026-02", "url": "https://cs.stanford.edu/~knuth/papers/claude-cycles.pdf", "field": "combinatorics", "verified": "Lean-verified (odd m)", "summary": "Claude Opus 4.6 decomposed m^3 digraph into 3 Hamiltonian cycles"},
    {"id": "numina-lean-agent", "label": "Numina-Lean-Agent", "kind": "paper", "org": "other", "date": "2026-01", "url": "https://arxiv.org/abs/2601.14027", "field": "formal mathematics", "verified": "Lean-verified", "summary": "Claude Opus 4.5 + Claude Code solved all Putnam 2025 in Lean"},
    {"id": "anth-science-blog", "label": "Anthropic Science blog launch", "kind": "paper", "org": "Anthropic", "date": "2026-03", "url": "https://www.anthropic.com/research/introducing-anthropic-science", "field": "meta", "verified": "n/a", "summary": "Collection page linking physics, math, bio posts"},
    {"id": "anth-riemann-zeta", "label": "Claude: 67.2% of zeta zeros on the critical line", "kind": "paper", "org": "Anthropic", "date": "2026-08", "url": "https://www.anthropic.com/research/riemann-zeta", "field": "analytic number theory", "verified": "Lean-verified; internal validation", "summary": "Raised Montgomery-type lower bound from 41.6% to 67.2%"},
    {"id": "alpoge-buckmaster-forced-blowup", "label": "Forced blow-up: IPM, Boussinesq, Euler (Alpöge-Buckmaster)", "kind": "paper", "org": "other", "date": "2026-09", "url": "https://cims.nyu.edu/~tristanb/statement.pdf", "field": "fluid PDE", "verified": "Lean-verified; exposition & priority disputed", "summary": "Claude + Codex extended Córdoba-Martínez-Zoroa to smooth forcing and 3D Euler"},
    {"id": "anth-nine-loops", "label": "Nine-loop N=4 SYM hexagon amplitude", "kind": "paper", "org": "Anthropic", "date": "2026-09", "url": "https://www.anthropic.com/research/yes-claude-can-do-nine-loops", "field": "scattering amplitudes", "verified": "independently verified (Dixon)", "summary": "Claude Fable 5.1 in Claude Science bootstrapped nine loops unsupervised"},
    {"id": "anth-claude-shaped-science", "label": "Claude-shaped science (BootLoops)", "kind": "paper", "org": "Anthropic", "date": "2026-10", "url": "https://www.anthropic.com/research/claude-shaped-science", "field": "multi-field", "verified": "mostly under verification", "summary": "36 manuscripts in 18 fields: Feynman integrals, random walks, cosmology, ecology, pop-gen"},
    {"id": "anth-quantum-circuits", "label": "Efficient quantum circuits with Claude", "kind": "paper", "org": "Anthropic", "date": "2026-10", "url": "https://arxiv.org/abs/2610.22367", "field": "quantum computing", "verified": "evaluator-verified; Lean identities", "summary": "Claude Mythos 5: 17x fewer gates for ECC point addition; 12x for DQI decoder"},
    {"id": "anth-ecdsa-origins", "label": "ECDSA curve seed origins", "kind": "paper", "org": "Anthropic", "date": "2026-10", "url": "https://www.anthropic.com/research/ecdsa-curve-origins", "field": "cryptography", "verified": "reproducible code", "summary": "NIST seeds are lrand48 outputs seeded by 1997-98 timestamps; LLL recovery"},
    {"id": "gdm-alphaevolve", "label": "AlphaEvolve (blog)", "kind": "paper", "org": "Google DeepMind", "date": "2025-05", "url": "https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/", "field": "optimization/combinatorics", "verified": "self-reported; checkable constructions", "summary": "Gemini evolutionary coding agent; improved open constructions"},
    {"id": "gdm-imo-gold", "label": "Gemini Deep Think IMO gold", "kind": "paper", "org": "Google DeepMind", "date": "2025-07", "url": "https://deepmind.google/blog/advanced-version-of-gemini-with-deep-think-officially-achieves-gold-medal-standard-at-the-international-mathematical-olympiad/", "field": "olympiad math", "verified": "IMO-graded", "summary": "35/42 official gold standard"},
    {"id": "gdm-alphaevolve-tao", "label": "Mathematical exploration and discovery at scale", "kind": "paper", "org": "Google DeepMind", "date": "2025-11", "url": "https://arxiv.org/abs/2511.02864", "field": "analysis/combinatorics/geometry/number theory", "verified": "self-reported", "summary": "AlphaEvolve on 67 problems with Tao, Gómez-Serrano, Wagner"},
    {"id": "gdm-gemini-erdos", "label": "Semi-autonomous discovery with Gemini (Erdős)", "kind": "paper", "org": "Google DeepMind", "date": "2026-01", "url": "https://arxiv.org/abs/2601.22401", "field": "combinatorics/number theory", "verified": "partially verified", "summary": "700 open conjectures; 5 novel + 8 literature"},
    {"id": "gdm-aletheia", "label": "Towards Autonomous Mathematics Research (Aletheia)", "kind": "paper", "org": "Google DeepMind", "date": "2026-02", "url": "https://arxiv.org/abs/2602.10177", "field": "combinatorics/algebra", "verified": "self-reported; some Lean", "summary": "Autonomous eigenweights paper; 4 Erdős problems; autonomy levels"},
    {"id": "hodge-laplacian-3spheres", "label": "Hodge Laplacian on 1-forms of homogeneous 3-spheres", "kind": "paper", "org": "other", "date": "2026-05", "url": "https://arxiv.org/abs/2605.05406", "field": "spectral geometry", "verified": "self-reported; AI-found formal proof", "summary": "Full Berger-sphere 1-form spectrum; spectrum determines metric up to isometry"},
    {"id": "schiffer-colbrook-stepaniants", "label": "Computer-assisted counterexample to Pompeiu & Schiffer", "kind": "paper", "org": "other", "date": "2026-08", "url": "https://arxiv.org/abs/2608.01579", "field": "spectral theory / rigorous numerics", "verified": "rigorous certificate; not peer-reviewed", "summary": "Non-circular planar domain with boundary-constant Neumann eigenfunction; GPT-5.5 Codex debugging aid"},
    {"id": "schiffer-caolabora-dediospont", "label": "Counterexamples to Schiffer's conjecture", "kind": "paper", "org": "other", "date": "2026-08", "url": "https://arxiv.org/abs/2608.05114", "field": "spectral theory / bifurcation", "verified": "Lean check claimed; not peer-reviewed", "summary": "Infinitely many N-fold symmetric counterexamples; GPT-5.5/5.6 & Claude as tools"}
  ],
  "edges": [
    {"source": "oai-bubeck-convex-opt", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-bubeck-convex-opt", "target": "m-gpt5-pro", "rel": "produced_by"},
    {"source": "oai-bubeck-convex-opt", "target": "t-optimization-algorithms", "rel": "about"},
    {"source": "oai-bubeck-convex-opt", "target": "t-research-practice", "rel": "about"},

    {"source": "oai-aaronson-qma", "target": "org-academia", "rel": "authored_by"},
    {"source": "oai-aaronson-qma", "target": "m-gpt5", "rel": "produced_by"},
    {"source": "oai-aaronson-qma", "target": "t-quantum-info", "rel": "about"},
    {"source": "oai-aaronson-qma", "target": "t-tcs", "rel": "about"},
    {"source": "oai-aaronson-qma", "target": "t-spectral-theory", "rel": "about"},
    {"source": "oai-aaronson-qma", "target": "exp-copper-sphere", "rel": "adjacent_to_experiment"},

    {"source": "oai-erdos-overclaim-oct2025", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-erdos-overclaim-oct2025", "target": "m-gpt5", "rel": "produced_by"},
    {"source": "oai-erdos-overclaim-oct2025", "target": "t-erdos-combinatorics", "rel": "about"},
    {"source": "oai-erdos-overclaim-oct2025", "target": "t-research-practice", "rel": "about"},
    {"source": "tao-erdos-ai-wiki", "target": "oai-erdos-overclaim-oct2025", "rel": "cites"},

    {"source": "oai-science-acceleration-gpt5", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-science-acceleration-gpt5", "target": "m-gpt5", "rel": "produced_by"},
    {"source": "oai-science-acceleration-gpt5", "target": "m-gpt5-pro", "rel": "produced_by"},
    {"source": "oai-science-acceleration-gpt5", "target": "t-erdos-combinatorics", "rel": "about"},
    {"source": "oai-science-acceleration-gpt5", "target": "t-graph-theory", "rel": "about"},
    {"source": "oai-science-acceleration-gpt5", "target": "t-gr-cosmology", "rel": "about"},
    {"source": "oai-science-acceleration-gpt5", "target": "t-plasma", "rel": "about"},
    {"source": "oai-science-acceleration-gpt5", "target": "t-optimization-algorithms", "rel": "about"},
    {"source": "oai-science-acceleration-gpt5", "target": "t-probability-statistics", "rel": "about"},
    {"source": "oai-science-acceleration-gpt5", "target": "t-biology", "rel": "about"},
    {"source": "oai-science-acceleration-gpt5", "target": "t-wave-helmholtz", "rel": "about"},
    {"source": "oai-science-acceleration-gpt5", "target": "exp-copper-sphere", "rel": "adjacent_to_experiment"},
    {"source": "oai-frontierscience", "target": "oai-science-acceleration-gpt5", "rel": "cites"},
    {"source": "oai-first-proof", "target": "oai-science-acceleration-gpt5", "rel": "cites"},

    {"source": "oai-frontierscience", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-frontierscience", "target": "m-gpt52-pro", "rel": "produced_by"},
    {"source": "oai-frontierscience", "target": "m-gemini-deep-think", "rel": "produced_by"},
    {"source": "oai-frontierscience", "target": "m-claude-opus-45", "rel": "produced_by"},
    {"source": "oai-frontierscience", "target": "t-benchmarks", "rel": "about"},
    {"source": "oai-frontierscience", "target": "t-biology", "rel": "about"},

    {"source": "oai-erdos-728-gpt52pro", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-erdos-728-gpt52pro", "target": "org-academia", "rel": "authored_by"},
    {"source": "oai-erdos-728-gpt52pro", "target": "m-gpt52-pro", "rel": "produced_by"},
    {"source": "oai-erdos-728-gpt52pro", "target": "m-aristotle", "rel": "produced_by"},
    {"source": "oai-erdos-728-gpt52pro", "target": "t-erdos-combinatorics", "rel": "about"},
    {"source": "oai-erdos-728-gpt52pro", "target": "t-rigorous-numerics-lean", "rel": "about"},
    {"source": "tao-erdos-ai-wiki", "target": "oai-erdos-728-gpt52pro", "rel": "cites"},

    {"source": "oai-gluon-single-minus", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-gluon-single-minus", "target": "m-gpt52-pro", "rel": "produced_by"},
    {"source": "oai-gluon-single-minus", "target": "t-amplitudes", "rel": "about"},
    {"source": "anth-field-notes-feb2026", "target": "oai-gluon-single-minus", "rel": "cites"},
    {"source": "anth-vibe-physics", "target": "oai-gluon-single-minus", "rel": "cites"},
    {"source": "oai-first-proof", "target": "oai-gluon-single-minus", "rel": "cites"},

    {"source": "oai-first-proof", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-first-proof", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "oai-first-proof", "target": "t-benchmarks", "rel": "about"},
    {"source": "oai-first-proof", "target": "t-research-practice", "rel": "about"},
    {"source": "anth-field-notes-feb2026", "target": "oai-first-proof", "rel": "cites"},
    {"source": "gdm-aletheia", "target": "oai-first-proof", "rel": "cites"},

    {"source": "oai-graviton-single-minus", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-graviton-single-minus", "target": "m-gpt52-pro", "rel": "produced_by"},
    {"source": "oai-graviton-single-minus", "target": "t-amplitudes", "rel": "about"},
    {"source": "oai-graviton-single-minus", "target": "t-gr-cosmology", "rel": "about"},
    {"source": "oai-graviton-single-minus", "target": "oai-gluon-single-minus", "rel": "cites"},
    {"source": "anth-vibe-physics", "target": "oai-graviton-single-minus", "rel": "cites"},

    {"source": "oai-unit-distance-disproof", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-unit-distance-disproof", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "oai-unit-distance-disproof", "target": "t-discrete-convex-geometry", "rel": "about"},
    {"source": "oai-unit-distance-disproof", "target": "t-erdos-combinatorics", "rel": "about"},
    {"source": "oai-unit-distance-disproof", "target": "t-analytic-number-theory", "rel": "about"},
    {"source": "oai-ten-advances", "target": "oai-unit-distance-disproof", "rel": "cites"},
    {"source": "anth-claude-shaped-science", "target": "oai-unit-distance-disproof", "rel": "cites"},
    {"source": "tao-erdos-ai-wiki", "target": "oai-unit-distance-disproof", "rel": "cites"},

    {"source": "oai-ten-advances", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-ten-advances", "target": "m-astra", "rel": "produced_by"},
    {"source": "oai-ten-advances", "target": "t-discrete-convex-geometry", "rel": "about"},
    {"source": "oai-ten-advances", "target": "t-operator-algebras-groups", "rel": "about"},
    {"source": "oai-ten-advances", "target": "t-tcs", "rel": "about"},
    {"source": "oai-ten-advances", "target": "t-quantum-info", "rel": "about"},
    {"source": "oai-ten-advances", "target": "t-erdos-combinatorics", "rel": "about"},
    {"source": "oai-ten-advances", "target": "t-rigorous-numerics-lean", "rel": "about"},

    {"source": "oai-navier-stokes-euler", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-navier-stokes-euler", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "oai-navier-stokes-euler", "target": "m-astra", "rel": "produced_by"},
    {"source": "oai-navier-stokes-euler", "target": "t-fluid-pde", "rel": "about"},
    {"source": "oai-navier-stokes-euler", "target": "t-rigorous-numerics-lean", "rel": "about"},
    {"source": "oai-navier-stokes-euler", "target": "t-research-practice", "rel": "about"},
    {"source": "oai-navier-stokes-euler", "target": "alpoge-buckmaster-forced-blowup", "rel": "cites"},
    {"source": "oai-navier-stokes-euler", "target": "exp-copper-sphere", "rel": "adjacent_to_experiment"},
    {"source": "oai-agmai-advisory", "target": "oai-navier-stokes-euler", "rel": "cites"},
    {"source": "oai-722-release", "target": "oai-navier-stokes-euler", "rel": "cites"},
    {"source": "anth-nine-loops", "target": "oai-navier-stokes-euler", "rel": "cites"},

    {"source": "oai-agmai-advisory", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-agmai-advisory", "target": "t-research-practice", "rel": "about"},
    {"source": "oai-722-release", "target": "oai-agmai-advisory", "rel": "cites"},

    {"source": "oai-722-release", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-722-release", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "oai-722-release", "target": "t-tcs", "rel": "about"},
    {"source": "oai-722-release", "target": "t-erdos-combinatorics", "rel": "about"},
    {"source": "oai-722-release", "target": "t-algebraic-geometry", "rel": "about"},
    {"source": "oai-722-release", "target": "t-analytic-number-theory", "rel": "about"},
    {"source": "oai-722-release", "target": "t-kinetic-statmech", "rel": "about"},
    {"source": "oai-722-release", "target": "t-operator-algebras-groups", "rel": "about"},
    {"source": "oai-722-release", "target": "t-fluid-pde", "rel": "about"},
    {"source": "oai-722-release", "target": "t-discrete-convex-geometry", "rel": "about"},
    {"source": "oai-722-release", "target": "t-probability-statistics", "rel": "about"},
    {"source": "oai-722-release", "target": "t-rigorous-numerics-lean", "rel": "about"},
    {"source": "oai-722-release", "target": "t-research-practice", "rel": "about"},
    {"source": "oai-722-release", "target": "oai-ten-advances", "rel": "cites"},

    {"source": "oai-quasi-riemann", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-quasi-riemann", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "oai-quasi-riemann", "target": "t-analytic-number-theory", "rel": "about"},
    {"source": "oai-722-release", "target": "oai-quasi-riemann", "rel": "cites"},

    {"source": "oai-hadwiger-counterexample", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-hadwiger-counterexample", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "oai-hadwiger-counterexample", "target": "t-graph-theory", "rel": "about"},
    {"source": "oai-722-release", "target": "oai-hadwiger-counterexample", "rel": "cites"},

    {"source": "oai-integer-multiplication", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-integer-multiplication", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "oai-integer-multiplication", "target": "t-tcs", "rel": "about"},
    {"source": "oai-722-release", "target": "oai-integer-multiplication", "rel": "cites"},

    {"source": "oai-mahler-conjectures", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-mahler-conjectures", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "oai-mahler-conjectures", "target": "t-discrete-convex-geometry", "rel": "about"},
    {"source": "oai-722-release", "target": "oai-mahler-conjectures", "rel": "cites"},

    {"source": "oai-vlasov-maxwell", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-vlasov-maxwell", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "oai-vlasov-maxwell", "target": "t-kinetic-statmech", "rel": "about"},
    {"source": "oai-vlasov-maxwell", "target": "t-fluid-pde", "rel": "about"},
    {"source": "oai-722-release", "target": "oai-vlasov-maxwell", "rel": "cites"},

    {"source": "oai-heisenberg-ferromagnet", "target": "org-openai", "rel": "authored_by"},
    {"source": "oai-heisenberg-ferromagnet", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "oai-heisenberg-ferromagnet", "target": "t-kinetic-statmech", "rel": "about"},
    {"source": "oai-722-release", "target": "oai-heisenberg-ferromagnet", "rel": "cites"},

    {"source": "epoch-frontiermath", "target": "org-epoch", "rel": "authored_by"},
    {"source": "epoch-frontiermath", "target": "org-openai", "rel": "authored_by"},
    {"source": "epoch-frontiermath", "target": "m-gpt52-pro", "rel": "produced_by"},
    {"source": "epoch-frontiermath", "target": "m-gemini-deep-think", "rel": "produced_by"},
    {"source": "epoch-frontiermath", "target": "t-benchmarks", "rel": "about"},

    {"source": "horizonmath", "target": "org-academia", "rel": "authored_by"},
    {"source": "horizonmath", "target": "m-gpt54-pro", "rel": "produced_by"},
    {"source": "horizonmath", "target": "m-gpt56-sol", "rel": "produced_by"},
    {"source": "horizonmath", "target": "t-benchmarks", "rel": "about"},
    {"source": "horizonmath", "target": "t-erdos-combinatorics", "rel": "about"},

    {"source": "tao-erdos-ai-wiki", "target": "org-academia", "rel": "authored_by"},
    {"source": "tao-erdos-ai-wiki", "target": "m-gpt52-pro", "rel": "produced_by"},
    {"source": "tao-erdos-ai-wiki", "target": "m-gpt54-pro", "rel": "produced_by"},
    {"source": "tao-erdos-ai-wiki", "target": "m-gpt55", "rel": "produced_by"},
    {"source": "tao-erdos-ai-wiki", "target": "m-oai-internal", "rel": "produced_by"},
    {"source": "tao-erdos-ai-wiki", "target": "m-claude-mythos", "rel": "produced_by"},
    {"source": "tao-erdos-ai-wiki", "target": "m-claude-fable-5", "rel": "produced_by"},
    {"source": "tao-erdos-ai-wiki", "target": "m-aletheia", "rel": "produced_by"},
    {"source": "tao-erdos-ai-wiki", "target": "m-alphaevolve", "rel": "produced_by"},
    {"source": "tao-erdos-ai-wiki", "target": "m-aristotle", "rel": "produced_by"},
    {"source": "tao-erdos-ai-wiki", "target": "t-erdos-combinatorics", "rel": "about"},
    {"source": "tao-erdos-ai-wiki", "target": "t-research-practice", "rel": "about"},
    {"source": "tao-erdos-ai-wiki", "target": "gdm-alphaevolve-tao", "rel": "cites"},
    {"source": "tao-erdos-ai-wiki", "target": "gdm-gemini-erdos", "rel": "cites"},
    {"source": "tao-erdos-ai-wiki", "target": "gdm-aletheia", "rel": "cites"},

    {"source": "anth-ai-for-science-program", "target": "org-anthropic", "rel": "authored_by"},
    {"source": "anth-ai-for-science-program", "target": "t-biology", "rel": "about"},

    {"source": "anth-vibe-physics", "target": "org-anthropic", "rel": "authored_by"},
    {"source": "anth-vibe-physics", "target": "org-academia", "rel": "authored_by"},
    {"source": "anth-vibe-physics", "target": "m-claude-opus-45", "rel": "produced_by"},
    {"source": "anth-vibe-physics", "target": "m-gpt52-pro", "rel": "produced_by"},
    {"source": "anth-vibe-physics", "target": "m-gemini-deep-think", "rel": "produced_by"},
    {"source": "anth-vibe-physics", "target": "t-qcd-resummation", "rel": "about"},
    {"source": "anth-vibe-physics", "target": "t-research-practice", "rel": "about"},
    {"source": "anth-vibe-physics", "target": "gdm-alphaevolve", "rel": "cites"},
    {"source": "anth-vibe-physics", "target": "gdm-imo-gold", "rel": "cites"},
    {"source": "anth-vibe-physics", "target": "numina-lean-agent", "rel": "cites"},
    {"source": "anth-science-blog", "target": "anth-vibe-physics", "rel": "cites"},
    {"source": "anth-claude-shaped-science", "target": "anth-vibe-physics", "rel": "cites"},
    {"source": "anth-nine-loops", "target": "anth-vibe-physics", "rel": "cites"},

    {"source": "anth-field-notes-feb2026", "target": "org-anthropic", "rel": "authored_by"},
    {"source": "anth-field-notes-feb2026", "target": "t-research-practice", "rel": "about"},
    {"source": "anth-field-notes-feb2026", "target": "t-amplitudes", "rel": "about"},

    {"source": "knuth-claude-cycles", "target": "org-academia", "rel": "authored_by"},
    {"source": "knuth-claude-cycles", "target": "m-claude-opus-46", "rel": "produced_by"},
    {"source": "knuth-claude-cycles", "target": "m-gpt54-pro", "rel": "produced_by"},
    {"source": "knuth-claude-cycles", "target": "t-graph-theory", "rel": "about"},
    {"source": "knuth-claude-cycles", "target": "t-rigorous-numerics-lean", "rel": "about"},
    {"source": "anth-science-blog", "target": "knuth-claude-cycles", "rel": "cites"},

    {"source": "numina-lean-agent", "target": "org-academia", "rel": "authored_by"},
    {"source": "numina-lean-agent", "target": "m-claude-opus-45", "rel": "produced_by"},
    {"source": "numina-lean-agent", "target": "t-rigorous-numerics-lean", "rel": "about"},

    {"source": "anth-science-blog", "target": "org-anthropic", "rel": "authored_by"},
    {"source": "anth-science-blog", "target": "t-research-practice", "rel": "about"},
    {"source": "anth-science-blog", "target": "t-biology", "rel": "about"},
    {"source": "anth-science-blog", "target": "anth-ai-for-science-program", "rel": "cites"},

    {"source": "anth-riemann-zeta", "target": "org-anthropic", "rel": "authored_by"},
    {"source": "anth-riemann-zeta", "target": "m-claude-internal", "rel": "produced_by"},
    {"source": "anth-riemann-zeta", "target": "t-analytic-number-theory", "rel": "about"},
    {"source": "anth-riemann-zeta", "target": "t-rigorous-numerics-lean", "rel": "about"},
    {"source": "anth-claude-shaped-science", "target": "anth-riemann-zeta", "rel": "cites"},
    {"source": "anth-nine-loops", "target": "anth-riemann-zeta", "rel": "cites"},

    {"source": "alpoge-buckmaster-forced-blowup", "target": "org-academia", "rel": "authored_by"},
    {"source": "alpoge-buckmaster-forced-blowup", "target": "org-anthropic", "rel": "authored_by"},
    {"source": "alpoge-buckmaster-forced-blowup", "target": "m-claude-internal", "rel": "produced_by"},
    {"source": "alpoge-buckmaster-forced-blowup", "target": "m-gpt56-sol", "rel": "produced_by"},
    {"source": "alpoge-buckmaster-forced-blowup", "target": "m-astra", "rel": "produced_by"},
    {"source": "alpoge-buckmaster-forced-blowup", "target": "t-fluid-pde", "rel": "about"},
    {"source": "alpoge-buckmaster-forced-blowup", "target": "t-rigorous-numerics-lean", "rel": "about"},
    {"source": "alpoge-buckmaster-forced-blowup", "target": "t-research-practice", "rel": "about"},
    {"source": "alpoge-buckmaster-forced-blowup", "target": "exp-copper-sphere", "rel": "adjacent_to_experiment"},

    {"source": "anth-nine-loops", "target": "org-anthropic", "rel": "authored_by"},
    {"source": "anth-nine-loops", "target": "m-claude-fable-5", "rel": "produced_by"},
    {"source": "anth-nine-loops", "target": "t-amplitudes", "rel": "about"},

    {"source": "anth-claude-shaped-science", "target": "org-anthropic", "rel": "authored_by"},
    {"source": "anth-claude-shaped-science", "target": "org-academia", "rel": "authored_by"},
    {"source": "anth-claude-shaped-science", "target": "m-claude-fable-5", "rel": "produced_by"},
    {"source": "anth-claude-shaped-science", "target": "t-amplitudes", "rel": "about"},
    {"source": "anth-claude-shaped-science", "target": "t-probability-statistics", "rel": "about"},
    {"source": "anth-claude-shaped-science", "target": "t-gr-cosmology", "rel": "about"},
    {"source": "anth-claude-shaped-science", "target": "t-biology", "rel": "about"},
    {"source": "anth-claude-shaped-science", "target": "t-research-practice", "rel": "about"},
    {"source": "anth-claude-shaped-science", "target": "anth-nine-loops", "rel": "cites"},
    {"source": "anth-claude-shaped-science", "target": "anth-quantum-circuits", "rel": "cites"},
    {"source": "anth-claude-shaped-science", "target": "anth-ecdsa-origins", "rel": "cites"},

    {"source": "anth-quantum-circuits", "target": "org-anthropic", "rel": "authored_by"},
    {"source": "anth-quantum-circuits", "target": "org-academia", "rel": "authored_by"},
    {"source": "anth-quantum-circuits", "target": "m-claude-mythos", "rel": "produced_by"},
    {"source": "anth-quantum-circuits", "target": "t-quantum-info", "rel": "about"},
    {"source": "anth-quantum-circuits", "target": "t-cryptography", "rel": "about"},
    {"source": "anth-quantum-circuits", "target": "t-rigorous-numerics-lean", "rel": "about"},

    {"source": "anth-ecdsa-origins", "target": "org-anthropic", "rel": "authored_by"},
    {"source": "anth-ecdsa-origins", "target": "m-claude-internal", "rel": "produced_by"},
    {"source": "anth-ecdsa-origins", "target": "t-cryptography", "rel": "about"},

    {"source": "gdm-alphaevolve", "target": "org-deepmind", "rel": "authored_by"},
    {"source": "gdm-alphaevolve", "target": "m-alphaevolve", "rel": "produced_by"},
    {"source": "gdm-alphaevolve", "target": "t-optimization-algorithms", "rel": "about"},
    {"source": "gdm-alphaevolve", "target": "t-discrete-convex-geometry", "rel": "about"},

    {"source": "gdm-imo-gold", "target": "org-deepmind", "rel": "authored_by"},
    {"source": "gdm-imo-gold", "target": "m-gemini-deep-think", "rel": "produced_by"},
    {"source": "gdm-imo-gold", "target": "t-benchmarks", "rel": "about"},
    {"source": "oai-first-proof", "target": "gdm-imo-gold", "rel": "cites"},

    {"source": "gdm-alphaevolve-tao", "target": "org-deepmind", "rel": "authored_by"},
    {"source": "gdm-alphaevolve-tao", "target": "org-academia", "rel": "authored_by"},
    {"source": "gdm-alphaevolve-tao", "target": "m-alphaevolve", "rel": "produced_by"},
    {"source": "gdm-alphaevolve-tao", "target": "m-gemini-deep-think", "rel": "produced_by"},
    {"source": "gdm-alphaevolve-tao", "target": "t-erdos-combinatorics", "rel": "about"},
    {"source": "gdm-alphaevolve-tao", "target": "t-discrete-convex-geometry", "rel": "about"},
    {"source": "gdm-alphaevolve-tao", "target": "t-optimization-algorithms", "rel": "about"},
    {"source": "gdm-alphaevolve-tao", "target": "gdm-alphaevolve", "rel": "cites"},

    {"source": "gdm-gemini-erdos", "target": "org-deepmind", "rel": "authored_by"},
    {"source": "gdm-gemini-erdos", "target": "m-gemini-deep-think", "rel": "produced_by"},
    {"source": "gdm-gemini-erdos", "target": "t-erdos-combinatorics", "rel": "about"},
    {"source": "gdm-gemini-erdos", "target": "t-research-practice", "rel": "about"},
    {"source": "gdm-gemini-erdos", "target": "oai-erdos-overclaim-oct2025", "rel": "cites"},

    {"source": "gdm-aletheia", "target": "org-deepmind", "rel": "authored_by"},
    {"source": "gdm-aletheia", "target": "m-aletheia", "rel": "produced_by"},
    {"source": "gdm-aletheia", "target": "m-gemini-deep-think", "rel": "produced_by"},
    {"source": "gdm-aletheia", "target": "t-erdos-combinatorics", "rel": "about"},
    {"source": "gdm-aletheia", "target": "t-research-practice", "rel": "about"},
    {"source": "gdm-aletheia", "target": "gdm-gemini-erdos", "rel": "cites"},

    {"source": "hodge-laplacian-3spheres", "target": "org-academia", "rel": "authored_by"},
    {"source": "hodge-laplacian-3spheres", "target": "t-spectral-theory", "rel": "about"},
    {"source": "hodge-laplacian-3spheres", "target": "t-inverse-spectral", "rel": "about"},
    {"source": "hodge-laplacian-3spheres", "target": "exp-copper-sphere", "rel": "adjacent_to_experiment"},

    {"source": "schiffer-colbrook-stepaniants", "target": "org-academia", "rel": "authored_by"},
    {"source": "schiffer-colbrook-stepaniants", "target": "m-gpt55", "rel": "produced_by"},
    {"source": "schiffer-colbrook-stepaniants", "target": "t-spectral-theory", "rel": "about"},
    {"source": "schiffer-colbrook-stepaniants", "target": "t-inverse-spectral", "rel": "about"},
    {"source": "schiffer-colbrook-stepaniants", "target": "t-wave-helmholtz", "rel": "about"},
    {"source": "schiffer-colbrook-stepaniants", "target": "t-rigorous-numerics-lean", "rel": "about"},
    {"source": "schiffer-colbrook-stepaniants", "target": "exp-copper-sphere", "rel": "adjacent_to_experiment"},

    {"source": "schiffer-caolabora-dediospont", "target": "org-academia", "rel": "authored_by"},
    {"source": "schiffer-caolabora-dediospont", "target": "m-gpt55", "rel": "produced_by"},
    {"source": "schiffer-caolabora-dediospont", "target": "m-gpt56-sol", "rel": "produced_by"},
    {"source": "schiffer-caolabora-dediospont", "target": "m-claude-fable-5", "rel": "produced_by"},
    {"source": "schiffer-caolabora-dediospont", "target": "t-spectral-theory", "rel": "about"},
    {"source": "schiffer-caolabora-dediospont", "target": "t-inverse-spectral", "rel": "about"},
    {"source": "schiffer-caolabora-dediospont", "target": "t-wave-helmholtz", "rel": "about"},
    {"source": "schiffer-caolabora-dediospont", "target": "t-rigorous-numerics-lean", "rel": "about"},
    {"source": "schiffer-caolabora-dediospont", "target": "schiffer-colbrook-stepaniants", "rel": "cites"},
    {"source": "schiffer-caolabora-dediospont", "target": "exp-copper-sphere", "rel": "adjacent_to_experiment"},

    {"source": "exp-copper-sphere", "target": "t-spectral-theory", "rel": "about"},
    {"source": "exp-copper-sphere", "target": "t-inverse-spectral", "rel": "about"},
    {"source": "exp-copper-sphere", "target": "t-wave-helmholtz", "rel": "about"}
  ]
}
```

---

## 5. Source log

Fetched in full: openai.com (accelerating-science-gpt-5, new-result-theoretical-physics, extending-single-minus-amplitudes-to-gravitons, model-disproves-discrete-geometry-conjecture, ten-advances-in-mathematics, navier-stokes-solution, advisory-group-on-mathematics-and-ai, sharing-ai-progress-in-mathematics, frontierscience, first-proof-submissions, research-acceleration-view-inside-openai); github.com/openai/math README; en.wikipedia.org (OpenAI bulk release; GPT-5.4); anthropic.com (vibe-physics, claude-shaped-science, introducing-anthropic-science, riemann-zeta, yes-claude-can-do-nine-loops, designing-efficient-quantum-circuits, ecdsa-curve-origins, roundup-feb-2026, ai-for-science-program, claude-science-ai-workbench); arXiv abstracts 2601.02484, 2511.16072, 2509.21131, 2603.15617, 2601.14027, 2602.10177, 2601.22401, 2511.02864, 2605.05406, 2608.01579, 2608.05114; Tao's Erdős-AI wiki (two reads); Tao's blog 7 Sep 2026; Buckmaster statement.pdf; Knuth claude-cycles.pdf; Quanta (Aug 2026); The Decoder (Oct 2025, Jan 2026); Unite.AI; Retraction Watch; Math Scholar; cellcog.ai catalogue summary; hub.valency.io; Epoch FrontierMath Tier 4; Aaronson blog; allthings.how; kingy.ai tracker record.

Blocked (robots/site): github.com/openai/math CONTENTS.md, preprints listing, overview.pdf; New Scientist; Wired; Scientific American; sites.pitt.edu Hajłasz catalogue. Not fetched (snippet only): DeepMind AlphaEvolve and IMO-gold blog posts.
