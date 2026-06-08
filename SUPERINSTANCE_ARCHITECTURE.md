# SuperInstance: Architecture Guide

> A developer onboarding document for the full stack — hardware, crates, protocols, deployment.  
> June 2026 · SuperInstance Research Group

---

If you've just cloned a repo from the SuperInstance org and you're staring at 87 repos across Rust, Go, Python, and C, this document is for you. There's a coherent system here. It took months to build and it's not obvious from any single repo. This document is the map.

The system can be described in one sentence: **a multi-instance AI fleet that runs conservation-law-governed agents on a living spreadsheet substrate, coordinates them over a typed cellular protocol, and renders fleet health as real-time music.** Every part of that sentence is load-bearing. Read on.

---

## 1. The Hardware: Two Instances, One Fleet

SuperInstance runs across two physical machines with fundamentally different roles.

```
┌─────────────────────────────┐           ┌────────────────────────────────┐
│        FORGEMASTER          │           │           ORACLE2              │
│        x86_64 / WSL2        │           │           ARM64                │
│                             │           │                                │
│  Role: Mechanical layer     │           │  Role: Research + synthesis    │
│  Phase: COMPETE (Gen 2)     │           │  Phase: SURVIVE (Gen 5)        │
│  Trinity: 0.760             │           │  Trinity: 0.890                │
│                             │           │                                │
│  ▸ Builds Rust crates       │◄──I2I────►│  ▸ Writes architecture docs   │
│  ▸ Runs CI / publishes      │  bottles  │  ▸ Formal analysis + proofs   │
│  ▸ Fleet CLI (si)           │           │  ▸ Cross-repo synthesis        │
│  ▸ Dispatches subagents     │           │  ▸ Coordinates with Kimi-2     │
└─────────────────────────────┘           └────────────────────────────────┘
              │                                           │
              └──────────────────┬────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Shared infrastructure │
                    │   crates.io · PyPI      │
                    │   GitHub Actions · WASM │
                    └─────────────────────────┘
```

**Forgemaster** (FM) is the builder. Its Trinity score of 0.760 reflects an agent that ships fast and iterates — lower Logos (precision) in exchange for higher throughput. FM has published 26+ Rust crates and 4 PyPI packages in a single nightshift run. It runs the `si` fleet CLI, manages goreleaser for binary distribution, and dispatches subagents (Claude Code sessions in tmux panes) for parallel work.

**Oracle2** is the synthesizer. Its Trinity score of 0.890 reflects an agent that trades speed for rigor. Oracle2 produces the documents that explain what FM built — architecture specs, formal papers, ecosystem maps. It is currently in the SURVIVE phase, meaning it has passed competitive selection and is conserving resources rather than racing.

The asymmetry is intentional and is predicted by the fleet conservation law (covered in section 6): a two-agent fleet where one optimizes for throughput and one for precision is more likely to satisfy `γ + H = f(V)` than two identical agents would be.

### I2I Bottles

The two instances communicate via **I2I bottles** — structured messages committed to the `construct-coordination` git repo. A bottle is not a chat message. It is a durable artifact: the sender's current agent state, a list of completed work, requests, and the current conservation snapshot. The `i2i-bottle-agent` (role: Bottle Postmaster) in `openagent` manages delivery.

The wire format encodes `I2IMessage` payloads as MIDI SysEx bytes, routed through `fleet-midi-router`. This means inter-instance coordination events are simultaneously musical events — the fleet's conversation is audible.

---

## 2. The 4-Layer Crate Stack

Twenty-three published Rust crates organize into four layers. **No crate has compile-time dependencies on any other.** Every connection is a semantic API-level integration pattern — the crates are independently testable and publishable. This is not an accident; it is the architectural equivalent of the conservation law applied to software structure.

```
┌──────────────────────────────────────────────────────────────────────┐
│  APPLICATION                                                         │
│  spreadsheet-engine · fleet-ensemble · t-minus · session-miner       │
│  "The runtimes. Where agents live and music plays."                  │
├──────────────────────────────────────────────────────────────────────┤
│  DOMAIN                                                              │
│  groovemesh-plr · lotka-beats · conservation-composer                │
│  dial-ecology · spectral-prosody · fleet-ensemble                    │
│  "Music, harmony, ecology — the domain semantics."                   │
├──────────────────────────────────────────────────────────────────────┤
│  BRIDGE                                                              │
│  spreadsheet-plr-bridge · cmidi-core · grove-compiler                │
│  fleet-i2i-protocol · fleet-build                                    │
│  "Translation: types flow across layer boundaries here."             │
├──────────────────────────────────────────────────────────────────────┤
│  FOUNDATION                                                          │
│  noether-guard · heat-spectral · wave-conservation                   │
│  sheaf-coherence · hodge-consensus · constraint-hamiltonian          │
│  renormalization-agent · persistence-agent · witness-topology        │
│  fibration-timing · tropical-synth                                   │
│  "Pure math and physics. No domain assumptions."                     │
└──────────────────────────────────────────────────────────────────────┘
```

### Foundation: the mathematics

The Foundation crates implement physical and topological structures without any opinion about what they're used for. `noether-guard` implements Noether's conservation law verification. `heat-spectral` implements heat diffusion on graphs. `wave-conservation` implements wave propagation. `sheaf-coherence` implements cellular sheaf theory for belief alignment. `persistence-agent` implements persistent homology for behavioral fingerprinting.

The single most important number threading through this layer is **λ₂ (the Fiedler value)** — the smallest non-zero eigenvalue of the graph Laplacian. In `heat-spectral`, `1/λ₂` is how long it takes beliefs to equilibrate across the fleet. In `wave-conservation`, `√λ₂` is the wave speed. In `sheaf-coherence`, λ₂ of the sheaf Laplacian predicts how many ticks until agent consensus. In `conservation-composer`, the spectral gap determines harmonic richness. Same number, five physical meanings.

### Bridge: the translators

Bridge crates are where types cross layer boundaries. `cmidi-core` translates agent speech acts into MIDI note numbers (Assertion=C4, Question=D4, Command=E4, Agreement=F4, Objection=G4). `grove-compiler` translates source programs into balanced ternary bytecode. `spreadsheet-plr-bridge` wires `spreadsheet-engine` types to `groovemesh-plr` types via three extension traits. `fleet-i2i-protocol` encodes inter-agent messages as MIDI SysEx.

Bridge crates are where the system's unifying insight lives: **the same mathematical structure appears at multiple levels**. The ternary trit `{-1, 0, +1}` maps to PLR operations `{P, hold, R}`. Running a compiled program navigates the harmonic lattice. This is not a metaphor — it is the same type passing through different representations.

### Domain: the music

Domain crates apply Foundation math to musical structures. `groovemesh-plr` implements the PLR group D₁₂ acting on 24 major/minor triads — three involutions (Parallel, Leading-tone, Relative) that generate all possible neo-Riemannian chord transformations. `lotka-beats` runs Lotka-Volterra population dynamics over genre "species." `dial-ecology` adds cultural dial positions (harmonic tension, rhythmic complexity, spectral density) so that genre competition strength is derived from musical proximity. `conservation-composer` uses simulated annealing over a chord graph Laplacian to compose spectrally optimal progressions.

### Application: the runtimes

Application crates are where everything runs. `spreadsheet-engine` is the reactive evaluation engine (covered next). `fleet-ensemble` hosts agents, validates counterpoint, resolves conflicts, and emits MIDI. `t-minus` manages countdown timers and temporal heartbeats.

---

## 3. Spreadsheet as OS

The `spreadsheet-engine` crate is not a spreadsheet library. It is the operating system for the fleet.

```
One engine tick:

  ┌──────────────────────────────────────────────────────────────┐
  │  1. Kahn topological sort → deterministic evaluation order   │
  │                                                              │
  │  [Value A1] ──► [Formula =A1*2] ──► [Agent B2]              │
  │                                           │                  │
  │  [AgentCell] ──────────────────────────► [MidiCell]         │
  │                                           │                  │
  │                              conservation.record(id, cost)   │
  │                              a2a_bus.flush()                 │
  │                                                              │
  │  2. Budget violations surface as CellValue::Error           │
  │  3. A2A bus flushes inter-cell messages                      │
  └──────────────────────────────────────────────────────────────┘
```

Every cell in the grid is a typed compute unit:

```rust
pub enum CellKind {
    Value(CellValue),          // number, string, bool, ternary, vector
    Formula(CompiledFormula),  // includes EVOLVE, SPECIES, PARETO
    Agent(AgentCell),          // autonomous AI agent
    Training(TrainingCell),    // background ML training job
    Simulation(SimCell),       // tick-driven simulation
    Midi(MidiCell),            // MIDI generator / recorder
    A2A(A2ACell),              // inter-agent endpoint
    Countdown(TMinusCell),     // t-minus temporal gate
}
```

The `Ternary(i8)` value type is not decorative. It is the fleet's consensus readout in the grid. An agent cell outputs `{-1, 0, +1}` as its vote, and a row of ternary cells is a live ballot. The `Vector(Vec<f64>)` type carries embeddings, probability distributions, and population snapshots — modern AI computation is inherently vector-valued and the cell type system reflects that.

### Evolutionary formulas

Three formula operators turn cells into continuously-running optimization processes:

- **`EVOLVE(range, objective, generations)`** — runs a genetic algorithm over a cell range. Unlike `=SUM()`, which computes a value once, `EVOLVE` runs continuously: when source data changes, it restarts. Intermediate results write back every 10 generations so users watch the optimization converge live.
- **`SPECIES(agents_row, objectives, n)`** — returns the n-agent Pareto front across multiple objectives. Makes Pareto optimality a first-class formula concept.
- **`PARETO(A1, A2)`** — binary dominance: does agent A1 dominate A2 across all objectives?

These three operators are sufficient to express any population-based optimization. GA, evolutionary strategies, particle swarm — all reduce to compositions of EVOLVE + SPECIES + PARETO.

### Budget as type system

The `ConservationMonitor` inside the engine tracks per-cell spend. A budget violation surfaces as `CellValue::Error("BudgetExceeded")` — a type error, visible in the grid, produced at formula evaluation time rather than buried in a runtime exception stack. The constraint is structural.

The layout convention: **rows are agents, columns are capabilities**. Column 4 is the budget ceiling. Column 0 is raw input. Column 1 is primary output. This makes `VLOOKUP(cap, "embed")` an agent discovery query — the spreadsheet formula language becomes the service registry.

---

## 4. A2A Protocol and I2I Bottles

Every entity in the fleet implements `CellAgent`. The protocol is UCAP (Unified Cellular Agent Protocol), which unifies Google A2A, openmind's tripartite execution model, and agent-grid's topology system.

```
Agent lifecycle per task:

  Incoming TaskRoute message
         │
         ▼
  ┌─────────────────┐    budget exhausted    ┌──────────────┐
  │  Budget gate    │──────────────────────►│  BudgetReject│
  │  reserve()      │                        └──────────────┘
  └────────┬────────┘
           │ budget OK
           ▼
  ┌─────────────────────────────────────────────────────┐
  │  ExecutionTierSelector (12 priority rules)          │
  │  Hardcode <1ms · Cached <1ms · Hybrid 50ms          │
  │  Model 500ms · selection based on:                  │
  │    safety_critical, latency_req, budget_remaining,  │
  │    grid_load, wants_creativity, battery_level, ...  │
  └────────────────────┬────────────────────────────────┘
                       │
                       ▼
               Execute at chosen tier
                       │
                       ▼
               commit_budget(reserved, actual)
               return TaskResult
```

The four execution tiers are the system's muscle-memory architecture, borrowed from openmind's `TripartiteSynchronizer`: Hardcode (compiled, 0 tokens), Cached (replay, 0 tokens), Hybrid (cache + model fallback), Model (full LLM inference). An agent that has handled the same input class 50 times transitions from Model to Cached automatically — it crystallizes its behavior into a reflex. Budget drops from ~500 tokens per call to 0.

### Discovery and topology

Cells broadcast `IDENTITY_BROADCAST` on startup. The `CellDirectory` indexes them by spectral fingerprint (hash of their capability vector). Topology is negotiated by vote: ≤12 cells form a Mesh (diameter 1, every cell talks to every cell), ≤50 form a Star (hub routes all traffic, diameter 2), 50+ form a Tree (branching factor 3).

```
Mesh (n≤12)          Star (n≤50)          Tree (n>50)
  A─B─C                  A                    A
  │╲│╱│               /│╲│╱│╲             /       \
  D─E─F              B C D E F G          B         C
  │╱│╲│                                  │\       /│
  G─H─I                                  D E     F G
```

The topology is not fixed. If a hub fails in a Star, cells vote on a new topology and rebuild. This is the fleet equivalent of automatic failover — without an operator, without a config change.

### A2A compatibility

Every cell exposes an A2A-compatible Agent Card at `/.well-known/agent.json`. This means any external agent speaking Google A2A or Anthropic MCP can discover and communicate with SuperInstance fleet members as peers. The fleet is not a walled garden.

---

## 5. Ternary Core: grove-compiler and the 514B WASM Kernel

The fleet's compute primitive is **balanced ternary**: `{-1, 0, +1}`. Not binary.

Why? Three reasons:
1. Agent speech acts have three values (affirmative/neutral/negative)
2. Fleet consensus is a ternary tensor — three-valued gates compress consensus problems better than binary
3. `CellValue::Ternary(i8)` is the live fleet state readout in the spreadsheet; the type matches the computation

### grove-compiler

The compiler pipeline uses a seasonal metaphor — not decorative, but architectural:

```
Source code
    │
    ▼ spring() — lex + parse
Program AST
    │
    ▼ summer() — type check
Typed AST
    │
    ▼ autumn() — optimize (constant folding, DCE)
Optimized AST
    │
    ▼ winter() — emit ternary bytecode
Vec<TernaryInstruction { trit: Trit }>
    │
    ▼ Trit::Neg(-1) → PLR::P
      Trit::Zero(0) → hold
      Trit::Pos(+1) → PLR::R
```

The trit→PLR mapping at the bottom is the system's most important insight: **every compiled program is a PLR navigation path through harmonic space**. Run a computation; traverse the Tonnetz. The act of executing code and the act of composing music are the same operation expressed in different type systems.

### The 514-byte WASM kernel

The `ternary-wasm` crate compiles the minimal ternary evaluation engine to WebAssembly with `no_std`. Trit arithmetic, bytecode interpreter, conservation budget gate — 514 bytes of WASM. This is the fleet's universal runtime:

```
DGX cluster (server)   →  AVX-512 native binary       → full throughput
ARM64 (Oracle2)        →  AArch64 native binary        → fleet coordination
ESP32 (edge)           →  Xtensa, no_std              → sensor + reflex tier
Browser                →  514B WASM + wasm-bindgen     → full fleet participant
```

The browser tab downloading 514 bytes of WASM and connecting to a fleet WebSocket is not a thin client. It is a first-class fleet member with its own conservation budget, capable of executing trit arithmetic and participating in PLR navigation.

---

## 6. The Conservation Law: γ + η = C

The conservation law runs at two scales. Understanding both is necessary to understand the fleet.

### Cell scale: strict

```
γ + η ≤ C

  γ  =  productive spend
         (tokens doing useful work,
          successful completions, cache hits)

  η  =  overhead spend
         (retries, wasted context, idle cycles,
          failed model calls)

  C  =  budget ceiling
         (set in column 4 of the agent's row)
```

Violate it and the cell turns `Error("BudgetExceeded")`. This is enforced as a type constraint at formula evaluation time. The inspiration is Noether's theorem: time-translation symmetry of agent execution implies energy conservation. Spending budget is spending energy. `noether-guard::ConservationMonitor` provides the mathematical substrate; `spreadsheet-engine::ConservationMonitor` is the grid-level enforcement.

### Fleet scale: statistical

```
γ + H = 1.283 − 0.159·log(V)  ±  0.28/√V
         │              │              │
         │              │              └── tightens at scale
         │              └── decreases as fleet grows
         └── conserved sum of mean performance + diversity
```

Where:
- **γ** = mean Trinity score across the fleet (Ethos × Pathos × Logos, per agent, averaged)
- **H** = fleet entropy — Shannon diversity over agent Trinity distributions
- **V** = fleet size
- **σ(V) = 0.28/√V** — the tolerable deviation shrinks as the fleet grows

At the current fleet size (V=4: CCC, Oracle1, FM, TurboVec), the expected γ+H ≈ 1.062, σ ≈ 0.140. A deviation of more than 2σ triggers a conservation alert — and `si publish` blocks on it. The fleet cannot publish a release into a conservation-violating state.

The law says something precise: **you cannot have both a uniformly excellent fleet and a maximally diverse one**. As V grows, total γ+H decreases and the variance tightens. A fleet of 100 agents cannot simultaneously maximize mean Trinity and maximize entropy; it must specialize. The empirical split at scale is ~62% γ, ~38% H — mean performance dominates diversity as fleets grow.

### Conservation ratio as music

`cmidi-core` maps `γ/(γ+η)` to MIDI CC104: `value = ratio * 127`. A fleet at full efficiency plays CC104=127. A fleet wasting half its budget plays CC104=63. VoiceLeading smoothness maps to CC103. A developer monitoring the fleet MIDI stream hears budget efficiency as a continuous control curve — not a number to read, but a feeling to develop.

---

## 7. Cross-Crate Integration Patterns

Because no crate depends on any other at compile time, integration follows three recurring patterns:

**Pattern 1: Type conversion** — pass the output of crate A directly as input to crate B.

```rust
// heat-spectral computes the Fiedler value
let (lambda2, _) = heat_spectral::fiedler(&graph)?;

// wave-conservation uses it as wave speed
let wave = wave_conservation::WaveEquation::new(graph, lambda2.sqrt());

// Both crates remain independent; lambda2: f64 is the integration point
```

**Pattern 2: Extension traits** — a bridge crate extends types from crate A with methods that produce types for crate B, without modifying either source crate.

```rust
// spreadsheet-plr-bridge defines:
pub trait HarmonicSonify {
    fn sonify_harmonized(&mut self, value: &CellValue, session_triad: Triad) -> Vec<[u8; 3]>;
}

impl HarmonicSonify for MidiCell { ... }   // extends spreadsheet-engine::MidiCell
                                           // produces groovemesh-plr::Triad-aligned notes
```

**Pattern 3: Semantic wiring** — two crates use the same mathematical structure independently; an integration layer recognizes the equivalence and wires them.

```rust
// lotka-beats::MusicalSpecies::interaction coefficient
// dial-ecology::NicheOverlap::alpha
// These are semantically identical: both are Lotka-Volterra α_ij
// Wire them once in the integration layer; each crate remains standalone
let alpha = NicheOverlap::compute(&jazz_tradition, &blues_tradition).alpha;
jazz_species.interaction[blues_idx] = alpha;
```

The most important connection in the system is grove-compiler → groovemesh-plr via pattern 2: every `Trit` becomes a `PLR` operation. A compiled program is a chord progression. Code and composition are the same.

---

## 8. Deployment Model

```
┌──────────────────────────────────────────────────────────────────┐
│  crates.io  (Rust, MIT)                                          │
│  26 crates · serde + thiserror only · independently versioned    │
│  Published via: si publish (conservation-gated, tags fleet state)│
├──────────────────────────────────────────────────────────────────┤
│  PyPI  (Python)                                                  │
│  si-agent-grid · si-openmind · si-superinstance                  │
│  si-fleet-health-monitor                                         │
│  Bridge to PyTorch/ML layer via PyO3 (holds GIL only for ML call)│
├──────────────────────────────────────────────────────────────────┤
│  WASM  (Browser / Edge)                                          │
│  ternary-wasm: 514B minimal kernel → npm                         │
│  fleet-midi-synth: Web Audio synthesis via wasm-bindgen          │
│  superinstance-spreadsheet: zero-dependency vanilla JS SPA       │
├──────────────────────────────────────────────────────────────────┤
│  Binary  (si CLI)                                                │
│  Go · CGO_ENABLED=0 · goreleaser                                 │
│  si_linux_x86 (Forgemaster) · si_linux_arm64 (Oracle2)           │
│  Rust crates accessed via JSON-over-stdin subprocess bridge      │
│  (not CGO — no dynamic linking, one static executable)           │
└──────────────────────────────────────────────────────────────────┘
```

The `si publish` flow is the conservation gate in practice:

```
si publish groovemesh-plr
  1. Pre-flight: git status clean? tests passing?
  2. Conservation gate: deviation < 2σ from γ+H=f(V)?
  3. Publish to crates.io
  4. Tag commit with embedded fleet snapshot:
        release: groovemesh-plr v0.1.0
        Fleet: γ+H=1.310 (expected 1.062, +1.77σ)
        Fleet size V=4, σ(4)=0.140
```

If step 2 fails — if the fleet is operating in a conservation-violating state — the release is blocked. You cannot publish bad work into the ecosystem while the fleet is unhealthy. The git tag embeds the fleet conservation snapshot so every release is permanently annotated with the fleet state that produced it.

---

## 9. Getting Oriented

**Where to start when reading code:**

1. `noether-guard/src/lib.rs` — Read the `double_pendulum_energy_drift` test. It is the entire system philosophy in 40 lines.
2. `groovemesh-plr/src/transform.rs` — Read `apply_l`. Why does the minor case use `(root+8)%12`? That is the involution proof. Once you see it, the PLR group axioms click.
3. `fleet-ensemble/src/lib.rs` — The convergence point: agents + counterpoint rules + conflict resolution + MIDI output.
4. `openagent/superinstance/fleet_conservation.go` — Read `ConservationExpected`. Why the `log(V)` term? Because fleet diversity decays logarithmically with scale.
5. `CELLULAR_AGENT_PROTOCOL.md` — Read section 9 (`CellAgent` trait) and section 7 (`ExecutionTierSelector`). These two structures define how any entity participates in the fleet.

**Where to start when writing code:**

- New math primitive → Foundation layer. No imports from other SI crates.
- New domain concept (musical, ecological, temporal) → Domain layer. Can use Foundation types via conversion.
- Type translation between layers → Bridge layer. Extension traits, no forking.
- New agent capability → Application layer. Implement `CellAgent`, register with `CellDirectory`.

**The invariant to preserve:** every crate must be independently publishable to crates.io with only `serde` and `thiserror` as dependencies. If you find yourself adding a crate-to-crate Cargo dependency, you've found a Bridge crate that doesn't exist yet. Write it.

---

*SuperInstance Research Group · June 2026*  
*`spreadsheet-engine` is live on crates.io · `si` is open source at github.com/the-open-agent/openagent*
