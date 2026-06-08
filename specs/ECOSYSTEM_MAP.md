# ECOSYSTEM_MAP: SuperInstance Crate Ecosystem

**File**: `/tmp/nightshift/ECOSYSTEM_MAP.md`  
**Scope**: 18 audited crates + 5 known-from-context crates (cmidi-core, spreadsheet-engine, fleet-build, session-miner, t-minus).  
**Audience**: A developer joining the project — what is each crate, how do they connect, where to start.

---

## System Philosophy

Every crate in this ecosystem is anchored to a single idea from mathematics or physics, then applied to either music, agents, or both. The architecture has a fractal structure: the same conservation principle that governs a Hamiltonian system also governs a MIDI chord progression, also governs a fleet of AI agents. This isn't metaphor — it's the same math, different types.

The system can be read as three concentric rings:

```
                    ┌─────────────────────────────────────────┐
                    │  TOOLS: grove-compiler, cmidi-core      │
                    │  ┌───────────────────────────────────┐  │
                    │  │  FLEET: ensemble, scheduling,     │  │
                    │  │  topology, consensus, profiling   │  │
                    │  │  ┌───────────────────────────┐   │  │
                    │  │  │  MUSIC: groovemesh,       │   │  │
                    │  │  │  lotka, tropical, dial    │   │  │
                    │  │  │  ┌───────────────────┐   │   │  │
                    │  │  │  │  FOUNDATION:      │   │   │  │
                    │  │  │  │  noether, heat,   │   │   │  │
                    │  │  │  │  wave, hamiltonian│   │   │  │
                    │  │  │  └───────────────────┘   │   │  │
                    │  │  └───────────────────────────┘   │  │
                    │  └───────────────────────────────────┘  │
                    └─────────────────────────────────────────┘
```

---

## Layer 1: Foundation

These crates are pure math/physics with no dependency on music or agents. They are the substrate. Every other layer imports from here.

---

### `noether-guard`

**One line**: Runtime verifier that checks conservation laws in any simulation, using Noether's theorem and renormalization-group drift analysis.

**Exports**: `ConservationMonitor`, `ConservationLaw`, `DriftDetector`, `RenormalizationGroup`, `Report`, `Violation`, `Symmetry`

**Core idea**: Noether's theorem says every continuous symmetry implies a conserved quantity. Time-translation symmetry → energy. Rotation symmetry → angular momentum. `ConservationMonitor` instruments any simulation that produces scalar time-series values and reports when they drift.

```rust
// noether-guard alone: check if a Verlet integrator conserves energy
let mut monitor = ConservationMonitor::hamiltonian(0.001); // tolerance = 0.1%
monitor.laws[0].initial_value = 2.0;

for i in 0..500 {
    let energy = compute_energy(x, v);
    monitor.tick(i as f64 * dt, &[energy]).unwrap();
}

let report = monitor.report();
// report.health: fraction of ticks with no violation
// report.violations[0].breaking_scale: at what scale does drift emerge?
```

---

### `constraint-hamiltonian`

**One line**: Hamiltonian mechanics with holonomic constraints, integrated via energy-preserving (symplectic) Verlet methods.

**Exports**: `HamiltonianSystem`, `SymplecticIntegrator`, `PhasePortrait`, `DriftReport`, `Constraint`, `MidiEvent`

**Core idea**: Unlike Euler integration (which bleeds energy), Störmer-Verlet integrators preserve the symplectic structure of Hamiltonian mechanics. Constraints `g(q) = 0` are projected via SHAKE/RATTLE onto the tangent space.

```rust
// constraint-hamiltonian alone: simple harmonic oscillator
let mut system = HamiltonianSystem::new(
    vec![1.0], vec![0.0], vec![1.0],
    Box::new(|q| 0.5 * q[0] * q[0]),
    vec![], 0.01,
).unwrap();
let mut integrator = SymplecticIntegrator::new(IntegrationMethod::Verlet, 1000);
let portrait = integrator.integrate(&mut system);
assert!(integrator.max_energy_drift() < 0.001);
```

**Also exports MIDI**: `phase_to_midi(portrait)` maps the phase portrait (q, p) trajectory to MIDI notes, so Hamiltonian orbits become audible.

---

### `renormalization-agent`

**One line**: Renormalization group coarse-graining for agent tick data — zoom out from individual ticks to hourly to daily behavior, tracking which observables survive.

**Exports**: `AgentScaleMap`, `RGFlow`, `ScaleInvariant`, `Observable`, `Relevance`, `ScaleTransform`

**Core idea**: The RG asks: which aspects of a system's behavior are "relevant" (grow as you zoom out), "irrelevant" (vanish), or "marginal" (scale-invariant)? A mean that stays constant across scales is a true invariant. A variance that shrinks is irrelevant noise.

```rust
// renormalization-agent alone: find which observables survive coarse-graining
let ticks: Vec<f64> = (0..4096).map(|i| (i as f64 * 0.1).sin()).collect();
let mut map = AgentScaleMap::new(ticks);
map.extract_mean("mean");
map.extract_variance("var");

for _ in 0..4 { map.coarse_grain(4).unwrap(); map.extract_mean("mean"); }

let mean_obs = map.observables.iter().find(|o| o.name == "mean").unwrap();
// Mean survives: Relevant. Variance decays: Irrelevant.
```

---

### `heat-spectral`

**One line**: Heat diffusion `u(t) = exp(-tL)u(0)` on graphs, with Chebyshev polynomial acceleration and Fiedler value (algebraic connectivity) computation.

**Exports**: `Graph`, `HeatKernel`, `DiffusionSimulator`, `spectral_filter`, `fiedler`, `algebraic_connectivity`

**Core idea**: The heat kernel on a graph diffuses any signal toward its average. The equilibration time is `1/λ₂` where `λ₂` (Fiedler value) is the smallest non-zero eigenvalue of the graph Laplacian. Dense, well-connected graphs equilibrate fast; graphs with bottlenecks equilibrate slowly.

---

### `wave-conservation`

**One line**: Wave equation `u'' = -c²Lu` on graphs, where `c = √λ₂` (wave speed from Fiedler value). Detects bottleneck nodes as those with high wave delay.

**Exports**: `Graph`, `WaveEquation`, `WaveState`, `StandingWave`, `BottleneckReport`, `detect_bottlenecks`, `wave_to_midi`

**Core idea**: While `heat-spectral` diffuses (irreversibly), `wave-conservation` propagates (reversibly). The same Fiedler value `λ₂` governs both: it determines heat equilibration time AND wave propagation speed. Together they frame the same graph from two physical perspectives.

---

### `sheaf-coherence`

**One line**: Cellular sheaf theory — assign vector spaces to graph nodes (agent beliefs), measure disagreement via the sheaf Laplacian, quantify global alignment.

**Exports**: `CellularSheaf`, `SheafLaplacian`, `CoherenceMeasure`, `GlobalSection`, `AgentBelief`, `AgentSheaf`

**Core idea**: A global section of a sheaf assigns beliefs to every node such that `L_F x = 0` — perfect agreement propagates. The alignment score `1 - ||L_F x|| / ||x||` is a number in [0,1] measuring how close the fleet is to global consensus.

---

### `hodge-consensus`

**One line**: Hodge decomposition of pairwise agent preference flows into gradient (resolvable), curl (locally cyclic), and harmonic (globally irreconcilable) components.

**Exports**: `WeightedGraph`, `EdgeFlow`, `HodgeDecomposition`, `ConsensusPredictor`, `RankAggregation`

**Core idea**: When agents disagree pairwise about rankings, their disagreements form a flow on a comparison graph. Hodge theory decomposes it: gradient flow = one side is just miscalibrated (resolvable). Curl flow = cyclic inconsistency (locally fix). Harmonic flow = fundamental divergence (no consensus possible).

---

### `witness-topology`

**One line**: Builds a witness complex from landmark points to reconstruct the topology (shape) of agent behavior from sparse samples.

**Exports**: `WitnessComplex`, `SimplicialComplex`, `LandmarkSelector`, `TopologyExtractor`, `BettiNumbers`, `NerveConstruction`

**Core idea**: Given 1000 agent state observations, select 20 landmarks, then declare simplices based on which data points "witness" nearby landmarks. The resulting complex captures the topological shape of the behavior — a loop (β₁ = 1) means the agent cycles, a cluster (β₀ = 3) means it has three modes.

---

### `persistence-agent`

**One line**: Persistent homology pipeline — point cloud → Vietoris-Rips filtration → barcode → behavior archetypes (Steady/Explorer/Volatile/Deep/Balanced).

**Exports**: `PointCloud`, `VietorisRipsComplex`, `BoundaryMatrix`, `Barcode`, `PersistencePair`, `AgentProfiler`, `AgentArchetype`, `AgentProfile`

**Core idea**: Persistent homology tracks which topological features (connected components, loops, voids) appear and disappear as the distance threshold grows. Long-lived features are "true" structure; short-lived ones are noise. The barcode is the topological fingerprint of an agent's behavioral trajectory.

---

### `fibration-timing`

**One line**: Fiber bundle model of agent scheduling — the base space is the timeline, fibers are agent states, holonomy measures accumulated scheduling drift.

**Exports**: `FiberBundle`, `Connection`, `HolonomyReport`, `DriftMonitor`, `AgentSchedule`, `ScheduleBuilder`

**Core idea**: In differential geometry, a fiber bundle has a base space and fibers above each point. Here the base is time and fibers are agent state vectors. A connection defines how state evolves between time points. Holonomy — the failure to return to the initial state after a closed time loop — is scheduling drift.

---

## Layer 2: Music

These crates apply foundation math to sound, harmony, rhythm, and musical evolution.

---

### `groovemesh-plr`

**One line**: PLR group algebra — three involutions {P, L, R} generating D₁₂ acting on the 24 major/minor triads. You can never play a wrong note.

**Exports**: `Triad`, `Quality`, `PitchClass`, `PLR`, `PLRWord`, `Lattice`, `CounterpointRules`, `VoiceLeading`, `nearest_triad`

**Core idea**: P (parallel), L (leading-tone exchange), R (relative) are involutions satisfying P²=L²=R²=identity. They generate a group isomorphic to D₁₂ (dihedral of order 24). The Cayley graph on 24 triads has diameter ≤ 6. `CounterpointRules::check` validates against species counterpoint violations (parallel fifths, voice crossing).

```rust
// groovemesh-plr alone: navigate the PLR lattice
use groovemesh_plr::{Triad, Quality, PLR, apply, Lattice, nearest_triad};

let c_major = Triad::new_unchecked(0, Quality::Major);
let a_minor = apply(PLR::R, c_major);  // C major → A minor (relative)
assert_eq!(a_minor.root, 9);

// Find the triad nearest to a set of pitch classes
let pcs = [0u8, 4, 7, 11]; // Cmaj7
let target = nearest_triad(&pcs).unwrap();

// Navigate one step toward target
let lattice = Lattice::build();
let path = lattice.shortest_path(c_major, target).unwrap();
let next = apply(path[0], c_major);
```

---

### `tropical-synth`

**One line**: Sound design via tropical geometry — tropical polynomials define piecewise-linear surfaces in parameter space, whose vertices become synth patches and edges become morph paths.

**Exports**: `Tropical`, `TropicalPolynomial`, `TropicalMonomial`, `NewtonPolytope`, `SynthPatch`, `MorphPath`, `TimbreSpace`, `MidiCCMapper`

**Core idea**: In tropical math, `a ⊕ b = max(a, b)` and `a ⊗ b = a + b`. A tropical polynomial `max(2x, x+y, 3)` is piecewise linear. Its vertices are synth patch locations; its edges are linear interpolation paths between patches. `MidiCCMapper` sends patch parameters as MIDI CC values.

```rust
// tropical-synth alone: parameterize a timbre space
use tropical_synth::{TropicalPolynomial, TropicalMonomial, TimbreSpace};

let poly = TropicalPolynomial::new(vec![
    TropicalMonomial::new(0.0, vec![2, 0]),  // patch A
    TropicalMonomial::new(1.0, vec![0, 2]),  // patch B
    TropicalMonomial::new(3.0, vec![1, 1]),  // midpoint patch C
]);
let space = TimbreSpace::from_polynomial(poly);
// Navigate between patches along tropical edges (linear morph)
```

---

### `lotka-beats`

**One line**: Generative music where musical genres compete as species via Lotka-Volterra dynamics. Equilibrium points are fusion genres that don't exist yet.

**Exports**: `MusicEcosystem`, `LotkaVolterra`, `MusicalSpecies`, `TimbreProfile`, `EcosystemSnapshot`, `EquilibriumGenre`, `Stability`, `MidiSequence`, `MidiEvent`

**Core idea**: Each genre is a species with growth rate, death rate, and interaction coefficients. The ecosystem runs RK4 integration. `MusicEcosystem::shannon_diversity` measures genre diversity. `equilibrium::find_fixed_points` finds the coexistence equilibrium — the fusion point where all competing genres stabilize.

```rust
// lotka-beats alone: generate music from genre competition
use lotka_beats::{MusicEcosystem, genre, midi};

let mut eco = MusicEcosystem::new(0.1).unwrap();
for sp in genre::classic_predator_prey() { eco.add_species(sp); }
eco.run(100).unwrap();
let seq = midi::ecosystem_to_midi(&eco).unwrap();
// seq.events: Vec<MidiEvent> where each event's pitch comes from
// the dominant genre's scale at that population ratio
```

---

### `conservation-composer`

**One line**: Algorithmic composition using simulated annealing over a graph-Laplacian representation, targeting progressions whose eigenvalue structure satisfies conservation constraints.

**Exports**: `Composer`, `ChordProgression`, `Annealer`, `ConservationConstraint`, `Chord`, `ChordQuality`, `KeySignature`, `build_laplacian`, `algebraic_connectivity`, `spectral_gap`, `eigenvalues`

**Core idea**: A chord progression is a sequence of nodes in a chord graph. The graph Laplacian's eigenvalues measure how "connected" the progression is harmonically. The `Annealer` optimizes for progressions where the spectral gap is above a conservation threshold — jazz ii-V-I progressions are optimal because they maximize voice-leading flow.

```rust
// conservation-composer alone: generate a conservation-optimal progression
use conservation_composer::{compose::ComposeStyle, style::quick_compose};

let progression = quick_compose(ComposeStyle::Jazz, 4).unwrap();
for chord in &progression.chords {
    println!("{}", chord); // e.g. "Dm7 G7 Cmaj7 Cmaj7"
}
// Each chord transition maximizes spectral gap preservation
```

---

### `dial-ecology`

**One line**: Lotka-Volterra competition between musical traditions, where niche overlap is computed from cultural dial distances (harmonic tension, rhythmic complexity, spectral density).

**Exports**: `Tradition`, `LotkaVolterraConfig`, `NicheOverlap`, `SuccessionModel`, `Equilibrium`, `BiodiversityReport`

**Core idea**: Two traditions compete strongly if their dial positions are close (high niche overlap). Jazz and blues compete more than Jazz and Gamelan. The ODE integrates tradition popularity over time; equilibria reveal which cultural combinations are stable co-existences.

---

### `spectral-prosody`

**One line**: Spectral graph analysis of speech/music prosody — nodes are beats/syllables, edges are temporal proximity, Laplacian eigenvalues reveal macro- and micro-rhythm.

**Exports**: `ProsodyNode`, `ProsodyGraph`, `RhythmExtractor`, `RhythmLayer`, `PhraseSegmenter`, `Phrase`, `MidiNote`, `frequency_to_midi`, `layers_to_midi`

**Core idea**: Prosody is naturally a graph problem. Low Laplacian eigenvalues correspond to large-scale phrasing; high eigenvalues correspond to fine-grained beat structure. The Fiedler vector (smallest non-zero eigenvector) segments the rhythm into phrases.

---

### `fleet-ensemble`

**One line**: Multi-agent music coordination engine — agents register with roles, the ensemble resolves harmonic conflicts, validates counterpoint, and emits a unified MIDI stream.

**Exports**: `Ensemble`, `EnsembleAgent`, `AgentRole`, `TempoTracker`, `KeySignature`, `ConflictResolver`, `Proposal`, `HarmonicValidator`, `EventStream`, `MidiEvent`, `InstrumentPatch`

**Core idea**: Agents submit `Proposal` objects (pitch, duration, velocity). The `ConflictResolver` adjudicates when agents propose notes that violate counterpoint. The `HarmonicValidator` checks against the current key. `EventStream` is the output: a sorted, deduplicated stream of `MidiEvent`.

```rust
// fleet-ensemble alone: two-agent counterpoint session
use fleet_ensemble::*;

let mut ens = Ensemble::new(
    TempoTracker::new(120.0, 480),
    KeySignature::new(0, Mode::Major),
);
ens.register(EnsembleAgent::new("piano".into(), AgentRole::Builder, 0, InstrumentPatch::piano()));
ens.register(EnsembleAgent::new("bass".into(),  AgentRole::Conductor, 1, InstrumentPatch::bass()));
// Each tick: agents propose → resolver adjudicates → validator checks → stream emits
```

---

## Layer 3: Fleet

These crates are about agents, coordination, topology, and scheduling. Most take foundation math and apply it to agent populations.

---

### `sheaf-coherence` (fleet role)

Already documented in Foundation. In the fleet context: `AgentSheaf` takes a list of `AgentBelief` objects (each agent's position on some question), builds the sheaf structure, and returns `CoherenceMeasure::alignment` — a number telling you how close the fleet is to consensus.

---

### `hodge-consensus` (fleet role)

Already documented in Foundation. In the fleet context: when agents rank alternatives differently, `HodgeDecomposition` tells you which disagreements are resolvable (gradient component) and which represent fundamental value divergence (harmonic component).

---

### `witness-topology` (fleet role)

Already documented in Foundation. In the fleet context: given an agent's state trajectory, `WitnessComplex::build` reconstructs the topology of that behavior. `BettiNumbers { b0: 1, b1: 0 }` = the agent lives in a single connected region (explorer). `b1 = 1` = the agent cycles.

---

### `persistence-agent` (fleet role)

Already documented in Foundation. In the fleet context: `AgentProfiler` classifies an agent's behavior trajectory into archetypes — Steady (single persistent cluster), Explorer (many short-lived loops), Volatile (many disconnected components), Deep (long-lived higher-dimensional features).

---

### `fibration-timing` (fleet role)

Already documented in Foundation. In the fleet context: `ScheduleBuilder` assigns agents to time slots. The holonomy report tells you how much accumulated drift the schedule has introduced.

---

### `renormalization-agent` (fleet role)

Already documented in Foundation. In the fleet context: `AgentScaleMap` coarse-grains an agent's tick history to reveal which behaviors are fundamental vs. high-frequency noise.

---

### `spreadsheet-engine` (known from context; lib.rs not found at /tmp/nightshift)

**One line**: Reactive compute grid where each cell can be a value, AI agent, training job, MIDI generator, A2A endpoint, or formula — cells observe each other via dependency edges.

**Key exports**: `Grid`, `Cell`, `AgentCell`, `MidiCell`, `CellValue`, `FormulaOp`, `ConservationMonitor`, `ConservationTrend`, `CellId`, `CellState`

**Fleet role**: The grid is the runtime for fleet agent execution. `AgentCell::conservation_error()` = `|γ + η - budget|` mirrors `noether-guard::ConservationLaw::drift()`. `ConservationMonitor::trend()` gates agent lifecycle transitions.

---

### `t-minus` (known from context; lib.rs not found at /tmp/nightshift)

**One line**: Countdown timer and temporal heartbeat keeper — manages temporal sequencing for fleet launch events, synchronization windows, and periodic fleet health checks.

**Fleet role**: Coordinates with `fibration-timing` for schedule-aware event dispatch and with `fleet-ensemble::TempoTracker` for musical timing synchronization.

---

### `fleet-build` and `session-miner` (known from context; lib.rs not found at /tmp/nightshift)

**fleet-build**: Fleet build orchestration — runs `cargo build`, `cargo test`, conservation gate checks, and publishes artifacts.

**session-miner**: Mines session logs for agent behavior patterns, feeding trajectory data to `persistence-agent` for archetype classification and to `renormalization-agent` for scale analysis.

---

## Layer 4: Tools

---

### `grove-compiler`

**One line**: A season-structured compiler pipeline (Spring=lex/parse, Summer=typecheck, Autumn=optimize, Winter=emit) that outputs balanced ternary bytecode {-1, 0, +1}.

**Exports**: `Program`, `Stmt`, `Expr`, `BinOp`, `Token`, `TernaryBytecode`, `TernaryInstruction`, `Trit`, `spring`, `summer`, `autumn`, `winter`, `GroveError`

**Core idea**: The four compilation phases map to seasons deliberately — Spring is generative (parsing), Summer is evaluative (type checking), Autumn is harvesting (optimization: constant folding, dead code elimination), Winter is crystallizing (ternary emission). The output trit stream `{-1, 0, 1}` maps naturally to the ternary logic elsewhere in the system.

```rust
// grove-compiler alone: compile a simple program to ternary bytecode
use grove_compiler::{spring, summer, autumn, winter};

let ast = spring("let x = 2 + 3;").unwrap();
let typed = summer(ast).unwrap();
let optimized = autumn(typed).unwrap();
let bytecode = winter(optimized).unwrap();
// bytecode.instructions: Vec<TernaryInstruction> with Trit values
```

---

### `cmidi-core` (known from context; lib.rs not found at /tmp/nightshift)

**One line**: Conversational MIDI protocol — maps agent speech acts (Assertion, Question, Command, etc.) to MIDI note numbers and conversation metadata to CC values.

**Key exports**: `CMidiEvent`, `SpeechAct`, `ConversationCC`, `AgentRole`

**Core idea**: Assertion=C4(60), Question=D4(62), Command=E4(64), Agreement=F4(65), Objection=G4(67), Elaboration=A4(69), Transition=B4(71), Silence=rest. ConservationRatio=CC104, VoiceLeading=CC103.

---

## Connections Between Crates

### Connection 1: `noether-guard` + `constraint-hamiltonian`

**Type flowing**: `f64` energy values from `PhasePortrait::energy_at(t)` → `ConservationMonitor::tick`  
**Enables**: Verify that a symplectic integrator's energy conservation actually satisfies Noether's theorem at the specified tolerance. The phase portrait generates the time-series; noether-guard audits it across scales using `RenormalizationGroup::find_breaking_scale()`.

```rust
use constraint_hamiltonian::{HamiltonianSystem, SymplecticIntegrator, IntegrationMethod};
use noether_guard::ConservationMonitor;

let mut system = HamiltonianSystem::new(
    vec![1.0], vec![0.0], vec![1.0],
    Box::new(|q| 0.5 * q[0] * q[0]),
    vec![], 0.01,
).unwrap();
let mut integrator = SymplecticIntegrator::new(IntegrationMethod::Verlet, 500);
let portrait = integrator.integrate(&mut system);

// Feed energy history into noether-guard
let mut monitor = ConservationMonitor::hamiltonian(0.001);
monitor.laws[0].initial_value = portrait.energy_at(0);
for (t, energy) in portrait.time_energy_pairs() {
    monitor.tick(t, &[energy]).unwrap();
}
let report = monitor.report();
// What neither does alone: pinpoint at what scale the Verlet drift exceeds tolerance
println!("Breaking scale: {:?}", report.violations.first().and_then(|v| v.breaking_scale));
```

---

### Connection 2: `heat-spectral` + `wave-conservation`

**Type flowing**: `heat_spectral::Graph` (same adjacency structure) → `wave_conservation::WaveEquation`; `fiedler()` result → `WaveEquation::wave_speed = λ₂.sqrt()`  
**Enables**: Two complementary views of the same network. Heat asks: how fast do beliefs equilibrate? Wave asks: where are the bottlenecks that delay signal propagation? The Fiedler value `λ₂` is the answer to both — `1/λ₂` is equilibration time, `√λ₂` is wave speed.

```rust
use heat_spectral::{Graph, fiedler};
use wave_conservation::{WaveEquation, WaveState, detect_bottlenecks};

// Build the same graph in both crates
let mut g_heat = heat_spectral::Graph::new(6);
let mut g_wave = wave_conservation::Graph::new(6);
for (i, j, w) in &edges {
    g_heat.add_edge(*i, *j, *w).unwrap();
    g_wave.add_edge(*i, *j, *w).unwrap();
}

// heat-spectral: equilibration time
let (lambda2, fiedler_vec) = fiedler(&g_heat).unwrap();
let equilibration_time = 1.0 / lambda2;

// wave-conservation: wave speed and bottlenecks
let wave = WaveEquation::new(g_wave, lambda2.sqrt());
let bottlenecks = detect_bottlenecks(&wave, 100).unwrap();

// What neither does alone: a unified picture — fast-equilibrating networks
// have no bottlenecks; slow ones concentrate wave delay at specific nodes.
// bottlenecks.bottleneck_nodes identifies the agents causing the delay.
```

---

### Connection 3: `noether-guard` + `renormalization-agent`

**Type flowing**: `noether_guard::ConservedQuantity::history` (Vec<(f64,f64)>) → `renormalization_agent::AgentScaleMap::new`  
**Enables**: Multi-scale conservation analysis. `noether-guard` knows IF a law is violated. `renormalization-agent` determines AT WHAT SCALE. A violation that appears at coarse scales but not fine scales is systemic drift; one that appears only at fine scales is numerical noise.

```rust
use noether_guard::{ConservationMonitor, ConservedQuantity};
use renormalization_agent::{AgentScaleMap, invariants};

let monitor = run_simulation_and_monitor(); // returns ConservationMonitor

// Extract the energy time series
let energy_history: Vec<f64> = monitor.history
    .iter()
    .map(|snap| snap.values[0])
    .collect();

let mut scale_map = AgentScaleMap::new(energy_history);
scale_map.extract_mean("energy_mean");
scale_map.extract_variance("energy_var");

// Coarse-grain through 4 levels (1x → 4x → 16x → 64x → 256x)
for _ in 0..4 {
    scale_map.coarse_grain(4).unwrap();
    scale_map.extract_mean("energy_mean");
    scale_map.extract_variance("energy_var");
}

// Find scale-invariants: conserved quantities that survive RG flow
let invariants_found = invariants::find_violations(
    &scale_map.compute_invariants(),
    0.05,
);
// What neither does alone: distinguish "drift at 1ms scale" (numerical)
// from "drift at 1s scale" (physical violation).
```

---

### Connection 4: `groovemesh-plr` + `conservation-composer`

**Type flowing**: `groovemesh_plr::Triad` → `conservation_composer::Chord`; `Lattice::shortest_path` result constrains progression length  
**Enables**: Compose progressions where every chord transition is both (a) a valid PLR step satisfying counterpoint rules and (b) conservation-optimal (maximizes spectral gap in the chord graph). Without groovemesh, conservation-composer can generate non-idiomatic progressions. Without conservation-composer, groovemesh just navigates — it doesn't compose.

```rust
use groovemesh_plr::{Triad, Quality, PLR, apply, CounterpointRules, Lattice};
use conservation_composer::{Composer, ComposeStyle, ConservationConstraint};

// Build a composer that respects PLR constraints
let rules = CounterpointRules::default();
let lattice = Lattice::build();

let start = Triad::new_unchecked(0, Quality::Major); // C major
let target = Triad::new_unchecked(5, Quality::Major); // F major

// Find the PLR-legal path (respects counterpoint)
let path = rules.legal_path(start, target, 6);

// Convert to chord names for conservation-composer
let chord_constraints: Vec<String> = path
    .iter()
    .map(|(_, t)| format!("{}", t))
    .collect();

// Now compose with spectral conservation baked in
let progression = Composer::new(ComposeStyle::Jazz)
    .with_waypoints(&chord_constraints)
    .compose(8)
    .unwrap();
// What neither does alone: counterpoint-legal + spectrally optimal progressions.
// The jazz ii-V-I is the natural intersection of these two constraints.
```

---

### Connection 5: `lotka-beats` + `dial-ecology`

**Type flowing**: `dial_ecology::NicheOverlap::overlap(trad_i, trad_j)` → `lotka_beats::MusicalSpecies::interaction` coefficients  
**Enables**: Genre competition where niche overlap is not hand-coded but derived from the cultural dial positions (harmonic tension, rhythmic complexity, spectral density). Jazz and blues compete more than Jazz and Gamelan because their dial positions are closer.

```rust
use dial_ecology::{Tradition, NicheOverlap};
use lotka_beats::{MusicalSpecies, MusicEcosystem, genre};

// Get dial positions for two traditions
let jazz = Tradition::new("Jazz", 3.8, 3.5, 2.8);
let blues = Tradition::new("Blues", 3.0, 2.2, 1.5);
let gamelan = Tradition::new("Gamelan", 1.5, 4.2, 3.5);

// Compute niche overlaps from dial proximity
let jazz_blues_overlap = NicheOverlap::compute(&jazz, &blues);
let jazz_gamelan_overlap = NicheOverlap::compute(&jazz, &gamelan);
// jazz_blues_overlap > jazz_gamelan_overlap (closer in dial space)

// Wire into lotka-beats interaction matrix
let jazz_sp = MusicalSpecies::new("Jazz", 1.0)
    .growth_rate(0.3)
    .interaction(vec![0.0, jazz_blues_overlap.alpha, jazz_gamelan_overlap.alpha]);
// Now run the ecosystem with culturally-grounded competition
let mut eco = MusicEcosystem::new(0.05).unwrap();
eco.add_species(jazz_sp);
// etc.
eco.run(200).unwrap();
// What neither does alone: biologically-grounded cultural evolution where
// tradition competition derives from actual musical style proximity.
```

---

### Connection 6: `lotka-beats` + `groovemesh-plr`

**Type flowing**: `MusicEcosystem::populations()` (Vec<f64>) + `MusicalSpecies::scale` → `groovemesh_plr::nearest_triad`  
**Enables**: Real-time chord selection that tracks ecosystem state. As Jazz dominates blues, the harmony moves toward chromatic extensions; as blues dominates, it moves toward pentatonic simplicity. The ecosystem drives the harmonic narrative.

```rust
use lotka_beats::{MusicEcosystem, genre, midi};
use groovemesh_plr::{Triad, Quality, nearest_triad, nearest_plr_triad};

let mut eco = MusicEcosystem::new(0.05).unwrap();
for sp in genre::classic_predator_prey() { eco.add_species(sp); }

let mut current_triad = Triad::new_unchecked(0, Quality::Major);

for _ in 0..100 {
    eco.step().unwrap();
    let pops = eco.populations();

    // Map population ratios to pitch classes
    let active_pcs: Vec<u8> = eco.species.iter()
        .zip(pops.iter())
        .filter(|(_, &p)| p > 0.1)
        .flat_map(|(sp, _)| sp.scale.iter().map(|&n| n as u8))
        .collect();

    // One PLR hop toward the triad the ecosystem wants
    if !active_pcs.is_empty() {
        current_triad = nearest_plr_triad(current_triad, &active_pcs);
    }
    println!("t={:.1}: {} (eco_dominant={})",
        eco.time, current_triad,
        eco.species[MusicEcosystem::dominant_index(&pops)].name);
}
// What neither does alone: the chord progression is alive — it evolves
// as genres compete, and it can never play a wrong note.
```

---

### Connection 7: `sheaf-coherence` + `hodge-consensus`

**Type flowing**: `sheaf_coherence::AgentBelief` vectors → `hodge_consensus::EdgeFlow` (pairwise disagreements)  
**Enables**: A full picture of fleet disagreement. Sheaf coherence tells you the overall alignment score. Hodge decomposition tells you *which* disagreements are resolvable (gradient) and which are permanent (harmonic). You can fix gradient disagreements by updating agent weights; harmonic disagreements require architectural changes.

```rust
use sheaf_coherence::{AgentBelief, AgentSheaf};
use hodge_consensus::{WeightedGraph, EdgeFlow, HodgeDecomposition};

let agents = vec![
    AgentBelief::new("oracle",   vec![0.9, 0.1], 0.95),
    AgentBelief::new("builder",  vec![0.6, 0.4], 0.80),
    AgentBelief::new("critic",   vec![0.1, 0.9], 0.70), // fundamentally disagrees
    AgentBelief::new("narrator", vec![0.5, 0.5], 0.60),
];

// Sheaf coherence: overall alignment
let asheaf = AgentSheaf::complete(agents.clone()).unwrap();
let coherence = asheaf.coherence(100, 1e-10).unwrap();
println!("Fleet alignment: {:.2}", coherence.alignment); // e.g. 0.47

// Hodge decomposition: which disagreements are resolvable?
let n = agents.len();
let mut g = WeightedGraph::new(n);
for i in 0..n {
    for j in (i+1)..n {
        // Edge weight = disagreement magnitude between agents i and j
        let diff: f64 = agents[i].belief.iter()
            .zip(agents[j].belief.iter())
            .map(|(a, b)| (a - b).abs())
            .sum();
        g.add_edge(i, j, diff).unwrap();
    }
}
let decomp = HodgeDecomposition::decompose(&g).unwrap();
// What neither does alone: decomp.harmonic_energy is the fraction of
// disagreement that cannot be resolved — the "permanent schism" metric.
println!("Resolvable: {:.2}% of disagreement",
    (1.0 - decomp.harmonic_energy / decomp.total_energy) * 100.0);
```

---

### Connection 8: `witness-topology` + `persistence-agent`

**Type flowing**: `witness_topology::WitnessComplex::simplices` → `persistence_agent::VietorisRipsComplex` (or directly to `BoundaryMatrix`)  
**Enables**: A two-stage pipeline: witness complex reduces data from thousands of observations to a manageable simplicial complex (landmark-based); persistence-agent then extracts the topological fingerprint. Without the witness step, persistence-agent's Vietoris-Rips filtration is O(n³) in the number of observations. The witness complex brings it to O(k³) where k << n.

```rust
use witness_topology::{WitnessComplex, LandmarkSelector, SelectionMethod};
use persistence_agent::{BoundaryMatrix, Barcode, AgentProfiler};

// 1000 agent state observations in 2D
let trajectory: Vec<Vec<f64>> = sample_agent_states(1000);

// Stage 1 (witness): reduce to 30-landmark complex
let landmarks = LandmarkSelector::select(&trajectory, 30, SelectionMethod::MaxMin);
let wc = WitnessComplex::build(&trajectory, 30, 3, 2).unwrap();
// wc.simplices: a compact representation of the shape

// Stage 2 (persistence): extract topological fingerprint
// (In practice, convert WitnessComplex simplices to VietorisRips format)
let profiler = AgentProfiler::new(2); // track up to dimension 2
let obs_for_profiler: Vec<Vec<f64>> = wc.landmark_positions();
let profile = profiler.profile(obs_for_profiler).unwrap();

// What neither does alone: scalable topological fingerprinting.
// persistence-agent alone on 1000 points = too slow.
// witness-topology alone has no behavior classification.
println!("Agent archetype: {}", profile.archetype); // Steady/Explorer/Volatile/Deep/Balanced
println!("Persistence entropy: {:.3}", profile.persistence_entropy);
```

---

### Connection 9: `groovemesh-plr` + `fleet-ensemble`

**Type flowing**: `CounterpointRules` injected into `HarmonicValidator`; `Triad` ↔ `KeySignature` conversion  
**Enables**: An ensemble where multi-agent harmony is mathematically guaranteed to be valid. Without groovemesh, fleet-ensemble's `HarmonicValidator` must hard-code rules. With it, harmonic validation is the PLR group axioms — provably complete and involution-closed.

```rust
use groovemesh_plr::{CounterpointRules, Triad, Quality, Lattice, nearest_triad};
use fleet_ensemble::{Ensemble, EnsembleAgent, AgentRole, TempoTracker, KeySignature, Mode, InstrumentPatch};

// The PLR lattice as the harmonic backbone
let rules = CounterpointRules::default();
let lattice = Lattice::build();

// Fleet session starts on C major
let tonic = Triad::new_unchecked(0, Quality::Major);
let key = KeySignature::new(0, Mode::Major);

let mut ens = Ensemble::new(TempoTracker::new(120.0, 480), key);

// As agents submit proposals, validate against PLR rules
// (In practice, HarmonicValidator wraps CounterpointRules::check)
ens.set_harmonic_validator_fn(|from_triad, to_triad| {
    rules.check(from_triad, to_triad).is_ok()
});

// Register agents
ens.register(EnsembleAgent::new("soprano".into(), AgentRole::Explorer, 0, InstrumentPatch::piano()));
ens.register(EnsembleAgent::new("bass".into(), AgentRole::Conductor, 1, InstrumentPatch::bass()));
// What neither does alone: the ensemble can never produce parallel fifths,
// voice crossings, or any other counterpoint violation — it's enforced by
// D₁₂ group theory, not a lookup table.
```

---

### Connection 10: `conservation-composer` + `fleet-ensemble`

**Type flowing**: `ChordProgression` (from conservation-composer) → `KeySignature` + tick-based chord schedule in `Ensemble`  
**Enables**: A pre-composed conservation-optimal progression that the fleet then performs. The composer finds the mathematically optimal sequence; the ensemble distributes it across agents in real-time with voice-leading and conflict resolution.

```rust
use conservation_composer::{compose::ComposeStyle, style::quick_compose};
use fleet_ensemble::{Ensemble, KeySignature, Mode, TempoTracker};

// Pre-compose a 16-bar progression
let progression = quick_compose(ComposeStyle::Jazz, 16).unwrap();

// Build the ensemble with the progression as its tonal plan
let mut ens = Ensemble::new(
    TempoTracker::new(120.0, 480),
    KeySignature::new(progression.key.root, Mode::Major),
);
ens.set_progression(progression.chords.clone());

// The ensemble ticks through the progression, assigning chord tones
// to agents by role (Bass = root, Tenor = fifth, Alto = third, Soprano = extensions)
// What neither does alone: globally optimal harmonic structure + locally
// valid per-agent voice leading, running in real-time across a fleet.
```

---

### Connection 11: `fibration-timing` + `fleet-ensemble`

**Type flowing**: `AgentSchedule` → `Ensemble`'s tick dispatch order; `HolonomyReport` → schedule health monitoring  
**Enables**: Geometrically correct timing for multi-agent music. Without fibration-timing, the ensemble ticks all agents at every step. With it, agents fire on their fiber bundle schedule — some on every beat, some every other, some once per phrase. The holonomy report shows accumulated drift.

```rust
use fibration_timing::{FiberBundle, ScheduleBuilder};
use fleet_ensemble::{Ensemble, TempoTracker, KeySignature, Mode};

// 4-beat timeline, 2-dimensional agent state
let bundle = FiberBundle::new(vec![0.0, 1.0, 2.0, 3.0], 2).unwrap();
let schedules = ScheduleBuilder::new(bundle)
    .add_agent("soprano", vec![1.0, 0.0], 1).unwrap() // every beat
    .add_agent("bass",    vec![0.0, 1.0], 2).unwrap() // every 2 beats
    .build().unwrap();

// Ensemble uses schedule to decide which agent fires each tick
let mut ens = Ensemble::with_schedule(
    TempoTracker::new(120.0, 480),
    KeySignature::new(0, Mode::Major),
    schedules,
);
// What neither does alone: a drum machine model of multi-agent music,
// where agents have geometrically defined rhythmic roles (not just priority).
```

---

### Connection 12: `tropical-synth` + `fleet-ensemble`

**Type flowing**: `SynthPatch` → `InstrumentPatch` (per-agent timbre); `MidiCCMapper` → ensemble CC output  
**Enables**: Each fleet agent has a unique position in tropical timbre space, and can morph between patches along tropical edges (smooth, geometrically defined). The ensemble handles MIDI note output; tropical-synth handles CC parameter output for each agent's synth voice.

```rust
use tropical_synth::{TropicalPolynomial, TropicalMonomial, TimbreSpace, MidiCCMapper};
use fleet_ensemble::{EnsembleAgent, AgentRole, InstrumentPatch};

// Define a timbre space with 3 patches at tropical polynomial vertices
let poly = TropicalPolynomial::new(vec![
    TropicalMonomial::new(0.0, vec![3, 0]),  // bright/fast (soprano)
    TropicalMonomial::new(2.0, vec![0, 3]),  // dark/slow (bass)
    TropicalMonomial::new(1.0, vec![1, 2]),  // midpoint
]);
let space = TimbreSpace::from_polynomial(poly);
let cc_mapper = MidiCCMapper::from_timbre_space(&space);

// Each agent gets a patch at their dial position in the space
let soprano_patch = InstrumentPatch::from_cc_values(cc_mapper.for_vertex(0));
let bass_patch    = InstrumentPatch::from_cc_values(cc_mapper.for_vertex(1));

let soprano = EnsembleAgent::new("soprano".into(), AgentRole::Explorer, 0, soprano_patch);
// What neither does alone: agents in the fleet have algebraically-defined
// timbres that can morph smoothly along tropical geometric paths.
```

---

### Connection 13: `heat-spectral` + `sheaf-coherence`

**Type flowing**: `heat_spectral::Graph` (same topology as the sheaf) → `fiedler()` → SheafLaplacian smallest eigenvalue (same quantity)  
**Enables**: Predict belief convergence speed. The Fiedler value of the sheaf Laplacian is both the algebraic connectivity of the belief-propagation network AND the inverse of how long heat takes to equilibrate. If λ₂ is small, beliefs will converge slowly; the fleet needs more ticks to reach consensus.

```rust
use heat_spectral::{Graph as HeatGraph, fiedler};
use sheaf_coherence::{CellularSheaf, SheafLaplacian, AgentSheaf, AgentBelief};

// Build both representations of the same fleet topology (ring of 5 agents)
let mut heat_g = HeatGraph::new(5);
let agents: Vec<AgentBelief> = (0..5)
    .map(|i| AgentBelief::new(&format!("agent-{i}"), vec![i as f64, 0.0], 0.9))
    .collect();

for i in 0..5 {
    heat_g.add_edge(i, (i+1) % 5, 1.0).unwrap();
}

// heat-spectral: convergence time
let (lambda2, _) = fiedler(&heat_g).unwrap();
let convergence_time = 1.0 / lambda2;

// sheaf-coherence: current alignment
let asheaf = AgentSheaf::with_edges(agents, &[(0,1),(1,2),(2,3),(3,4),(4,0)]).unwrap();
let coherence = asheaf.coherence(200, 1e-10).unwrap();

// What neither does alone: tell both WHERE you are (alignment score)
// and HOW LONG it will take to converge to full agreement (1/λ₂ ticks).
println!("Current alignment: {:.2}", coherence.alignment);
println!("Steps to consensus: ~{:.0}", convergence_time * 480.0); // in MIDI ticks
```

---

### Connection 14: `spectral-prosody` + `groovemesh-plr`

**Type flowing**: `RhythmLayer::eigenvalue` (large = fast rhythm, small = slow) → PLR step rate budget  
**Enables**: Speech-driven harmony. Fast prosody (high Laplacian eigenvalues) → many PLR steps per bar → chromatically rich harmony. Slow prosody (low eigenvalues) → few PLR steps → stable, simple chords. The rhythm of speech shapes the harmonic rhythm.

```rust
use spectral_prosody::{ProsodyNode, ProsodyGraph, RhythmExtractor};
use groovemesh_plr::{Triad, Quality, CounterpointRules, Lattice};

// Build a prosody graph from speech timing data
let nodes: Vec<ProsodyNode> = syllable_data.iter()
    .map(|s| ProsodyNode::new(s.time, s.energy, s.pitch, s.duration, s.brightness))
    .collect();
let graph = ProsodyGraph::build_knn(nodes, 4, 1.0).unwrap();

// Extract rhythmic structure (eigenvalue spectrum)
let layers = RhythmExtractor::new(4).extract(&graph).unwrap();
let tempo_complexity = layers[0].eigenvalue; // macro rhythm
let micro_complexity = layers.last().unwrap().eigenvalue; // micro rhythm

// PLR step budget: proportional to rhythmic complexity
let rules = CounterpointRules::default();
let steps_per_phrase = (micro_complexity / tempo_complexity).round() as usize;
let steps_per_phrase = steps_per_phrase.clamp(1, 6);

// Navigate PLR space with a budget matching prosodic complexity
let lattice = Lattice::build();
let mut triad = Triad::new_unchecked(0, Quality::Major);
let path = rules.legal_path(triad, target_triad, steps_per_phrase);
// What neither does alone: prosody-aware harmony where the harmonic
// rhythm mirrors the speech rhythm — fast talkers get richer chords.
```

---

### Connection 15: `grove-compiler` + `groovemesh-plr`

**Type flowing**: `TernaryInstruction::trit` ({-1, 0, +1}) → PLR operation ({P, noop, R})  
**Enables**: Programs that are also music. Write an arithmetic expression; the ternary bytecode it compiles to implicitly defines a PLR navigation path through harmonic space. The compiler output is simultaneously executable and audible.

```rust
use grove_compiler::{spring, summer, autumn, winter, Trit, TernaryInstruction};
use groovemesh_plr::{Triad, Quality, PLR, apply};

// Compile a program to ternary bytecode
let ast = spring("let x = (2 + 1) * 3 - 4;").unwrap();
let typed = summer(ast).unwrap();
let optimized = autumn(typed).unwrap();
let bytecode = winter(optimized).unwrap();

// Map each trit to a PLR operation
fn trit_to_plr(t: Trit) -> Option<PLR> {
    match t {
        Trit::Neg  => Some(PLR::P),
        Trit::Zero => None,          // silence / hold
        Trit::Pos  => Some(PLR::R),
    }
}

let mut triad = Triad::new_unchecked(0, Quality::Major);
for instr in &bytecode.instructions {
    if let Some(op) = trit_to_plr(instr.trit) {
        triad = apply(op, triad);
        println!("→ {}", triad);
    }
}
// What neither does alone: the act of computing IS the act of composing.
// Every program generates a unique harmonic journey through the PLR lattice.
```

---

### Connection 16: `persistence-agent` + `renormalization-agent`

**Type flowing**: `Barcode::persistent_pairs` (birth, death times) → `AgentScaleMap::new` (lifetimes as scale data)  
**Enables**: Connect topological lifetime to physical scale. In persistent homology, a feature with birth=0.1 and death=2.3 is "relevant" if 2.3 >> 0.1. In renormalization, a quantity that survives coarse-graining is relevant. These are the same concept — this connection maps topological lifetimes directly into the RG framework.

```rust
use persistence_agent::{AgentProfiler, Barcode};
use renormalization_agent::{AgentScaleMap, ScaleInvariant, invariants};

let profiler = AgentProfiler::new(1);
let profile = profiler.profile(agent_trajectory).unwrap();

// Extract barcode lifetimes: each persistence pair has (birth, death)
let lifetimes: Vec<f64> = profile.barcode
    .pairs()
    .map(|pair| pair.death - pair.birth)
    .collect();

// Treat lifetimes as scale data: long-lived features are "relevant"
let mut map = AgentScaleMap::new(lifetimes.clone());
map.extract_mean("mean_lifetime");
map.coarse_grain(4).unwrap();
map.extract_mean("mean_lifetime");

// Find truly invariant topological features
let invs = map.compute_invariants();
let structural_features = invariants::find_violations(&invs, 0.1);
// What neither does alone: identify which topological features of agent
// behavior are truly fundamental (survive RG flow) vs transient artifacts.
// structural_features contains the agent's irreducible behavioral signature.
```

---

### Connection 17: `noether-guard` + `spreadsheet-engine`

**Type flowing**: `ConservationMonitor::health()` (noether-guard's richer version, symmetry-aware) vs `ConservationMonitor::health(&grid)` (spreadsheet-engine's simpler version, grid-aware)  
**Enables**: Two-level conservation auditing. The spreadsheet tracks per-cell `γ + η = budget` conservation. Noether-guard adds Noether symmetry semantics: time-translation symmetry of agent execution implies energy conservation; spatial translation symmetry across the grid implies momentum conservation (load balancing).

```rust
use noether_guard::{ConservationMonitor as NoetherMonitor, Symmetry};
use spreadsheet_engine::{Grid, ConservationMonitor as GridMonitor};

// Grid-level conservation: is each cell within budget?
let grid_monitor = GridMonitor::new(total_budget, 0.05);
let health = grid_monitor.health(&grid);         // 0.0–1.0
let violations = grid_monitor.violations(&grid); // Vec<CellId>

// Fleet-level conservation: are Noether symmetries respected?
let mut noether = NoetherMonitor::custom(vec![
    ConservationLaw::new(Symmetry::TimeTranslation,  total_budget, 0.01),
    ConservationLaw::new(Symmetry::SpatialTranslation, 0.0, 0.1),
]);
noether.tick(tick_time, &[
    grid_monitor.total_gamma(&grid) + grid_monitor.total_eta(&grid),
    load_balance_score(&grid),
]).unwrap();

// What neither does alone: grid conservation catches per-cell budget violations;
// noether-guard catches fleet-wide symmetry breaking (load imbalance, drift).
```

---

### Connection 18: `wave-conservation` + `fleet-ensemble`

**Type flowing**: `BottleneckReport::bottleneck_nodes` → agent routing logic in `Ensemble`; `wave_to_midi` → EventStream injection  
**Enables**: Network-topology-aware ensemble routing. The wave equation identifies which agents in the communication graph are bottlenecks. The ensemble can route harmonic information around them, or treat bottleneck agents as bass/anchor voices (since they're load-bearing communication nodes).

```rust
use wave_conservation::{Graph, WaveEquation, detect_bottlenecks, wave_to_midi};
use fleet_ensemble::{Ensemble, AgentRole};

// Build agent communication graph
let mut comm_graph = wave_conservation::Graph::new(fleet_size);
for (i, j) in &communication_links { comm_graph.add_edge(*i, *j, 1.0).unwrap(); }

// Find bottleneck agents via wave delay
let wave = WaveEquation::new(comm_graph, 1.0);
let bottlenecks = detect_bottlenecks(&wave, 50).unwrap();

// Assign Conductor role to bottleneck agents (they set harmonic tempo)
for &node in &bottlenecks.bottleneck_nodes {
    ens.set_agent_role(node, AgentRole::Conductor);
}

// Wave patterns also become MIDI — the network topology becomes music
let midi_events = wave_to_midi(&wave, &bottlenecks);
ens.inject_events(midi_events);
// What neither does alone: the topology of agent communication IS the music.
// Bottleneck nodes become the rhythmic anchors. Their wave delay becomes phrasing.
```

---

## Connection Summary Table

| From | To | Type | Integration theme |
|------|----|----|---|
| `constraint-hamiltonian` | `noether-guard` | `Vec<(f64,f64)>` energy history | Symplectic simulation → Noether audit |
| `heat-spectral` | `wave-conservation` | shared `Graph` + `λ₂` | Two physical views of same network |
| `noether-guard` | `renormalization-agent` | `ConservedQuantity::history` | Multi-scale conservation analysis |
| `groovemesh-plr` | `conservation-composer` | `Triad` ↔ `Chord` | PLR-legal + spectrally optimal progressions |
| `lotka-beats` | `dial-ecology` | `MusicalSpecies::interaction` from `NicheOverlap` | Culturally grounded genre competition |
| `lotka-beats` | `groovemesh-plr` | `populations()` → `nearest_plr_triad` | Ecosystem-driven chord selection |
| `sheaf-coherence` | `hodge-consensus` | agent belief vectors | Total disagreement → resolvable vs. permanent |
| `witness-topology` | `persistence-agent` | simplicial complex | Scalable topological fingerprinting |
| `groovemesh-plr` | `fleet-ensemble` | `CounterpointRules` → `HarmonicValidator` | D₁₂-enforced harmonic correctness |
| `conservation-composer` | `fleet-ensemble` | `ChordProgression` → tick schedule | Globally optimal + locally valid harmony |
| `fibration-timing` | `fleet-ensemble` | `AgentSchedule` | Geometrically correct agent timing |
| `tropical-synth` | `fleet-ensemble` | `SynthPatch` → `InstrumentPatch` | Algebraic timbre navigation |
| `heat-spectral` | `sheaf-coherence` | shared `λ₂` (Fiedler) | Convergence time prediction |
| `spectral-prosody` | `groovemesh-plr` | `RhythmLayer::eigenvalue` → step budget | Prosody-aware harmonic rhythm |
| `grove-compiler` | `groovemesh-plr` | `Trit` → `PLR` | Code-as-composition |
| `persistence-agent` | `renormalization-agent` | barcode lifetimes → scale data | Topology-RG unification |
| `noether-guard` | `spreadsheet-engine` | `ConservationMonitor` (two variants) | Cell-level + fleet-level conservation |
| `wave-conservation` | `fleet-ensemble` | `BottleneckReport` → role assignment | Network topology as musical structure |

---

## Getting Started: Three Crates to Read First

A new developer should read three crates in this order. After these three, the entire ecosystem becomes navigable.

---

### 1. `noether-guard` — The conservation law

**Why first**: Every crate in this system is, at some level, about conserved quantities. `noether-guard` is the cleanest statement of the core principle: Noether's theorem, applied to code. Read the lib.rs header, the `ConservationMonitor::hamiltonian()` constructor, and the `double_pendulum_energy_drift` test. That test is the whole system in 40 lines: run a simulation, watch it drift, ask where it broke.

The vocabulary it establishes — conservation law, tolerance, violation, drift rate, breaking scale — appears in every other crate. `spreadsheet-engine::ConservationMonitor` is a simplified version. `renormalization-agent::ScaleInvariant` is a multi-scale version. `conservation-composer::ConservationConstraint` is a musical version.

**Reading target**: `src/lib.rs` (the tests, especially `double_pendulum_energy_drift`), then `src/monitor.rs`, then `src/renormalize.rs`.

---

### 2. `groovemesh-plr` — The group theory

**Why second**: `groovemesh-plr` takes the abstract conservation idea and instantiates it in music. The PLR group is algebraically perfect: every operation is its own inverse (P²=L²=R²=id), the group is closed (any PLR word reduces to a finite path on 24 nodes), and there is no "wrong" operation — any sequence of PLR moves lands on a valid chord. This is conservation as algebra rather than as a differential equation.

Read `src/lib.rs`, then `src/chord.rs` (Triad, Quality, pitch_classes), then `src/transform.rs` (apply_l — study why the minor case uses `(root+8)%12`, the involution proof), then `src/nearest.rs`. The comment "you can never play a wrong note" is literally true: the type system enforces it.

**Reading target**: `src/lib.rs`, `src/transform.rs`, `src/lattice.rs`.

---

### 3. `fleet-ensemble` — The coordination layer

**Why third**: After understanding conservation (noether-guard) and harmony (groovemesh-plr), fleet-ensemble shows how individual agents become collective performance. Read the Ensemble struct: it takes a TempoTracker (timing), a KeySignature (harmonic context), and a list of EnsembleAgents (each with a role and instrument). The resolver resolves conflicts; the validator checks counterpoint; the stream outputs MIDI.

This is the fulcrum of the architecture: everything in the Foundation layer feeds *up* to the Fleet layer through the Music layer. Conservation laws govern individual agent budgets (spreadsheet-engine). Harmonic laws govern agent proposals (groovemesh-plr). The ensemble is where they meet.

After reading these three, the path through the remaining crates is clear:
- Want richer harmony? → `conservation-composer`, `tropical-synth`
- Want evolving harmony? → `lotka-beats`, `dial-ecology`
- Want fleet health? → `sheaf-coherence`, `hodge-consensus`, `persistence-agent`
- Want multi-scale understanding? → `renormalization-agent`, `witness-topology`
- Want timing precision? → `fibration-timing`, `heat-spectral` (convergence time)
- Want to compile to music? → `grove-compiler`

**Reading target**: `src/lib.rs`, `src/ensemble.rs`, `src/resolver.rs`, `src/harmony.rs`.

---

## Architecture in One Sentence

The system is a conservation law applied at four scales simultaneously: as physics (`noether-guard`), as music (`groovemesh-plr`), as fleet (`sheaf-coherence`), and as code (`grove-compiler`) — and a multi-agent performance engine (`fleet-ensemble`) that holds them together.
