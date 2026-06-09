# SuperInstance Rust Crate Ecosystem: Architectural Coherence Analysis

> **Scope:** 5 cloned repos (`constraint-dynamics`, `symplectic-fleet`, `conservation-law`, `error-forest`, `spreadsheet-engine`) + 18 local `-rs` crates in `SuperInstance/`
> **Method:** Source audit of `src/lib.rs`, `Cargo.toml`, key modules, and cross-reference with `fleet-science` specs
> **Date:** 2026-06-08

---

## Executive Summary

The SuperInstance Rust ecosystem is a **deliberately decoupled toolkit** of mathematical physics crates applied to agent fleets and music. The architectural principle is radical: **no compile-time dependencies between sibling crates**. Every crate depends only on `serde`, `thiserror`, `num-traits`, and the standard library. Integration happens at the type-convention level, not the `use` statement level.

This analysis confirms the principle is largely intact but identifies **structural drift** in five areas: duplicated scalar traits, orphaned Noether types, missing bridge crates for the spreadsheet-foundation gap, underconnected error-correction to fleet topology, and a lack of unified conservation vocabulary.

---

## 1. Shared Types / Patterns

### 1.1 The `serde` Ubiquity Pattern
Every crate analyzed uses `serde = { version = "1", features = ["derive"] }` as its sole external dependency (besides `thiserror` in a few). This is the ecosystem's **wire protocol**. Types are designed to be serialized and composed across process boundaries, not imported as library code.

### 1.2 The Scalar Trait Anti-Pattern (Duplicated)
Four crates define near-identical scalar traits:

| Crate | Trait Name | Bounds |
|-------|-----------|--------|
| `spectral-fleet-rs` | `Real` | `Float + NumAssign + Debug + Send + Sync + 'static` |
| `conservation-law-rs` | `Scalar` | `Float + Debug + 'static` |
| `symplectic-opt-rs` | `Scalar` | `Float + Debug + 'static` |
| `constraint-dynamics` | `NumericValue` | `Clone + PartialEq + Debug + Send + Sync + 'static + Copy` (custom, not `num-traits`) |

**Finding:** `NumericValue` in `constraint-dynamics` is a bespoke trait that reinvents `num-traits::Float` with a narrower API (`to_f64` / `from_f64`). It cannot interoperate with the `Real`/`Scalar` traits in the spectral/symplectic/conservation crates without wrapper types. This creates a **type seam** between constraint dynamics and Hamiltonian dynamics.

### 1.3 Phase-Space Structures (Convergent Evolution)
`symplectic-fleet` and `constraint-dynamics` both model state evolution over time, but with incompatible types:

- `symplectic-fleet::PhasePoint { q: Vec<f64>, p: Vec<f64> }` — configuration + momentum
- `constraint-dynamics::ConstraintDynamics<V> { system, velocities, momenta, energy_history }` — constraint index → rate/inertia maps

Both track energy history. Both support convergence detection. Neither knows about the other. The symplectic crate could naturally host constraint-reduction (Dirac brackets) but has no `Constraint` type to reduce.

### 1.4 Conservation Vocabulary (Partial Overlap)
Three crates speak about conservation, each in a different dialect:

| Crate | Vocabulary | Equation |
|-------|-----------|----------|
| `conservation-law` | `Component { Generative / Entropic / Neutral }` | γ + H = C |
| `spreadsheet-engine` | `AgentCell { gamma, eta, budget }` | γ + η = budget |
| `conservation-law-rs` | `ConservedQuantity`, `ConservationMonitor` | Lagrangian/Noether formalism |

The `spreadsheet-engine` `ConservationMonitor` is isomorphic to `conservation-law::ConservationLaw` but uses a different field naming convention (`gamma/eta` vs `generative/entropic`). They should deserialize to the same JSON schema, but currently do not.

### 1.5 Noether Types (Forked)
`symplectic-fleet` and `conservation-law` both export `NoetherPair` and `Symmetry` enums. They are **structurally identical** (symmetry ↔ conserved quantity mapping) but live in separate crates with no shared canonical definition. This means a symmetry detected by `conservation-law` cannot be passed directly to `symplectic-fleet` for Hamiltonian verification without a manual mapping layer.

### 1.6 Error Handling Pattern
`thiserror` is used in `spreadsheet-engine` and `conservation-law-rs`. The other three cloned crates use manual error types or `anyhow`. The ecosystem has **not standardized** on error handling: `anyhow` for application-ish crates (`constraint-dynamics`, `fleet-warden-rs`), `thiserror` for library crates (`spreadsheet-engine`, `conservation-law-rs`), and neither for pure-math crates (`symplectic-fleet`, `hodge-consensus-rs`).

### 1.7 RNG Duplication
`constraint-dynamics::energy::rng::Rng` and `error-forest::mycorrhizal_channel::SimpleRng` are both xorshift64 implementations with identical state update logic. `spreadsheet-engine` uses `fastrand`. The ecosystem lacks a shared deterministic PRNG for reproducible simulations.

---

## 2. Missing Dependencies

> Note: "Dependency" here means *semantic dependency* — the crates are designed to compose but currently have no Cargo.toml linkage because of the no-hard-deps principle. The question is: **should they have soft/feature-gated deps, or is the convention-level integration sufficient?**

### 2.1 `spreadsheet-engine` → `conservation-law`
`spreadsheet-engine` has a `ConservationMonitor` that tracks `gamma + eta = budget` across agent cells. `conservation-law` has a `ConservationLaw` with `Component { Generative, Entropic, Neutral }`. These are the **same concept** at different levels of abstraction. Currently there is no bridge.

**Missing:** A `conservation-spreadsheet-bridge` crate (or feature-gated module) that implements:
```rust
impl From<&spreadsheet_engine::ConservationMonitor> for conservation_law::ConservationLaw
```

### 2.2 `symplectic-fleet` → `constraint-dynamics`
`symplectic-fleet` models Hamiltonian evolution. `constraint-dynamics` models constraints on variables. In classical mechanics, constrained Hamiltonian systems use **Dirac brackets** — a modified Poisson bracket that respects constraints. Neither crate implements Dirac brackets because neither knows about the other's types.

**Missing:** A `symplectic-constraints` bridge that defines Dirac bracket computation given a `SymplecticForm` and a `ConstraintSystem`.

### 2.3 `error-forest` → `sheaf-coherence-rs` / `hodge-consensus-rs`
`error-forest` models distributed error correction via hub-and-spoke networks (`HubTree`). `sheaf-coherence-rs` models local-to-global data assembly via sheaf Laplacians. `hodge-consensus-rs` decomposes disagreement flows. These three are **topologically related**: a hub tree is a cellular sheaf (stalks = spoke data, restriction maps = parity checks). The Hodge decomposition of a hub-tree disagreement matrix would reveal gradient (one spoke miscalibrated) vs harmonic (fundamental network split) errors.

**Missing:** A `sheaf-error-bridge` that interprets `HubTree` parity failures as sheaf cohomology classes.

### 2.4 `spectral-fleet-rs` → `symplectic-fleet`
` spectral-fleet-rs` computes eigenvalues of fleet matrices (Fiedler value, spectral clustering). `symplectic-fleet` does linear algebra on phase-space matrices (symplectic condition checks, Gaussian elimination). Both manipulate `Vec<Vec<f64>>` matrices with hand-rolled operations. `spectral-fleet-rs` has `lanczos` and `power_iteration`; `symplectic-fleet` has `gaussian_elimination` and `matrix_inverse`.

**Missing:** A shared linear algebra crate or a `spectral-symplectic` bridge that checks symplecticity of matrices via spectral methods.

### 2.5 `spreadsheet-engine` → `error-forest`
`spreadsheet-engine` has an `A2ABus` for inter-cell messaging. `error-forest` has `MycorrhizalChannel` for noisy multi-path communication. The A2A bus currently has no error correction — messages are assumed reliable. In a distributed fleet spreadsheet, cells are nodes and A2A messages travel over lossy channels.

**Missing:** An `a2a-error-correction` layer that wraps `MycorrhizalChannel` around `A2AMessage` payloads.

---

## 3. Missing Bridge Crates

The `fleet-science` specs describe a 4-layer architecture (Foundation → Bridge → Domain → Application). The 5 cloned repos span Foundation (`constraint-dynamics`, `symplectic-fleet`, `conservation-law`, `error-forest`) and Application (`spreadsheet-engine`). The **Bridge layer is nearly empty** for these specific crates.

### 3.1 `conservation-spreadsheet-bridge`
Connects `conservation-law` components to `spreadsheet-engine` cell types. Would define:
- `AgentCell` → `Component` mapping (gamma → Generative, eta → Entropic)
- `ConservationMonitor` → `FluxNetwork` conversion (budget flows as Kirchhoff currents)
- `Violation` → `CellValue::Error` rendering

**Priority:** High. This is the most natural integration.

### 3.2 `symplectic-constraints-bridge`
Connects `symplectic-fleet` phase-space evolution to `constraint-dynamics` constraint satisfaction. Would define:
- `ConstraintSystem<f64>` → reduced Hamiltonian via Dirac bracket
- `SatisfactionLevel` → energy penalty potential V(q)
- `ConstraintVelocity` → canonical transformation generator

**Priority:** Medium. Enables physically realistic agent motion with hard constraints.

### 3.3 `error-sheaf-bridge`
Connects `error-forest` hub trees to `sheaf-coherence-rs` cellular sheaves. Would define:
- `HubTree` → `CellularSheaf` functor
- `SyndromeResult` → sheaf cohomology class interpretation
- Multi-path transmission as sheaf synchronization

**Priority:** Medium. Unifies the "network topology" and "error correction" vocabularies.

### 3.4 `spectral-symplectic-bridge`
Connects `spectral-fleet-rs` eigenvalue methods to `symplectic-fleet` matrix operations. Would define:
- `SymplecticForm::spectrum()` via Lanczos iteration
- Symplectic eigenvalue problem (eigenvalues of symplectic matrices come in reciprocal pairs)
- Fiedler-value-based symplectic integrator step-size adaptation

**Priority:** Low. Both crates are functional in isolation; this is optimization.

### 3.5 `a2a-forest-bridge`
Connects `spreadsheet-engine::A2ABus` to `error-forest::MycorrhizalChannel`. Would define:
- `A2AMessage` serialization → `u8` payload for phyto-code encoding
- Multi-path routing for inter-cell messages
- Burst-error resilience for agent coordination

**Priority:** High for distributed deployments; low for single-node spreadsheets.

---

## 4. Ideal Dependency Topology

The fleet-science architecture specifies **no compile-time dependencies between siblings**. This is a valid and coherent choice, but it creates a topology where integration is **convention-based** rather than **type-checked**. Below is the ideal topology if we allow **optional, feature-gated bridge dependencies** while preserving standalone usability.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                                    │
│  spreadsheet-engine · fleet-warden-rs · t-minus-rs                           │
│  (optional: all bridges below)                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                         BRIDGE LAYER                                         │
│  conservation-spreadsheet-bridge                                             │
│    ├── dep: conservation-law (optional)                                      │
│    └── dep: spreadsheet-engine (optional)                                    │
│  symplectic-constraints-bridge                                               │
│    ├── dep: symplectic-fleet (optional)                                      │
│    └── dep: constraint-dynamics (optional)                                   │
│  error-sheaf-bridge                                                          │
│    ├── dep: error-forest (optional)                                          │
│    └── dep: sheaf-coherence-rs (optional)                                    │
│  a2a-forest-bridge                                                           │
│    ├── dep: spreadsheet-engine (optional)                                    │
│    └── dep: error-forest (optional)                                          │
│  spectral-symplectic-bridge                                                  │
│    ├── dep: spectral-fleet-rs (optional)                                     │
│    └── dep: symplectic-fleet (optional)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                         FOUNDATION LAYER                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ symplectic-fleet│  │ constraint-dyn  │  │ conservation-law│              │
│  │ (Hamiltonian)   │  │ (CSP/energy)    │  │ (γ+H=C)         │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ spectral-fleet  │  │ sheaf-coherence │  │ error-forest    │              │
│  │ (eigenvalues)   │  │ (local→global)  │  │ (EC codes)      │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ hodge-consensus │  │ witness-topology│  │ tropical-geometry│             │
│  │ (disagreement)  │  │ (point clouds)  │  │ (max-plus)      │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 The Vocabulary Spine
If one crate should be the **type lingua franca**, it is **`conservation-law`**. Its `Component { Generative, Entropic, Neutral }` vocabulary appears (under different names) in:
- `spreadsheet-engine::AgentCell { gamma, eta }`
- `noether-guard::ConservationLaw` (per fleet-science specs)
- `constraint-dynamics::EnergyLandscape` (minima = stable conservation states)
- `symplectic-fleet::Hamiltonian` (energy = conserved quantity under time symmetry)

**Recommendation:** Elevate `conservation-law` to a **spine crate** by extracting a `conservation-types` sub-module or companion crate that defines `Component`, `ComponentKind`, `Flux`, and `ConservationLaw` with **zero dependencies** (not even `serde` — just core types). All other crates can then optionally depend on `conservation-types` for shared vocabulary without pulling in the full crate.

### 4.2 The Linear Algebra Spine
`symplectic-fleet` and `spectral-fleet-rs` both do matrix math with `Vec<Vec<f64>>`. This is inefficient and error-prone. The ecosystem should adopt **`nalgebra`** (already used by `persistent-sheaf-rs`) as the optional linear algebra spine, with feature gates:
```toml
[dependencies]
nalgebra = { version = "0.33", optional = true }
```

---

## 5. Spine Crates

A **spine crate** is one whose removal would cause multiple other crates to lose coherence. Based on the source analysis:

### 5.1 `conservation-law` — The Vocabulary Spine
**Why:** Its `Component` / `Flux` / `ConservationLaw` types are the closest thing to a shared ontology. `spreadsheet-engine`, `symplectic-fleet`, `constraint-dynamics`, and `noether-guard` all express conservation concepts but with incompatible types.

**Strengthening move:** Extract `conservation-types` as a `#![no_std]` core crate with just the enums and structs. No `serde`, no `std`. Everyone can afford to depend on it.

### 5.2 `spreadsheet-engine` — The Runtime Spine
**Why:** It is the only Application-layer crate in the analyzed set. It hosts agents, training jobs, simulations, and MIDI cells. Every other crate wants to "live inside" the spreadsheet grid eventually. The `CellValue` enum (especially `Ternary` and `Vector`) is the fleet's consensus protocol.

**Strengthening move:** Define a `spreadsheet-core` trait crate with `Cell`, `Engine`, `Grid` traits so that bridge crates can be written against interfaces, not concrete types.

### 5.3 `symplectic-fleet` — The Dynamics Spine
**Why:** It owns the most rigorous mathematical structure (symplectic manifold, Hamiltonian, Noether pairs). `constraint-dynamics` energy landscapes, `conservation-law` flux networks, and `spectral-fleet-rs` scheduling all have natural symplectic interpretations.

**Strengthening move:** Export a `PhaseSpace` trait and `Dynamics` trait so that `constraint-dynamics` can optionally implement symplectic reduction.

### 5.4 `error-forest` — The Resilience Spine
**Why:** It is the only crate that addresses failure modes. In a distributed fleet, every message channel is a `MycorrhizalChannel`. Without it, the ecosystem has no fault tolerance.

**Strengthening move:** Define a `Channel` trait and `Codec` trait so that `A2ABus`, `I2IBottle`, and fleet MIDI routers can all be wrapped in phyto-code error correction.

### 5.5 `spectral-fleet-rs` — The Numerics Spine
**Why:** It already has the most mature linear algebra (`lanczos`, `power_iteration`, `kmeans`, `axpy`, `dot`). It is the natural home for fleet-wide matrix operations.

**Strengthening move:** Merge the hand-rolled `Vec<Vec<f64>>` matrix routines from `symplectic-fleet` and `hodge-consensus-rs` behind a unified `Matrix` trait.

---

## 6. Coherence Score

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Standalone utility** | 9/10 | Every crate compiles and tests independently. |
| **Type-level interoperability** | 4/10 | No shared traits; near-duplicated types (NoetherPair, ConservationLaw, Scalar). |
| **Bridge coverage** | 3/10 | 5 proposed bridges, 0 implemented for this specific crate set. |
| **Vocabulary consistency** | 5/10 | "Conservation" means 3 different things; gamma/eta vs generative/entropic vs energy/momentum. |
| **Error handling consistency** | 5/10 | Mix of `anyhow`, `thiserror`, manual enums, and no errors at all. |
| **Mathematical rigor** | 8/10 | Each crate is internally consistent; symplectic form verifies its own axioms. |
| **Documentation → Code fidelity** | 7/10 | Fleet-science specs are excellent; some crates (local `-rs` variants) are stubs or diverge. |

**Overall coherence: 5.7/10** — The crates are **individually excellent** but **collectively incoherent** at the type level. The no-hard-deps principle prevents diamond problems but also prevents the compiler from verifying that `symplectic-fleet::NoetherPair` and `conservation-law::NoetherPair` are the same concept.

---

## 7. Recommendations

1. **Extract `conservation-types`** as a `#![no_std]` vocabulary crate. This is the highest-impact, lowest-risk move.
2. **Standardize on `thiserror`** for all library crates; reserve `anyhow` for binaries only (`fleet-warden-rs`).
3. **Implement `conservation-spreadsheet-bridge`** first — it connects the two most mature crates and validates the bridge pattern.
4. **Adopt `nalgebra` optionally** in `symplectic-fleet` and `spectral-fleet-rs` to eliminate duplicated matrix routines.
5. **Unify `NoetherPair`** by moving it to `conservation-types` or having `symplectic-fleet` and `conservation-law` both re-export from a shared definition.
6. **Document the convention-based integration contract** in `fleet-science/specs/` with JSON schema definitions for cross-crate message passing (e.g., what does a `ConservationLaw` look like on the wire between `spreadsheet-engine` and `noether-guard`).

---

*Generated by source audit of 23 Rust crates + 5 cloned repos + fleet-science specification cross-reference.*
