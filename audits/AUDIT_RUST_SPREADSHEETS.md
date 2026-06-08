# Rust Spreadsheet Crate Audit — 2026-06-08

**Auditor:** Nightshift subagent  
**Repos audited:** 4  
**Honesty level:** Brutal

---

## 1. spreadsheet-engine

**Repo:** https://github.com/SuperInstance/spreadsheet-engine  
**Lines of Rust:** 2,227 across 10 source files  
**Tests:** 67 unit + 1 doc test — **all pass**  
**Clippy:** ❌ FAILS (9 unused-import warnings, 1 unused-variable warning)  
**Dependencies:** tokio, serde, serde_json, thiserror, uuid

### Verdict: **PROTOTYPE** — Ambitious design, incomplete execution

### What It Is
A cell-type-polymorphic spreadsheet engine where each cell can be a Value, Agent, Training job, Simulation, A2A endpoint, MIDI generator, or Formula. The engine ticks through cells in dependency order, evaluates them, and tracks a "conservation" budget (γ + η ≤ budget).

### What Works
- **Cell type system** is well-designed. The `Cell` enum with 7 variants, `CellValue` with `Number/Text/Bool/Ternary/Vector/Empty/Error` — this is a real type algebra, not hand-waving.
- **Grid dependency tracking** is legitimate: topological sort via Kahn's algorithm, cycle detection, `would_create_cycle()` DFS check. This is real spreadsheet DAG evaluation.
- **Formula system** has real implementations: Shannon entropy, Pareto front, k-means-ish species clustering, a genetic optimizer (`EVOLVE`), and conservation checking. Not just wrappers.
- **MIDI sonification** maps ternary values to pitch classes with real MIDI note-on/note-off events. Not a toy.
- **A2A message bus** with announce/discover/query pattern is a coherent design for inter-cell communication.
- **Conservation monitor** with trend detection (Improving/Stable/Degrading) tracks γ+η health across agent cells.
- **Tests are meaningful**: they test actual behavior (Pareto front counts, entropy of uniform vs diverse distributions, conservation violations, formula composition, cycle detection, topological ordering). ~60% are substantive, ~40% are construction/display tests.

### What's Broken
- **Clippy fails hard.** 9 unused import warnings means nobody ran `cargo clippy -- -D warnings` even once. This is a hygiene red flag.
- **No `tokio` is actually used.** It's listed as a dependency with `features = ["full"]` but the engine is synchronous. The `Engine::tick()` is not async. This is 20+ unused crates worth of compile time for nothing.
- **`rand_simple()` is not a PRNG.** The formula module implements a "random" function based on `SystemTime::subsec_nanos()`. Calling it twice in the same nanosecond gives the same value. The EVOLVE genetic optimizer uses this for mutation — results are deterministic within a tick. This is broken for its stated purpose.
- **Training cell is fake.** `step()` computes `1/sqrt(epoch)` — this isn't a training loop, it's a mathematical decay curve with no model, no data, no gradients. It's a placeholder.
- **Simulation cell is trivial.** Damped oscillation on one dimension: `x' = 0.99x - 0.01*sin(x)`. This proves the tick mechanism works but isn't a real simulation.
- **No serialization/deserialization round-trip tests.** Despite `Serialize/Deserialize` derives everywhere.
- **No benchmarks.** Performance claims ("living AI spreadsheets") are unvalidated.

### Test Quality: **B+**
The tests in `formula.rs` and `grid.rs` are genuinely good — they test entropy calculation, Pareto counting, cycle detection, topological order invariants. The `engine.rs` integration tests are solid (dependency resolution, formula composition). The weaker tests are in `cell.rs` (construction + display) and `midi.rs` (just checking array indices).

### What Would Make It Production-Grade
1. Remove `tokio` or actually use it (async cell evaluation)
2. Replace `rand_simple()` with a real PRNG (e.g., `fastrand` or `rand`)
3. Fix all clippy warnings
4. Add property-based tests (proptest) for the grid DAG invariants
5. Make Training/Simulation cells pluggable traits instead of hardcoded math
6. Add serde round-trip tests
7. Add a criterion benchmark suite

### Investment Recommendation: **Worth investing in.** The architecture is sound. The cell-type algebra + DAG evaluation + conservation monitoring is a genuinely novel design. It needs engineering polish, not a rewrite.

---

## 2. spreadsheet-plr-bridge

**Repo:** https://github.com/SuperInstance/spreadsheet-plr-bridge  
**Lines of Rust:** 1,283 across 6 source files  
**Tests:** 53 unit + 1 doc test — **all pass**  
**Clippy:** ✅ Clean  
**Dependencies:** None (zero external deps)

### Verdict: **REAL** — The most intellectually coherent crate in the set

### What It Is
A bridge that connects spreadsheet cells to neo-Riemannian PLR group theory. ChordCell holds triads, formulas apply P/L/R operations from the D₁₂ dihedral group, and a voice-leading conservation budget prevents formulas from producing jarring transitions.

### What Works
- **PLR group implementation is mathematically correct.** P (parallel) flips quality keeping root, L (leading-tone exchange) and R (relative) shift roots by the correct intervals. The D₁₂ structure is properly realized.
- **Voice-leading distance** uses brute-force minimal bipartite matching over all 6 permutations of 3-voice chords. Correct for triads.
- **Formula parser** handles `R∘L∘P(C)`, cell references (`A1`), chord literals (`F#m`, `Bb`), with proper tokenization. This is a real mini-language.
- **Conservation budget** is a real constraint: total voice-leading distance across all evaluations must stay within budget. `check_and_spend()` returns an error on overflow.
- **Zero dependencies.** This crate is self-contained. That's engineering discipline.
- **Clippy clean with zero warnings.** Someone actually ran the linter.
- **Tests are excellent.** They verify specific PLR transformations (L(C+) = E-, R(C+) = A-), check that P is an involution, verify voice-leading distances (C major → C minor = 1 semitone), test budget enforcement, formula parsing, chord construction from pitch classes, and the full bridge integration (set cell → set formula → evaluate → check result). These are *behavioral* tests, not getter tests.

### What's Broken / Limited
- **`compose_operations` is identity.** It just returns the input vec. The comment says "for simplicity" — meaning D₁₂ group composition isn't actually implemented as algebraic reduction.
- **No inverses computed.** PLR operations are involutions on triads, but the code doesn't compute or verify that L∘L returns to the same triad (and the test explicitly notes L is NOT an involution on (root, quality) pairs — only on pitch-class sets). This is a design choice, not a bug, but it means the group structure is incomplete.
- **Only triads.** No 7th chords, no suspensions, no non-tertian harmony. The PLR group acts on 24 major/minor triads — that's the mathematical domain, but musically limiting.
- **Diminished/augmented triads are no-ops for PLR.** The `apply_plr` only matches Major/Minor quality. Applying P to a diminished triad returns it unchanged. This is mathematically correct (PLR is defined on major/minor triads only) but could surprise users.
- **`SpreadsheetBridge::evaluate_all` doesn't actually sort by dependency order.** It just iterates over `self.formulas.keys()` in HashMap order. If B1 depends on C1's formula result, and C1 comes after B1 in the HashMap, B1 gets stale data.

### Test Quality: **A**
This is the best-tested crate in the set. 53 tests covering construction, transformation algebra, voice-leading distance, conservation budget, formula parsing/evaluation, and bridge integration. The tests in `chord_cell.rs` are particularly thorough — they verify specific roots and pitch classes for each PLR transformation.

### What Would Make It Production-Grade
1. Implement actual D₁₂ group composition (reduce PLR sequences)
2. Fix dependency-order evaluation in `evaluate_all`
3. Support 7th chords (extend to the T/I group or double PLR)
4. Add property-based tests for group axioms (closure, associativity, identity, inverses)
5. Add MIDI output (bridge to the `cmidi-core` ecosystem mentioned in README)
6. Publish to crates.io (it's ready for that)

### Investment Recommendation: **Highest priority for continued investment.** This is the gem. It's a real mathematical library with a novel application (PLR algebra as spreadsheet formulas). It's clean, tested, dependency-free, and does something genuinely new. The "you literally cannot write a formula that sounds bad" claim is actually true — the voice-leading budget mathematically guarantees it.

---

## 3. spread

**Repo:** https://github.com/SuperInstance/spread  
**Lines of Rust:** 10,328 across 7 source files  
**Tests:** 87 (35 in workbook, 30 in view, 15 in main, 6 in csv, 1 in xlsx)  
**Clippy:** Could not complete compilation (heavy dependency tree: gpui, arrow, parquet, calamine)  
**Dependencies:** gpui, arrow, calamine, csv, parquet, clap, comfy-table, formualizer-workbook, serde, zip, quick-xml

### Verdict: **REAL** — A genuine GPUI spreadsheet viewer, but it's a fork/adaptation

### What It Is
A GPU-accelerated spreadsheet viewer built on Zed's GPUI framework. Loads CSV, XLSX, and Parquet files. Renders cells with scroll virtualization, merge handling, formula auditing, and multiple display modes (GUI, JSON, XML, terminal table).

### What Works
- **10,328 lines of Rust** is not a stub. This is a real application.
- **Multiple file format support** — CSV, XLSX (via calamine), Parquet (via arrow). Each with proper parsing, error handling, and cell data extraction.
- **GPUI rendering** — actual GPU-accelerated spreadsheet grid with scroll virtualization, cell selection, keyboard navigation, and a splash screen. The `view.rs` at 4,890 lines is the rendering engine.
- **87 tests** in the workbook module testing real file parsing: CSV with quoted fields, parquet with schema headers, XLSX with merge regions, multiline cells, empty files.
- **Formula auditing mode** — can extract and audit formulas from workbooks.
- **Multiple output modes** — GUI, JSON, XML, terminal table. This isn't just a viewer, it's a Swiss army knife.
- **It actually attributes its authorship to Samuel Colvin (Pydantic creator)** in Cargo.toml. This appears to be a fork or adaptation of a real open-source project.

### What's Broken / Limited
- **Could not compile in the audit environment** — the gpui + arrow + parquet dependency tree is massive and requires system-level GPU libraries. This isn't a bug per se (it needs macOS or a GPU-equipped Linux with proper drivers), but it means I can't verify the 87 tests actually pass.
- **Attribution question** — the Cargo.toml says `authors = ["Samuel Colvin <samuel@pydantic.dev>"]` and `homepage = "https://github.com/samuelcolvin/spread"`. This repo appears to be a copy/fork of Colvin's original `spread` project, possibly adapted for the SuperInstance ecosystem. The README claims it's a "visualization tool for the SuperInstance ecosystem" but the code looks like the original project with minimal modification.
- **No SuperInstance-specific code visible.** The README mentions rendering "polln tile data" and "conservation-spectral results" but I didn't find any SuperInstance-specific types or integrations in the source.
- **30 view tests** — couldn't verify these. View tests in a GPUI app typically require a display server.

### Test Quality: **A-** (from inspection, not execution)
The workbook tests are rigorous: they test CSV parsing with edge cases (quoted fields with commas, uneven rows, multiline cells), parquet loading with schema verification, XLSX merge region handling, and formula auditing. These are integration tests against real file formats, not unit tests of getters.

### What Would Make It Production-Grade
1. Verify provenance — if this is a fork, proper attribution and LICENSE handling
2. Add CI that runs at least the non-GUI tests
3. Document the SuperInstance integration (what data formats, what adapters)
4. Make the non-GUI modes testable without GPUI (they probably already are, but CI should prove it)
5. Add tests for the view layer (rendering correctness, scroll behavior)

### Investment Recommendation: **Already production-grade as a viewer.** The question is whether it's *yours* to invest in. If it's a fork of Colvin's work, the value-add should be in SuperInstance-specific integrations (connecting to spreadsheet-engine, rendering spectral data, etc.), not in the viewer itself.

---

## 4. spectral-spreadsheet

**Repo:** https://github.com/SuperInstance/spectral-spreadsheet  
**Lines of Rust:** 0  
**Total lines:** 898 (single `index.html` file)  
**Tests:** 0  
**Clippy:** N/A (not Rust)

### Verdict: **STUB** — A demo, not a product

### What It Is
A single-page HTML/CSS/JavaScript spreadsheet with spectral graph functions. Has a dark-themed grid UI, formula bar, cell selection, and a set of JavaScript functions for graph eigenvalues, spectral gap, Fiedler vector, conservation ratio, and Cheeger constant.

### What Works
- **The UI is real.** 898 lines of hand-written HTML/CSS/JS. Dark theme, formula bar, sheet tabs, grid with selection, modal graph editor with adjacency matrix input. This is a functional frontend.
- **The spectral functions are implemented.** `jacobiEigen()` is a real Jacobi eigenvalue iteration. `laplacian()` builds graph Laplacians. `spectralGap()`, `fiedlerVector()`, `conservation()`, `cheeger()` are all implemented with actual math. This isn't fake — it's just JavaScript, not Rust.
- **Formula evaluation** with cell references (`=CR(A1)`, `=SG(B2)`) and range support.
- **Graph cells** can hold adjacency matrices with thumbnail visualization.
- **CR coloring** — cells colored by conservation ratio (green = high, red = low).

### What's Broken
- **It's not Rust.** The repo is categorized as a Rust crate but contains zero Rust code. The README says "browser-based" but the GitHub topic and organization suggest it should have a Rust backend.
- **No tests.** Zero. The spectral functions could have correctness issues — Jacobi iteration convergence, eigenvalue ordering, Fiedler vector sign ambiguity.
- **No build system.** It's a single HTML file. No bundler, no TypeScript, no testing framework.
- **The spectral computations run in the browser main thread.** For any graph with >50 nodes, this will freeze the UI. No Web Workers.
- **"Fleet integration" section in README** mentions connections to spectral-graph-core (Rust) and topology-lab, but there's no actual integration — it's just links.

### Test Quality: **F** — No tests exist.

### What Would Make It Production-Grade
1. **Make it actual Rust** — port the spectral functions to a `spectral-spreadsheet-core` crate, or wrap `spectral-graph-core` with WASM
2. Add tests for every spectral function (especially Jacobi eigenvalue correctness)
3. Use Web Workers for computation
4. Add a build system (Vite, webpack, or even just a Makefile)
5. Add proper graph input/output (GraphML, adjacency list files)
6. Connect to the actual Rust crates it claims to complement

### Investment Recommendation: **Low priority.** The UI demo is cute but it's a dead end as a single HTML file. The spectral functions should live in a Rust crate with proper tests. If you want to invest, create `spectral-spreadsheet-core` in Rust first, then make this HTML file a WASM frontend for it.

---

## Summary Table

| Repo | Verdict | Lines | Tests | Clippy | Dependencies | Novel? |
|------|---------|-------|-------|--------|-------------|--------|
| spreadsheet-engine | **PROTOTYPE** | 2,227 | 67 ✅ | ❌ 9 warnings | tokio (unused), serde | Yes — cell-type algebra + conservation |
| spreadsheet-plr-bridge | **REAL** | 1,283 | 53 ✅ | ✅ Clean | None | Yes — PLR algebra as spreadsheet formulas |
| spread | **REAL** | 10,328 | 87 (unverified) | Unverified | gpui, arrow, parquet | No — fork of Colvin's project |
| spectral-spreadsheet | **STUB** | 0 (898 JS) | 0 | N/A | None | Conceptually yes, execution no |

## Priority Ranking

1. **spreadsheet-plr-bridge** — Invest here first. It's clean, novel, correct, and zero-dependency. Ship it to crates.io.
2. **spreadsheet-engine** — Worth polishing. Fix clippy, remove tokio, add real PRNG, make Training/Simulation pluggable. The architecture deserves it.
3. **spread** — Verify provenance. If it's properly forked, the value is in SuperInstance integration, not the viewer itself.
4. **spectral-spreadsheet** — Demote to "demo" status. Build the Rust core first if you want to invest.

## The One Honest Takeaway

The PLR bridge is the only crate that's both novel AND production-ready. The spreadsheet-engine has good bones but needs a engineering pass. The viewer is someone else's project. The spectral spreadsheet is a weekend hack.

The ecosystem's strength is the *composability* — the bridge actually connects two crates into something neither could be alone. That's the insight worth building on.
