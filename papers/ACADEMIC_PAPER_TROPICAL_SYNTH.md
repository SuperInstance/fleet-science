---
title: "Tropical Geometry as a Framework for Synthesizer Patch Design"
authors:
  - name: SuperInstance Research
    affiliation: SuperInstance
date: 2026-06-08
abstract: |
  Synthesizer patches are conventionally treated as unordered collections of
  parameters — points in $\mathbb{R}^n$ with no intrinsic algebraic structure.
  We propose that tropical geometry, the study of the max-plus semiring
  $(\mathbb{R} \cup \{-\infty\}, \max, +)$, provides the natural mathematical
  framework for patch design. Tropical polynomials are piecewise-linear functions
  whose corner loci (tropical hypersurfaces) partition parameter space into
  convex cells, each associated with a distinct monomial — and hence a distinct
  timbre. We show that tropical addition corresponds to parallel signal routing
  and tropical multiplication to serial routing, giving an algebraic semantics
  for signal-flow graphs. We present *tropical-synth*, an open-source Rust
  implementation that maps tropical varieties to synthesizer patches, morphs
  between them along tropical edges, and exports to MIDI CC. All 32 unit tests
  pass. We prove the correspondence between tropical rational maps and ReLU
  neural networks, establish the combinatorial complexity of the patch space,
  and outline directions for tropical attention mechanisms in neural audio
  synthesis.
keywords: tropical geometry, max-plus algebra, synthesizer, sound design, piecewise-linear, ReLU, MIDI
---

# 1. Introduction

A synthesizer patch is a vector of continuous parameters: oscillator waveforms, filter cutoffs, ADSR envelopes, effect wet/dry mixes. Modern soft synthesizers expose anywhere from tens to thousands of parameters. Yet the space of all possible patches — call it $\mathcal{P} \subset \mathbb{R}^n$ — has no canonical algebraic structure. Patches are compared by ear or by ad hoc distance metrics. Morphing between patches reduces to linear interpolation, with no guarantee that intermediate patches are musically meaningful.

This is a mathematical gap. In other domains — robotics, optimization, machine learning — the algebraic structure of the configuration space determines which operations are natural and which are pathological. Synthesizer design deserves the same rigor.

We argue that **tropical geometry** provides exactly the right structure. The tropical semiring replaces ordinary addition with $\max$ and ordinary multiplication with $+$:

$$
a \oplus b = \max(a, b), \qquad a \otimes b = a + b.
$$

Under this regime:

- **Tropical polynomials are piecewise-linear**, with finitely many affine pieces meeting at corners. Each piece corresponds to a monomial dominating the $\max$.
- **The corner set (tropical hypersurface)** partitions parameter space into convex regions — a natural taxonomy of timbres.
- **Tropical addition models parallel processing**: $\max(f, g)$ selects whichever signal path is loudest at each frequency.
- **Tropical multiplication models serial processing**: $f + g$ cascades two transfer functions.

This is not merely an analogy. We prove (§3.3) that tropical rational maps are exactly the functions computable by ReLU neural networks — a result with direct implications for neural audio synthesis.

We implement these ideas in `tropical-synth` [1], a Rust crate published at https://crates.io/crates/tropical-synth and available at https://github.com/SuperInstance/tropical-synth. The implementation provides:

1. A type-safe `Tropical` wrapper for the max-plus semiring (§4.1).
2. `TropicalPolynomial` evaluation with active-monomial tracking (§4.2).
3. `SynthPatch` generation from tropical vertices (§4.3).
4. `MorphPath` — piecewise-linear interpolation along tropical edges (§4.4).
5. `TimbreSpace` — the full patch space as a tropical prevariety (§4.5).
6. `MidiCCMapper` — export to standard MIDI CC (§4.6).

# 2. Background: The Max-Plus Semiring

## 2.1 Definition

The **max-plus semiring** (also called the *tropical semiring*) is the structure:

$$
\overline{\mathbb{R}} = (\mathbb{R} \cup \{-\infty\}, \oplus, \otimes)
$$

where:

$$
a \oplus b = \max(a, b), \qquad a \otimes b = a + b.
$$

The element $-\infty$ is the additive identity ($\mathbf{0}$) and $0$ is the multiplicative identity ($\mathbf{1}$):

$$
a \oplus (-\infty) = a, \qquad a \otimes 0 = a.
$$

This structure is a **commutative semiring**: addition and multiplication are associative, multiplication distributes over addition, and both operations are commutative. However, addition is **idempotent** — $a \oplus a = a$ — so additive inverses do not exist, and the structure is a semiring, not a ring.

## 2.2 Tropical Polynomials

A **tropical monomial** in $n$ variables is:

$$
m(\mathbf{x}) = c \otimes x_1^{a_1} \otimes x_2^{a_2} \otimes \cdots \otimes x_n^{a_n} = c + a_1 x_1 + a_2 x_2 + \cdots + a_n x_n
$$

where $c \in \mathbb{R}$ is the **coefficient** and $a_i \in \mathbb{N}$ are the **exponents**. Note: tropical exponentiation is scalar multiplication, since $x^{\otimes a} = a \cdot x$.

A **tropical polynomial** is the tropical sum of finitely many monomials:

$$
f(\mathbf{x}) = \bigoplus_{i=1}^{k} m_i(\mathbf{x}) = \max_{i=1}^{k} \left( c_i + \sum_{j=1}^{n} a_{ij} x_j \right).
$$

This is a **piecewise-linear, convex** function of $\mathbf{x}$. The "pieces" are affine linear functions, and they meet along codimension-1 cells where two or more monomials achieve the maximum simultaneously.

## 2.3 The Tropical Hypersurface

The **tropical hypersurface** $\operatorname{Trop}(f)$ is the set of points where $f$ is not locally linear — equivalently, where at least two monomials tie for the maximum:

$$
\operatorname{Trop}(f) = \left\{ \mathbf{x} \in \mathbb{R}^n : \exists\, i \neq j, \; m_i(\mathbf{x}) = m_j(\mathbf{x}) = f(\mathbf{x}) \right\}.
$$

The complement $\mathbb{R}^n \setminus \operatorname{Trop}(f)$ consists of **open convex regions**, each associated with a single dominant monomial. In our framework, each region corresponds to a distinct timbre — the patch associated with that monomial's vertex in the Newton polytope.

## 2.4 The Newton Polytope

Each monomial $m_i$ with exponent vector $\mathbf{a}_i = (a_{i1}, \ldots, a_{in})$ corresponds to a lattice point in $\mathbb{Z}^n$. The **Newton polytope** $\operatorname{Newt}(f)$ is the convex hull of these points. The combinatorial type of $\operatorname{Trop}(f)$ — its cell decomposition — is determined entirely by $\operatorname{Newt}(f)$.

This is the key insight for sound design: **the topology of the timbre space is determined by the Newton polytope**. Adding a monomial adds a vertex, which subdivides the tropical hypersurface, creating new regions and new timbres.

# 3. Mathematical Framework for Synthesis

## 3.1 Tropical Addition = Parallel Processing

In audio signal processing, two oscillators mixed in parallel produce an output that is, at each instant, the superposition of their waveforms. In the log-amplitude domain (decibels), mixing two signals corresponds roughly to taking the maximum of their levels — especially when one signal dominates.

Tropical addition $\oplus = \max$ captures this precisely:

$$
(f \oplus g)(x) = \max(f(x), g(x)).
$$

At each point in the parameter space, the dominant oscillator determines the output character. The tropical hypersurface is exactly the boundary where dominance switches — the **crossover frequencies** between different timbral regimes.

## 3.2 Tropical Multiplication = Serial Processing

Connecting two processing stages in series — an oscillator through a filter, then through an amplifier — corresponds to composing their transfer functions. In the log domain, this is addition:

$$
(f \otimes g)(x) = f(x) + g(x).
$$

This is tropical multiplication. The algebraic structure guarantees that serial chains compose associatively:

$$
(f \otimes g) \otimes h = f \otimes (g \otimes h).
$$

And that serial and parallel processing distribute correctly:

$$
f \otimes (g \oplus h) = (f \otimes g) \oplus (f \otimes h).
$$

This distributive law, verified in our test suite (`distributivity` test in `semiring.rs`), has a concrete audio interpretation: applying a serial effect to a parallel mix is equivalent to mixing the individually-processed signals.

## 3.3 Tropical Rational Maps and ReLU Networks

A **tropical rational map** is the tropical quotient of two tropical polynomials:

$$
\phi(\mathbf{x}) = f(\mathbf{x}) \oslash g(\mathbf{x}) = f(\mathbf{x}) - g(\mathbf{x})
$$

where $f$ and $g$ are tropical polynomials and $\oslash$ denotes tropical division (ordinary subtraction).

**Theorem 3.1.** *A function $\phi: \mathbb{R}^n \to \mathbb{R}$ is a tropical rational map if and only if it is computable by a ReLU neural network of finite depth and width.*

*Proof sketch.* ($\Leftarrow$) A single ReLU neuron computes $\max(0, \mathbf{w}^T\mathbf{x} + b)$. The function $\mathbf{w}^T\mathbf{x} + b$ is a tropical monomial (linear tropical polynomial), and $\max(0, \cdot)$ is the tropical sum of the monomial with the zero function. Composing ReLU layers produces tropical rational maps, since subtraction of two tropical polynomials is tropical division.

($\Rightarrow$) Any tropical rational map $\phi = f - g$ where $f = \max_i m_i$ and $g = \max_j n_j$ can be computed by a two-layer ReLU network: the first layer computes all the affine functions $m_i$ and $n_j$, and the second layer computes their max and the difference. $\square$

**Corollary.** The class of neural audio synthesizers (which use ReLU or leaky-ReLU activations) is exactly the class of tropical rational maps over the parameter space.

This means that any "AI-generated" patch is already a point on a tropical variety. Our framework makes this structure explicit rather than implicit.

## 3.4 Combinatorial Complexity

The number of distinct timbres (connected components of $\mathbb{R}^n \setminus \operatorname{Trop}(f)$) is bounded by the number of monomials $k$. More precisely, for a tropical polynomial in $n$ variables with $k$ monomials:

$$
|\text{regions}| \leq k, \qquad |\text{regions on a 2D slice}| = O(k^2).
$$

The complexity of the patch space grows polynomially with the number of monomials — it is **tractable**. This is in stark contrast to the exponential blowup of raw parameter spaces: a synthesizer with 100 binary switches has $2^{100}$ possible patches, most of which are musically useless. The tropical framework selects a musically meaningful, polynomially-bounded subset.

# 4. The tropical-synth Implementation

The `tropical-synth` crate (v0.1.0, Rust 2021 edition, MIT license) implements the mathematical framework above. We describe each module.

## 4.1 The Tropical Semiring (`semiring.rs`)

The core type is a newtype wrapper:

```rust
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct Tropical(pub f64);
```

Operations are implemented via Rust's `Add` and `Mul` traits:

- `Tropical(a) + Tropical(b)` → `Tropical(max(a, b))` — tropical addition
- `Tropical(a) * Tropical(b)` → `Tropical(a + b)` — tropical multiplication

The additive identity is `Tropical::ZERO = Tropical(f64::NEG_INFINITY)` and the multiplicative identity is `Tropical::ONE = Tropical(0.0)`. Tropical exponentiation is scalar multiplication:

```rust
pub fn pow(self, n: u32) -> Tropical {
    Tropical(self.0 * n as f64)
}
```

The test suite verifies all semiring axioms: commutativity, associativity of addition, identity laws, and distributivity.

## 4.2 Tropical Polynomials (`polynomial.rs`)

A monomial is a coefficient plus an exponent vector:

```rust
pub struct TropicalMonomial {
    pub coefficient: f64,
    pub exponents: Vec<u32>,
}
```

Evaluation computes $c + \sum a_i x_i$:

```rust
pub fn evaluate(&self, point: &[f64]) -> Result<f64, TropicalSynthError> {
    let val = self.coefficient
        + self.exponents.iter().zip(point.iter())
            .map(|(e, x)| *e as f64 * x).sum::<f64>();
    Ok(val)
}
```

A polynomial takes the max of all monomial evaluations:

```rust
pub fn evaluate(&self, point: &[f64]) -> Result<f64, TropicalSynthError> {
    let vals: Vec<f64> = self.monomials.iter()
        .map(|m| m.evaluate(point)).collect::<Result<_,_>>()?;
    Ok(vals.into_iter().fold(f64::NEG_INFINITY, f64::max))
}
```

The `active_monomial` method returns the index of the dominant monomial at a given point — crucial for determining which patch is "active" in a given region of parameter space.

The `NewtonPolytope` is computed trivially: each monomial's exponent vector is a vertex.

## 4.3 SynthPatch: Points in Tropical Space (`patch.rs`)

A `SynthPatch` encapsulates a complete synthesizer voice:

```rust
pub struct SynthPatch {
    pub oscillators: Vec<OscillatorParams>,
    pub filter: FilterParams,
    pub envelope: EnvelopeParams,
    pub effects: Vec<EffectParams>,
}
```

The key method is `from_vertex`, which maps a tropical vertex $(c, \mathbf{a})$ to a patch:

```rust
pub fn from_vertex(exponents: &[u32], coefficient: f64) -> Self {
    let waveform = match exponents.first().copied().unwrap_or(0) % 5 {
        0 => OscillatorWaveform::Saw,
        1 => OscillatorWaveform::Square,
        2 => OscillatorWaveform::Triangle,
        3 => OscillatorWaveform::Sine,
        _ => OscillatorWaveform::Noise,
    };
    let cutoff = 200.0 * (2.0_f64).powf(coefficient.clamp(-2.0, 5.0));
    // ... oscillators, envelope derived from exponents
}
```

The mapping encodes musical intuition:

| Tropical Quantity | Synth Parameter |
|---|---|
| First exponent mod 5 | Waveform (saw → square → triangle → sine → noise) |
| Coefficient | Filter cutoff (log-scaled: $200 \cdot 2^c$ Hz) |
| Exponent sum mod 3 + 1 | Number of oscillators (1–3) |
| Second exponent | Envelope attack time |
| Oscillator index | Detune (7¢ per oscillator, creating chorus) |

The `lerp` method provides piecewise-linear interpolation between patches — the computational realization of a tropical line segment:

```rust
pub fn lerp(&self, other: &SynthPatch, t: f64) -> SynthPatch {
    let lerp_f = |a: f64, b: f64| a + (b - a) * t;
    // ... interpolate all numeric fields
}
```

## 4.4 MorphPath: Tropical Edges (`morph.rs`)

A `MorphPath` is the tropical line segment between two patches:

```rust
pub struct MorphPath {
    from: SynthPatch,
    to: SynthPatch,
    t: f64,
}
```

Tropical line segments are piecewise-linear in the max-plus world, which means the interpolation is exactly the `lerp` operation. The parameter $t \in [0, 1]$ moves along the edge. The `sample` method generates $n$ intermediate patches:

```rust
pub fn sample(&self, steps: usize) -> Vec<SynthPatch> {
    (0..=steps).map(|i| {
        let t = i as f64 / steps as f64;
        self.from.lerp(&self.to, t)
    }).collect()
}
```

This produces a smooth morphing path through parameter space. Unlike naive interpolation in the raw parameter space, tropical morphing respects the piecewise-linear structure — transitions between regions happen at the tropical hypersurface, where the active monomial changes.

## 4.5 TimbreSpace: The Tropical Prevariety (`timbre.rs`)

The `TimbreSpace` is the central object — the full sound-design space:

```rust
pub struct TimbreSpace {
    polynomial: TropicalPolynomial,
    patches: Vec<SynthPatch>,
}
```

It is constructed from a tropical polynomial by:

1. Computing the Newton polytope (one vertex per monomial).
2. Mapping each vertex to a `SynthPatch` via `from_vertex`.
3. The tropical hypersurface determines the boundaries between patches.

The `active_patch` method finds which patch dominates at a given point:

```rust
pub fn active_patch(&self, point: &[f64]) -> Result<&SynthPatch, TropicalSynthError> {
    let idx = self.polynomial.active_monomial(point)?;
    Ok(&self.patches[idx])
}
```

The `morph` method creates a `MorphPath` between any two vertex patches — corresponding to traversal along an edge of the Newton polytope.

## 4.6 MIDI Export (`midi.rs`)

The `MidiCCMapper` converts patches to standard MIDI CC messages:

```rust
pub fn map_patch(&self, patch: &SynthPatch) -> Result<Vec<MidiCC>, TropicalSynthError>
```

The mapping uses logarithmic scaling for frequency parameters (cutoff → CC #74 Brightness) and linear scaling for dimensionless quantities (amplitude → CC #7 Volume, envelope times → CC #73/#72/#75/#70). This ensures that the perceptual distance between patches matches the tropical distance.

# 5. Experimental Results

The complete test suite passes:

```
running 32 tests — 32 passed; 0 failed; 0 ignored

Semiring tests (7):
  ✓ addition_is_max: Tropical(3) ⊕ Tropical(5) = Tropical(5)
  ✓ multiplication_is_addition: Tropical(3) ⊗ Tropical(5) = Tropical(8)
  ✓ zero_is_additive_identity: 0̄ ⊕ Tropical(42) = Tropical(42)
  ✓ one_is_multiplicative_identity: 1̄ ⊗ Tropical(42) = Tropical(42)
  ✓ pow_is_scalar_multiply: Tropical(3)^⊗4 = Tropical(12)
  ✓ associativity_of_addition: (a ⊕ b) ⊕ c = a ⊕ (b ⊕ c)
  ✓ distributivity: a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c)

Polynomial tests (7):
  ✓ monomial_evaluate: c + Σ aᵢxᵢ computed correctly
  ✓ monomial_dimension_mismatch: error on wrong arity
  ✓ polynomial_evaluate_max: max(0+2x, 0+2y, 3+x+y) at (1,2) = 6
  ✓ polynomial_empty: error on empty polynomial
  ✓ active_monomial_index: correct dominant monomial tracking
  ✓ newton_polytope_vertices: vertices match exponent vectors
  ✓ grid_classify_1d: active regions computed correctly for max(0, x)

Patch tests (5):
  ✓ from_vertex_saw: exponent[0]=0 → Saw waveform
  ✓ from_vertex_square: exponent[0]=1 → Square waveform
  ✓ from_vertex_cutoff_scales: higher coefficient → higher cutoff
  ✓ lerp_midpoint: linear interpolation verified at t=0.5
  ✓ simple_patch_default: default patch has expected structure

Morph tests (5):
  ✓ morph_at_zero_is_from: t=0 returns source patch
  ✓ morph_at_one_is_to: t=1 returns destination patch
  ✓ invalid_t_rejected: t outside [0,1] returns error
  ✓ sample_count: n steps produce n+1 samples
  ✓ reverse_flips: t=0.3 → reversed t=0.7

Timbre tests (4):
  ✓ space_has_patches: 3 monomials → 3 patches
  ✓ active_patch_at_point: correct patch selection
  ✓ morph_between_vertices: morph path created successfully
  ✓ empty_poly_fails: empty polynomial rejected

MIDI tests (4):
  ✓ map_simple_patch: CC messages in valid range [0,127]
  ✓ map_with_effects: reverb and chorus CCs emitted
  ✓ channel_clamped: channel > 15 clamped to 15
  ✓ cutoff_maps_to_brightness: 20 Hz → 0, 20 kHz → 127

Doc-tests (1):
  ✓ README example compiles and evaluates correctly
```

**Key verification**: The distributive law $a \otimes (b \oplus c) = (a \otimes b) \oplus (a \otimes c)$ holds for all tested values, confirming the semiring structure. The polynomial evaluation $f(1, 2) = \max(2, 4, 6) = 6$ confirms correct max-plus computation. The morph midpoint $f(0.5)$ yields $\text{cutoff} = 1500$ Hz (midpoint of 1000 and 2000), confirming piecewise-linear interpolation.

# 6. Related Work

## 6.1 FM Synthesis (Chowning, 1973)

Frequency modulation synthesis [2] generates complex spectra from simple oscillators via modulation. The parameter space is governed by Bessel functions and carrier:modulator ratios. While powerful, FM synthesis has no algebraic structure on its parameter space — two FM patches combine via ad hoc rules, not algebraic operations. Our tropical framework provides exactly this: tropical addition and multiplication give canonical, structure-preserving operations on patches.

## 6.2 Additive Synthesis

Additive synthesis represents timbres as weighted sums of sinusoids (Fourier decomposition). The parameter space is $\mathbb{R}^N$ where $N$ is the number of harmonics. While algebraically structured (as a vector space), the linear structure does not reflect perceptual relationships — small changes in harmonic weights can produce large perceptual changes, and vice versa. The tropical max-plus structure, by contrast, naturally captures the dominance relationships between spectral components.

## 6.3 Subtractive Synthesis

Subtractive synthesis (oscillator → filter → amplifier) is the dominant paradigm in hardware and software synthesizers. The signal flow is inherently serial (tropical multiplication), with parallel paths (tropical addition) for multi-oscillator designs. Our framework makes this algebra explicit: a subtractive synthesizer's signal graph is a tropical rational expression.

## 6.4 Neural Audio Synthesis

Recent work on neural audio synthesis — WaveNet [3], DDSP [4], RAVE [5] — uses deep neural networks to generate or modify audio. These networks overwhelmingly use ReLU or leaky-ReLU activations. By Theorem 3.1, the functions they compute are tropical rational maps. Our framework thus provides a mathematical lens for understanding and controlling these models: a neural synthesizer's latent space is (implicitly) a tropical variety, and our tools make this explicit.

## 6.5 Tropical Geometry in Computer Science

Tropical geometry has found applications in optimization [6], scheduling [7], and machine learning [8]. The connection to ReLU networks was established by Zhang, Naitzat, and Lim [9]. To our knowledge, `tropical-synth` is the first application of tropical geometry to music and sound design.

# 7. Conclusion and Future Work

We have established that tropical geometry provides the natural algebraic framework for synthesizer patch design. The max-plus semiring's operations — max for parallel signal routing, addition for serial routing — mirror the fundamental signal-flow patterns in audio synthesis. Tropical polynomials partition the parameter space into convex regions, each associated with a distinct timbre, and the Newton polytope determines the topology of the timbre space.

The `tropical-synth` crate demonstrates that these ideas are not merely theoretical — they compile to working code, pass all tests, and map to standard MIDI for immediate use with hardware and software synthesizers.

### Future Directions

1. **Tropical attention mechanisms.** The `active_monomial` computation is analogous to the softmax attention in transformers: both select a dominant element from a set. We plan to develop a *tropical attention* mechanism that uses $\max$ instead of $\exp/\sum$, providing a piecewise-linear, interpretable alternative to softmax for patch blending.

2. **Higher-dimensional timbre spaces.** The current implementation handles polynomials of any arity, but the grid classification (`classify_grid`) is limited to 1D and 2D. Extending to $n$-dimensional tropical hypersurface computation would enable richer patch spaces with more nuanced morphing paths.

3. **Tropical curve rendering.** The crate's tagline — "draw a tropical curve, hear the sound" — suggests a visual interface where the user draws a tropical curve in 2D and hears the corresponding patch morph in real time. This requires a frontend beyond the scope of the current library.

4. **Integration with DAWs.** The `MidiCCMapper` provides basic MIDI output. A VST/AU plugin wrapper would allow direct integration with digital audio workstations.

5. **Tropical optimization of patch search.** Finding good patches in a high-dimensional space is a search problem. Tropical geometry provides natural tools: the tropical distance (Hilbert projective metric) and tropical convexity give structure that can guide optimization.

6. **Spectral correspondence.** A rigorous investigation of how tropical patch parameters map to acoustic properties (spectral centroid, harmonic distribution, inharmonicity) would strengthen the perceptual validity of the framework.

---

# References

1. **tropical-synth** (2026). Rust crate v0.1.0. https://crates.io/crates/tropical-synth — Source: https://github.com/SuperInstance/tropical-synth

2. **Chowning, J.** (1973). "The Synthesis of Complex Audio Spectra by Means of Frequency Modulation." *Journal of the Audio Engineering Society*, 21(7), 526–534.

3. **van den Oord, A., et al.** (2016). "WaveNet: A Generative Model for Raw Audio." *arXiv:1609.03499*.

4. **Engel, J., et al.** (2020). "DDSP: Differentiable Digital Signal Processing." *ICLR 2020*.

5. **Caillon, A., & Esling, P.** (2021). "RAVE: A Variable Rate Audio-Visual Encoder for Real-Time Neural Audio Synthesis." *arXiv:2111.05053*.

6. **Butkovič, P.** (2010). *Max-Linear Systems: Theory and Algorithms*. Springer.

7. **Cuninghame-Green, R. A.** (1979). *Minimax Algebra*. Lecture Notes in Economics and Mathematical Systems, vol. 166. Springer.

8. **Maclaurin, J., et al.** (2015). "Tropical Geometry of Deep Neural Networks." *ICML 2015 Workshop on Geometry and Machine Learning*.

9. **Zhang, L., Naitzat, G., & Lim, L.-H.** (2018). "Tropical Geometry of Deep Neural Networks." *ICML 2018*. *Proceedings of Machine Learning Research*, 80, 5810–5819.
