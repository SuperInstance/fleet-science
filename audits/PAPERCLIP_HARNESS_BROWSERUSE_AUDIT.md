# SuperInstance Ecosystem Integration Audit

**Target Repos:** `paperclip` · `harness-evals` · `browser-use`  
**Date:** June 2026  
**Method:** Web source reconnaissance + SuperInstance crate inventory + architectural mapping  

---

## Executive Summary

Three high-velocity open-source projects dominate complementary niches in the 2026 AI-agent landscape:

| Repo | Niche | Language | Why It Matters |
|------|-------|----------|----------------|
| **paperclip** | Multi-agent business orchestration | TypeScript/Node | "If OpenClaw is an employee, Paperclip is the company." Org charts, budgets, governance, goal alignment. |
| **harness-evals** | LLM-agent evaluation framework | Python | Normalized 0–1 scores across 5 dimensions. CI-native, production-trace evaluation. |
| **browser-use** | AI-driven browser automation | Python + Rust core | LLM + Playwright + vision. ~95k stars. The fastest-growing AI automation repo. |

**Thesis:** Each repo re-implements patterns that already exist—often with deeper mathematical grounding—in the SuperInstance crate ecosystem. Rather than competing, SuperInstance can **substrate** these projects: our crates become the physics engine beneath their application logic, adding capabilities they cannot build themselves (spectral consensus, tropical optimization, conservation-governed scheduling, PLR-harmonic agent coordination).

**Integration posture:** Not "fork and replace." Instead: **"import and enhance."** Our crates expose Rust libraries with WASM and Python bindings. Paperclip, Harness, and Browser-Use keep their UX and communities; we give them math they didn't know they needed.

---

## 1. Paperclip (`paperclipai/paperclip`)

### 1.1 What It Does and Why It's Popular

Paperclip is an open-source control plane for running a business with AI agents. It is a Node.js server with a React UI that models companies—not codebases.

**Popularity drivers:**
- **Pain-point precision:** Solves the "20 Claude Code tabs" problem. Gives solo operators an org chart, ticket system, and budget dashboard for multiple agents.
- **Metaphor clarity:** "If OpenClaw is an employee, Paperclip is the company." Instantly understandable value proposition.
- **Atomic execution + governance:** Task checkout and budget enforcement are atomic. Approval gates are revisioned and rollback-safe.
- **Multi-tenancy:** One deployment runs many companies with complete data isolation—appealing to MSPs and agencies.
- **Plugin ecosystem:** Out-of-process plugin workers with capability-gated host services.

**Short roadmap:** Cloud/sandbox agents, memory/knowledge, enforced outcomes, deep planning, work queues, self-organization, automatic organizational learning, CEO chat.

### 1.2 Core Architecture and Key Abstractions

Paperclip is a 12-subsystem monolith:

```
┌──────────────────────────────────────────────────────────────┐
│                       PAPERCLIP SERVER                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │Identity & │  │  Work &   │  │ Heartbeat │  │Governance │  │
│  │  Access   │  │   Tasks   │  │ Execution │  │& Approvals│  │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │ Org Chart │  │Workspaces │  │  Plugins  │  │  Budget   │  │
│  │ & Agents  │  │ & Runtime │  │           │  │ & Costs   │  │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │ Routines  │  │ Secrets & │  │ Activity  │  │  Company  │  │
│  │& Schedules│  │  Storage  │  │ & Events  │  │Portability│  │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Key abstractions:**
- **Agent:** Entity with role, title, reporting line, permissions, budget. Adapters connect to Claude Code, Codex, Cursor, OpenClaw, HTTP bots.
- **Issue:** Ticket carrying company/project/goal/parent links, atomic checkout with execution locks, blocker dependencies, comments, work products.
- **Heartbeat:** DB-backed wakeup queue with coalescing, budget checks, workspace resolution, secret injection, skill loading, adapter invocation.
- **Routine:** Recurring task with cron/webhook/API trigger. Each execution creates a tracked issue.
- **Budget Policy:** Scoped token/cost tracking with warning thresholds and hard stops. Overspend pauses agents and cancels queued work.
- **Plugin:** Out-of-process worker with capability-gated host services, job scheduling, tool exposure, UI contributions.

**Data layer:** Embedded PostgreSQL (dev) or external Postgres (prod). Local disk or provider-backed object storage.

### 1.3 Where SuperInstance Crates Could Replace/Enhance Components

Paperclip's roadmap is a checklist of problems SuperInstance crates already solve:

| Paperclip Subsystem | Current State | SuperInstance Enhancement |
|---------------------|---------------|---------------------------|
| **Heartbeat Execution** | DB-backed wakeup queue, basic coalescing | `fleet-midi-pulse`: drift-corrected tick broadcasts, tempo ramps, swing quantization for agent scheduling. Heartbeats become a musical rhythm, not a cron table. |
| **Org Chart & Agents** | Static hierarchy with reporting lines | `sheaf-coherence` + `hodge-consensus`: agents as nodes in a sheaf, disagreements decomposed into gradient (fixable) vs harmonic (fundamental). The org chart becomes a living consensus graph. |
| **Budget & Cost Control** | Threshold-based hard stops | `noether-guard`: treat budget as a conserved quantity. Drift detection tells you *why* an agent is overspending (symmetry breaking), not just *that* it is. |
| **Work Queues / Self-Organization** | On roadmap | `constraint-schedule` CSP solver: agents submit constraints (deadlines, dependencies, capabilities), solver returns optimal schedule. No manual queue management. |
| **Memory / Knowledge** | On roadmap | `spreadsheet-engine` living spreadsheet: agent memories are cells in a topological grid. Formulas (EVOLVE, SPECIES, PARETO, ENTROPY, CONSERVE) compute derived knowledge. A2A cells route inter-agent messages. |
| **Goal Alignment** | Ancestry links on tasks | `conservation-protocol` Laplacian gossip: goals propagate as eigenvectors of the goal-graph Laplacian. Alignment = spectral gap. Misaligned agents are bottlenecks (low λ₂). |
| **Plugin System** | Out-of-process workers | `ternary-core` WASM runtime: plugins compile to ternary WASM, executed in a Z₃-arithmetic sandbox. Capability gating becomes algebraic. |
| **Governance & Approvals** | Board approval workflows | `fleet-ensemble` harmonic validator: proposals are musical notes, governance is counterpoint. Approvals resolve harmonic conflicts before execution. |
| **Activity & Events** | Durable activity log | `analog-spectral` spectral thermostats: event streams are eigenvalue spectra. Anomalies are spectral outliers. Thermostat logic holds system temperature constant. |

### 1.4 Specific Crate Mappings

#### `spreadsheet-engine` → Paperclip Memory/Knowledge Layer

Paperclip's roadmap lists "Memory / Knowledge" and "Deep Planning" as upcoming. `spreadsheet-engine` is a living spreadsheet where cells are typed:

- **ValueCell:** Scalar data
- **AgentCell:** `{ agent_id, capabilities, gamma, eta, budget, state }` — conservation-stateful agent representation
- **A2ACell:** Inter-agent message routing
- **FormulaCell:** Operations including `EVOLVE`, `SPECIES`, `PARETO`, `ENTROPY`, `CONSERVE`
- **MidiCell:** Sonifies cell state into raw MIDI

**Integration:** Paperclip issues become rows in a `spreadsheet-engine` grid. Agent context is not a JSON blob but a formula graph. When an agent checks out an issue, the `AgentCell` updates its `gamma` (generation rate) and `eta` (entropy/dissipation). The `CONSERVE` formula checks `γ + η = budget` across the org chart. Violations trigger governance alerts.

**Binding:** Rust crate compiled to WASM, loaded by Paperclip's plugin system. Node.js calls WASM exports via `wasm-bindgen`.

#### `fleet-i2i-protocol` → Paperclip Inter-Agent Messaging

Paperclip agents communicate through adapter-specific channels (Claude Code stdin/stdout, HTTP webhooks). There is no native agent-to-agent semantic protocol.

**Integration:** `fleet-i2i-protocol` provides multicast messaging with speech-act semantics (INFORM, REQUEST, COMMIT, REFUSE, PROPOSE, ACCEPT, REJECT). Paperclip's agent adapters become I2I endpoints. A Claude Code adapter speaks I2I/1.0 wire format; a Codex adapter speaks the same protocol.

**Binding:** Rust crate with optional `tokio` runtime. Paperclip plugin spawns an I2I gateway process.

#### `conservation-protocol` → Paperclip Goal Alignment

Paperclip's goal alignment is ancestry links: a task points to its parent, which points to a project, which points to a company goal. This is a tree. Trees are brittle.

**Integration:** `conservation-protocol` models goals as a graph Laplacian. Agents gossip Laplacian rows. Consensus = spectral gap λ₂ crossing a threshold. Misalignment is quantified as `1 - λ₂/λ_max`. The org chart becomes a spectral object; re-orgs are Laplacian rewiring.

**Binding:** Rust crate, native Node-API module or WASM.

#### `noether-guard` → Paperclip Budget & Cost Control

Paperclip budgets are threshold-based: warn at 80%, hard-stop at 100%. This is reactive.

**Integration:** `noether-guard` treats budget as a conserved quantity derived from a symmetry (time-translation invariance of spending rate). `ConservationMonitor` tracks energy (budget), momentum (spending velocity), angular momentum (spending rotation across categories). `DriftDetector` uses renormalization-group analysis to predict when spending will violate conservation *before* it happens.

**Binding:** WASM module loaded by Paperclip's budget subsystem. Returns `Report` with `health`, `violations`, and `breaking_scale`.

#### `constraint-schedule` → Paperclip Work Queues & Self-Organization

Paperclip has no constraint solver. Tasks are manually assigned and prioritized.

**Integration:** `constraint-schedule` is a CSP scheduler. Agents submit constraints (availability, skill requirements, deadline, dependencies). The solver returns a globally optimal schedule. Self-organization emerges: agents don't need a manager to assign work; the physics of constraints does it.

**Binding:** Rust crate with WASM export. Input: JSON constraint graph. Output: JSON schedule.

#### `fleet-ensemble` → Paperclip Governance & Approvals

Paperclip's governance is procedural: board approval workflows, review stages, decision tracking.

**Integration:** `fleet-ensemble` treats governance as harmonic coordination. Agents submit `Proposal` objects (pitch, duration, velocity = priority, deadline, resource cost). The `ConflictResolver` adjudicates violations. The `HarmonicValidator` checks against the company's "key signature" (strategic priorities). Approved proposals form an `EventStream` — a score that the company performs.

**Binding:** Rust crate, native plugin. Replaces Paperclip's approval workflow engine.

#### `fleet-midi-pulse` → Paperclip Heartbeat Execution

Paperclip heartbeats are cron-like: wake up, check work, act.

**Integration:** `fleet-midi-pulse` replaces cron with a musical pulse. BPM = company velocity. Swing quantization = alternating focus between deep work and administrative tasks. Tempo ramps = sprint accelerations. Fermata = pauses for governance review. Every heartbeat broadcasts a `TickEvent` with beat/bar/phase; agents subscribe and act on the beat.

**Binding:** Rust crate with WebSocket server. Paperclip heartbeat scheduler connects as a subscriber.

#### `analog-spectral` → Paperclip Activity Monitoring

Paperclip's activity log is a chronological stream of events.

**Integration:** `analog-spectral` treats the activity stream as a signal. `AnalogDial` banks estimate eigenvalues of the activity spectrum. `SpectralThermostat` controls the "temperature" of the company: if activity rate is too high (burnout risk), the thermostat reduces BPM via `fleet-midi-pulse`. If too low (stagnation), it increases BPM.

**Binding:** Rust crate, background analytics process. Reads Paperclip activity DB, outputs thermostat signals.

### 1.5 Novel Capabilities Our Math Adds

| Capability | Math Source | What Paperclip Gains |
|------------|-------------|----------------------|
| **Predictive budget conservation** | Noether's theorem + RG drift analysis | Know *before* an agent overspends. Not threshold-based; physics-based. |
| **Self-organizing work queues** | CSP + constraint propagation | No manager needed. Constraints find the optimal assignment. |
| **Quantified goal alignment** | Graph Laplacian spectral gap | A single number (λ₂) tells you how aligned your company is. Re-orgs are eigenvector recomputation. |
| **Harmonic governance** | PLR group + counterpoint rules | Approvals are musical. Conflicting proposals resolve like voice-leading. The company *sounds* healthy. |
| **Thermostatic company temperature** | Spectral thermostat + eigenvalue settling | Prevent burnout and stagnation automatically. The system self-regulates its pace. |
| **Topological memory** | Living spreadsheet with formula evolution | Agent memory is a DAG, not a JSON blob. Knowledge evolves via `EVOLVE` and `SPECIES` formulas. |


---

## 2. Harness (`harness/harness-evals`)

### 2.1 What It Does and Why It's Popular

Harness Evals is an open-source Python framework for evaluating LLM agents, prompts, and structured outputs. Every metric produces a normalized `Score` (0.0–1.0) with a configurable threshold.

**Popularity drivers:**
- **Dimensional clarity:** Five dimensions (Correctness, Groundedness, Safety, Trajectory, Performance) answer "where is my agent strong, and where is it weak?" Auto-generated radar charts.
- **CI-native:** `assert_test()` raises `AssertionError` on failure—works with pytest, GitHub Actions, GitLab CI.
- **Production trace evaluation:** `LangfuseSource` and `OTELSource` hydrate `EvalCase` from production traces.
- **Extensibility:** Custom metrics are a single class with a `measure()` method.
- **Security focus:** Dedicated remediation-quality metrics with composite Remediation Quality Index.

**Metric categories:** Deterministic, Structural, Operational, Reliability, Predictability, MCP, Similarity, LLM-Judged, RAG, Safety, Agent, Conversation, Security.

### 2.2 Core Architecture and Key Abstractions

```
Golden (authored) + agent output → EvalCase → Score (result)
Production traces (Langfuse/OTEL) → Source → EvalCase → Score (result)
```

**Key abstractions:**
- **Golden:** Author-defined input, expected output, optional context. Lives in dataset files.
- **EvalCase:** Golden enriched with agent's actual output and runtime metadata (latency, tokens, cost, messages, tool_calls, confidence, tags).
- **BaseMetric:** Scoring function. `measure(eval_case: EvalCase) -> Score`. Specialized: `ReliabilityMetric` (multi-run), `SafetyMetric` (reported separately, never averaged).
- **Score:** Value 0.0–1.0, threshold, auto-computed `passed` boolean.
- **Message:** Conversation turn with role, content, optional tool calls.
- **ToolCall:** Tool/function invocation with name, input, output.
- **Source:** Adapter hydrating EvalCase from production traces (Langfuse, OTEL).
- **Sink:** Output adapter (Stdout, JSON, Langfuse, OTLP).
- **evaluate():** Runs multiple metrics, never raises, returns all scores including failures.
- **assert_test():** Same as evaluate but raises AssertionError on failure.

### 2.3 Where SuperInstance Crates Could Replace/Enhance Components

Harness Evals is a metrics factory. Its weakness is that metrics are mostly *local* (score one output) or *statistical* (aggregate over runs). It has no *global* or *dynamical* perspective: how does an agent's performance evolve over time? How do multiple agents interact in evaluation? What is the topology of failure modes?

| Harness Component | Current State | SuperInstance Enhancement |
|-------------------|---------------|---------------------------|
| **Reliability Metrics** | OutcomeConsistency, ResourceConsistency, TrajectoryConsistency over repeated runs | `noether-guard`: track invariants across runs. A "reliable" agent conserves some quantity (accuracy, latency, cost) across perturbations. RG drift analysis finds the scale at which reliability breaks down. |
| **Predictability Metrics** | Calibration, Discrimination (confidence scores) | `analog-spectral`: agent confidence is a dial settling to an eigenvalue. Deadband = spectral gap. A well-calibrated agent has tight deadband (low variance). |
| **Safety Metrics** | PII, Toxicity, PromptInjection, Hallucination (LLM-judged or regex) | `sheaf-coherence`: safety violations are sheaf disagreement. Global safety = alignment of the safety sheaf. Local violations are gradient-fixable; systemic biases are harmonic (fundamental). |
| **Trajectory Metrics** | PlanAdherence, StepEfficiency, ToolCorrectness | `witness-topology` + `persistence-agent`: the agent's trajectory is a point cloud. Persistent homology extracts topological features: loops (repetitive behavior), clusters (modes), voids (blind spots). The barcode is the agent's behavioral fingerprint. |
| **Performance Metrics** | Latency, TokenCost, CostEfficiency | `tropical-synth`: treat cost/latency as a tropical polynomial. The Newton polytope vertices are Pareto-optimal operating points. Morph paths between vertices = cost/quality tradeoff curves. |
| **Evaluation Orchestration** | `evaluate_dataset()` runs cases sequentially or with basic parallelism | `fleet-ensemble`: evaluation cases are musical proposals. The ensemble resolves scheduling conflicts, validates counterpoint, and emits a unified evaluation stream with harmonic timing. |
| **Result Aggregation** | `summarize()` computes mean, pass_rate per metric | `hodge-consensus`: when multiple metrics disagree about an agent's quality, decompose the disagreement. Gradient component = one metric is miscalibrated. Harmonic component = fundamental tradeoff. |
| **CI/CD Integration** | pytest-native assertions | `constraint-schedule`: evaluation suites are CSPs. Dependencies between tests are constraints. The solver finds optimal CI pipeline order. |

### 2.4 Specific Crate Mappings

#### `noether-guard` → Harness Reliability & Predictability

Harness's `ReliabilityMetric` checks consistency across repeated runs. `PredictabilityMetric` checks calibration.

**Integration:** `noether-guard` treats reliability as conservation. Define a `ConservationLaw` for each metric: "Accuracy shall not drift more than 0.05 across 100 runs." The `ConservationMonitor` ticks after each run. `DriftDetector` uses RG coarse-graining to find the scale at which drift emerges.

**Binding:** Rust crate compiled to Python extension via PyO3/maturin.

#### `persistence-agent` + `witness-topology` → Harness Trajectory Analysis

Harness's `TrajectoryConsistency` checks if repeated runs follow similar paths.

**Integration:** `persistence-agent` builds a Vietoris-Rips filtration from agent trajectories. The barcode reveals: long-lived loops = stuck in repetitive patterns; long-lived clusters = distinct modes; voids = unexplored state space. `witness-topology` does the same with sparse landmark sampling.

**Binding:** Rust crate with Python bindings. Input: trajectories. Output: barcode + Betti numbers + archetype classification.

#### `tropical-synth` → Harness Performance Optimization

Harness tracks Latency, TokenCost, CostEfficiency as separate scalars.

**Integration:** `tropical-synth` models the cost/accuracy/latency tradeoff as a tropical polynomial in max-plus semiring. The `NewtonPolytope` vertices are Pareto-optimal configurations. A `MorphPath` between vertices is a smooth interpolation between operating points.

**Binding:** Rust crate, Python bindings. Input: (cost, latency, accuracy) triples. Output: polytope vertices, morph paths.

#### `analog-spectral` → Harness Calibration

Harness's `Calibration` metric computes Expected Calibration Error.

**Integration:** `analog-spectral` models confidence as an analog dial settling under gravity to an eigenvalue estimate. The deadband (friction/gravity ratio) is the spectral gap. A well-calibrated agent has small deadband. The `SpectralThermostat` can actively adjust the agent's temperature based on calibration drift.

**Binding:** Rust crate, Python bindings. Input: confidence/accuracy pairs. Output: dial positions, deadband widths, thermostat actions.

#### `hodge-consensus` → Harness Multi-Metric Disagreement

When Harness metrics disagree (e.g., high accuracy but low safety), there is no principled way to resolve the conflict.

**Integration:** `hodge-consensus` decomposes metric disagreement into gradient, curl, and harmonic components. Gradient = one metric is miscalibrated. Curl = cyclic inconsistency. Harmonic = fundamental divergence (speed vs. accuracy tradeoff—must choose).

**Binding:** Rust crate, Python bindings. Input: pairwise metric comparisons. Output: Hodge decomposition + consensus prediction.

#### `fleet-ensemble` → Harness Evaluation Orchestration

Harness runs evaluation cases sequentially or with basic parallelism.

**Integration:** `fleet-ensemble` treats evaluation cases as musical proposals. Each case has a pitch (priority), duration (runtime), velocity (resource need). The `ConflictResolver` ensures no two cases compete for the same resource. The `HarmonicValidator` checks that the evaluation suite covers all "keys" (dimensions). The `EventStream` is the execution schedule, harmonically timed.

**Binding:** Rust crate, Python bindings. Input: evaluation cases with metadata. Output: execution schedule.

#### `constraint-schedule` → Harness CI Pipeline Ordering

Harness tests have implicit dependencies (safety before performance, correctness before trajectory).

**Integration:** `constraint-schedule` models CI as a CSP. Variables = test stages. Domains = available agents/GPUs. Constraints = dependency order, resource limits, timeout bounds. The solver returns optimal pipeline order. If unsatisfiable, it explains which constraint is the bottleneck.

**Binding:** Rust crate, Python bindings. Input: test graph + resource specs. Output: schedule or conflict explanation.

#### `sheaf-coherence` → Harness Safety Consensus

Harness safety metrics are evaluated independently.

**Integration:** `sheaf-coherence` assigns a belief vector to each safety metric. The sheaf Laplacian measures global alignment. If all metrics agree the output is safe, `L_F x = 0` (perfect section). If metrics disagree, the alignment score tells you how close to consensus.

**Binding:** Rust crate, Python bindings. Input: safety metric scores as belief vectors. Output: coherence measure + global section.

### 2.5 Novel Capabilities Our Math Adds

| Capability | Math Source | What Harness Gains |
|------------|-------------|--------------------|
| **Invariant-based reliability** | Noether's theorem + RG | Reliability is not variance; it's conservation. Find the true invariants of your agent. |
| **Topological trajectory fingerprint** | Persistent homology | Every agent has a barcode—a topological fingerprint. Compare agents by barcode similarity. |
| **Pareto-optimal performance frontier** | Tropical geometry | The Newton polytope of (cost, latency, accuracy) reveals Pareto vertices. No more guessing at tradeoffs. |
| **Spectral confidence calibration** | Eigenvalue estimation + deadbands | Confidence is a physical dial. Calibration error is deadband width. Thermostatically controlled. |
| **Fundamental vs. fixable disagreement** | Hodge decomposition | When metrics conflict, know if you can fix it (gradient) or must choose (harmonic). |
| **Harmonic evaluation scheduling** | PLR group + ensemble coordination | Evaluation suites are musical scores. Conflict-free, harmonically timed execution. |
| **Optimal CI pipeline** | CSP + constraint propagation | Tests order themselves. Unsatisfiable pipelines explain their own bottlenecks. |
| **Global safety consensus** | Sheaf Laplacian alignment | Safety is not a boolean; it's a coherence measure. Global alignment tells you if your safety suite is internally consistent. |


---

## 3. Browser Use (`browser-use/browser-use`)

### 3.1 What It Does and Why It's Popular

Browser Use is an open-source Python library (with a Rust core in v0.13) that connects LLM reasoning to Playwright-driven browser actions. ~95k GitHub stars.

**Popularity drivers:**
- **Vision + DOM hybrid:** Takes screenshots and analyzes them visually. The LLM sees the page like a human does.
- **Natural language tasks:** "Put these items in my Instacart cart" or "Find the number of stars on the browser-use repo."
- **Rust core for speed:** v0.13 introduces a Rust-powered beta agent with persistent tools, recovery loops, and a real browser action space.
- **Cloud + open-source dual model:** Self-host for custom integrations, or use Cloud for stealth browsers, proxy rotation, CAPTCHA solving.
- **MCP integration:** Supports Model Context Protocol for Claude Desktop and other MCP clients.
- **CLI-first:** `browser-use open`, `snapshot`, `click`, `type`, `screenshot`, `close`. Fast iteration.

**Architecture:**
```
User Input → LLM Processing → DOM + Vision Analysis → Action Planning → Playwright Execution → State Update → Feedback Loop
```

### 3.2 Core Architecture and Key Abstractions

**Core components:**
- **Agent:** Top-level orchestrator. Takes a task string, an LLM, and optional browser/tools. Runs an iterative loop until complete.
- **Browser Profile:** Configuration for headless mode, allowed domains, authentication, proxy settings.
- **LLM Integration Layer:** Connects to OpenAI, Anthropic, Google, local models (Ollama), or Browser Use's own hosted models.
- **Browser Control Engine:** Playwright under the hood. WebSocket-based communication.
- **Visual Understanding System:** Screenshots + DOM extraction. Hybrid approach.
- **Tools:** Extensible action space. Custom tools via `@tools.action` decorator.
- **History:** Stateful session tracking. Final result extraction.
- **MCP Client:** Connects to external MCP servers to extend agent capabilities.

### 3.3 Where SuperInstance Crates Could Replace/Enhance Components

Browser Use is a single-agent system. Its architecture is a loop: observe → plan → act. SuperInstance crates can enhance every stage and add multi-agent browser coordination.

| Browser Use Component | Current State | SuperInstance Enhancement |
|-----------------------|---------------|---------------------------|
| **Action Planning** | LLM plans next action from scratch each step | `constraint-schedule`: the action space is a CSP. Constraints = page structure, user goals, safety rules. The solver prunes invalid actions before the LLM sees them. |
| **Visual Understanding** | Screenshots + DOM extraction | `persistence-agent`: page state history is a point cloud. Persistent homology extracts topological features: loops (navigation cycles), clusters (page sections), voids (unexplored areas). The agent knows what kind of page it's on by its barcode. |
| **State Update / Feedback Loop** | Simple state machine | `noether-guard`: define conservation laws for browser state (e.g., "form completeness is conserved under navigation"). Violations trigger recovery. |
| **Multi-Tab / Multi-Agent Coordination** | Single agent, single browser context | `fleet-ensemble` + `fleet-i2i-protocol`: multiple browser agents coordinate via I2I messaging. One agent researches, one fills forms, one monitors for CAPTCHAs. The ensemble resolves conflicts and validates harmonic timing. |
| **Timing / Scheduling** | Step-by-step, LLM-paced | `fleet-midi-pulse`: browser actions are timed to a musical pulse. Fast actions (clicking) on downbeats. Slow actions (reading) on sustained notes. Tempo ramps for urgent tasks. Fermata for human-in-the-loop pauses. |
| **Recovery / Resilience** | Basic retry loops | `renormalization-agent`: zoom out from individual steps to session-level behavior. RG analysis finds which observables survive coarse-graining (true resilience patterns) vs. noise. |
| **Session Authentication** | Chrome profile reuse, AgentMail | `conservation-protocol`: authenticated sessions are conserved quantities. The Laplacian of the session graph ensures auth state propagates correctly across agents. |
| **Tool Extensibility** | Python decorator + MCP | `ternary-core`: tools compile to ternary WASM. Execution is sandboxed and formally verifiable. Capabilities are ternary: permitted, forbidden, or governed. |
| **Performance Optimization** | Cloud scaling for parallel execution | `tropical-synth`: model the cost/latency/accuracy of browser tasks as a tropical polynomial. Find Pareto-optimal configurations. Morph between configurations based on task requirements. |
| **Network Topology Awareness** | Proxy rotation (cloud only) | `heat-spectral` + `wave-conservation`: the proxy network is a graph. Heat diffusion finds fastest paths. Wave propagation detects bottlenecks. The Fiedler value λ₂ measures network health. |

### 3.4 Specific Crate Mappings

#### `constraint-schedule` → Browser Use Action Planning

Browser Use's LLM plans actions from a large action space. Many actions are invalid on the current page.

**Integration:** `constraint-schedule` models the action space as a CSP. Variables = potential actions. Domains = available elements on the page. Constraints = element visibility, user goal relevance, safety rules. The solver prunes invalid actions, returning a small set of constraint-satisfying candidates. The LLM plans from this reduced set—faster, safer, more accurate.

**Binding:** Rust crate compiled to WASM, loaded by the Rust core. The browser harness calls the scheduler before each LLM invocation.

#### `noether-guard` → Browser Use State Conservation

Browser agents frequently lose state: navigate away from a half-filled form, close a tab with important information, overwrite clipboard content.

**Integration:** `noether-guard` defines conservation laws for browser state:
- "Form field values are conserved under navigation within the same domain"
- "Tab count is conserved unless explicitly closed by user instruction"
- "Authentication cookies are conserved across page loads"

`ConservationMonitor` ticks after each action. Violations trigger automatic recovery. `DriftDetector` predicts when conservation will break (e.g., a page with a 5-minute timeout).

**Binding:** Rust crate, integrated into the Rust core. Maintains state snapshot, compares pre/post action.

#### `fleet-ensemble` + `fleet-i2i-protocol` → Multi-Agent Browser Coordination

Browser Use is single-agent. Complex tasks require sequential execution, which is slow.

**Integration:** `fleet-i2i-protocol` provides multicast messaging between browser agents. Agent A (researcher) INFORMs Agent B (purchaser) of product details. Agent B COMMITs to a purchase. Agent C (monitor) REFUSEs if a CAPTCHA appears.

`fleet-ensemble` coordinates the agents. Each agent submits `Proposal` objects. The `ConflictResolver` prevents two agents from modifying the same cart. The `HarmonicValidator` ensures agents stay in the same "key" (user goal). The `EventStream` is the coordinated browsing session.

**Binding:** Rust crates, native integration. I2I gateway runs alongside the browser harness.

#### `fleet-midi-pulse` → Browser Action Timing

Browser Use actions are paced by LLM inference time—irregular and slow.

**Integration:** `fleet-midi-pulse` provides a musical clock. Actions are quantized to ticks:
- Downbeat: navigation actions (high latency, high impact)
- Offbeat: clicking actions (fast, precise)
- Sustain: reading/waiting actions (long duration, low CPU)
- Tempo ramp: urgent tasks accelerate the clock
- Fermata: human-in-the-loop pauses

This makes multi-agent coordination deterministic: all agents agree on the beat.

**Binding:** Rust crate, integrated into the Rust core. Pulse broadcasts `TickEvent` to all agents.

#### `persistence-agent` + `witness-topology` → Page Classification and Navigation

Browser Use agents navigate blindly—they don't know the "shape" of a website.

**Integration:** `persistence-agent` builds a Vietoris-Rips complex from the page's DOM tree. The barcode classifies page types: login page (β₀=1, β₁=0), product listing (β₀=1, β₁=high), multi-step form (β₀=1, β₁=loop). `witness-topology` does the same with sparse sampling for large SPAs.

The agent knows: "I'm on a login page" or "This is a wizard with 3 steps" by topological signature.

**Binding:** Rust crate, WASM or Python bindings. Called after page load, returns page archetype.

#### `tropical-synth` → Browser Task Cost Optimization

Browser Use Cloud charges for browser hours, proxy rotation, and CAPTCHA solving. Self-hosted costs include LLM tokens and compute.

**Integration:** `tropical-synth` models the cost structure as a tropical polynomial:
- Variables: model choice, proxy usage, headless mode, screenshot frequency
- Coefficients: measured costs per unit
- Vertices of Newton polytope = Pareto-optimal configurations

The agent can answer: "Given my $5 budget and 2-minute deadline, what is the optimal configuration?"

**Binding:** Rust crate, Python bindings. Called before task start, returns optimal config.

#### `renormalization-agent` → Session-Level Recovery

Browser Use has basic retry loops but no learning from failure.

**Integration:** `renormalization-agent` coarse-grains session data (individual clicks → page visits → task phases → full sessions). It extracts observables that survive coarse-graining:
- "Navigation depth before success" (relevant)
- "Exact click position" (irrelevant)
- "Time of day" (marginal)

Recovery strategies are trained on scale-invariant features.

**Binding:** Rust crate, background analytics. Feeds into the LLM's context as learned skills.

#### `heat-spectral` + `wave-conservation` → Proxy Network Health

Browser Use Cloud uses proxy rotation for stealth. Proxy health is opaque.

**Integration:** `heat-spectral` models the proxy network as a graph. Heat diffusion finds fastest paths. `wave-conservation` propagates signals through the proxy graph. Bottleneck proxies have high wave delay. The Fiedler value λ₂ measures overall network connectivity.

**Binding:** Rust crate, integrated into Browser Use Cloud's proxy manager.

#### `ternary-core` → Tool Sandbox

Browser Use's custom tools run as Python functions—untrusted code in the same process.

**Integration:** `ternary-core` compiles tools to ternary WASM. Execution is sandboxed. Tool capabilities are ternary: `True` (permitted), `False` (forbidden), `Unknown` (requires approval). Z₃ arithmetic enables formal verification: prove that no sequence of permitted tools can reach a forbidden state.

**Binding:** Rust crate with WASM executor. Replaces Python function tools in the Rust core.

#### `groovemesh-plr` → Browser Session Sonification

Browser Use sessions are silent. Operators can't hear when an agent is struggling.

**Integration:** `groovemesh-plr` sonifies the browsing session. Each page type is a triad. Navigation actions are PLR transformations. A smooth session sounds like a well-voice-led progression. A stuck session sounds like parallel fifths (repetitive error loops). The `CounterpointRules` detect when the agent is "playing wrong notes."

**Binding:** Rust crate, optional audio output. Integrates with `fleet-midi-pulse` timing.

### 3.5 Novel Capabilities Our Math Adds

| Capability | Math Source | What Browser Use Gains |
|------------|-------------|------------------------|
| **Constraint-pruned action planning** | CSP + constraint propagation | LLM plans from a pre-validated action subset. Invalid actions are impossible. |
| **Conservation-governed browsing** | Noether's theorem | Browser state (forms, auth, tabs) is physically conserved. Violations auto-recover. |
| **Multi-agent browser orchestration** | I2I speech acts + ensemble counterpoint | Research, purchase, and monitor agents coordinate without collision. |
| **Musical action timing** | Drift-corrected pulse + swing quantization | Actions happen on the beat. Multi-agent sync is deterministic. |
| **Topological page classification** | Persistent homology + witness complexes | Pages are classified by topological signature, not heuristics. |
| **Pareto-optimal task configuration** | Tropical geometry | Given budget and deadline, find the optimal (model, proxy, mode) configuration mathematically. |
| **Scale-invariant recovery learning** | Renormalization group | Learn which failure patterns matter across time scales. Ignore noise, remember structure. |
| **Spectral proxy health monitoring** | Graph Laplacian + heat/wave equations | Proxy networks report health via eigenvalue. Bottlenecks and partitions are detected algebraically. |
| **Formally verified tool sandbox** | Z₃ arithmetic + WASM | Tools are provably safe. No forbidden state is reachable from permitted actions. |
| **Audible session health** | PLR group + counterpoint | A struggling agent sounds discordant. Operators hear problems before dashboards show them. |


---

## 4. Cross-Repo Integration: The SuperInstance Substrate

The three target repos form a pipeline:

```
Paperclip (orchestrate) → Browser Use (execute) → Harness (evaluate)
```

SuperInstance crates can substrate this entire pipeline:

### 4.1 Unified Timing Layer

`fleet-midi-pulse` provides a single musical clock across all three repos:
- Paperclip heartbeats tick on the downbeat
- Browser Use actions sync to the same pulse
- Harness evaluation suites are scored in harmonic time

A company running on Paperclip, browsing with Browser Use, and evaluating with Harness operates to a shared rhythm.

### 4.2 Unified Conservation Layer

`noether-guard` monitors conservation across the pipeline:
- Paperclip: budget and goal alignment are conserved
- Browser Use: session state and auth are conserved
- Harness: accuracy and reliability are conserved

A single `ConservationMonitor` can track invariants end-to-end, detecting when a Paperclip budget violation causes a Browser Use session failure that degrades Harness accuracy.

### 4.3 Unified Consensus Layer

`conservation-protocol` + `sheaf-coherence` provide a shared consensus mechanism:
- Paperclip agents gossip Laplacian rows to align on company goals
- Browser Use agents gossip to align on task state
- Harness metrics gossip to align on quality thresholds

Consensus is not a meeting; it's a spectral gap.

### 4.4 Unified Scheduling Layer

`constraint-schedule` optimizes across repos:
- Paperclip work queues + Browser Use action plans + Harness CI pipelines = one global CSP
- Constraints: agent availability, browser pool size, GPU quota, deadline dependencies
- Output: unified schedule maximizing throughput

### 4.5 Unified Evaluation Layer

`hodge-consensus` + `persistence-agent` evaluate the pipeline itself:
- When Paperclip, Browser Use, and Harness disagree about quality, Hodge decomposition tells you why
- The pipeline's behavioral trajectory has a barcode. Compare pipeline versions by topological fingerprint.

---

## 5. Implementation Roadmap

### Phase 1: WASM Bindings (Months 1–2)

Compile foundation crates to WASM:
- `noether-guard`
- `tropical-synth`
- `constraint-schedule`
- `fleet-midi-pulse`

Expose via `wasm-bindgen` for Paperclip (Node.js) and Browser Use (Rust core can embed WASM).

### Phase 2: Python Bindings (Months 2–3)

Compile crates to Python extensions via PyO3/maturin:
- `noether-guard`
- `persistence-agent`
- `witness-topology`
- `tropical-synth`
- `hodge-consensus`
- `sheaf-coherence`
- `analog-spectral`

Target: Harness Evals and Browser Use Python APIs.

### Phase 3: Plugin Integration (Months 3–4)

Build Paperclip plugins wrapping:
- `spreadsheet-engine` (memory/knowledge layer)
- `fleet-i2i-protocol` (agent messaging gateway)
- `conservation-protocol` (goal alignment gossip)
- `fleet-ensemble` (governance engine)

### Phase 4: Rust Core Integration (Months 4–5)

Integrate into Browser Use's Rust core:
- `constraint-schedule` (action planning)
- `noether-guard` (state conservation)
- `fleet-midi-pulse` (timing)
- `ternary-core` (tool sandbox)
- `renormalization-agent` (recovery learning)

### Phase 5: Cross-Repo Orchestration (Months 5–6)

Deploy unified substrate:
- Single `fleet-midi-pulse` clock across Paperclip + Browser Use + Harness
- Shared `ConservationMonitor` tracking invariants end-to-end
- Global `constraint-schedule` optimizing CI + work queues + action plans

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **WASM/JS interop performance** | Medium | High | Benchmark before committing. Use `wasm-opt`. Fall back to native Node-API for hot paths. |
| **Python binding maintenance** | Medium | Medium | Use `maturin` + `pyo3` with minimal hand-written C. Automate wheel builds in CI. |
| **Upstream API churn** | High | Medium | Target stable abstractions. Don't fork; wrap. |
| **Math complexity scares contributors** | Medium | High | Expose simple APIs hiding the math. Document with examples, not proofs. |
| **Licensing incompatibility** | Low | High | All SuperInstance crates are MIT/Apache-2.0. Paperclip is MIT. Harness is Apache-2.0. Browser Use is MIT. Compatible. |

---

## 7. Conclusion

Paperclip, Harness, and Browser Use are application-layer innovations. They solve human problems with excellent UX and strong communities. Their weakness is that they re-invent foundational patterns—conservation, consensus, scheduling, coordination—that mathematics solved decades ago.

SuperInstance does not compete with these projects. It **substrates** them:
- Paperclip gains a physics engine for its company model
- Harness gains a dynamical systems perspective on evaluation
- Browser Use gains a mathematically grounded action space

The integration is not replacement. It is elevation: the same apps, running on deeper foundations, producing capabilities that neither community could build alone.

> *"If Paperclip is the company, Harness is the audit, and Browser Use is the hands—SuperInstance is the physics that makes them work."*

---

*Document generated from source-code reconnaissance of paperclipai/paperclip, harness/harness-evals, and browser-use/browser-use, combined with deep audit of 23 SuperInstance crates.*
