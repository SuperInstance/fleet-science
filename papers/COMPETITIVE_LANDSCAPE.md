# SuperInstance Competitive Landscape Analysis

**Date:** June 8, 2026
**Scope:** Crates, PyPI packages, and research positioning

---

## Key Findings

### 1. groovemesh-plr vs rstmt (Neo-Riemannian Theory)

**Competitor:** `rstmt` / `rstmt-nrt` / `rstmt-neo` on crates.io (last updated March 2026)
- Full PLR transformation library for Rust
- Part of a comprehensive music theory toolkit (`rstmt`)
- Abstract mathematical focus: triads, LPR transforms, HyperTonnetz

**Our differentiation:**
- `groovemesh-plr` is *collaborative counterpoint* — not just abstract PLR theory
- Nearest-legal-neighbor: given any pitch, find closest valid chord via PLR navigation
- Voice leading distance via BFS on the PLR lattice
- Counterpoint enforcement: parallel fifth/octave detection + automatic correction via PLR
- Built for real-time collaborative music, not just analysis

**Verdict:** Different niche. `rstmt` is a math library; `groovemesh-plr` is a collaborative music engine. Coexist fine.

### 2. tropical-synth — First of Its Kind

**Prior art:** Sancristoforo & Bocci "Tropical Additive Synthesis" (2018)
- Demonstrated in Max/MSP and CsoundQT
- Conceptual/theoretical — no standalone library
- Only paper: tropical algebra applied to additive synthesis waveforms

**Our positioning:**
- **First Rust library** for tropical geometry → sound design
- Tropical polynomial evaluation → Newton polytope → synth parameter mapping
- Piecewise-linear morphing between patches along tropical edges
- TimbreSpace: navigate full sound design space via tropical variety structure
- MIDI CC export for hardware integration

**Verdict:** Genuine novelty. No competing library on any platform.

### 3. spreadsheet-engine vs Salesforce Agentforce Grid

**Competitor:** Salesforce Agentforce Grid (April 2026)
- "Spreadsheet-like UI to coordinate data, automation, and AI agents"
- Run prompts, invoke agents, AI-based and deterministic actions in a grid
- Enterprise-focused, Salesforce ecosystem only

**Our differentiation:**
- **Open source** (MIT), not locked to any platform
- **Evolutionary formulas** (EVOLVE, SPECIES, PARETO, ENTROPY, CONSERVE) — no competitor has these
- **Conservation monitoring** baked in (γ + η ≤ budget per agent, per grid)
- **A2A protocol** as first-class cell type (inter-cell agent-to-agent communication)
- **MIDI sonification** — hear your spreadsheet's health as music
- **Ternary cell values** {-1, 0, +1} — unique to our ecosystem
- Rust backend = WASM-ready, embedded-ready, not just browser

**Verdict:** Salesforce has the enterprise UI; we have the mathematical soul. Different league.

### 4. noether-guard — No Direct Competitor

No known library monitors physics conservation laws in simulations via Noether's theorem.
- Physics engines (Box2D, PhysX, Bevy Rapier) verify their own integrators but don't export a general conservation monitoring framework
- `noether-guard` is a standalone verification layer you can wrap around *any* simulation
- Renormalization group analysis of symmetry-breaking scale is genuinely novel

**Verdict:** Blue ocean. First mover.

### 5. lotka-beats — No Direct Competitor

No known library maps Lotka-Volterra population dynamics to generative music.
- Lotka-Volterra is well-studied in ecology and economics
- Applied to music recommendation (genre popularity), but not to *generative composition*
- Our auto-generation of fusion genres from equilibrium points is novel

**Verdict:** Novel application of well-known math to a new domain.

### 6. conservation-composer — No Direct Competitor

Spectral graph theory + conservation laws applied to chord progression generation.
- Markov chain composition exists (e.g., `music21` in Python)
- Constraint-based composition exists (e.g., Strasheela)
- But *eigenvalue-matched conservation-optimal progressions* via simulated annealing? Nobody.

**Verdict:** Genuinely novel mathematical approach to composition.

---

## Ecosystem Moat

No individual crate is unassailable. But the **combination** is:

```
spreadsheet-engine (compute grid)
    ├── groovemesh-plr (harmony algebra)
    ├── tropical-synth (sound design)
    ├── lotka-beats (generative ecosystem)
    ├── conservation-composer (optimal composition)
    ├── noether-guard (physics verification)
    ├── cmidi-core (protocol)
    ├── cmidi-conservation (health sonification)
    ├── fleet-ensemble (coordination)
    └── capability-spec (agent introspection)
```

Nobody else has a mathematical ecosystem that connects:
- Conservation laws → harmonic tension → audible violations
- Tropical geometry → synth patches → piecewise-linear morphing
- Lotka-Volterra → genre ecosystems → fusion genres
- PLR group → collaborative counterpoint → "you can never play a wrong note"
- Noether's theorem → simulation verification → drift detection

Each connection is a paper. Each paper is a moat.

---

## Recommendations

1. **Write papers** for each novel crate (tropical-synth, lotka-beats, conservation-composer) — establish priority
2. **Differentiate from rstmt** in groovemesh-plr README — cite them, explain our focus
3. **Build the integration** (INTEGRATION_SPEC from Claude) — the ecosystem value is in connections, not individual crates
4. **Agentforce Grid comparison** — include in spreadsheet-engine README for SEO/discoverability
5. **Continue building** fleet-ensemble, fleet-midi-pulse, fleet-midi-harmonizer — the fleet-midi layer is our crown jewel per the manifesto
