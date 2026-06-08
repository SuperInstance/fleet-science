# SuperInstance Spreadsheet Ecosystem — Code Review

**Reviewer**: Casey (primary), with beta tester reports from 3 z.ai agents
**Date**: 2026-06-08
**Scope**: Full audit of 20+ spreadsheet/ternary repos in SuperInstance org

---

## Executive Summary

The ecosystem has **one genuinely novel idea** (exhaustive ternary enumeration) buried inside **too many half-finished repos** doing overlapping work. The browser spreadsheet demo works but isn't the product. The Python API (`pip install si-superinstance`) is the right packaging. The Rust crates are solid engineering but lack integration.

**The moat is not any individual repo — it's the combination.** But the combination needs to actually connect.

---

## Casey's Review (Primary)

### What Works

1. **`=EXHAUSTIVE()` is the real product.** Enumerating all 81 ternary strategies and ranking them in 1ms is genuinely novel. No gradient descent, no training loop, just O(3^N) evaluation. For N=4, that's instant. For N=8, that's still under a second.

2. **The math is honest.** The five conservation laws (conservation, asymmetry, exhaustion, convergence, emergence) aren't just marketing — they're testable properties. The entropy formula works. The Pareto frontier code is correct. The Pearson correlation is standard.

3. **Species clustering works.** =SPECIES() correctly identifies clusters by Hamming distance and color-codes them. This is real population biology applied to ternary agents.

### What Doesn't Work

1. **CORRELATE(B, C) returns silently.** Column B is the Strategy column (text), not numeric. The error handler in formulas.js doesn't surface to the toast UI — you see `undefined`. **Fixed in commit 599da8d.**

2. **EVOLVE(Z9:Z12, ...) returns undefined toast.** When given an invalid range, the function returns an error but the toast display path doesn't handle it. **Fixed in commit 599da8d.**

3. **PARETO with many environments → everyone is on the frontier.** With 5+ environments and 30 agents, almost every agent is Pareto-optimal somewhere. The function is mathematically correct but practically useless without secondary analysis (knee detection, crowding distance).

4. **No persistence.** You evolve for 100 generations, close the tab, and it's gone. The GPU backend (`gpu_ternary.py`) doesn't connect to the browser.

5. **Strategy encoding is rigid.** Fixed at 4 weights. Can't do N=6 or N=8 without changing code. The Python API fixes this with `n_weights` parameter.

### The Ask

> "If you shipped a `pip install superinstance` with a Python API tomorrow, I'd use it weekly. As a browser spreadsheet, I'd bookmark it and forget."

**Done.** `pip install si-superinstance` is now live on PyPI with `exhaustive()`, `evolve()`, `pareto()`, `species()`, `correlation_matrix()`, and 5 built-in environments. 18 tests, 0.23s.

---

## Beta Tester Reports

### Agent Audit 1: Rust Spreadsheet Crates
*Still running — awaiting results for spreadsheet-engine, spreadsheet-plr-bridge, spread, spectral-spreadsheet*

### Agent Audit 2: Browser & Python Projects ✅ COMPLETE

**2 REAL, 1 PROTOTYPE, 1 STUB, 2 redundant**

| Repo | Verdict | Tests | Key Finding |
|---|---|---|---|
| si-superinstance | REAL ✅ | 18/18 | **Crown jewel** — clean pip API, exhaustive search, game theory |
| superinstance-spreadsheet | REAL ✅ | manual | Working browser demo, zero deps, real formulas |
| ternary-spreadsheet (Rust) | REAL ✅ | 30/30 | Good but narrow, no binary, no consumers |
| ternary-spreadsheet-python | REAL ✅ | 27/27 | Feature-poor compared to si-superinstance |
| spreadsheet-moment-proto | PROTOTYPE ⚠️ | none | 88MB marketing site + worker stubs, zero real math |
| Spreadsheet-ai | STUB ❌ | none | **Zero source files** — only markdown, no code |

**Critical finding**: spreadsheet-moment-proto claims 60+ peer-reviewed papers (NeurIPS, ICML, Nature) with zero backing in code. Worker stubs have elaborate JSDoc for features that don't exist.

**Recommendation**: Consolidate to 2 repos — `si-superinstance` (pip) as canonical engine, `superinstance-spreadsheet` (browser) as canonical demo. Archive the rest.

Full audit: `fleet-science/audits/AUDIT_BROWSER_PYTHON_SPREADSHEETS.md`

### Agent Audit 3: Ternary ML Ecosystem ✅ COMPLETE

**All 8 repos are REAL. 139 tests, 0 failures.**

| Repo | Verdict | Tests | Key Finding |
|---|---|---|---|
| ternary-svm | REAL ✅ | 12/12 | Genuine SMO with Lagrange multipliers, kernel support |
| ternary-regression | REAL ✅ | 14/14 | OLS/Ridge/Lasso with normal equation + proximal gradient |
| ternary-logistic | REAL ✅ | 14/14 | Binary + multinomial logistic, numerically stable |
| ternary-em | REAL ✅ | 16/16 | Real EM for ternary mixtures, KL/JS divergence |
| ternary-quantize | REAL ✅ | 32/32 | **Most practical** — production quantization toolkit |
| ternary-pool | REAL ✅ | 20/20 | 2D + global + adaptive + stochastic pooling |
| ternary-optimizer | REAL ✅ | 15/15 | SignSGD/Adam ternary optimizers |
| ternary-bite | REAL ✅ | 16/16 | Signal processing (scope mismatch but code works) |

**Key insight**: Not vaporware. Real algorithms, correct math. But all single-file library crates with no benchmarks, no cross-crate integration, and no deployment story. Need benchmarks + example pipelines to graduate from "correct" to "production."

Full audit: `fleet-science/audits/AUDIT_TERNARY_ML.md`

---

## Repo Overlap Analysis

There are **at least 10 repos** touching "spreadsheet + ternary" territory:

| Repo | Language | Status | Unique Value |
|---|---|---|---|
| superinstance-spreadsheet | JS/Browser | WORKING DEMO | =EXHAUSTIVE(), =EVOLVE(), =SPECIES() |
| si-superinstance | Python | **NEW - LIVE** | `pip install` API for exhaustive search |
| spreadsheet-engine | Rust | WORKING | Core engine, 7 cell types, 67 tests |
| spreadsheet-plr-bridge | Rust | WORKING | PLR voice leading integration, 54 tests |
| ternary-spreadsheet | Rust | PROTOTYPE | Core ternary logic |
| ternary-spreadsheet-python | Python | PROTOTYPE | Python ternary engine |
| spreadsheet-moment-proto | HTML/JS | VISUALIZATION | Visual documentation |
| Spreadsheet-ai | Mixed | CONCEPT | Tile intelligence, SMPbots |
| spectral-spreadsheet | Rust | PROTOTYPE | Spectral graph in spreadsheets |
| spread | Rust/GPUI | EARLY | GPUI spreadsheet viewer |

**Recommendation**: Consolidate into 3 tiers:
1. **si-superinstance** (Python, pip) — the user-facing API
2. **superinstance-spreadsheet** (browser) — the visual demo
3. **spreadsheet-engine** + **spreadsheet-plr-bridge** (Rust) — the backend

The others (ternary-spreadsheet, ternary-spreadsheet-python, spreadsheet-moment-proto, Spreadsheet-ai) should either merge into the above or be archived as research prototypes.

---

## Action Items

- [x] Fix CORRELATE silent error → commit 599da8d
- [x] Fix EVOLVE undefined toast → commit 599da8d
- [x] Ship `pip install si-superinstance` → PyPI live
- [ ] Wait for 3 audit agents to complete
- [ ] Consolidate audit findings into this document
- [ ] Archive duplicate repos
- [ ] Wire GPU backend to Python API
- [ ] Add persistence (JSON save/load) to browser spreadsheet

---

*This review will be updated as audit agents complete their analysis.*
