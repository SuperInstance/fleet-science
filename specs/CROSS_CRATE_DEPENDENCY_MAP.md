# Cross-Crate Dependency Map

**Crates analyzed:** `groovemesh-plr`, `tropical-synth`, `lotka-beats`, `noether-guard`, `spreadsheet-engine`  
**Date:** June 2026  
**Method:** Manual source-code audit of all `src/**/*.rs` files and `Cargo.toml` manifests.

---

## 1. Type Inventory by Crate

### groovemesh-plr v0.1.0

| Module | Public Types | Key Functionality |
|--------|-------------|-------------------|
| `chord` | `PitchClass` (u8), `Quality` (Major/Minor), `Triad` { root, quality } | 24 major/minor triads, pitch-class arithmetic |
| `transform` | `PLR` (P/L/R), `PLRWord` { ops: Vec<PLR> }, `apply()`, `apply_p/l/r()` | Neo-Riemannian group actions, involution properties |
| `voice` | `VoiceLeading` { from, to, movements: [i8;4], distance: u32 }, `minimal_voice_leading()`, `voice_leading_distance()` | Close-position voice leading, semitone-minimal movement |
| `counterpoint` | `CounterpointRules` { no_parallel_fifths, no_parallel_octaves, no_voice_crossing, max_voice_distance: Option<u32> }, `legal_plr_step()`, `legal_path()` | Species counterpoint rule checker, legal PLR walk |
| `lattice` | `Lattice` { adj: HashMap<Triad, Vec<LatticeEdge>> }, `LatticeEdge` { op, target } | PLR Cayley graph, BFS shortest path, graph diameter |
| `nearest` | `nearest_triad()`, `nearest_plr_triad()`, `nearest_by_pitches()` | Pitch-class → nearest triad, PLR-lattice-constrained |
| `group` | `orbit()`, `suborbit()`, `cayley_table()`, `find_word()`, `verify_group_axioms()` | Group-theoretic operations on D12 |
| `error` | `PlrError` { InvalidChordName, InvalidPitchClass, NoValidTriad, NoPath, VoiceLeadingViolation, CounterpointViolation } | thiserror-based error enum |

**Dependencies:** `serde`, `thiserror`.
**No external crate dependencies on other SuperInstance crates.**

### tropical-synth v0.1.0

| Module | Public Types | Key Functionality |
|--------|-------------|-------------------|
| `semiring` | `Tropical` (f64 wrapper), `Tropical::ZERO` (NEG_INFINITY), `Tropical::ONE` (0.0) | max-plus semiring: add=max, mul=+ |
| `polynomial` | `TropicalMonomial` { coefficient, exponents }, `TropicalPolynomial` { monomials }, `NewtonPolytope` { vertices }, `PolytopeVertex` | Tropical polynomial evaluation, active-monomial detection, grid classification |
| `patch` | `SynthPatch` { oscillators, filter, envelope, effects }, `OscillatorWaveform` (Sine/Saw/Square/Triangle/Noise), `OscillatorParams`, `FilterType` (LowPass/HighPass/BandPass/Notch), `FilterParams`, `EnvelopeParams`, `EffectKind` (Reverb/Delay/Chorus/Distortion/Phaser), `EffectParams` | Synthesizer patch mapped from tropical vertex exponents |
| `morph` | `MorphPath` { from, to, t } | Piecewise-linear interpolation between patches |
| `timbre` | `TimbreSpace` { polynomial, patches } | Sound-design space: vertices=patches, edges=morph paths |
| `midi` | `MidiCC` { channel, cc, value }, `MidiCCMapper` { channel } | Maps `SynthPatch` to standard MIDI CC messages |
| `error` | `TropicalSynthError` { DimensionMismatch, EmptyPolynomial, InvalidMorphParameter, InvalidCCNumber, EmptyTimbreSpace } | Custom error enum |

**Dependencies:** `serde`.
**No external crate dependencies on other SuperInstance crates.**

### lotka-beats v0.1.0

| Module | Public Types | Key Functionality |
|--------|-------------|-------------------|
| `species` | `MusicalSpecies` { name, population, growth_rate, death_rate, interaction, scale, rhythm, tempo_range, timbre }, `TimbreProfile` { brightness, warmth, complexity, dynamics } | Agent-like species with musical DNA |
| `dynamics` | `LotkaVolterra` { intrinsic, interaction_matrix, n } | RK4 integration of n-species LV equations |
| `ecosystem` | `MusicEcosystem` { species, time, dt, history }, `EcosystemSnapshot` { time, populations, dominant, diversity } | Time-series simulation, Shannon diversity, dominant detection |
| `equilibrium` | `EquilibriumGenre` { populations, stability, name }, `Stability` (Stable/Unstable/Saddle/Neutral) | Fixed-point solver (Gaussian elimination), stability via Jacobian eigenvalues |
| `genre` | `jazz()`, `classical()`, `electronic()`, `folk()`, `blues()`, `ambient()`, `rock()`, `hip_hop()`, `classic_predator_prey()`, `competitive_three()` | Pre-built species presets with scales, rhythms, tempo ranges |
| `midi` | `MidiEvent` { tick, note, velocity, duration, channel }, `MidiSequence` { events, tempo_bpm, ppqn, name } | Export ecosystem history to MIDI events, population→chord mapping |
| `error` | `Error` { EmptyEcosystem, InvalidSpeciesIndex, InvalidStepSize, DivergentPopulation, InteractionMatrixMismatch } | Custom error enum |

**Dependencies:** `serde`.
**No external crate dependencies on other SuperInstance crates.**

### noether-guard v0.1.0

| Module | Public Types | Key Functionality |
|--------|-------------|-------------------|
| `symmetry` | `Symmetry` (TimeTranslation/SpatialTranslation/Rotation/Gauge(SymmetryGroup)), `SymmetryGroup` { name, generators } | Noether's theorem: symmetry → conserved quantity |
| `conservation` | `ConservationLaw` { symmetry, name, initial_value, tolerance }, `ConservedQuantity` { name, values, drift_rate } | Per-law tolerance checking, drift rate computation |
| `monitor` | `ConservationMonitor` { laws, history, drift_detectors }, `MonitorSnapshot` { time, values, violations } | Multi-law simultaneous monitoring, health scoring |
| `drift` | `DriftDetector` { law_index, threshold, breaking_scale, drift_history } | Threshold violation detection, first-violation time |
| `renormalize` | `RenormalizationGroup` { data }, coarse-grain, `find_breaking_scale()`, `beta_function()` | RG-style scale analysis: block averaging, monotonicity detection |
| `report` | `Report` { total_ticks, health, total_violations, violations }, `Violation` { law_name, law_index, first_violation, last_violation, violation_count, breaking_scale } | Text/JSON reporting, violation timeline |
| `error` | `Error` { NoLaws, ValueCountMismatch, InvalidTolerance, InvalidTime }, `Result<T>` | thiserror-based error enum |

**Dependencies:** `serde`, `serde_json`, `thiserror`.
**No external crate dependencies on other SuperInstance crates.**

### spreadsheet-engine v0.1.0

| Module | Public Types | Key Functionality |
|--------|-------------|-------------------|
| `cell` | `CellId` { row, col }, `CellValue` (Number/Text/Bool/Ternary/Vector/Empty/Error), `CellResult` { value, eval_time, conservation_ok }, `EvalContext` { dependencies, tick, total_budget }, `CellState` (Idle/Evaluating/Ready/Error/Running/Paused), `ValueCell`, `AgentCell` { agent_id, capabilities, gamma, eta, budget, state } | 7 cell types, A1-label addressing, ternary values |
| `grid` | `Grid` { cells, dependencies, dependents, total_budget, tolerance } | Sparse HashMap storage, Kahn's topological sort, cycle detection |
| `engine` | `Engine` { grid, a2a_bus, conservation, tick, tick_rate, values } | Tick-based evaluation loop, cell dispatch table |
| `formula` | `FormulaCell` { operation, inputs, cached, state }, `FormulaOp` (Add/Sub/Mul/Div/Sum/Average/Count/Max/Min/Identity/Evolve/Species/Pareto/Entropy/Conserve) | Evolutionary formulas: genetic optimization, k-means, Pareto front, entropy, conservation |
| `midi` | `MidiCell` { name, state, channel, base_note, velocity, last_event } | Sonifies CellValue → raw MIDI bytes (0x90/0x80) |
| `conservation` | `ConservationMonitor` { total_budget, tolerance, history }, `ConservationTrend` (Improving/Stable/Degrading) | Grid-wide γ+η=budget tracking, violation detection |
| `a2a` | `A2ABus`, `A2ACell`, `A2AMessage` | Inter-cell agent messaging |
| `training` | `TrainingCell`, `TrainingState` | ML training job cell |
| `simulation` | `SimulationCell`, `SimulationState` | Tick-based simulation cell |
| `error` | `Error` { CellNotFound, CycleDetected, ConservationViolation, TrainingError, SimulationError, A2AError, FormulaError }, `Result<T>` | thiserror-based error enum |

**Dependencies:** `tokio`, `serde`, `serde_json`, `thiserror`, `uuid`.
**No external crate dependencies on other SuperInstance crates.**

---

## 2. Proposed Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROPOSED IMPORT GRAPH                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────┐                                                    │
│   │   cmidi-core 0.2.0  │◄────────────────────────────────────┐              │
│   │   (protocol kernel) │                                     │              │
│   └─────────────────────┘                                     │              │
│            ▲                                                  │              │
│            │                                                  │              │
│   ┌────────┴────────┐   ┌─────────────────┐   ┌───────────────┘              │
│   │ cmidi-conservation│   │  si-music-types  │   │                             │
│   │     0.1.0         │   │   (NEW common)   │   │                             │
│   └───────────────────┘   └────────┬────────┘   │                             │
│                                    │             │                             │
│   ┌────────────────────────────────┼─────────────┼─────────────┐              │
│   │                                │             │             │              │
│   ▼                                ▼             ▼             ▼              │
│ ┌──────────────┐          ┌──────────────┐   ┌──────────┐   ┌─────────────┐  │
│ │ groovemesh-  │◄─────────│  lotka-beats │   │ tropical │   │   noether   │  │
│ │    plr       │          │    0.1.0     │   │  -synth  │   │   -guard    │  │
│ └──────┬───────┘          └──────┬───────┘   └────┬─────┘   └──────┬──────┘  │
│        │                         │                │                │         │
│        │    ┌────────────────────┘                │                │         │
│        │    │    ▲                                │                │         │
│        │    │    └────────────────────────────────┘                │         │
│        │    │         (timbre→patch mapping)                       │         │
│        │    │                                                      │         │
│        └───►│◄─────────────────────────────────────────────────────┘         │
│   (counterpoint│  (conservation monitoring, symmetry analysis)               │
│    rules for   │                                                             │
│    formula ops)│                                                             │
│                ▼                                                             │
│      ┌───────────────────┐                                                   │
│      │ spreadsheet-engine│                                                   │
│      │      0.1.0        │                                                   │
│      └───────────────────┘                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dependency Rationale

| Dependent | Dependency | Why |
|-----------|-----------|-----|
| `spreadsheet-engine` | `groovemesh-plr` | `FormulaOp::Evolve/Species/Pareto` need `CounterpointRules` and `VoiceLeading` to ensure generated sequences are musically valid. `PLRWord` can drive `FormulaCell` evolutionary search. |
| `spreadsheet-engine` | `lotka-beats` | `SimulationCell` should embed a `MusicEcosystem` for agent-population dynamics. `MidiCell` should use `ecosystem_to_midi()` instead of rolling its own raw bytes. |
| `spreadsheet-engine` | `tropical-synth` | `MidiCell` should output `SynthPatch` via `MidiCCMapper` rather than hardcoded 0x90 bytes. `AgentCell` capabilities could map to `TimbreProfile`. |
| `spreadsheet-engine` | `noether-guard` | `ConservationMonitor` in the grid should delegate to `noether_guard::ConservationMonitor` for symmetry-aware drift detection. `SimulationCell` should use `RenormalizationGroup` for scale analysis. |
| `spreadsheet-engine` | `cmidi-core` | `MidiCell` should produce `CMidiEvent` and `Conversation` instead of raw `[u8; 3]`. `AgentCell` speech acts should use `SpeechAct`. |
| `spreadsheet-engine` | `cmidi-conservation` | `AgentCell::gamma/eta/budget` is isomorphic to `ConservationVoice`. Grid health should use `FleetSymphony`. |
| `lotka-beats` | `groovemesh-plr` | `EquilibriumGenre::name` generation should use `Triad::from_name()` and `nearest_triad()` to map equilibrium populations to chords. `population_to_chord()` should use `VoiceLeading` for smooth voice leading between steps. |
| `lotka-beats` | `tropical-synth` | `TimbreProfile` should map to `SynthPatch` via `TimbreSpace` so each genre has a synthesizer voice. |
| `tropical-synth` | `groovemesh-plr` | `TimbreSpace::morph()` should validate transitions with `CounterpointRules::check()` to ensure patch morphs don't create parallel fifths in the harmonic domain. `nearest_triad()` can guide chord selection for polyphonic patches. |
| `noether-guard` | `cmidi-conservation` | `ConservationMonitor` should accept `ConservationVoice` inputs and emit `ChordQuality` health reports. Drift thresholds should map to `ConversationCC::Tension`. |

---

## 3. Shared Types to Extract into `si-music-types`

A new `si-music-types` crate (or expansion of `cmidi-core`) should own the following types currently duplicated or near-duplicated across crates:

### 3.1 MIDI Event Types (currently 3 incompatible implementations)

**Current state:**
- `lotka-beats::midi::MidiEvent` { tick, note, velocity, duration, channel }
- `tropical-synth::midi::MidiCC` { channel, cc, value }
- `spreadsheet-engine::midi::MidiCell` emits raw `[u8; 3]`
- `cmidi-core::event::CMidiEvent` { tick, agent_channel, speech_act, velocity, duration, cc_values }

**Extract to `cmidi-core` (extend existing):**
```rust
// In cmidi-core::event — already exists, but needs extension
pub struct CMidiEvent {
    pub tick: u32,
    pub agent_channel: u8,
    pub speech_act: SpeechAct,      // from cmidi-core
    pub velocity: u8,
    pub duration: u32,
    pub cc_values: Vec<(ConversationCC, u8)>,
}

// ADD: low-level MIDI event for synth integration
pub struct MidiNoteEvent {
    pub channel: u8,
    pub note: u8,
    pub velocity: u8,
    pub duration_ticks: u32,
}

pub struct MidiCCEvent {
    pub channel: u8,
    pub cc: u8,
    pub value: u8,
}
```

**Migration:**
- `lotka-beats::MidiEvent` → `cmidi_core::MidiNoteEvent` + `cmidi_core::Conversation` wrapper
- `tropical-synth::MidiCC` → `cmidi_core::MidiCCEvent`
- `spreadsheet-engine::MidiCell::sonify()` → returns `Vec<CMidiEvent>` instead of `Vec<[u8; 3]>`

### 3.2 Pitch Class / Triad Types (duplicated conceptually)

**Current state:**
- `groovemesh-plr::PitchClass` (u8), `Quality`, `Triad`
- `lotka-beats::MusicalSpecies::scale` (Vec<u8> of pitch classes)
- `spreadsheet-engine::MidiCell::base_note` (u8, treated as MIDI note)

**Extract to `groovemesh-plr` (it already owns the richest types):**
Keep `PitchClass`, `Quality`, `Triad` in `groovemesh-plr`. Other crates import them.

**Migration:**
- `lotka-beats::genre` presets should use `Triad::new()` for scale roots instead of magic numbers.
- `spreadsheet-engine::MidiCell` should accept a `Triad` + octave instead of raw `base_note: u8`.

### 3.3 Conservation / Budget Types (duplicated across 3 crates)

**Current state:**
- `cmidi-conservation::ConservationVoice` { agent_id, gamma, eta, budget, midi_channel }
- `spreadsheet-engine::AgentCell` { agent_id, capabilities, gamma, eta, budget, state }
- `noether-guard::ConservationLaw` { symmetry, name, initial_value, tolerance }
- `spreadsheet-engine::ConservationMonitor` { total_budget, tolerance, history }

**Extract to `cmidi-conservation` (already the canonical crate):**
```rust
// Already exists in cmidi-conservation — enrich it
pub struct ConservationVoice {
    pub agent_id: String,
    pub gamma: f64,
    pub eta: f64,
    pub budget: f64,
    pub midi_channel: u8,
    // ADD: capabilities map for spreadsheet-engine integration
    pub capabilities: HashMap<String, f64>,
}
```

**Migration:**
- `spreadsheet-engine::AgentCell` should wrap `ConservationVoice` + `CellState`.
- `spreadsheet-engine::ConservationMonitor` should wrap `FleetSymphony` + `MonitoringStream`.
- `noether-guard::ConservationMonitor` should accept `ConservationVoice` inputs and map `gamma+eta=budget` to a `ConservationLaw` with `Symmetry::Gauge`.

### 3.4 Timbre / Synth Descriptor Types

**Current state:**
- `lotka-beats::TimbreProfile` { brightness, warmth, complexity, dynamics }
- `tropical-synth::SynthPatch` { oscillators, filter, envelope, effects }

**Extract to `tropical-synth` (it owns the synthesis logic):**
Add a `TimbreProfile` → `SynthPatch` mapping function:
```rust
impl SynthPatch {
    pub fn from_timbre(profile: &TimbreProfile, base_note: u8) -> Self;
}
```

**Migration:**
- `lotka-beats::MusicalSpecies` keeps `TimbreProfile` but imports it from `tropical-synth`.

### 3.5 Error Type Unification

**Current state:** 5 custom error enums with overlapping variants.

**Recommendation:** Do NOT unify into a single error type — each crate's errors are domain-specific. Instead, implement `From<PlrError>`, `From<TropicalSynthError>`, etc., for `spreadsheet-engine::Error` so the engine can propagate sub-crate errors cleanly.

---

## 4. Version Compatibility Requirements

| Crate | Current | Target | SemVer Rule | Breaking Changes Needed |
|-------|---------|--------|-------------|------------------------|
| `cmidi-core` | 0.2.0 | 0.3.0 | Minor bump | Add `MidiNoteEvent`, `MidiCCEvent`, `Triad` integration |
| `cmidi-conservation` | 0.1.0 | 0.2.0 | Minor bump | Add `capabilities` to `ConservationVoice`, export `TimbreProfile` |
| `groovemesh-plr` | 0.1.0 | 0.1.0 | Patch | No breaking changes — it's the leaf crate |
| `tropical-synth` | 0.1.0 | 0.1.0 | Patch | No breaking changes — add `From<TimbreProfile>` impl |
| `lotka-beats` | 0.1.0 | 0.1.0 | Patch | No breaking changes — replace `MidiEvent` with cmidi-core types |
| `noether-guard` | 0.1.0 | 0.1.0 | Patch | No breaking changes — add `From<ConservationVoice>` convenience |
| `spreadsheet-engine` | 0.1.0 | 0.2.0 | Minor bump | Major internal refactoring to use all extracted types |

### Dependency Version Constraints

```toml
# In each dependent crate's Cargo.toml
[dependencies]
cmidi-core = "0.3"          # For MIDI protocol types
cmidi-conservation = "0.2"  # For conservation voice / fleet symphony
groovemesh-plr = "0.1"      # For PLR algebra / counterpoint rules
tropical-synth = "0.1"      # For synth patches / timbre space
lotka-beats = "0.1"         # For ecosystem dynamics / genre presets
noether-guard = "0.1"       # For symmetry analysis / drift detection
```

### Feature Flags for Optional Integration

Crates that are currently standalone should gate cross-crate integration behind feature flags so they remain usable independently:

```toml
# groovemesh-plr/Cargo.toml
[features]
default = []
cmidi = ["dep:cmidi-core"]  # Enable CMidiEvent output from triad sequences

# tropical-synth/Cargo.toml
[features]
default = []
counterpoint = ["dep:groovemesh-plr"]  # Enable CounterpointRules in morph()

# lotka-beats/Cargo.toml
[features]
default = []
plr = ["dep:groovemesh-plr"]       # Enable chord voice leading
synth = ["dep:tropical-synth"]     # Enable genre→patch mapping

# noether-guard/Cargo.toml
[features]
default = []
cmidi = ["dep:cmidi-conservation"]  # Enable ConservationVoice input

# spreadsheet-engine/Cargo.toml — all integrations required
[features]
default = ["full"]
full = ["cmidi", "conservation", "plr", "tropical", "lotka", "noether"]
cmidi = ["dep:cmidi-core", "dep:cmidi-conservation"]
plr = ["dep:groovemesh-plr"]
tropical = ["dep:tropical-synth"]
lotka = ["dep:lotka-beats"]
noether = ["dep:noether-guard"]
```

---

## 5. Proposed Workspace Cargo.toml

```toml
[workspace]
members = [
    "cmidi-core",
    "cmidi-conservation",
    "groovemesh-plr",
    "tropical-synth",
    "lotka-beats",
    "noether-guard",
    "spreadsheet-engine",
]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
authors = ["SuperInstance Fleet-Midi Collective"]
license = "MIT"
repository = "https://github.com/SuperInstance"
keywords = ["music", "agents", "midi", "ecosystem"]
rust-version = "1.78"

[workspace.dependencies]
# Internal crates — workspace-local paths
cmidi-core = { path = "cmidi-core", version = "0.3.0" }
cmidi-conservation = { path = "cmidi-conservation", version = "0.2.0" }
groovemesh-plr = { path = "groovemesh-plr", version = "0.1.0" }
tropical-synth = { path = "tropical-synth", version = "0.1.0" }
lotka-beats = { path = "lotka-beats", version = "0.1.0" }
noether-guard = { path = "noether-guard", version = "0.1.0" }
spreadsheet-engine = { path = "spreadsheet-engine", version = "0.2.0" }

# External shared dependencies
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "2"
tokio = { version = "1", features = ["full"] }
uuid = { version = "1", features = ["v4"] }
```

### Per-Crate Cargo.toml (after migration)

#### `spreadsheet-engine/Cargo.toml`
```toml
[package]
name = "spreadsheet-engine"
version = "0.2.0"
edition.workspace = true
authors.workspace = true
license.workspace = true
repository.workspace = true

[features]
default = ["full"]
full = ["cmidi", "plr", "tropical", "lotka", "noether"]
cmidi = ["dep:cmidi-core", "dep:cmidi-conservation"]
plr = ["dep:groovemesh-plr"]
tropical = ["dep:tropical-synth"]
lotka = ["dep:lotka-beats"]
noether = ["dep:noether-guard"]

[dependencies]
tokio = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
thiserror = { workspace = true }
uuid = { workspace = true }

cmidi-core = { workspace = true, optional = true }
cmidi-conservation = { workspace = true, optional = true }
groovemesh-plr = { workspace = true, optional = true }
tropical-synth = { workspace = true, optional = true }
lotka-beats = { workspace = true, optional = true }
noether-guard = { workspace = true, optional = true }
```

#### `lotka-beats/Cargo.toml`
```toml
[package]
name = "lotka-beats"
version = "0.1.0"
edition.workspace = true

[features]
default = []
plr = ["dep:groovemesh-plr"]
synth = ["dep:tropical-synth"]
cmidi = ["dep:cmidi-core"]

[dependencies]
serde = { workspace = true }
groovemesh-plr = { workspace = true, optional = true }
tropical-synth = { workspace = true, optional = true }
cmidi-core = { workspace = true, optional = true }
```

#### `tropical-synth/Cargo.toml`
```toml
[package]
name = "tropical-synth"
version = "0.1.0"
edition.workspace = true

[features]
default = []
counterpoint = ["dep:groovemesh-plr"]

[dependencies]
serde = { workspace = true }
groovemesh-plr = { workspace = true, optional = true }
```

#### `groovemesh-plr/Cargo.toml`
```toml
[package]
name = "groovemesh-plr"
version = "0.1.0"
edition.workspace = true

[features]
default = []
cmidi = ["dep:cmidi-core"]

[dependencies]
serde = { workspace = true }
thiserror = { workspace = true }
cmidi-core = { workspace = true, optional = true }
```

#### `noether-guard/Cargo.toml`
```toml
[package]
name = "noether-guard"
version = "0.1.0"
edition.workspace = true

[features]
default = []
cmidi = ["dep:cmidi-conservation"]

[dependencies]
serde = { workspace = true }
serde_json = { workspace = true }
thiserror = { workspace = true }
cmidi-conservation = { workspace = true, optional = true }
```

---

## 6. Refactoring Checklist

### Phase 1: Extract Common Types (1–2 days)
- [ ] Add `MidiNoteEvent`, `MidiCCEvent` to `cmidi-core::event`
- [ ] Add `capabilities: HashMap<String, f64>` to `cmidi-conservation::ConservationVoice`
- [ ] Move `TimbreProfile` from `lotka-beats` to `tropical-synth` (or new `si-music-types`)
- [ ] Bump `cmidi-core` to 0.3.0, `cmidi-conservation` to 0.2.0

### Phase 2: Leaf Crate Integration (2–3 days)
- [ ] `groovemesh-plr`: add optional `cmidi` feature mapping `PLRWord` → `Vec<CMidiEvent>`
- [ ] `tropical-synth`: add optional `counterpoint` feature validating `MorphPath` with `CounterpointRules`
- [ ] `lotka-beats`: add optional `plr` + `synth` + `cmidi` features; replace `MidiEvent` with `cmidi_core` types
- [ ] `noether-guard`: add optional `cmidi` feature accepting `ConservationVoice` inputs

### Phase 3: Engine Integration (3–4 days)
- [ ] `spreadsheet-engine`: refactor `MidiCell` to use `cmidi-core` types
- [ ] `spreadsheet-engine`: refactor `AgentCell` to wrap `ConservationVoice`
- [ ] `spreadsheet-engine`: refactor `ConservationMonitor` to use `FleetSymphony`
- [ ] `spreadsheet-engine`: add `FormulaOp::PlrWalk` using `groovemesh-plr::legal_path`
- [ ] `spreadsheet-engine`: add `Cell::Ecosystem` wrapping `lotka-beats::MusicEcosystem`
- [ ] `spreadsheet-engine`: add `Cell::Symmetry` wrapping `noether-guard::ConservationMonitor`

### Phase 4: Workspace Setup (1 day)
- [ ] Create root `Cargo.toml` with `[workspace]`
- [ ] Convert all crates to `workspace = true` shared metadata
- [ ] Verify `cargo check --workspace` passes with all feature combinations
- [ ] Add CI matrix testing each crate standalone + with all features enabled

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `cmidi-core` 0.3 breaks downstream consumers | High | High | Keep 0.2 compat layer, deprecate over 2 releases |
| `spreadsheet-engine` refactor is too large | Medium | High | Do it incrementally: one cell type per PR |
| Circular dependency if not careful | Medium | Critical | Strict DAG: core → conservation → leaf crates → engine. Never reverse. |
| Feature-flag explosion | Medium | Medium | Cap at 6 features per crate; require `full` for normal use |
| Performance regression from abstraction | Low | Medium | Benchmark `lotka-beats` MIDI export before/after; zero-cost abstractions only |

---

*Document generated from source-code audit of 48 Rust modules across 6 crates. All type names are verbatim from the source. Proposed changes preserve SemVer compatibility for leaf crates; only `cmidi-core`, `cmidi-conservation`, and `spreadsheet-engine` require minor version bumps.*
