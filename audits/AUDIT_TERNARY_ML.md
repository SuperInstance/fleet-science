# Ternary ML Ecosystem Audit

**Date:** 2026-06-08  
**Auditor:** Nightshift subagent  
**Scope:** 8 repos under `SuperInstance/` claiming ternary {-1, 0, +1} ML implementations  

---

## Executive Summary

All 8 repos are **genuine, working Rust implementations** of ML algorithms adapted for ternary feature spaces. None are stubs or trivial wrappers. All compile, all tests pass (139 tests total, 0 failures). The code quality is consistently high — well-documented, idiomatic Rust, with meaningful test coverage. The main limitation is that these are **library crates only** (no binaries, no datasets, no benchmarks), so they're ready for integration but not yet proven at scale.

---

## Per-Repo Verdicts

### 1. ternary-svm — **REAL** ✅

**Verdict:** Genuine SVM implementation  
**Lines of code:** 479 (src/lib.rs)  
**Tests:** 12 passed, 0 failed  

**What it implements:**
- Binary SVM with simplified SMO (Platt's algorithm) — real dual optimization with Lagrange multipliers, kernel matrix precomputation, sequential minimal optimization
- One-vs-rest ternary SVM for 3-class classification {-1, 0, +1}
- Three kernel functions: Linear, TernaryPolynomial, TernaryRBF
- Trit distance metric with Z₃-aware semantics (distance 0 for same, 1 for adjacent, 2 for opposite)
- Support vector identification, margin computation, decision function output

**Assessment:** This is a real SVM, not a wrapper. The SMO implementation includes proper:
- Kernel matrix precomputation
- Lagrange multiplier bounds checking (L/H clipping)
- Bias update with KKT condition checking
- Convergence via pass counting (no alpha changes)

**Gaps:** No working set selection heuristic (just picks i+1), no shrinking, no SMO caching for large problems. Fine for small datasets, won't scale to thousands of samples.

---

### 2. ternary-regression — **REAL** ✅

**Verdict:** Genuine linear regression implementation  
**Lines of code:** ~400 (src/lib.rs)  
**Tests:** 14 passed, 0 failed  

**What it implements:**
- OLS via normal equation (XᵀX + λI)β = Xᵀy with Gaussian elimination + partial pivoting
- Ridge regression (L2) via diagonal augmentation of normal equation
- Lasso regression (L1) via proximal gradient descent with soft-thresholding
- R² computation, residual analysis, MSE/MAE metrics
- Configurable learning rate, max iterations, convergence tolerance

**Assessment:** Genuine implementations of all three regression variants. The Gaussian elimination solver includes partial pivoting (not naive), and the Lasso uses the correct proximal operator (soft-thresholding). The code correctly computes intercepts separately from the normal equation.

**Gaps:** The Lasso solver always runs for `max_iter` iterations — no early convergence check. The fit_normal + fit_iterative chain means Lasso does an unnecessary OLS solve first. No elastic net (L1+L2 combined).

---

### 3. ternary-logistic — **REAL** ✅

**Verdict:** Genuine logistic regression implementation  
**Lines of code:** ~350 (src/lib.rs)  
**Tests:** 14 passed, 0 failed  

**What it implements:**
- Binary logistic regression with full-batch gradient descent
- Multinomial (3-class) logistic regression with softmax
- Numerically stable sigmoid (split formulation for ±z)
- Numerically stable softmax (max-subtraction trick)
- L2 regularization, log-loss / cross-entropy loss computation
- Accuracy metric

**Assessment:** Real logistic regression. The numerical stability is handled correctly (sigmoid split, softmax max-shift). The multinomial implementation properly computes per-class gradients with indicator functions. The regularization test verifies that L2 penalty actually reduces weight magnitude.

**Gaps:** Hard-coded to 3 classes for multinomial (no generic K-class). Full-batch only (no SGD/mini-batch). No L1 regularization (no sparse logistic). No convergence early-stopping in the fit loop.

---

### 4. ternary-em — **REAL** ✅

**Verdict:** Genuine Expectation-Maximization implementation  
**Lines of code:** ~600 (src/lib.rs)  
**Tests:** 16 passed, 0 failed  

**What it implements:**
- Ternary distribution type with PMF, log-PMF, mean, variance, sampling
- Mixture model EM: full E-step (posterior responsibilities), M-step (weighted counting)
- Log-likelihood monitoring with convergence detection
- KL divergence and Jensen-Shannon divergence for ternary distributions
- Data-driven initialization (split-into-chunks heuristic)
- Probability floor to prevent log(0)

**Assessment:** Real EM algorithm, not a toy. The implementation correctly:
- Uses the EM formulation γ(zₙₖ) = πₖ · pₖ(xₙ) / Σⱼ πⱼ · pⱼ(xₙ)
- M-step updates are weighted count estimates
- Tests verify monotonically increasing log-likelihood (fundamental EM property)
- Tests verify known parameter recovery

**Gaps:** 1D data only (scalar ternary values, not vectors). No variational EM, no online EM. The KL divergence uses the natural log form without special handling for q(x)=0 (only the floor mitigates this).

---

### 5. ternary-quantize — **REAL** ✅

**Verdict:** Genuine quantization toolkit  
**Lines of code:** 751 (src/lib.rs)  
**Tests:** 32 passed, 0 failed  

**What it implements:**
- Deterministic ternary quantization (fixed threshold → {-1, 0, +1})
- Stochastic ternary quantization with custom xoshiro128** PRNG (no external rand dependency)
- Learned-threshold quantization via numerical gradient descent on MSE
- Per-channel quantization (row-wise scale/threshold for 2D weight matrices)
- Per-channel dequantization
- Comprehensive error metrics: MSE, max error, distribution shift, trit distribution, sparsity
- QuantizationReport struct with Display formatting

**Assessment:** This is the most practically useful crate in the ecosystem. The quantization implementations are correct and well-tested. The stochastic quantization properly uses linear interpolation for probability weighting. The learned threshold uses numerical gradient approximation (finite differences). The per-channel quantization handles heterogeneous weight distributions correctly.

**Gaps:** No SIMD optimization (the README mentions this as potential). The PRNG is custom (xoshiro128**) — functional but not cryptographically reviewed. No quantization-aware training (straight-through estimator). No batch normalization folding.

---

### 6. ternary-pool — **REAL** ✅

**Verdict:** Genuine pooling operations  
**Lines of code:** 594 (src/lib.rs)  
**Tests:** 20 passed, 0 failed  

**What it implements:**
- 2D max pooling, min pooling, majority-vote pooling
- 2D average pooling (integer mean → round to trit)
- Global pooling variants: global avg, global max, global min, global majority
- Adaptive average and max pooling (target output size, like PyTorch)
- Stochastic pooling (weighted random sampling proportional to shifted values)
- TernaryMatrix type with construction, indexing, window extraction

**Assessment:** Real pooling implementations adapted for ternary data. The majority-vote pooling with tie-breaking (0 > 1 > -1) is a sensible Z₃-aware design. The stochastic pooling shifts values to non-negative {0, 1, 2} for probability weighting — correct approach. Adaptive pooling correctly handles non-divisible sizes via integer division of regions.

**Gaps:** No padding options. No dilated pooling. The `round_to_trit` function is a simple sign function (any positive sum → +1, any negative → -1), which may be too aggressive for large windows where the mean should be 0.

---

### 7. ternary-optimizer — **REAL** ✅

**Verdict:** Genuine optimization algorithms  
**Lines of code:** 506 (src/lib.rs)  
**Tests:** 15 passed, 0 failed  

**What it implements:**
- Ternary Gradient Descent (SignSGD-style): θ ← θ - lr × sign(∇L)
- Ternary Momentum: accumulates full-precision momentum, updates by sign
- Ternary Adam (sign-based): Adam structure with first/second moments, but sign-only updates
- Weight ternarization with two strategies: Fixed threshold, MaxScaled (α × max|w|)
- Optimal scale factor computation (minimizes ||W - sT||²)
- Ternary learning rate scheduler with patience-based increase/decrease

**Assessment:** Real optimizer implementations inspired by SignSGD and ternary weight networks literature. The Adam variant tracks second moments for diagnostics but only uses sign(m_hat) for updates — this is documented and intentional. The ternarization scale factor uses the correct least-squares formula (s = Σw·t / Σt²). The LR scheduler is a reasonable reduce-on-plateau variant.

**Gaps:** The second moment (v) in TernaryAdam is computed but unused — pure dead code. No weight decay. No gradient clipping. No warmup. The optimizers operate on flat parameter vectors (no per-layer parameter groups).

---

### 8. ternary-bite — **REAL** ✅

**Verdict:** Genuine signal processing / bit manipulation toolkit  
**Lines of code:** ~250 (src/lib.rs)  
**Tests:** 16 passed, 0 failed  

**What it implements:**
- Bitcrush: sample-rate-style downsampling (hold N samples at first value)
- Quantize: reduce to N discrete levels centered at 0
- Downsample: block averaging with integer division
- Bit rotate: circular shift through ternary values {-1, 0, +1} using modular arithmetic
- Wavefold: fold values exceeding threshold back (analog-inspired distortion)

**Assessment:** This is not ML in the traditional sense — it's a **signal processing crate** for ternary-valued signals. The implementations are correct: bitcrushing holds values properly, quantization maps to N levels, wavefolding implements the classic foldback distortion formula. The bit_rotate using Z₃ modular arithmetic (`rem_euclid(3)`) is a nice touch.

**Gaps:** Not an ML algorithm. The "ternary" framing is a stretch — most functions work on arbitrary i8 ranges, not just {-1, 0, +1}. Only `bit_rotate` truly exploits the ternary domain.

---

## Test Coverage Summary

| Repo | Tests | Passed | Coverage Quality |
|------|-------|--------|-----------------|
| ternary-svm | 12 | 12 | Good — covers kernels, binary classification, ternary classification, margin, support vectors |
| ternary-regression | 14 | 14 | Good — covers OLS, Ridge, Lasso, R², residuals, predictions, MSE/MAE |
| ternary-logistic | 14 | 14 | Good — covers sigmoid, softmax, binary/multinomial, regularization, losses |
| ternary-em | 16 | 16 | Good — covers distribution creation, PMF, EM convergence, KL/JS divergence, parameter recovery |
| ternary-quantize | 32 | 32 | Excellent — comprehensive coverage of all quantization modes, RNG, round-trip, metrics |
| ternary-pool | 20 | 20 | Good — covers all pooling variants, edge cases, global ops, stochastic |
| ternary-optimizer | 15 | 15 | Good — covers all optimizers, ternarization strategies, LR schedule |
| ternary-bite | 16 | 16 | Adequate — covers all operations, edge cases |
| **Total** | **139** | **139** | |

**Test quality notes:**
- Tests verify mathematical properties (R²=1 for perfect fit, softmax sums to 1, log-likelihood monotonically increases)
- Tests check invariants (output values in {-1,0,1}, probabilities in [0,1])
- Missing: property-based tests, fuzzing, performance benchmarks, large-scale integration tests
- No test utilities / fixtures shared across crates

---

## Genuine ML vs. Utility Classification

### Core ML Algorithms (genuine implementations):
- **ternary-svm** — Real SMO-based SVM with kernel support
- **ternary-regression** — Real OLS/Ridge/Lasso with normal equation + proximal gradient
- **ternary-logistic** — Real binary + multinomial logistic regression
- **ternary-em** — Real EM for ternary mixture models

### ML Infrastructure (genuine tooling):
- **ternary-quantize** — Production-quality quantization toolkit (most ready for real use)
- **ternary-pool** — Real pooling operations for ternary matrices
- **ternary-optimizer** — Real sign-based optimizers (SignSGD-family)

### Peripheral (useful but not ML):
- **ternary-bite** — Signal processing utilities, loosely ternary-related

---

## Recommendations

### Invest (high-value, keep and develop):
1. **ternary-quantize** — Most immediately useful. Could be used today for neural network weight quantization. Add SIMD, batch norm folding, and QAT support.
2. **ternary-optimizer** — Good foundation for low-precision training. Remove dead code (unused v in TernaryAdam), add per-layer parameter groups, weight decay.
3. **ternary-svm** — Solid implementation. Add working set selection heuristics for scalability.

### Keep (good quality, lower priority):
4. **ternary-regression** — Correct implementations, good for analysis. Add early stopping in Lasso, elastic net.
5. **ternary-logistic** — Good for classification tasks. Add mini-batch SGD, generic K-class support.
6. **ternary-pool** — Useful for CNN architectures with ternary activations. Add padding options.
7. **ternary-em** — Good for clustering analysis. Extend to multivariate ternary data.

### Reconsider scope:
8. **ternary-bite** — The only crate that doesn't clearly fit the ML framing. Consider merging into a `ternary-signal` or `ternary-dsp` crate with a more accurate description. The functions are useful but the "ternary" branding is misleading since most work on arbitrary i8.

### Cross-cutting improvements:
- **Shared test utilities** — Extract common test patterns (ternary data generation, assertion helpers) into a `ternary-test-utils` crate
- **Benchmarks** — Add criterion benchmarks to all crates; ML algorithms need perf validation
- **Integration tests** — Cross-crate scenarios (quantize → pool → classify, EM → regression)
- **CI matrix** — All repos have CI but only test on ubuntu-latest; add macOS and Windows
- **`no_std` support** — Several crates could work in embedded/WASM contexts with minor changes

---

## Bottom Line

This is a **coherent, well-executed ecosystem** — not vaporware. Every repo has real algorithm implementations, not stubs or wrappers. The mathematical foundations are correct (I verified the normal equation solver, SMO optimizer, EM convergence, sigmoid/softmax stability, and quantization formulas). The main risk is that these are all **single-file library crates** with no real-world deployment story yet. They need benchmarks, integration tests, and example pipelines to move from "correct implementations" to "production-ready tools."
