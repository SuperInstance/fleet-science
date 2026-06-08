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
*Pending — agent running on spreadsheet-engine, spreadsheet-plr-bridge, spread, spectral-spreadsheet*

### Agent Audit 2: Browser & Python Spreadsheet Projects
*Pending — agent running on superinstance-spreadsheet, ternary-spreadsheet, ternary-spreadsheet-python, spreadsheet-moment-proto, Spreadsheet-ai, si-superinstance*

### Agent Audit 3: Ternary ML Ecosystem
*Pending — agent running on ternary-svm, ternary-regression, ternary-logistic, ternary-em, ternary-quantize, ternary-pool, ternary-optimizer, ternary-bite*

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
