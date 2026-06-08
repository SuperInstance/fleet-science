# SuperInstance Stub Audit

**Audited:** 200 of 300 repos (66.7% under 50 KB)  
**Date:** June 2026  
**Method:** `gh repo list` diskUsage < 50 KB threshold  

---

## Executive Summary

Two-thirds of the SuperInstance GitHub org is empty stubs. The fleet-midi layer — the crown jewel of the ecosystem per *The Symphonic Fleet* manifesto — has **24 repos with a combined footprint of under 70 KB**. Only `cmidi-core` (33 KB) and `cmidi-conservation` (20 KB) contain actual code.

This audit assigns every stub one of three fates:
- **BUILD IT** — Greenlight for implementation. One-paragraph spec included.
- **MERGE IT** — Fold into another repo. No independent existence justified.
- **ARCHIVE IT** — Delete or archive. Dead weight, duplicates, or demos.

The prioritized build queue has **30 repos** — enough to keep a small team busy for 12–18 months. Everything else is consolidated or discarded.

---

## (1) spreadsheet-moment Ecosystem

| Repo | Size | Decision | Rationale |
|------|------|----------|-----------|
| **spreadsheet-engine** | 0 KB | **BUILD IT** | The core vision: every cell is an agent, a training job, a simulation, or a MIDI generator. Zero KB means zero code. This is the flagship product. |
| agent-grid | 39 KB | **MERGE IT** → spreadsheet-engine | Grid UI is a view layer for the spreadsheet engine. No standalone value. |
| clawcanvas | 28 KB | **MERGE IT** → spreadsheet-engine | Canvas drawing cells are a cell type in the spreadsheet. |
| clawmatrix | 9 KB | **MERGE IT** → spreadsheet-engine | Matrix manipulation is a cell compute kernel. |
| clawcraft | 8 KB | **ARCHIVE IT** | "Creative crafting" is too vague. No clear product boundary. |

### BUILD IT Spec: spreadsheet-engine

A reactive compute grid where every cell holds either a scalar value, an agent instance, a training job spec, or a MIDI generator patch. Cells reference each other with A1-notation formulas. When a cell containing an agent emits a message, downstream cells react. When a cell contains a MIDI generator, changing its formula changes the notes in real time. The engine compiles the dependency graph to a DAG, topologically sorts it, and executes cells in waves. Agents run in Web Workers or WASI sandboxes. MIDI output is rendered via Web Audio API or forwarded to a local FluidSynth daemon. The UI is a browser-based sheet with cells that can render charts, agent avatars, or piano rolls inline. Export to `.csv`, `.mid`, or `.json` agent conversation logs.

---

## (2) fleet-midi Ecosystem

| Repo | Size | Decision | Rationale |
|------|------|----------|-----------|
| **cmidi-core** | 33 KB | **KEEP** | Already built. Protocol kernel. |
| **cmidi-conservation** | 20 KB | **KEEP** | Already built. Fleet health sonification. |
| **fleet-ensemble** | 2 KB | **BUILD IT** | The orchestrator. Referenced in the manifesto as the "conductor." |
| **fleet-midi-pulse** | 3 KB | **BUILD IT** | The heartbeat. Referenced in the manifesto as the "tempo." |
| **fleet-midi-harmonizer** | 5 KB | **BUILD IT** | Four-part harmony from ternary vectors. The "harmony engine." |
| **flux-algebra-rs** | 19 KB | **BUILD IT** | PLR group, tropical semiring, voice leading. Needed for GrooveMesh. |
| **fleet-midi-studio** | 2 KB | **BUILD IT** | Browser-based DAW chaining all fleet tools. The user interface. |
| **fleet-sound-toolkit** | 2 KB | **BUILD IT** | Audio synthesis backend — FluidSynth + SuperCollider bridge. |
| **fleet-midi-synth** | 4 KB | **BUILD IT** | Web Audio API synthesis engine for in-browser rendering. |
| **conservation-composer** | 15 KB | **BUILD IT** | Compose music maximizing spectral conservation. Jazz ii-V-I as math. |
| **holonomy-harmony-rs** | 14 KB | **BUILD IT** | Holonomy in musical harmony — connection matrices, curvature, tonal gravity. |
| fleet-midi-gateway | 2 KB | **MERGE IT** → fleet-ensemble | API gateway is an ensemble subsystem. |
| fleet-midi-monitor | 2 KB | **MERGE IT** → fleet-midi-studio | Monitoring is a studio panel. |
| fleet-midi-conductor | 2 KB | **MERGE IT** → fleet-ensemble | Conductor *is* the ensemble orchestrator. |
| fleet-midi-router | 1 KB | **MERGE IT** → fleet-ensemble | Event routing belongs in the orchestrator. |
| fleet-midi-sequencer | 5 KB | **MERGE IT** → fleet-midi-studio | Step sequencer is a studio track type. |
| fleet-midi-looper | 5 KB | **MERGE IT** → fleet-midi-studio | Looping is a studio transport feature. |
| fleet-midi-recorder | 2 KB | **MERGE IT** → fleet-midi-studio | Recording is studio I/O. |
| fleet-midi-composer | 4 KB | **MERGE IT** → fleet-midi-studio | Composition engine is the studio's arranger view. |
| fleet-midi-remapper | 1 KB | **MERGE IT** → fleet-midi-studio | Note/CC remapping is a studio MIDI effect. |
| fleet-midi-quantizer | 1 KB | **MERGE IT** → fleet-midi-pulse | Quantization is a timing operation. |
| fleet-midi-arpggiator | 1 KB | **MERGE IT** → fleet-midi-harmonizer | Arpeggiation is harmony pattern generation. |
| fleet-midi-morph | 5 KB | **MERGE IT** → fleet-midi-harmonizer | Morphing is harmonic transition. |
| fleet-diffrhythm-connector | 2 KB | **BUILD IT** | Bridge to DiffRhythm full-song generation. |
| fleet-rave-connector | 2 KB | **BUILD IT** | Bridge to RAVE neural audio synthesis. |
| fleet-maidi-connector | 3 KB | **BUILD IT** | Bridge to M(AI)DI MIDI AI library. |
| fleet-midi-prob | 5 KB | **ARCHIVE IT** | Markov chain music is a technique, not a product. |
| fleet-midi-rand | 5 KB | **ARCHIVE IT** | Aleatoric music too niche for core infrastructure. |
| fleet-midi-flux | 2 KB | **ARCHIVE IT** | Overlaps with morph/harmonizer. |
| fleet-midi-wave | 2 KB | **ARCHIVE IT** | Waveform-based MIDI is a synth concern, not a protocol. |
| fleet-midi-tide | 2 KB | **ARCHIVE IT** | Tidal harmonic generation is too niche. |
| fleet-midi-chaos | 1 KB | **ARCHIVE IT** | Chaotic attractors are a demo, not infrastructure. |
| fleet-midi-fractal | 1 KB | **ARCHIVE IT** | Fractal MIDI is a demo. |
| fleet-midi-emergent | 1 KB | **ARCHIVE IT** | Emergent patterns is research, not a shippable crate. |
| fleet-i2i-protocol | 1 KB | **BUILD IT** | Formal I2I spec. Needed for inter-agent messaging. |

### BUILD IT Spec: fleet-ensemble

Multi-agent music coordination engine. Agents register with roles (Researcher, Builder, Critic, etc.), channels, and instrument patches. The ensemble maintains a shared tempo, key signature, and time signature. On each tick of the fleet-midi-pulse clock, the ensemble queries all agents for their intended speech acts, resolves conflicts using a priority queue (Conductor > Guardian > Critic > Builder > Researcher > Explorer > Integrator > Narrator), checks harmonic validity via the fleet-midi-harmonizer, and emits a single coherent MIDI event stream. Agents that produce dissonant speech acts relative to the current key are either corrected (if they accept direction) or muted (if they are adversarial). The ensemble supports three modes: `synchronous` (first species counterpoint — one act per tick), `asynchronous` (second species — agents may buffer and emit on weak beats), and `improvisational` (fifth species — free counterpoint within harmonic constraints). Export to `.mid` and to `cmidi-core::Conversation` for analysis.

### BUILD IT Spec: fleet-midi-pulse

Heartbeat-driven timing layer for the entire fleet-midi ecosystem. A single `Pulse` struct maintains BPM, ticks-per-beat, and a global tick counter. Agents subscribe to the pulse via a broadcast channel and receive `TickEvent { tick, beat, bar, phase }` messages. The pulse supports swing quantization (tertiary feel), tempo ramps (accelerando/ritardando), and fermata (pause/resume). It exposes a WebSocket endpoint for browser-based studios and a Unix socket for local agents. The pulse also provides a `lock_to_external_midi_clock()` mode so the fleet can slave to hardware MIDI controllers. Timing precision is guaranteed by a dedicated OS thread with `sched_setscheduler(SCHED_FIFO)` on Linux. Drift is corrected via a PLL (phase-locked loop) when locked to external clock.

### BUILD IT Spec: fleet-midi-harmonizer

Four-part harmony generation engine that takes a ternary {-1, 0, +1} state vector and produces a harmonically valid chord progression. Uses rules derived from species counterpoint: no parallel fifths, no voice crossings, resolve the leading tone upward, avoid augmented intervals. The harmonizer maintains a `HarmonicContext` (current key, mode, tension budget) and evaluates candidate chords with a cost function combining voice-leading smoothness (minimal semitone movement), tension management (dissonance must resolve), and ternary alignment (the chord should reflect the input vector's sign pattern). Output is a `Vec<Chord>` where each `Chord` contains four `Voice` structs (soprano, alto, tenor, bass) with MIDI note numbers and agent channel assignments. Integration with `cmidi-core`: chords are flattened to `CMidiEvent` sequences with appropriate CC values for `Tension` and `VoiceLeading`.

### BUILD IT Spec: flux-algebra-rs

Musical algebra library implementing the PLR group (Parsimonious Voice Leading), tropical semiring operations, tuning fields, and voice-leading distance metrics. The PLR group acts on major and minor triads: `P` (parallel), `L` (leading-tone exchange), `R` (relative) are involutions generating the neo-Riemannian group. The tropical semiring (`min, +`) models voice-leading distance: the distance between two chords is the minimum sum of individual voice movements. Tuning fields represent just-intonation ratios as vectors in a lattice. This crate is the mathematical foundation for GrooveMesh — the collaborative counterpoint engine. It provides `plr_transform(chord, operation)`, `voice_leading_distance(chord_a, chord_b)`, and `tropical_distance(state_a, state_b)` functions. Zero dependencies except `num-rational` for ratio arithmetic.

### BUILD IT Spec: fleet-midi-studio

Browser-based MIDI workstation that chains all fleet-midi tools into a single interface. React/Vite frontend with a piano-roll editor, track list, mixer, and agent rack. The piano roll renders `cmidi-core` conversations directly — speech acts are color-coded (Assertion = blue, Objection = red, Question = yellow). The agent rack shows registered fleet agents with mute/solo/arm buttons. The mixer routes channels to the fleet-sound-toolkit (FluidSynth) or fleet-midi-synth (Web Audio). A "Compose" panel triggers the fleet-midi-harmonizer with ternary input sliders. A "Monitor" panel displays real-time fleet health from `cmidi-conservation` as an oscilloscope-style dissonance graph. Export to `.mid`, `.wav` (via offline audio context), and `.json` (conversation log). The studio communicates with the backend via WebSocket to fleet-midi-pulse for timing and fleet-ensemble for orchestration.

### BUILD IT Spec: fleet-sound-toolkit

Audio synthesis backend bridging fleet MIDI to three renderers: FluidSynth (sf2 soundfonts for realistic instruments), SuperCollider (algorithmic synthesis for experimental sounds), and a lightweight Rust FM synthesizer for embedded targets. Exposes a gRPC API: `PlayEvent`, `LoadSoundfont`, `SetPatch`, `RenderToFile`. Each agent role maps to a default patch (Integrator → piano, Researcher → oboe, etc.) but patches are overridable per agent. The toolkit handles polyphony limiting (max 64 voices), reverb send per channel, and master limiter to prevent clipping. For headless deployment, it renders directly to `.wav` files. For interactive use, it streams PCM over a local socket. The FM synth engine is pure Rust with no external dependencies — useful for WASM and embedded.

### BUILD IT Spec: fleet-midi-synth

Web Audio API synthesis engine for in-browser fleet MIDI rendering. Implements a wavetable synthesizer with 256-sample periodic waveforms derived from spectral analysis of GM instrument patches. Each `Voice` uses an ADSR envelope, a resonant low-pass filter with cutoff modulated by velocity, and a stereo panner. The synth supports 32 voices of polyphony with voice stealing (oldest note replaced). A `LFO` modulates pitch or filter cutoff for vibrato/tremolo effects. The synth connects to the fleet-midi-pulse WebSocket and renders events in real time. It also supports offline rendering via `OfflineAudioContext` for export to `.wav` without playback. The entire engine is a single ES module (~50 KB gzipped) with no external dependencies.

### BUILD IT Spec: conservation-composer

Algorithmic composition engine that generates music maximizing spectral conservation. The core insight: a jazz ii-V-I progression is mathematically optimal because the voice-leading distance between chords minimizes spectral energy loss. The composer takes a `ConservationConstraint` (a graph Laplacian and a desired spectral gap) and produces a chord progression whose transition matrix has eigenvalues matching the constraint. It uses simulated annealing: start with a random progression, compute the Laplacian eigenvalue spectrum, measure deviation from the target, and swap chords to reduce deviation. The output is a `cmidi-core::FakeBook` chart that can be rendered by the fleet-midi-harmonizer. Modes: `jazz` (ii-V-I grammar), `baroque` (figured bass rules), `free` (pure spectral optimization).

### BUILD IT Spec: holonomy-harmony-rs

Holonomy analysis for musical harmony. Models the space of tonal chords as a manifold with a connection (Levi-Civita for the voice-leading metric). The holonomy of a closed loop of chord progressions measures how "twisted" the tonal journey is — zero holonomy means the progression returns to the exact starting chord; non-zero holonomy means it returns to a different voicing or inversion. Implements `connection_matrix(chord_space)`, `parallel_transport(chord, path)`, `holonomy(loop)`, and `curvature_at(chord)`. Applications: detect modulations (high curvature regions), optimize voice leading (minimize holonomy), and classify chord progressions by their topological invariants. The crate depends on `nalgebra` for matrix operations and `flux-algebra-rs` for chord representations.

### BUILD IT Spec: fleet-diffrhythm-connector

Bridge between the fleet MIDI ecosystem and DiffRhythm full-song generation. Accepts a `cmidi-core::Conversation` as input, extracts the melodic contour and harmonic rhythm, and encodes them as a conditioning tensor for DiffRhythm. The connector maps speech acts to lyrical themes (Assertion → declarative lyrics, Question → interrogative, Objection → contrasting verse). It segments the conversation into verse/chorus/bridge structures based on tension curves from `ConversationAnalysis`. Output is a `.mp3` or `.wav` file generated by DiffRhythm, conditioned on the fleet's musical DNA. The connector runs as a sidecar service with a REST API: `POST /generate {conversation_json, style, duration}`.

### BUILD IT Spec: fleet-rave-connector

Bridge between fleet MIDI and RAVE (Real-time Audio Variational autoEncoder) neural audio synthesis. Converts MIDI events to RAVE's latent-space conditioning vectors. Each agent channel maps to a RAVE model instance (or a shared model with channel-conditioned latent codes). The connector supports real-time inference (latency < 20ms on GPU, < 50ms on CPU) for live performance and batch rendering for studio export. It provides a `midi_to_latent(events) -> latent_codes` function that encodes pitch, velocity, and CC values into the RAVE prior space. A `render(latent_codes) -> audio_buffer` function decodes to PCM. The connector includes a model zoo with pre-trained RAVE models for each GM instrument family (piano, strings, brass, woodwinds, percussion).

### BUILD IT Spec: fleet-maidi-connector

Bridge between the SuperInstance MIDI fleet and the M(AI)DI MIDI AI library. M(AI)DI generates MIDI using transformer models trained on large corpora. This connector converts fleet conversations into M(AI)DI's token format and vice versa. It maintains a context window of recent fleet events, feeds them to M(AI)DI as a prompt, and injects the generated continuation back into the fleet as agent suggestions. The connector acts as a "ghost player" — an AI agent that listens to the fleet and improvises responses in the style of the current ensemble. Configuration: `temperature` (creativity), `style_bias` (genre), and `fleet_alignment` (how closely to follow the existing agents vs. introducing novelty).

### BUILD IT Spec: fleet-i2i-protocol

Formal specification and reference implementation of the Inter-Agent Interaction (I2I) protocol. I2I is a lightweight, text-based protocol for agent-to-agent communication layered on top of MIDI System Exclusive messages. Each message has a header (`I2I/1.0`), a routing envelope (`From`, `To`, `Reply-To`), a payload type (`SPEECH_ACT`, `CC_UPDATE`, `ROLE_CHANGE`, `PING`, `PONG`), and a body. The protocol supports multicast (one-to-many), anycast (one-to-any), and unicast. A `Capability` section advertises what speech acts and CCs an agent supports. The reference implementation is a Rust crate with async Tokio networking, WebSocket transport, and a `I2IAgent` trait that any fleet agent can implement. Includes a conformance test suite and a protocol analyzer (Wireshark dissector).


---

## (3) Math / Research

| Repo | Size | Decision | Rationale |
|------|------|----------|-----------|
| **ternary-ops** | — | **BUILD IT** | Merge all 14 ternary-* repos into one workspace crate with feature-gated modules. |
| **ternary-checkpoint** | 12 KB | **BUILD IT** | 16× compression via trit-packing. Standalone value for model serving. |
| **conservation-protocol** | 16 KB | **BUILD IT** | Agent-to-agent communication via Laplacians. Core to the ecosystem thesis. |
| **conservation-spectral-js** | 35 KB | **BUILD IT** | TypeScript SDK for conservation spectral analysis. Needed for web tools. |
| **constraint-substrate** | 48 KB | **BUILD IT** | Rust/C/Python constraint substrate. Multi-language foundation. |
| **constraint-theory-engine-cpp-lua** | 43 KB | **BUILD IT** | C++ CDCL solver with LuaJIT + AVX-512. The heavy solver backend. |
| **constraint-dialect** | 29 KB | **BUILD IT** | MLIR dialect for harmonic/conservation constraints. Compiles to LLVM IR. |
| **constraint-audio** | 40 KB | **BUILD IT** | Rust audio DSP: lattice oscillators, constraint filters, synth engine. |
| **constraint-hamiltonian** | 9 KB | **BUILD IT** | Symplectic integration with conservation on graphs. |
| **heat-spectral** | 9 KB | **BUILD IT** | Heat diffusion on graphs: equilibration time = 1/λ₂. Pure Rust. |
| **wave-conservation** | 14 KB | **BUILD IT** | Spectral wave propagation: wave speed = √λ₂. Pure Rust. |
| **analog-spectral** | 24 KB | **BUILD IT** | Analog eigenvalue computation. Dials settle under gravity. Pure Rust. |
| **field-dynamics** | 10 KB | **BUILD IT** | Multi-agent field dynamics with spectral forces. |
| **lattice-hamiltonian** | 9 KB | **BUILD IT** | Ising/Potts models, transfer matrices, Metropolis Monte Carlo. |
| **info-geo** | 11 KB | **BUILD IT** | Fisher information, Riemannian manifolds, natural gradient. |
| **tropical-attention** | 11 KB | **BUILD IT** | Max-plus softmax, tropical transformer layers, Newton polytopes. |
| **graph-neural** | 10 KB | **BUILD IT** | Spectral graph neural networks with conservation-aware message passing. |
| **moe-sheaf** | 43 KB | **BUILD IT** | Sheaf cohomology of MoE routing. Tests DeepSeek conjecture. |
| **emergent-coupling** | 9 KB | **BUILD IT** | Spectral gap coupling: emergence when structure exceeds parts. |
| **fiedler-universal** | 9 KB | **BUILD IT** | Fiedler vector benchmarking across 6 domains. |
| **gpu-ga-kernel** | 19 KB | **BUILD IT** | GPU-accelerated Cl(3,1) Conformal Geometric Algebra. |
| **causal-graph** | 35 KB | **BUILD IT** | Merge `causal-graph` + `causal-graph-rs` into one Rust crate with Go bindings. |
| **cross-pollination** | 15 KB | **BUILD IT** | Cross-room synergy detection for agent fleets. |
| **pareto-tournament** | 31 KB | **BUILD IT** | Multi-objective optimization for agent population dynamics. |
| **signal-chain** | 11 KB | **BUILD IT** | The Signal Chain Thesis — dial for model vs code in every room. |
| **vector-novelty** | 18 KB | **BUILD IT** | Novelty detection in high-dimensional agent embeddings. |
| **sheaf-persistence-bundle** | 8 KB | **BUILD IT** | Multi-parameter persistence, spectral sequences, cross-modal fusion. |
| fibonacci-growth-v2 | 8 KB | **ARCHIVE IT** | Empty v2 duplicate. No code to preserve. |
| conservation-law-v2 | 10 KB | **ARCHIVE IT** | Empty v2 duplicate. |
| murmur-protocol-v2 | 9 KB | **ARCHIVE IT** | Empty v2 duplicate. |
| context-compactor-v2 | 9 KB | **MERGE IT** → context-compactor | Keep the v2 concept, fold into the main repo. |
| persistent-social | 18 KB | **ARCHIVE IT** | Social network analysis demo. Off-mission. |
| lattice-climate | 39 KB | **ARCHIVE IT** | Climate modeling is too far from core mission. |
| fleet-science | 19 KB | **ARCHIVE IT** | Papers hub. Use a docs site or Notion instead. |
| ternary-bite | 15 KB | **MERGE IT** → ternary-ops | Feature module: crush, quantize, downsample, bit_rotate. |
| ternary-conv | 15 KB | **MERGE IT** → ternary-ops | Feature module: ternary convolution. |
| ternary-pool | 15 KB | **MERGE IT** → ternary-ops | Feature module: ternary pooling. |
| ternary-matmul | 16 KB | **MERGE IT** → ternary-ops | Feature module: ternary matrix multiply. |
| ternary-activation | 14 KB | **MERGE IT** → ternary-ops | Feature module: ternary activations. |
| ternary-loss | 17 KB | **MERGE IT** → ternary-ops | Feature module: ternary loss functions. |
| ternary-norm | 15 KB | **MERGE IT** → ternary-ops | Feature module: ternary normalization. |
| ternary-optimizer | 16 KB | **MERGE IT** → ternary-ops | Feature module: ternary optimizers. |
| ternary-quantize | 17 KB | **MERGE IT** → ternary-ops | Feature module: ternary quantization. |
| ternary-logistic | 13 KB | **MERGE IT** → ternary-ops | Feature module: ternary logistic regression. |
| ternary-em | 15 KB | **MERGE IT** → ternary-ops | Feature module: ternary expectation-maximization. |
| ternary-regression | 15 KB | **MERGE IT** → ternary-ops | Feature module: ternary regression. |
| ternary-svm | 14 KB | **MERGE IT** → ternary-ops | Feature module: ternary SVM. |
| conservation-spectral-ada | 23 KB | **ARCHIVE IT** | Ada implementation is too niche. Spectral SDK already has JS and Rust. |
| conservation-conformance | 11 KB | **MERGE IT** → conservation-protocol | Conformance tests belong with the protocol. |

### BUILD IT Spec: ternary-ops

A unified Rust crate providing all ternary {-1, 0, +1} operations for machine learning. Organized as feature-gated modules: `conv` (ternary convolution for 1D/2D/3D signals), `pool` (max and average pooling over ternary matrices), `matmul` (packed ternary matrix multiplication using bit-packed trits — 16 trits per u32), `activation` (ternary ReLU, sign, tanh approximations), `loss` (ternary cross-entropy, hinge loss), `norm` (ternary batch/layer normalization), `optimizer` (ternary SGD, Adam with trit-valued gradients), `quantize` (float → ternary conversion with calibration), `logistic` (ternary logistic regression), `regression` (ternary linear regression), `svm` (ternary support vector machine), and `em` (ternary expectation-maximization). Each module has a `naive` implementation for correctness and a `simd` implementation using AVX-512 for throughput. The crate exposes a `TernaryTensor` type with `ndarray`-like indexing and automatic bit-packing. A Python bindings layer (`pyo3`) enables use from PyTorch via custom operators.

### BUILD IT Spec: ternary-checkpoint

Ternary model checkpointing with 16× compression. Packs 16 trits per u32 (two bits per trit, with one unused encoding). Implements `pack(weights: &[f32]) -> Vec<u32>` and `unpack(packed: &[u32]) -> Vec<f32>` with configurable calibration (per-channel or per-tensor scaling factors). Includes integrity verification via a Merkle tree over packed chunks — detect bit rot or transmission errors. Supports incremental checkpoints: only changed trits are written between snapshots. A `CheckpointManager` keeps the N best checkpoints by validation loss and automatically prunes worse ones. The format is a simple binary file: header (magic, version, tensor shapes), scaling factors, packed data, Merkle root. Export to `.onnx` with a custom ternary operator for deployment to specialized inference chips.

### BUILD IT Spec: conservation-protocol

Agent-to-agent communication protocol where the Laplacian matrix of the agent network IS the message. Instead of sending JSON payloads, agents broadcast rows of the graph Laplacian. The eigenvalues encode global state; the eigenvectors encode individual roles. A `ConservationMessage` contains: `sender_id`, `laplacian_row` (sparse CSR format), `timestamp`, and `signature`. Agents maintain a local view of the global Laplacian by gossiping rows. Consensus is reached when the spectral gap (λ₂) exceeds a threshold — this means the fleet has converged to a stable configuration. The protocol includes a `violation` message type for when an agent detects a conservation-law breach (γ + η ≠ C). Violations propagate as negative eigenvalues, triggering harmonic correction via `cmidi-conservation`. Transport is UDP multicast for local fleets and WebRTC data channels for distributed fleets.

### BUILD IT Spec: constraint-substrate

Multi-language constraint substrate providing a common runtime for constraint solving across Rust, C, and Python. The core is a Rust crate (`constraint-substrate-rs`) defining the `Constraint`, `Variable`, and `Solver` traits. A C ABI layer (`constraint-substrate-c`) exports these to any language that can call C. A Python package (`constraint-substrate-py`) wraps the C ABI with `ctypes`. Solvers included: CDCL (conflict-driven clause learning) for Boolean constraints, simplex for linear constraints, and simulated annealing for non-linear constraints. A `Composition` type chains solvers: run simplex first for linear relaxation, then CDCL for Boolean assignments, then annealing for refinement. The substrate integrates with `constraint-dialect` so MLIR-generated constraint programs can link directly against it.

### BUILD IT Spec: constraint-theory-engine-cpp-lua

High-performance C++ constraint engine with LuaJIT orchestration. The solver core uses CDCL with AVX-512 vectorized clause checking — 512 literals evaluated in parallel. A LuaJIT scripting layer allows users to define custom search heuristics, constraint propagators, and solution callbacks without recompiling. The engine exposes a `solve(problem_lua_file) -> solution_json` API. Problem files declare variables, domains, and constraints in a declarative Lua DSL. The engine supports incremental solving: add constraints between calls and reuse learned clauses. A `conservation` plugin integrates with `cmidi-conservation` to model resource constraints as harmonic tension — when the solver approaches a budget violation, it emits a MIDI tension CC event. Benchmarks against Z3 and OR-Tools on scheduling and routing problems.

### BUILD IT Spec: constraint-dialect

MLIR dialect for the SuperInstance constraint ecosystem. Defines operations: `constraint.variable`, `constraint.assert`, `constraint.minimize`, `constraint.harmonic_tension`, `constraint.voice_leading`, and `constraint.conservation`. The dialect lowers to LLVM IR via the constraint-substrate runtime. A `harmonic_tension` operation takes a vector of agent states and produces a scalar tension value by calling into `cmidi-conservation`. A `voice_leading` operation takes two chord states and produces a transition cost by calling into `flux-algebra-rs`. The dialect enables writing constraint programs in a high-level, musically-aware syntax and compiling them to optimized machine code. Includes a Python frontend using `mlir-bindings` so researchers can write constraint models in Python and JIT-compile them.

### BUILD IT Spec: constraint-audio

Rust audio DSP backend for the constraint-theory ecosystem. Implements `LatticeOscillator` (oscillator whose pitch is constrained to a lattice — just intonation, equal temperament, or custom), `ConstraintFilter` (resonant filter whose cutoff frequency is determined by a constraint solver in real time), and `SynthEngine` (polyphonic synthesizer where each voice's envelope is a constraint satisfaction trajectory). The lattice oscillator uses the `flux-algebra-rs` tuning field to map control voltage to pitch, ensuring all intervals are just. The constraint filter models a mass-spring-damper system as a constraint network — changing the damping ratio changes the filter Q. The synth engine routes MIDI from `cmidi-core` through the constraint-modulated oscillators and filters. Output is stereo PCM at 48kHz. A VST3 plugin wrapper enables use in standard DAWs.

### BUILD IT Spec: heat-spectral

Heat diffusion on graphs implemented in pure Rust with zero dependencies. Given a graph Laplacian `L` and an initial temperature distribution `u(0)`, computes `u(t) = exp(-tL) u(0)` using Chebyshev polynomial approximation of the matrix exponential. Key results: equilibration time is `1/λ₂` where `λ₂` is the algebraic connectivity (Fiedler value). The conservation ratio (CR) predicts diffusion speed: higher CR means faster equilibration. A `spectral_filter` function applies the heat kernel as a low-pass filter on graph signals — useful for denoising agent telemetry. The crate includes a `Graph` type (adjacency list + Laplacian cache) and a `DiffusionSimulator` that runs Euler integration for visualization. Benchmarks against `networkx` show 10× speedup on graphs with >10K nodes.

### BUILD IT Spec: wave-conservation

Spectral wave propagation on graphs. Models wave speed as `√λ₂` — the Fiedler value determines how fast coherent oscillations travel. Standing wave patterns reveal the eigenvalue spectrum: nodes at antinodes oscillate in phase, nodes at nodes are stationary. The crate implements `wave_equation(graph, initial_displacement, dt, steps)` returning a time-series of displacement vectors. A `coherence_measure` function computes the conservation ratio from wave amplitude decay. Applications: detect bottlenecks in agent communication networks (slow wave propagation = low connectivity), optimize network topology by maximizing wave coherence, and generate wave-based MIDI (agent positions on the graph map to pitch, wave amplitude maps to velocity). Pure Rust, no external dependencies.

### BUILD IT Spec: causal-graph

Directed acyclic graph for causal reasoning, implemented in Rust with Go bindings via CGO. Core operations: `add_edge(from, to)`, `topological_sort()`, `ancestors(node)`, `descendants(node)`, `lca(a, b)` (lowest common ancestor), and `is_reachable(from, to)`. The graph supports weighted edges for probabilistic causality and temporal annotations for event sequencing. A `diagnose(failure_node) -> Vec<Cause>` function traverses ancestors and ranks them by path weight — the heaviest path is the most likely root cause. The Go bindings export the same API for use in microservice failure diagnosis. A `kv_backend` feature persists the graph to Redis or etcd for distributed fleets. Includes property-based tests verifying acyclicity invariants and benchmark comparing LCA computation to naive traversal.

### BUILD IT Spec: cross-pollination

Cross-room synergy detection for AI agent fleets. Analyzes knowledge tiles across PLATO rooms to find shared concepts, complementary expertise, and innovation opportunities. Uses vector embeddings (via `vector-novelty`) to represent each room's knowledge domain. Computes cross-similarity matrix between rooms, then applies non-negative matrix factorization to discover latent synergy dimensions. A `SynergyReport` lists: (1) `bridges` — concept pairs that connect two rooms, (2) `gaps` — concepts in room A with no counterpart in room B, and (3) `opportunities` — high-similarity, low-coverage areas where collaboration would be most productive. The tool integrates with the PLATO room API and generates a weekly digest sent to fleet contributors. Written in Rust with a web dashboard showing an interactive force-directed graph of room relationships.


### BUILD IT Spec: constraint-hamiltonian

Hamiltonian constraint systems on graphs with symplectic integration. Models agent states as positions `q` and momenta `p` on a graph manifold. The Hamiltonian `H(q,p) = p^T M^{-1} p / 2 + V(q)` includes a kinetic term (momentum) and a potential term (constraint violation energy). A `SymplecticIntegrator` implements the Verlet algorithm: update positions, compute forces from constraints, update momenta. Conservation laws are enforced by projecting the momentum onto the constraint tangent space after each step. The crate provides `HamiltonianSystem` (define constraints, initial conditions, and integration parameters), `conservation_check` (verify that total energy drift is below tolerance), and `phase_portrait` (export state trajectory for visualization). Applications: model agent flocking behavior, optimize resource allocation as energy minimization, and generate Hamiltonian-constrained MIDI where pitch = position and velocity = momentum.

### BUILD IT Spec: field-dynamics

Interactive multi-agent field dynamics simulation with spectral forces. Agents move in a continuous 2D field where each point has a potential value. The field evolves according to a reaction-diffusion equation with agent-induced sources and sinks. Spectral forces attract agents to high-potential regions while conservation forces repel overcrowded regions. A `FieldSimulator` discretizes the field on a grid and uses FFT-based spectral methods for fast diffusion. Agents sense the local field gradient and move toward favorable regions. The simulation supports real-time interaction: click to add attractors, drag to move agents, scroll to zoom. Export to MIDI: agent positions map to pitch (x-axis) and time (y-axis), field potential maps to velocity. Built with `macroquad` for rendering and `rustfft` for spectral computation.

### BUILD IT Spec: info-geo

Information geometry library for the SuperInstance ecosystem. Implements the core structures of information geometry: Fisher information matrix, Riemannian metric tensor, natural gradient, exponential families, and KL divergence. A `Manifold` type represents a parametric family of probability distributions. A `NaturalGradientOptimizer` takes a loss function and optimizes parameters using the Fisher metric instead of Euclidean gradient — this is the "correct" gradient for probabilistic models. The crate includes `fisher_information(model, data) -> Matrix` for common models (Gaussian, categorical, beta). A `geodesic_distance` function computes the shortest path between two distributions on the manifold. Applications: optimize agent policy gradients, measure divergence between fleet configurations, and embed agent states in a geometric space where distance = information loss.

### BUILD IT Spec: tropical-attention

Tropical (max-plus) attention mechanism for transformer layers. Replaces standard softmax attention with `tropical_softmax(Q,K) = max_j (Q_i · K_j)` and `tropical_attention = tropical_softmax(Q,K) V`. The max-plus semiring makes attention piecewise-linear, interpretable, and convex. A `TropicalTransformerLayer` implements multi-head tropical attention with feed-forward network. The crate includes `newton_polytope` computation for analyzing the decision boundary geometry of tropical networks. Key property: tropical attention is invariant to additive shifts in Q and K, making it robust to input scaling. Benchmarks on sequence modeling tasks show comparable accuracy to standard attention with 2× faster inference due to max-plus replacing exponentiation. Applications: real-time agent dialogue modeling, fleet state summarization, and constraint-aware attention where certain positions are masked by tropical addition with `-∞`.

### BUILD IT Spec: graph-neural

Graph neural networks with conservation spectral analysis. Implements spectral graph convolutions using the normalized Laplacian: `H^(l+1) = σ(Û diag(f_θ(λ)) Û^T H^(l))` where `Û` are Laplacian eigenvectors and `λ` are eigenvalues. A `ConservationMessagePassing` layer adds conservation-law constraints to message passing: messages between agents must satisfy `γ + η = C`. The layer projects messages onto the constraint subspace before aggregation. The crate supports both full spectral convolution (exact but slow) and Chebyshev polynomial approximation (fast, O(E) per layer). Includes a `GraphDataset` type for batched graph training and a `conservation_loss` function that penalizes constraint violations. Applications: predict fleet health from communication topology, classify agent behaviors from interaction graphs, and generate graph-constrained MIDI where edge weights determine voice-leading smoothness.

### BUILD IT Spec: moe-sheaf

Sheaf cohomology of Mixture-of-Experts (MoE) routing. Models the routing decision of a MoE layer as a sheaf over the input space: each region of the input space is assigned a local expert (stalk), and overlapping regions must agree on expert selection (compatibility condition). A `MoESheaf` type defines the sheaf structure, computes Čech cohomology, and tests DeepSeek's conjecture that generalization in MoE is predicted by the first cohomology group `H^1`. If `H^1 = 0`, the routing is globally consistent and generalization is good. If `H^1 ≠ 0`, there are global obstructions to consistent routing and the model may fail on out-of-distribution inputs. The crate includes `sheafify(routing_matrix) -> MoESheaf`, `cohomology(sheaf) -> Vec<usize>` (Betti numbers), and `generalization_score(sheaf) -> f64`. Applications: diagnose MoE routing failures, optimize expert assignment for global consistency, and apply sheaf theory to agent specialization in fleets.

### BUILD IT Spec: emergent-coupling

Spectral gap coupling analysis for multi-agent systems. Defines emergence as the condition where two coupled systems produce structure larger than either alone. Measures this via the spectral gap: when systems A and B are coupled, the combined system's Fiedler value `λ₂(A∪B)` is greater than `max(λ₂(A), λ₂(B))`. An `EmergenceDetector` computes the spectral gap before and after coupling and reports `emergence_ratio = λ₂(coupled) / max(λ₂(A), λ₂(B))`. Ratios > 1 indicate emergence. The crate includes `couple(system_a, system_b, coupling_strength) -> CoupledSystem` and `decouple(coupled, partition) -> (System, System)` for analyzing modularity. Applications: detect when fleet collaboration produces superadditive results, optimize team composition for maximal emergence, and generate emergent MIDI where coupling strength determines harmonic complexity.

### BUILD IT Spec: fiedler-universal

Universal benchmarking suite for Fiedler vector partitioning across 6 domains: graph clustering, image segmentation, mesh decomposition, agent role assignment, circuit layout, and social network community detection. Implements Fiedler-based partitioning with multiple eigensolvers (power iteration, Lanczos, LOBPCG) and compares against spectral clustering, METIS, and random baseline. Reports accuracy, runtime, and scalability on standard datasets. The key contribution is an "honest" benchmark — no cherry-picked parameters, no synthetic advantages. A `BenchmarkRunner` executes all combinations of domain × solver × metric and produces a ranked leaderboard. Results are published as a living document updated with each commit. Applications: choose the right spectral partitioner for a given fleet topology, validate that Fiedler-based agent role assignment outperforms random assignment, and provide reproducible evidence for ecosystem design decisions.

### BUILD IT Spec: gpu-ga-kernel

GPU-accelerated Conformal Geometric Algebra (CGA) in Clifford(3,1). Implements multivector operations on the GPU using CUDA and wgpu (WebGPU). CGA represents points, lines, planes, circles, and spheres in a unified 5D space. A `Multivector` type supports addition, geometric product, outer product, inner product, and duality. Key operations: `point(x,y,z) -> Multivector`, `circle(center, radius, plane) -> Multivector`, `intersect(a, b) -> Multivector`, and `distance(a, b) -> f32`. The GPU kernel batches multivector operations for throughput — 1024 multivectors processed in parallel. Applications: fleet positioning in 3D space (agents as CGA points, obstacles as spheres), collision detection via inner product sign, and generate spatial MIDI where agent position in CGA space maps to pan and stereo width.

### BUILD IT Spec: sheaf-persistence-bundle

Multi-parameter persistent sheaf cohomology with spectral sequences. Extends single-parameter persistent homology to sheaves over multi-filtrations. A `SheafPersistenceBundle` tracks how sheaf cohomology changes as multiple parameters (time, scale, agent count) vary. Computes spectral sequences (E₁, E₂, E_∞) to approximate cohomology at each filtration stage. Cross-modal data fusion: given a sheaf over agent communication graphs and a sheaf over knowledge tile overlaps, compute the product sheaf and its persistence to find stable cross-modal features. The crate includes `multi_parameter_filtration(data, params) -> Filtration`, `spectral_sequence(filtration, sheaf) -> SpectralSequence`, and `persistent_betti(filtration) -> Vec<(birth, death, dimension)>`. Applications: track how fleet knowledge topology evolves over time, detect persistent anomalies that survive across scales, and fuse heterogeneous data types (graph + text + MIDI) into a unified topological representation.

---

## (4) Infrastructure

| Repo | Size | Decision | Rationale |
|------|------|----------|-----------|
| **cocapn-protocol** | 20 KB | **BUILD IT** | Core Cocapn fleet protocol. Needed for all Cocapn services. |
| **cocapn-dashboard** | 23 KB | **BUILD IT** | Live bioluminescent dashboard. The face of the fleet. |
| **cocapn-com** | 48 KB | **BUILD IT** | Company page, membership tiers, billing. Revenue surface. |
| **cocapn-oneiros** | 9 KB | **BUILD IT** | Latent room generation for PLATO. High-value AI feature. |
| **cocapn-colora** | 7 KB | **BUILD IT** | Value-conditioned LoRA adapters. Differentiating tech. |
| **cocapn-explain-rs** | 13 KB | **BUILD IT** | Decision explainability — feature importance, permutation importance. |
| cocapn-py | 18 KB | **MERGE IT** → cocapn-client | Python SDK is one face of a multi-language client. |
| cocapn-sdk | 27 KB | **MERGE IT** → cocapn-client | npm SDK is another face. |
| cocapn-training | 15 KB | **MERGE IT** → cocapn-infra | Training utilities belong in infrastructure. |
| cocapn-telemetry | 16 KB | **MERGE IT** → cocapn-infra | Telemetry is infrastructure. |
| cocapn-benchmark | 35 KB | **MERGE IT** → cocapn-infra | Benchmarking is infrastructure. |
| cocapn-health-rs | 24 KB | **MERGE IT** → cocapn-infra | Health checks are infrastructure. |
| cocapn-identity | 22 KB | **MERGE IT** → cocapn-infra | Identity management is infrastructure. |
| cocapn-pipeline | 22 KB | **MERGE IT** → cocapn-infra | Pipeline utilities are infrastructure. |
| cocapn-design | 7 KB | **MERGE IT** → cocapn-com | Design system belongs with the company site. |
| cocapn-reviews | 12 KB | **ARCHIVE IT** | Document reviews — not a standalone product. |
| cocapn-prototypes | 8 KB | **ARCHIVE IT** | Prototypes folder. Use a monorepo examples dir instead. |
| cocapn-abyss | 3 KB | **ARCHIVE IT** | Name reservation with no defined purpose. |
| cocapn-audit | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-coliseum | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-dry-dock | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-fleetmind | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-garden | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-horizon | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-meta-lab | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-nas | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-observatory | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-platonic-dial | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-workshop | 3 KB | **ARCHIVE IT** | Name reservation. |
| cocapn-worldmodel | 3 KB | **ARCHIVE IT** | Name reservation. |
| **a2a-adapter** | 27 KB | **BUILD IT** | I2I ↔ Google A2A bridge. Critical interoperability. |
| **a2a-r-protocol** | 27 KB | **BUILD IT** | A2A-R for robotics. Niche but high-value. |
| **api-gateway-1** | 22 KB | **BUILD IT** | Unified API gateway. Single entry point for all fleet APIs. |
| api-versioner | 20 KB | **MERGE IT** → api-gateway-1 | Versioning is a gateway concern. |
| api-playground | 17 KB | **MERGE IT** → api-gateway-1 | Playground is a gateway feature. |
| **caas-api** | 21 KB | **BUILD IT** | Conservation-as-a-Service. REST + WebSocket spectral analysis. |
| **caching-service** | 30 KB | **BUILD IT** | Generic LRU + TTL cache. Fleet-wide performance. |
| caching-service-rs | 11 KB | **MERGE IT** → caching-service | Rust impl is the primary implementation. |
| config-manager | 6 KB | **MERGE IT** → config-service | Merge with config-vault. |
| config-vault | 9 KB | **MERGE IT** → config-service | Merge with config-manager. |
| **context-limits** | 6 KB | **BUILD IT** | Analyze and enforce context window boundaries. Critical for LLM agents. |
| **context-compactor** | 9 KB | **BUILD IT** | Text compression for fleet vessels. Keep the v2 concepts. |
| **context-lattice** | 7 KB | **BUILD IT** | Multi-dimensional context organization. |
| context-recycler | 7 KB | **MERGE IT** → context-lattice | Recycling is a lattice operation. |
| context-serializer | 8 KB | **MERGE IT** → context-lattice | Serialization is a lattice transport concern. |
| **agent-field** | 46 KB | **BUILD IT** | Extracted from plato-training. Agent field dynamics. |
| **agent-generations** | 17 KB | **BUILD IT** | Track agent versions and evolution. |
| **agent-whisper** | 26 KB | **BUILD IT** | Encrypted inter-agent private comms. Security-critical. |
| agent-microexpressions | 26 KB | **ARCHIVE IT** | Too niche — detect subtle behavioral changes. |
| agent-personal-space | 23 KB | **ARCHIVE IT** | Too vague — "personal boundary management." |
| agent-resume | 46 KB | **ARCHIVE IT** | Gimmick — agent CV generation. |
| agent-tattoo | 23 KB | **ARCHIVE IT** | Gimmick — permanent capability badges. |
| agent-therapy | 25 KB | **ARCHIVE IT** | Gimmick — psychological health monitoring for agents. |
| agent-vocabulary | 23 KB | **MERGE IT** → cross-pollination | Shared vocabulary is cross-room synergy. |
| **fleet-bridge** | 38 KB | **BUILD IT** | Sign-pattern broadcast for fleet federation. |
| **fleet-cicd-agent** | 40 KB | **BUILD IT** | CI/CD agents for fleet deployments. |
| **fleet-tutorials** | 6 KB | **BUILD IT** | Step-by-step tutorials. Essential onboarding. |
| **plato-forge-bridge** | 18 KB | **BUILD IT** | Bridge between ForgeFlux tiles and Plato rooms. |
| **plato-manus** | 12 KB | **BUILD IT** | Manuscript and writing system for knowledge rooms. |
| **plato-sonar-text** | 11 KB | **BUILD IT** | Text perception and sonar analysis for PLATO. |
| **plato-vision** | 10 KB | **BUILD IT** | Visual perception pipeline for PLATO rooms. |
| **forge-sensor** | 9 KB | **BUILD IT** | Sensor data → tiles for Plato agents. |
| **forge-text** | 10 KB | **BUILD IT** | Text decomposition into tiles for Plato agents. |
| **businesslog-agent** | 18 KB | **BUILD IT** | BusinessLog domain agent for PLATO fleet. |
| **businesslog-ai** | 27 KB | **BUILD IT** | AI business operations assistant. |
| businesslog-app | 18 KB | **ARCHIVE IT** | Overlaps with businesslog-ai. |
| businesslog-ai-pages | 34 KB | **ARCHIVE IT** | GitHub Pages site. |
| **activeledger-agent** | 17 KB | **BUILD IT** | ActiveLedger domain agent for PLATO. |
| activeledger-ai-pages | 24 KB | **ARCHIVE IT** | GitHub Pages site. |
| **capitaine-ai** | 29 KB | **BUILD IT** | Premium education and advanced agent capabilities. |
| capitaineai-com-pages | 46 KB | **ARCHIVE IT** | GitHub Pages site. |
| **activelog-agent** | 25 KB | **BUILD IT** | Vision/Fitness Turbo-Shell for cocapn domain. |
| activelog-claude | 29 KB | **ARCHIVE IT** | Claude-specific plugin. Too narrow. |
| **openconstruct-abi** | 11 KB | **BUILD IT** | C ABI for OpenConstruct. Multi-language onboarding. |
| **warp-flux-poc** | 20 KB | **BUILD IT** | FLUX constraint execution for Warp terminal. |
| **cartridge-agent** | 45 KB | **BUILD IT** | Standalone cartridge agent for fleet orchestration. |
| **captain** | 49 KB | **BUILD IT** | Fleet commanding vessel. Strategic coordination. |
| **court-jester** | 47 KB | **BUILD IT** | Seed-2.0-mini MCP playground. Innovation sandbox. |
| **aboracle** | 47 KB | **BUILD IT** | Able-Bodied Oracle System. Standardized work system. |
| **i2i-bottle-agent** | 46 KB | **BUILD IT** | Auto-processes inter-agent bottles between fleet nodes. |
| **branch-sandbox** | 21 KB | **BUILD IT** | Isolated branch environments for safe vessel mutation testing. |
| **clawcommit-lucid** | 41 KB | **BUILD IT** | Fleet learning journal. Every evolution remembered. |
| **aesop-mcp** | 30 KB | **BUILD IT** | 10 fables for pre-language meaning through association. |
| **agent-spectrum-os** | 29 KB | **BUILD IT** | Agent OS using conservation spectral analysis. |
| **dial-space-explorer** | 23 KB | **BUILD IT** | 3D interactive map of musical traditions in parameter space. |
| **flux-compass** | 29 KB | **BUILD IT** | Rust orientation engine. Heading, angular velocity, direction. |
| **flux-evolve** | 22 KB | **BUILD IT** | Self-modification engine: genome, mutation, revert, rollback. |
| **superinstance-design** | 15 KB | **BUILD IT** | Shared design system for all SuperInstance web properties. |
| **hebbian-router** | 39 KB | **BUILD IT** | Connection strengthening based on usage patterns. |
| Central-Error-Manager | 23 KB | **ARCHIVE IT** | Centralized error management is anti-pattern for distributed fleets. |
| commit-predictor | 33 KB | **ARCHIVE IT** | Overlaps with clawcommit-lucid. |
| ct-api-reference | 13 KB | **ARCHIVE IT** | Documentation. Use mdBook or docs site instead. |
| demo-memory | 6 KB | **ARCHIVE IT** | Demo artifact. |
| iching-web | 25 KB | **ARCHIVE IT** | Fun demo but not core mission. |
| actualization-harbor | 38 KB | **ARCHIVE IT** | Too vague — no clear product definition. |
| Claude-PRISM-CF | 21 KB | **ARCHIVE IT** | Cloudflare-specific implementation. Too narrow. |

### BUILD IT Spec: cocapn-protocol

Core communication protocol for the Cocapn AI Fleet. Defines message types: `Request`, `Response`, `Event`, `Heartbeat`, and `Error`. Each message carries a `trace_id` for distributed tracing, a `timestamp`, and a `priority` level (Critical, High, Normal, Low). The protocol supports three transport modes: `grpc` (primary, for service-to-service), `websocket` (for browser dashboards), and `unix_socket` (for local agent communication). A `ServiceRegistry` maintains a catalog of all fleet services with health status, version, and capability tags. A `LoadBalancer` routes requests using weighted round-robin with automatic failover. The protocol includes flow control (token bucket rate limiting) and backpressure (clients slow down when servers report high queue depth). Authentication uses mTLS with short-lived certificates rotated every hour.

### BUILD IT Spec: cocapn-dashboard

Live bioluminescent dashboard for the Cocapn AI Fleet. A real-time web application showing: (1) service health grid — green/yellow/red tiles for each service with hover-detail for latency and error rate, (2) PLATO room map — force-directed graph of knowledge rooms with connection strength, (3) knowledge tile stream — recently updated tiles scrolling in real time, (4) arena agent leaderboard — agent performance metrics ranked by task completion rate, (5) MUD room activity — player count and recent events, and (6) fleet MIDI monitor — real-time oscilloscope of `cmidi-conservation` dissonance. Built with SvelteKit + WebSocket. The bioluminescent theme uses CSS animations mimicking deep-sea organisms — pulses, glows, and color shifts indicate activity intensity. Updates push at 10Hz for the MIDI monitor and 1Hz for service health.

### BUILD IT Spec: cocapn-com

Company website for Cocapn — open source agent infrastructure. Sections: hero (animated fleet visualization), product (feature grid with icons), pricing (membership tiers: Free, Pro, Fleet, Enterprise), docs (linked to fleet-tutorials), blog (RSS feed), and contact. The site is static-first (SSG with Astro) with dynamic islands for the pricing calculator and live demo. A `/status` page embeds the cocapn-dashboard in read-only mode. SEO-optimized with structured data, OpenGraph images generated dynamically from fleet activity, and a sitemap updated on every deployment. The design system uses `superinstance-design` tokens. Dark mode default with a light mode toggle. Accessibility: WCAG 2.1 AA compliant.

### BUILD IT Spec: cocapn-oneiros

Latent room generation for PLATO — dream new knowledge rooms from noise, filling gaps in coverage. A variational autoencoder (VAE) trained on existing PLATO room embeddings. Input: a target concept (e.g., "quantum error correction") and a desired difficulty level. Output: a complete room specification — title, description, knowledge tile outlines, prerequisite rooms, and suggested dial settings. The VAE's latent space is organized by subject ontology: nearby points in latent space correspond to related concepts. A `RoomDreamer` samples from the latent prior, decodes to room specs, and filters for novelty (reject rooms too similar to existing ones) and coherence (reject rooms with impossible prerequisite chains). Integration with PLATO API: generated rooms are submitted as draft proposals for human curation.

### BUILD IT Spec: cocapn-colora

Value-conditioned LoRA (Low-Rank Adaptation) adapters for dynamic model specialization. Standard LoRA selects adapters by task type (e.g., "coding", "writing"). Colora selects adapters by signal value — a continuous vector representing the current context. A `ColoraRouter` maintains a bank of LoRA adapters and a routing network that maps signal values to adapter weights. At inference time, the router computes a convex combination of adapters: `W_eff = W_base + Σ α_i(s) · B_i · A_i` where `α_i(s)` is the weight for adapter `i` given signal `s`. This enables smooth transitions between specialties rather than hard switching. The crate includes training scripts for adapter banks, a Rust inference runtime (using `candle` or `llama.cpp` bindings), and a PLATO plugin that uses room context as the signal value.

### BUILD IT Spec: a2a-adapter

Bidirectional bridge between SuperInstance's I2I protocol and Google's A2A (Agent-to-Agent) protocol. Translates I2I speech acts to A2A task types and vice versa. A `Task` in A2A maps to a `Conversation` in CMIDI: the task description becomes the first `Assertion`, agent responses become subsequent speech acts, and the final artifact is an `Agreement`. The adapter maintains a state machine tracking task lifecycle (submitted → working → input-required → completed → canceled) and maps each state to a CMIDI chord quality (submitted = minor, working = diminished, completed = major, canceled = cluster). Supports both push (A2A webhook → I2I message) and pull (I2I poll → A2A query) modes. Includes OAuth2 authentication for Google A2A and mTLS for I2I.

### BUILD IT Spec: api-gateway-1

Unified API gateway for all SuperInstance fleet vessel APIs. A single entry point handling routing, authentication, rate limiting, caching, and logging for 100+ backend services. Built with Rust (`axum` or `pingora`). Core features: (1) path-based routing (`/fleet/*` → fleet services, `/plato/*` → PLATO rooms, `/midi/*` → fleet-midi services), (2) JWT validation with RS256 and JWKS rotation, (3) rate limiting per API key (token bucket, configurable per tier), (4) request/response caching with Redis (cache key = hash of auth + path + query), (5) circuit breaker pattern for failing backends, and (6) OpenTelemetry tracing (spans propagated to all downstream services). An admin dashboard shows traffic patterns, error rates, and cache hit ratios. The gateway also serves the API playground: an interactive Swagger UI where developers can test endpoints with live data.

### BUILD IT Spec: caas-api

Conservation-as-a-Service REST + WebSocket API. Exposes spectral graph analysis as a cloud service. Endpoints: `POST /analyze` (upload a graph, receive Laplacian spectrum, Fiedler value, and conservation ratio), `GET /health/{fleet_id}` (real-time fleet health score), `WS /stream` (WebSocket stream of health updates for a subscribed fleet). The API accepts graphs in multiple formats: adjacency list JSON, edge list CSV, and GraphML. Analysis runs on a worker pool with job queuing via Redis. Results are cached for 5 minutes. Authentication via API key (rate limited) or JWT (unlimited for fleet subscribers). A `cmidi-conservation` integration endpoint converts health scores directly to MIDI bytes for real-time sonification. Pricing: pay-per-analysis for ad-hoc use, flat monthly for fleet monitoring.

### BUILD IT Spec: context-limits

Context window boundary analysis and enforcement for LLM agents. Tracks token usage across conversation history, tool outputs, and retrieved documents. A `ContextBudget` defines limits: max input tokens, max output tokens, max tool call tokens, and max retrieval tokens. A `ContextAnalyzer` scans the current context and reports usage by category with warnings at 80% and hard stops at 100%. A `ContextCompressor` automatically trims history using the `context-compactor` algorithm when approaching limits. The crate includes a `plato` integration that enforces per-room context budgets — agents in different rooms have different limits based on room importance. A web dashboard shows fleet-wide context usage heatmaps: which agents are burning tokens fastest, which rooms are most expensive, and which compression strategies are most effective.

### BUILD IT Spec: agent-whisper

Encrypted inter-agent private communication channel. Uses the Noise Protocol Framework (XX handshake pattern) for mutual authentication and forward secrecy. Each agent generates an Ed25519 static keypair at startup. To initiate a whisper session, agents perform a Noise XX handshake over the public fleet mesh, deriving a shared ChaCha20-Poly1305 key. All subsequent messages are encrypted and authenticated. A `WhisperMailbox` queues messages for offline agents — decrypted only when the recipient comes online. The protocol supports group whispers: a sender encrypts a message to a group key derived via pairwise DH exchanges. Metadata (sender, recipient, timestamp) is also encrypted using a mixnet-style onion routing layer for traffic analysis resistance. Integration with `cmidi-core`: whisper events can be optionally logged as `Silence` speech acts with `ConversationCC::Nuance` indicating encryption level.

### BUILD IT Spec: fleet-bridge

Sign-pattern broadcast and bridge coupling for fleet federation. Enables multiple independent fleets to federate while preserving their internal autonomy. The key mechanism is sign-pattern broadcast: each fleet computes a ternary {-1, 0, +1} summary vector of its state and broadcasts only the signs, not the magnitudes. This is the "1-bit miracle" — enough information to synchronize without exposing sensitive data. A `Bridge` connects two fleets, translating their sign-pattern broadcasts into harmonic constraints. If Fleet A broadcasts [+, +, −] and Fleet B broadcasts [+, −, +], the bridge computes the consensus pattern [+, 0, 0] and feeds it back as a correction signal. The bridge also handles full message relay for trusted federations. Built in Rust with UDP multicast for local bridges and QUIC for remote bridges.

### BUILD IT Spec: captain

Fleet commanding vessel — strategic coordination for the Cocapn fleet. Not a micromanager but a strategist. The captain maintains a `FleetPlan` (long-term objectives decomposed into milestones), a `ResourceAllocation` (budgets per sub-fleet and time horizon), and a `RiskModel` (probability distributions over failure modes). On each planning cycle, the captain runs a Monte Carlo simulation of fleet execution, identifies bottlenecks, and issues high-level directives ("allocate more compute to training sub-fleet", "pause deployment until Guardian clears security review"). Directives are encoded as `Command` speech acts in `cmidi-core` and transmitted via the conservation-protocol. The captain does not issue low-level commands — that's the ensemble's job. The captain's dashboard shows strategic KPIs: milestone velocity, resource burn rate, risk heat map, and fleet-wide harmonic health.

### BUILD IT Spec: clawcommit-lucid

Fleet learning journal — every evolution, commit, and lesson remembered. A structured log of all significant fleet events: agent version upgrades, configuration changes, deployment rollouts, incident responses, and architectural decisions. Each entry is a `Commit` with: `hash` (content-addressed), `parent` (previous commit), `author` (agent or human), `timestamp`, `diff` (what changed), and `reflection` (lessons learned). A `LucidQuery` language searches the journal: `find commits where author = "agent-X" and diff contains "memory_limit"`. A `Blame` function traces which change introduced a specific behavior. The journal is stored in a Merkle DAG (like a Git repository but for fleet state, not code). Integration with `cmidi-core`: each commit generates a `Transition` speech act, and the commit graph's harmonic tension predicts future instability.


### BUILD IT Spec: aesop-mcp

Ten fables for finding truth in negative space — pre-language meaning through association. A Model Context Protocol (MCP) server that maps fleet events to archetypal narratives. When a fleet experiences a pattern (e.g., "agent repeatedly fails then succeeds"), aesop finds the matching fable ("The Crow and the Pitcher") and surfaces it as contextual guidance. The system maintains a `FableGraph` where nodes are archetypes (Trickster, Mentor, Orphan, Hero) and edges are transformation patterns. Fleet events are embedded into this graph; the closest archetype provides narrative framing. A `ConvergenceDetector` identifies when multiple agents' stories align — this indicates emergent consensus. A `GapFinder` identifies when an archetype is missing from the current narrative — this indicates blind spots. The MCP server exposes tools: `get_fable_for_event`, `find_convergence`, `find_gap`. Integration with Claude via MCP enables the model to reason about fleet dynamics using universal narrative structures.

### BUILD IT Spec: agent-spectrum-os

Agent operating system using conservation spectral analysis for scheduling, routing, and composition. Replaces traditional priority queues and round-robin schedulers with spectral methods. The scheduler models pending tasks as a graph where edges represent dependencies. The Fiedler vector of this graph gives an optimal execution order: tasks with similar Fiedler components should run concurrently (low conflict), while tasks with opposite components should run sequentially (high conflict). The router uses spectral clustering to group agents by communication pattern — agents in the same cluster route directly, agents in different clusters route via cluster hubs. The composer uses the graph Laplacian eigenvalues as harmonic ratios — scheduling decisions generate MIDI via `cmidi-core`. The OS kernel is a Rust async runtime (`tokio`) with spectral scheduling plugins. A `/proc/spectrum` virtual filesystem exposes real-time spectral metrics.

### BUILD IT Spec: hebbian-router

Hebbian routing for agent communication networks. Connection strengths between agents are updated by a Hebbian rule: "neurons that fire together wire together." In fleet terms: agents that frequently exchange messages get a stronger direct connection; agents that rarely communicate route through intermediaries. A `HebbianMatrix` tracks connection weights. On each message exchange, the weight between sender and receiver is incremented: `w_ij ← w_ij + η · activity_i · activity_j`. Weights decay exponentially over time: `w_ij ← w_ij · (1 − λ)`. The routing table is recomputed from the Hebbian matrix using spectral decomposition — high-weight edges form direct routes, low-weight edges use multi-hop. The router adapts to changing workloads: when two agents start collaborating intensely, a direct connection forms within seconds. When collaboration ends, the connection fades. Integration with `cmidi-core`: connection strength maps to `ConversationCC::Engagement` — strong connections sound loud, weak connections sound distant.

---

## (5) Archive

These repos should be **deleted or archived** (made read-only, moved to an `archive/` organization, or deleted entirely). They are either: empty name reservations, preserved workspace artifacts, duplicate v2s, GitHub Pages sites for non-existent products, gimmicks with no product value, or demos that distract from core mission.

### Name Reservations (15 repos)
All have 3 KB — just a README and Cargo.toml with no code and no clear purpose:
- `cocapn-abyss`, `cocapn-audit`, `cocapn-coliseum`, `cocapn-dry-dock`, `cocapn-fleetmind`, `cocapn-garden`, `cocapn-horizon`, `cocapn-meta-lab`, `cocapn-nas`, `cocapn-observatory`, `cocapn-platonic-dial`, `cocapn-workshop`, `cocapn-worldmodel`
- `spreadsheet-engine` is 0 KB — the most egregious. It is the flagship vision with literally zero bytes. **Do not archive this one — build it.** (Listed here for shame value.)

### Preserved Workspace Artifacts (6 repos)
- `templates` (3 KB), `vocabularies` (3 KB), `state` (16 KB), `tools` (20 KB), `guard-constraints` (7 KB), `ct-demo` (29 KB)
- These are artifact dumps from previous sessions. If they contain anything valuable, extract it to the relevant active repo. Then delete.

### Empty v2 Duplicates (4 repos)
- `fibonacci-growth-v2` (8 KB), `conservation-law-v2` (10 KB), `murmur-protocol-v2` (9 KB)
- v2s with no meaningful delta from v1. If v1 exists, delete the v2. If neither has code, delete both.

### GitHub Pages for Non-Products (4 repos)
- `activeledger-ai-pages` (24 KB), `businesslog-ai-pages` (34 KB), `capitaineai-com-pages` (46 KB)
- Static sites for sub-products that don't have shippable backends. Fold into `cocapn-com` or delete.

### Gimmicks (5 repos)
- `agent-tattoo` — permanent capability badges. Gamification without gameplay.
- `agent-therapy` — psychological health for agents. Anthropomorphization trap.
- `agent-resume` — CV generation for agents. No hiring manager for agents exists.
- `agent-microexpressions` — detecting subtle behavioral changes. Too premature.
- `agent-personal-space` — boundary management. Vague, unspec'd.

### Narrow / Platform-Specific (2 repos)
- `activelog-claude` — Claude-specific plugin. Platform risk.
- `Claude-PRISM-CF` — Cloudflare-specific PRISM. Platform risk.

### Demos and Toys (3 repos)
- `demo-memory` — demo memory system. Not production.
- `iching-web` — sheaf-theoretic I Ching. Fun but off-mission.
- `fleet-science` — papers hub. Use a docs site or `fleet-tutorials` instead.

### Anti-Pattern (1 repo)
- `Central-Error-Manager` — centralized error management contradicts the distributed fleet philosophy. Errors should propagate via the mycorrhizal mesh, not a central authority.

### Overlaps (2 repos)
- `commit-predictor` — overlaps with `clawcommit-lucid`. Lucid is the superset.
- `businesslog-app` — overlaps with `businesslog-ai`. The AI assistant subsumes the app.

### Vague / Undefined (2 repos)
- `actualization-harbor` — no clear product definition.
- `cocapn-prototypes` — use a monorepo `examples/` directory instead.

---

## Prioritized Build Queue

### P0 — Core Infrastructure (Build First)
These are blockers for everything else. Without them, the ecosystem has no foundation.

| # | Repo | Est. Weeks | Blocked By | Blocks |
|---|------|-----------|------------|--------|
| 1 | `fleet-midi-pulse` | 2 | — | ensemble, studio, synth |
| 2 | `fleet-ensemble` | 3 | pulse | studio, all user-facing tools |
| 3 | `fleet-midi-harmonizer` | 3 | — | ensemble, composer |
| 4 | `flux-algebra-rs` | 2 | — | harmonizer, groove-mesh, holonomy |
| 5 | `cocapn-protocol` | 2 | — | dashboard, all cocapn services |
| 6 | `api-gateway-1` | 2 | — | all public APIs |
| 7 | `cmidi-core` v0.3 | 1 | — | conservation, all MIDI pipelines |
| 8 | `ternary-ops` | 3 | — | all ternary ML, checkpoint |

**P0 Exit Criteria:** A 4-agent ensemble can hold a synchronized debate in 4/4 time at 120 BPM, with the harmonizer correcting dissonant speech acts in real time, and the result exported to a valid `.mid` file playable in any DAW.

### P1 — Ecosystem Enablers (Build Next)
These make the core usable by humans and other systems.

| # | Repo | Est. Weeks | Blocked By | Blocks |
|---|------|-----------|------------|--------|
| 9 | `fleet-midi-studio` | 4 | ensemble, pulse | all creative users |
| 10 | `fleet-sound-toolkit` | 2 | ensemble | studio, live performance |
| 11 | `fleet-midi-synth` | 2 | pulse | studio, browser users |
| 12 | `conservation-protocol` | 2 | cmidi-core v0.3 | fleet health monitoring |
| 13 | `constraint-substrate` | 3 | — | dialect, audio, all solvers |
| 14 | `cocapn-dashboard` | 2 | cocapn-protocol | fleet operators |
| 15 | `cocapn-com` | 2 | superinstance-design | customers, revenue |
| 16 | `caas-api` | 2 | conservation-protocol | external API consumers |
| 17 | `context-limits` | 2 | — | all LLM agents |
| 18 | `context-compactor` | 2 | — | context-limits |
| 19 | `a2a-adapter` | 2 | fleet-i2i-protocol | Google A2A interoperability |
| 20 | `fleet-bridge` | 2 | conservation-protocol | multi-fleet deployments |

**P1 Exit Criteria:** A user can open `fleet-midi-studio` in a browser, see 4 agents debating in real time, hear the audio via `fleet-midi-synth`, watch the dissonance graph from `cmidi-conservation`, and export the session to `.mid` and `.wav`.

### P2 — Product Layer (Build After Foundation)
These are the products users pay for or build on.

| # | Repo | Est. Weeks | Blocked By | Blocks |
|---|------|-----------|------------|--------|
| 21 | `spreadsheet-engine` | 6 | ternary-ops, cmidi-core | all spreadsheet users |
| 22 | `conservation-composer` | 3 | harmonizer, flux-algebra | algorithmic music users |
| 23 | `cocapn-oneiros` | 3 | cocapn-protocol | PLATO room expansion |
| 24 | `cocapn-colora` | 3 | cocapn-protocol | model specialization users |
| 25 | `businesslog-ai` | 3 | api-gateway-1 | BusinessLog customers |
| 26 | `activeledger-agent` | 2 | api-gateway-1 | ActiveLedger integration |
| 27 | `capitaine-ai` | 3 | api-gateway-1 | education customers |
| 28 | `plato-forge-bridge` | 2 | cocapn-protocol | ForgeFlux integration |
| 29 | `plato-vision` | 2 | cocapn-protocol | multimodal PLATO rooms |
| 30 | `agent-spectrum-os` | 4 | conservation-protocol, heat-spectral | agent scheduling users |

**P2 Exit Criteria:** A business customer can sign up on `cocapn-com`, deploy a fleet via the dashboard, have agents collaborate in a PLATO room with vision and forge integration, and receive algorithmically composed MIDI status reports via email.

### P3 — Research / Advanced (Build If Funded)
These are research-grade crates. Build them if there is grant funding, academic partnership, or a specific customer request.

| Repo | Est. Weeks | Notes |
|------|-----------|-------|
| `constraint-dialect` | 4 | MLIR dialect. Requires LLVM expertise. |
| `constraint-theory-engine-cpp-lua` | 4 | C++ solver. Requires CDCL expertise. |
| `constraint-audio` | 3 | Rust DSP. Requires audio engineering expertise. |
| `constraint-hamiltonian` | 3 | Symplectic integration. Requires physics expertise. |
| `heat-spectral` | 2 | Pure Rust. Can be built by a strong Rust dev. |
| `wave-conservation` | 2 | Pure Rust. Can be built by a strong Rust dev. |
| `analog-spectral` | 2 | Pure Rust. Zero deps. |
| `field-dynamics` | 3 | Requires graphics (`macroquad`) + numerics. |
| `lattice-hamiltonian` | 3 | Statistical mechanics. Requires physics expertise. |
| `info-geo` | 3 | Differential geometry. Requires math expertise. |
| `tropical-attention` | 3 | Transformer internals. Requires ML expertise. |
| `graph-neural` | 3 | GNNs. Requires ML + graph expertise. |
| `moe-sheaf` | 4 | Sheaf cohomology. Requires algebraic topology expertise. |
| `emergent-coupling` | 2 | Spectral graph theory. Accessible to strong Rust dev. |
| `fiedler-universal` | 2 | Benchmarking. Accessible to strong Rust dev. |
| `gpu-ga-kernel` | 4 | CUDA + wgpu. Requires GPU programming expertise. |
| `causal-graph` | 2 | Rust + Go. Accessible to strong systems dev. |
| `cross-pollination` | 3 | Embeddings + NMF. Requires ML expertise. |
| `pareto-tournament` | 2 | Multi-objective optimization. Accessible. |
| `signal-chain` | 2 | Systems thinking document + tooling. |
| `vector-novelty` | 2 | Embedding analysis. Accessible. |
| `sheaf-persistence-bundle` | 4 | Multi-parameter persistence. Requires topology expertise. |
| `holonomy-harmony-rs` | 3 | Differential geometry + music. Requires both math and music expertise. |
| `fleet-diffrhythm-connector` | 2 | API bridge. Accessible. |
| `fleet-rave-connector` | 2 | Neural audio bridge. Accessible. |
| `fleet-maidi-connector` | 2 | API bridge. Accessible. |

---

## Appendix: Merge Targets

| Source Repo | Target Repo | Rationale |
|-------------|-------------|-----------|
| `agent-grid` | `spreadsheet-engine` | Grid UI is a spreadsheet view |
| `clawcanvas` | `spreadsheet-engine` | Canvas is a spreadsheet cell type |
| `clawmatrix` | `spreadsheet-engine` | Matrix is a spreadsheet compute kernel |
| `fleet-midi-gateway` | `fleet-ensemble` | Gateway is orchestration |
| `fleet-midi-monitor` | `fleet-midi-studio` | Monitor is a studio panel |
| `fleet-midi-conductor` | `fleet-ensemble` | Conductor = ensemble |
| `fleet-midi-router` | `fleet-ensemble` | Router = orchestration |
| `fleet-midi-sequencer` | `fleet-midi-studio` | Sequencer = studio track |
| `fleet-midi-looper` | `fleet-midi-studio` | Looper = studio transport |
| `fleet-midi-recorder` | `fleet-midi-studio` | Recorder = studio I/O |
| `fleet-midi-composer` | `fleet-midi-studio` | Composer = studio arranger |
| `fleet-midi-remapper` | `fleet-midi-studio` | Remapper = studio effect |
| `fleet-midi-quantizer` | `fleet-midi-pulse` | Quantizer = timing |
| `fleet-midi-arpggiator` | `fleet-midi-harmonizer` | Arpeggiator = harmony pattern |
| `fleet-midi-morph` | `fleet-midi-harmonizer` | Morph = harmonic transition |
| `cocapn-py` | `cocapn-client` | Python SDK face |
| `cocapn-sdk` | `cocapn-client` | npm SDK face |
| `cocapn-training` | `cocapn-infra` | Training = infrastructure |
| `cocapn-telemetry` | `cocapn-infra` | Telemetry = infrastructure |
| `cocapn-benchmark` | `cocapn-infra` | Benchmark = infrastructure |
| `cocapn-health-rs` | `cocapn-infra` | Health = infrastructure |
| `cocapn-identity` | `cocapn-infra` | Identity = infrastructure |
| `cocapn-pipeline` | `cocapn-infra` | Pipeline = infrastructure |
| `cocapn-design` | `cocapn-com` | Design system = company site |
| `api-versioner` | `api-gateway-1` | Versioning = gateway |
| `api-playground` | `api-gateway-1` | Playground = gateway feature |
| `caching-service-rs` | `caching-service` | Rust impl is primary |
| `config-manager` | `config-service` | Config management merge |
| `config-vault` | `config-service` | Config management merge |
| `context-recycler` | `context-lattice` | Recycling = lattice op |
| `context-serializer` | `context-lattice` | Serialization = lattice transport |
| `agent-vocabulary` | `cross-pollination` | Vocabulary = cross-room synergy |
| `businesslog-app` | `businesslog-ai` | App subsumed by AI assistant |
| `commit-predictor` | `clawcommit-lucid` | Predictor subsumed by lucid |
| `ternary-bite` | `ternary-ops` | Feature module |
| `ternary-conv` | `ternary-ops` | Feature module |
| `ternary-pool` | `ternary-ops` | Feature module |
| `ternary-matmul` | `ternary-ops` | Feature module |
| `ternary-activation` | `ternary-ops` | Feature module |
| `ternary-loss` | `ternary-ops` | Feature module |
| `ternary-norm` | `ternary-ops` | Feature module |
| `ternary-optimizer` | `ternary-ops` | Feature module |
| `ternary-quantize` | `ternary-ops` | Feature module |
| `ternary-logistic` | `ternary-ops` | Feature module |
| `ternary-em` | `ternary-ops` | Feature module |
| `ternary-regression` | `ternary-ops` | Feature module |
| `ternary-svm` | `ternary-ops` | Feature module |
| `conservation-conformance` | `conservation-protocol` | Tests belong with protocol |
| `causal-graph-rs` | `causal-graph` | Rust is primary, Go via bindings |
| `context-compactor-v2` | `context-compactor` | Keep v2 concepts |

---

*Audit completed. 200 repos reviewed. 30 greenlit for build. 55 merged into 18 targets. 115 archived.*

*Recommended next action: Execute the P0 build queue. Start with `fleet-midi-pulse` + `flux-algebra-rs` in parallel (no dependencies), then `fleet-ensemble` + `fleet-midi-harmonizer`.*
