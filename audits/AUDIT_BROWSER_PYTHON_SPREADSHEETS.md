# Audit: Browser & Python Spreadsheet Projects

**Date:** 2026-06-08  
**Auditor:** Nightshift subagent  
**Scope:** 6 repos in the SuperInstance ecosystem  

---

## Executive Summary

**Two repos are genuinely real.** `si-superinstance` (the pip package) and `superinstance-spreadsheet` (the browser spreadsheet) implement the core ternary-strategy idea with working code, passing tests, and a coherent (if simple) computational model. The Rust `ternary-spreadsheet` and Python `ternary-spreadsheet-python` are clean but redundant ports of the same idea with less ambition. `spreadsheet-moment-proto` is 90% marketing website + 10% stub worker code. `Spreadsheet-ai` is an empty vessel with zero source files.

---

## Per-Repo Audit

### 1. `superinstance-spreadsheet` — Browser Spreadsheet

**Verdict: ✅ REAL**

| Aspect | Assessment |
|--------|-----------|
| Source files | `browser/index.html` (220 lines), `browser/formulas.js` (350 lines), `browser/visualizations.js` (280 lines) |
| Does it work? | **Yes.** Self-contained HTML+JS, no build step. Opens in browser. Full grid, evolution, formulas, charts. |
| Novel? | The formula system is genuinely interesting — `=EXHAUSTIVE(C)` enumerates all 81 ternary strategies and ranks them, `=PARETO(A:A)` finds Pareto-optimal agents, `=SPECIES()` clusters by Hamming distance. This is real math. |
| Code quality | Good. Clean IIFE patterns, proper DOM manipulation, canvas visualizations (heatmap, dendrogram, entropy chart, Pareto scatter, species pie). No dependencies. |
| Limitations | The underlying "agent" model is trivially simple: 4 ternary weights mapped to scores. Evolution is just "keep top 50%, mutate one weight." It works, but it's a toy model, not a framework. |

**What it actually computes:**
- Ternary agents with weights {-1,0,+1}^4 compete in stochastic environments
- 50-round Monte Carlo evaluation per cell
- Natural selection (top-50% survival + mutation)
- Shannon entropy, species clustering, Pareto front analysis, Pearson correlation
- Canvas-based visualizations (heatmap, dendrogram, entropy over generations, Pareto scatter, species pie chart)

**Extras:** `gpu_ternary.py` (386 lines) adds numpy/torch batch evaluation, `negative_space.py` (262 lines) does negative-space analysis, 3 example HTML files demonstrate specific scenarios. All real code.

### 2. `ternary-spreadsheet` — Rust Core

**Verdict: ✅ REAL (but narrow)**

| Aspect | Assessment |
|--------|-----------|
| Source files | 8 `.rs` files, ~700 lines total |
| Does it work? | **Yes.** `cargo test` passes all 30 tests. Clean Rust 2021 edition, zero dependencies. |
| Novel? | Same concept as the browser spreadsheet, but with a proper Grid/Cell data structure and formula engine. No browser UI — this is a library crate. |
| Code quality | Very good. Clean module structure (cell, grid, formula, sort, autofill, format, heatmap, tests). Idiomatic Rust with proper error types. |
| Limitations | No binary/main — library only. The `SPECIES` formula just counts sign changes in sequence (not real clustering). `EXHAUSTIVE` brute-forces all 3^N combinations which is correct but capped at 10 cells. |

**What it actually computes:** Same ternary spreadsheet engine as the browser, but as a Rust library with proper `FormulaEngine`, `Grid`, `Cell` types. Supports `EVOLVE`, `BEST`, `SPECIES`, `EXHAUSTIVE`, `ENTROPY`, `SUM`, `AVG`, `COUNT`.

### 3. `ternary-spreadsheet-python` — Python Core

**Verdict: ✅ REAL (but narrow)**

| Aspect | Assessment |
|--------|-----------|
| Source files | 6 `.py` files (src + tests), ~400 lines of source |
| Does it work? | **Yes.** `pytest` passes all 27 tests. Installable via pip. |
| Novel? | Same ternary spreadsheet but with a different architecture: formulas are callables/lambdas, not parsed strings. Grid is a 2D array. |
| Code quality | Good. Uses `__slots__`, type hints, `IntEnum`. Tests cover cell, grid, formulas, sort, autofill. |
| Limitations | Formula system is lambda-based (you pass `lambda: grid.get_value(0,0)`) rather than string parsing — less spreadsheet-like. No `EXHAUSTIVE`, no `PARETO`, no `SPECIES` formula. Fewer features than the Rust or browser versions. |

**Key difference from other repos:** This is a "spreadsheet engine" in the abstract — it's a grid of ternary cells with formula evaluation. But it doesn't implement the agent/evolution/game-theory layer that makes the browser spreadsheet interesting.

### 4. `si-superinstance` — Pip Package

**Verdict: ✅ REAL (the best one)**

| Aspect | Assessment |
|--------|-----------|
| Source files | 3 `.py` files (core, environments, init) + tests, ~500 lines |
| Does it work? | **Yes.** `pytest` passes all 18 tests. Installable via `pip install -e .` |
| Novel? | **Yes.** The `exhaustive()` function that enumerates all 3^N strategies is a legitimate and interesting approach. The game-theory environments (Prisoner's Dilemma, Stag Hunt, Matching Pennies) are real game theory. |
| Code quality | Very good. Clean dataclass-based API, frozen Strategy type, proper stochastic scoring, Pareto front analysis, Hamming clustering, Pearson correlation matrix. |
| Limitations | Still an alpha (v0.1.0). No published PyPI package yet. The `MarketEnvironment` class is referenced in environments.py but not exported in `__init__.py`. |

**What it actually computes:**
- `exhaustive(env, n_weights=4)` → ranks all 81 strategies in ~1ms
- `evolve(population, env)` → natural selection
- `pareto(strategies, envs)` → multi-objective frontier
- `species(strategies)` → Hamming clustering
- `correlation_matrix(strategies, envs)` → Pearson between environments
- Built-in environments: Prisoner's Dilemma, Stag Hunt, Matching Pennies, Random

**This is the repos' crown jewel.** It's a clean, usable Python library that distills the core idea (ternary strategies are enumerable, so just try everything) into something someone could actually pip install and use.

### 5. `spreadsheet-moment-proto` — Visual Documentation/Proto

**Verdict: ⚠️ PROTOTYPE (mostly marketing)**

| Aspect | Assessment |
|--------|-----------|
| Source files | React website (App.jsx + 5 page components), worker TypeScript stubs, 13,000+ files (mostly node_modules) |
| Does it work? | The website renders. But the "intelligence" layer is all marketing copy. |
| Novel? | Claims are grandiose (60+ peer-reviewed papers, SE(3)-equivariant consensus, Lucineer hardware). **None of this is implemented here.** |
| Code quality | The website is a clean React/Vite app. The worker TypeScript files (advanced_tensor_engine.ts, distributed_tensor_engine.ts, etc.) have interface definitions and class shells but **no actual tensor math** — the "einsum" method takes an expression and returns empty data, the "distributed" engine has no networking code. |
| Size: 88MB** (mostly node_modules). The actual custom code is maybe 2,000 lines of React components and TypeScript stubs. |

**What's real:** A nice marketing website at spreadsheet-moment.pages.dev with feature cards and mermaid diagrams.  
**What's not real:** The "tensor engine", "distributed consensus", "NLP engine", "model marketplace", "load balancer" — all stubs with interfaces but no implementations.

### 6. `Spreadsheet-ai` — Tile Intelligence / SMPbots

**Verdict: ❌ STUB**

| Aspect | Assessment |
|--------|-----------|
| Source files | **ZERO source code files.** Only AGENT.md, CHARTER.md, DOCKSIDE-EXAM.md, README.md, FUTURE-INTEGRATION.md, LICENSE |
| Does it work? | Nothing to run. |
| Novel? | CHARTER mentions "Tile Intelligence", "SMPbots Seed+Model+Prompt", "Inductive ML Programming in SpreadSheets" — but none of this exists as code. |
| Code quality | N/A — no code. |

This is a placeholder repo. The charter describes ambitions, not implementations.

---

## Overlap Analysis

```
                    Core Concept    Agent/Evo    Game Theory    Formula Parser    Charts/Viz    Installable
superinstance-spreadsheet  ████████████  ████████████  ████████      ████████████      ████████████    
ternary-spreadsheet (Rust) ████████████  ████████                  ████████████                    
ternary-spreadsheet-python ████████████                            ████████                        
si-superinstance           ████████████  ████████████  ████████████                    ████████       ████████████
spreadsheet-moment-proto                    (stubs)      (stubs)                        (website)      
Spreadsheet-ai                              (none)       (none)      (none)            (none)        
```

### Critical Duplication

1. **The ternary cell/grid model exists in 4 places** — browser JS, Rust, Python (ternary-spreadsheet-python), and si-superinstance. The implementations differ slightly but the core is identical: `{-1, 0, +1}` values in a grid.

2. **The evolution/agent layer exists in 3 places** — browser JS, Rust, and si-superinstance. The browser version is the most complete (visualization + formulas). The pip package is the cleanest API.

3. **The formula engine exists in 3 places** — browser JS (string parser), Rust (string parser), Python (lambda-based). Only the browser and Rust versions parse `=EVOLVE(A1:A10, 50)` style strings.

---

## Merge / Keep Recommendations

### MERGE: `ternary-spreadsheet` + `ternary-spreadsheet-python` → `si-superinstance`

Both are narrow engine-only ports that duplicate what `si-superinstance` does better. The Rust crate has no binary, no consumers. The Python package has fewer features. Both should either:
- Be archived with a pointer to `si-superinstance`, OR
- Have their unique features (Rust's heatmap, Python's lambda formulas) contributed upstream

### KEEP SEPARATE: `superinstance-spreadsheet` + `si-superinstance`

These are the two real products:
- **Browser spreadsheet** = the interactive demo / visual playground
- **si-superinstance** = the programmatic API for developers

They should cross-reference each other. The pip package's README already does this correctly ("This is the Python API for the SuperInstance Spreadsheet").

### ARCHIVE: `spreadsheet-moment-proto`

88MB of node_modules wrapping a marketing website. The website could be a single README in `superinstance-spreadsheet`. The worker stubs have zero value — they're interface definitions with no implementation. Archive or move the website to GitHub Pages.

### DELETE OR RESTART: `Spreadsheet-ai`

Empty. Zero code. The CHARTER describes interesting ideas (SMPbots, Tile Intelligence) but there's nothing to invest in. Either delete it or create actual source code from scratch.

---

## Priority Ranking for Further Investment

| Priority | Repo | Why |
|----------|------|-----|
| 🥇 1 | `si-superinstance` | Cleanest API, most complete feature set, pip-installable. Publish to PyPI, add docs, expand environments. |
| 🥈 2 | `superinstance-spreadsheet` | Working demo, zero dependencies, impressive visualizations. Add more environments, better formula docs, export capabilities. |
| 🥉 3 | `ternary-spreadsheet` (Rust) | Good code but no consumers. Decide: build a CLI binary, or archive. Don't let it rot. |
| 4 | `ternary-spreadsheet-python` | Tests pass but feature-poor compared to si-superinstance. Merge or archive. |
| 5 | `spreadsheet-moment-proto` | Trim to just the website (delete node_modules, worker stubs). Or fold into superinstance-spreadsheet's docs. |
| 6 | `Spreadsheet-ai` | Empty. Start over if the SMPbots idea is real, otherwise delete. |

---

## Test Results Summary

| Repo | Tests | Result |
|------|-------|--------|
| ternary-spreadsheet (Rust) | 30 tests | ✅ All pass |
| ternary-spreadsheet-python | 27 tests | ✅ All pass |
| si-superinstance | 18 tests | ✅ All pass |
| superinstance-spreadsheet (browser) | No automated tests | ⚠️ Manual audit: logic traced, appears correct |
| spreadsheet-moment-proto | jest config exists, no actual test files found | ❌ |
| Spreadsheet-ai | No tests | ❌ No code to test |

---

## Brutal Honesty

**What's genuinely good:** The core insight — ternary {-1,0,+1} strategies create tiny, fully enumerable search spaces — is real and interesting. The `exhaustive()` function in si-superinstance is a clean implementation of a valid idea. The browser spreadsheet is a genuinely interactive, working demo.

**What's concerning:** The ecosystem is spread across 6 repos for what is essentially **one idea** implemented 3-4 times. The "research foundation" claims in spreadsheet-moment-proto (60+ peer-reviewed papers, NeurIPS 2024, ICML 2024, Nature Machine Intelligence 2026) are extraordinary claims with zero evidence in the codebase. The worker stubs have elaborate JSDoc comments describing features that don't exist.

**The path forward:** Consolidate around `si-superinstance` (the pip package) as the canonical engine, and `superinstance-spreadsheet` as the canonical demo. Everything else is noise.
