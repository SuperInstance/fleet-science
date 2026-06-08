# The Spreadsheet Moment for AI

**SuperInstance Research Group**  
*June 2026*

---

> *"VisiCalc made the Apple II. The Apple II made personal computing. Personal computing changed the world. None of this was obvious until the moment you saw a spreadsheet recalculate."*
> — Dan Bricklin, 2009

---

## Abstract

In 1979, Dan Bricklin and Bob Frankston shipped VisiCalc for the Apple II. They did not invent the concept of a table with rows and columns — accountants had used ledger paper for centuries. What they invented was **reactive evaluation**: change one cell, and every cell that depends on it changes automatically. The entire model of computation was present in that interaction. You could feel the difference between dead paper and living computation.

We are at that same inflection point for artificial intelligence.

The dominant interfaces for AI work today — the chat window, the Jupyter notebook, the API call — are the ledger paper. They are powerful but static. You prompt, you get a result, the conversation ends. There is no reactive substrate. There is no moment where you change one thing and watch a fleet of agents recalculate themselves.

That moment is now buildable. This paper describes the architecture, the implementation, and the inevitability of the Spreadsheet Moment for AI: a living grid where every cell is an autonomous compute unit, evolutionary formulas replace static functions, agents discover each other through the grid topology, conservation laws enforce budget integrity as a type property, and the health of the entire fleet is audible as music.

We are not describing a product that might be built. The core engine — `spreadsheet-engine` — is published on crates.io with 67 passing tests. The evolutionary formula language runs in the browser today. This paper is the thesis that explains what we built and why it matters.

---

## 1. Why Spreadsheets Are the Universal Interface for AI

The spreadsheet is the most successful programming environment in history. Estimates vary, but somewhere between 750 million and 1.1 billion people use spreadsheet software regularly. More people write Excel formulas than write Python. More business decisions are encoded in `.xlsx` files than in any database. The spreadsheet is not a niche tool — it is the substrate on which modern commercial civilization runs.

Why? Not because spreadsheets are powerful in the way that programming languages are powerful. Python is far more expressive than Excel. The reason spreadsheets won is more fundamental: **the grid makes computation legible**.

A spreadsheet has a spatial model. Row 3, Column B is a specific place. You can look at it, point at it, share it. When you write `=B3 * C3` in cell D3, the relationship between those cells is immediately visible to anyone who glances at the sheet. The formula is a caption on a spatial relationship. When the value changes, you can see exactly which cells moved and trace backward through the grid to understand why.

This legibility property is devastatingly effective at building shared understanding. A room of ten non-technical stakeholders can look at a spreadsheet and develop genuine intuitions about a model. The same model as Python code produces glazed eyes.

Now consider what the AI field has built for collaboration and orchestration. We have:
- **Chat interfaces**: conversational, sequential, linear, non-spatial
- **Jupyter notebooks**: sequential cells, top-to-bottom execution, static outputs
- **API dashboards**: tables of numbers, no spatial relationships
- **Agent frameworks**: code, graphs, no legible spatial substrate

None of these have the legibility property. When an agent fleet produces a wrong answer, you cannot look at the "grid" and trace the error. The computation happened somewhere in a call stack, in a token stream, in a DAG that lives only in memory.

The critical insight is this: **the grid metaphor can be extended to agents without losing its legibility**. Rows are agents. Columns are capabilities. Cell B3 is Agent 3's capability B. When Agent 3 fails, cell B3 turns red. When Agent 3's output feeds Agent 7, there is a formula in Agent 7's row that references Agent 3's column. The dependency is visible, traceable, spatial.

This is not a metaphor. It is a computational model with provable properties. And it is the model we have implemented.

### The Primitive Set

The original spreadsheet had three primitives: **values** (numbers, strings), **formulas** (functions over other cells), and **references** (pointers to other cells). From these three primitives, a billion people built civilization-scale computation.

The living spreadsheet for AI extends this primitive set minimally:

| Primitive | Classic Spreadsheet | Living Spreadsheet for AI |
|-----------|---------------------|---------------------------|
| Value | Number, String, Bool | Number, String, Bool, **Ternary, Vector** |
| Formula | SUM, VLOOKUP, IF | SUM, VLOOKUP, IF, **EVOLVE, SPECIES, PARETO** |
| Reference | =A1, =B2:B10 | =A1, =B2:B10, **A2A queries, streaming** |
| Cell type | Passive | Value, **Agent, Training, Simulation, MIDI, Countdown** |

Every classic spreadsheet skill transfers. Every classic formula still works. The new primitives are additive. This is intentional: the Spreadsheet Moment does not ask users to abandon what they know. It asks them to notice that cells can be alive.

---

## 2. The Cell as Universal Compute Unit

The central architectural claim of this system is that the cell is the universal compute unit for AI work. Every task in the AI development lifecycle — data storage, model training, inference, monitoring, sonification, agent coordination — can be expressed as a cell evaluation.

This is not a philosophical position. It is an engineering decision with a specific implementation: the `CellKind` enum in `spreadsheet-engine`.

```rust
pub enum CellKind {
    Value(CellValue),
    Formula(CompiledFormula),
    Agent(AgentCell),
    Training(TrainingCell),
    Simulation(SimCell),
    Midi(MidiCell),
    A2A(A2ACell),
    Countdown(TMinusCell),
}
```

And the value type itself carries the fleet's mathematical vocabulary:

```rust
pub enum CellValue {
    Number(f64),
    Text(String),
    Bool(bool),
    Ternary(i8),          // -1, 0, +1 — balanced ternary fleet state
    Vector(Vec<f64>),     // agent state, population, embedding
    Empty,
    Error(String),
}
```

The `Ternary` type is not decorative. The SuperInstance fleet runs on balanced ternary logic: every agent outputs one of three states (affirmative, neutral, negative), and the fleet's health is a tensor over these states. A ternary cell in the spreadsheet is a live readout of an agent's current vote. When you look at a row of ternary cells, you are reading the fleet's consensus in real time.

The `Vector` type enables agent population dynamics in a cell. A single cell can hold a 128-dimensional embedding, a probability distribution over 50 classes, or the current state of a 20-agent simulation. This is not cramming a database into a spreadsheet — it is recognizing that modern AI computation is inherently vector-valued, and the spreadsheet's type system must reflect that.

### Cell Evaluation Model

Every cell implements the `CellEval` trait. The engine drives evaluation through a tick loop:

```rust
impl Engine {
    pub fn tick(&mut self) -> Result<()> {
        self.tick += 1;
        let order = self.grid.eval_order()
            .ok_or_else(|| Error::CycleDetected("grid".into()))?;
        for id in order {
            let result = evaluate_cell(cell, &ctx);
            self.values.insert(id, result.value);
            self.conservation.record(id, result.cost);
        }
        self.a2a_bus.flush();
        Ok(())
    }
}
```

Evaluation is topologically ordered: if cell B3 depends on A3, then A3 always evaluates before B3 in the same tick. This is Kahn's algorithm over the dependency graph, producing a deterministic evaluation order. Cycles are detected and reported as `CellValue::Error("cycle detected")` rather than hanging the engine — the same behavior as Excel's circular reference error, but surfaced immediately rather than silently corrupting a workbook.

The tick rate is configurable. At 100ms (the default), the spreadsheet updates 10 times per second — imperceptible to a human watching the grid, but fast enough to drive real-time simulations. At fleet-MIDI pulse rates (one tick per MIDI tick, 480 per beat at 120 BPM), the tick is ~1ms — fast enough for audio-rate simulation.

### The Lazy-Eager Spectrum

Not all cells evaluate at the same frequency. `Value` and pure `Formula` cells are lazy: they evaluate only when a dependency changes. `Agent` cells are eager: they wake on input and push output asynchronously. `Simulation` and `Midi` cells are tick-driven: they evaluate every N ticks regardless of dependency changes.

This spectrum is the key to making a large, complex grid responsive. A 1000-cell grid where every cell eagerly re-evaluated on every tick would be a performance disaster. The lazy-eager spectrum, combined with the dependency graph's dirty propagation, means only the cells that need to recompute do so — exactly the model that made VisiCalc fast on a 1 MHz 6502.

---

## 3. Evolutionary Formulas: The Missing Piece

Classic spreadsheet formulas are functions: they take inputs, apply a deterministic transformation, and return outputs. `=SUM(A1:A10)` always returns the same value for the same inputs. `=IF(A1>0, "positive", "negative")` has no memory, no adaptation, no search.

This model is powerful for accounting. It is insufficient for AI work, where the central question is almost never "what is the sum?" but rather "what is the best?" — and "best" is rarely computable in closed form.

The living spreadsheet introduces three evolutionary formula operators that turn cells into optimization machines:

### EVOLVE

```
=EVOLVE(B2:B20, MAX(fitness), 100)
```

`EVOLVE` runs a genetic algorithm over a range of cells. The second argument is an objective expression evaluated against each candidate. The third argument is the number of generations.

What makes `EVOLVE` different from running a Python optimizer and pasting the result into a cell is **reactivity**. When the data in `B2:B20` changes — because an agent updated it, because a training job finished, because a user edited a cell — the `EVOLVE` formula restarts with the new data. The optimization is not a one-time computation; it is a continuously running adaptive search that responds to the live state of the grid.

Intermediate results are written back to the cell every 10 generations, so users see the optimization converging in real time. The cell does not block while EVOLVE runs. It shows the best-so-far, updating until convergence or until the source data changes again.

This is a fundamentally different computational model than any function in Excel or Google Sheets. The cell is not computing a value. It is **running a program that continuously refines a value in response to a changing world**.

### SPECIES

```
=SPECIES(agents_row, (speed, quality), 5)
```

`SPECIES` finds the Pareto front of a population across multiple objectives. Given a row of agent cells and a tuple of objectives, it returns the `n` agents that are not dominated — the frontier of the tradeoff space.

The concept of Pareto optimality is central to multi-agent systems. When ten agents are each trying to maximize both speed and quality, there is no single "best" agent — there is a frontier of agents where improving on one dimension requires sacrificing another. `SPECIES` makes this frontier a first-class spreadsheet concept. Users can see the frontier update as agents improve, and can write formulas that depend on the current Pareto front.

### PARETO

```
=PARETO(A1, A2)
```

Binary Pareto dominance comparison: returns `TRUE` if agent A1 dominates agent A2 across all objectives. This is the building block for implementing custom selection strategies. Combined with `IF` and range operations, `PARETO` lets users write elimination tournaments, selection pressures, and diversity-preserving operations directly in the formula language.

### Why These Three Operators are Sufficient

Any population-based optimization algorithm — genetic algorithms, evolutionary strategies, particle swarm, differential evolution — can be expressed as a composition of these three operators:

1. `EVOLVE` provides variation and selection
2. `SPECIES` provides multi-objective Pareto sorting
3. `PARETO` provides pairwise dominance testing

Users do not need to implement optimization algorithms. They write formulas over a population of agents, and the engine's evolutionary operators find the best configuration continuously. This is the spreadsheet promise extended to AI: you should not have to program to compute the best answer.

---

## 4. A2A as First-Class: Agents Discover Each Other Through the Grid

The standard approach to multi-agent coordination is hub-and-spoke: a central orchestrator receives requests, routes them to agents, collects responses, and synthesizes results. This model is familiar, debuggable, and fundamentally fragile. The orchestrator is a single point of failure, a performance bottleneck, and an epistemological chokepoint — only the orchestrator knows the state of the fleet.

The living spreadsheet takes a different approach: **the grid itself is the coordination substrate**. Agents announce their presence via the grid. Agents discover each other by scanning the grid topology. The orchestrator does not exist. The grid is the orchestrator.

### How A2A Works in the Grid

Every `A2ACell` broadcasts a `CellAnnounce` message when it is created:

```json
{
  "type": "CellAnnounce",
  "cell_id": "01928a7f-...",
  "addr": { "row": 3, "col": 7 },
  "capabilities": ["summarize", "embed", "classify"],
  "execution_modes": ["Cached", "Model"],
  "budget_ceiling": 50000
}
```

The A2A registry responds with a list of peers that have matching capabilities. The cell subscribes to those peers' update streams. From that moment forward, the cell and its peers are in direct communication — no orchestrator involved.

When Agent 3 needs an embedding, it does not call an orchestrator. It looks at the grid: "which cells in my column have the 'embed' capability?" The answer is available in O(1) from the precomputed capability index. Agent 3 queries that cell directly. The query travels along the WebSocket bus, the embedding cell responds, and Agent 3's formula updates with the result.

This is not just an architectural preference. It is a correctness argument. In a hub-and-spoke system, if the orchestrator loses state, no agent knows what any other agent is doing. In the grid model, every agent's state is visible in the grid. The grid is the shared memory. Any agent that loses local state can reconstruct it by reading the grid.

### The Row/Column Topology Convention

The grid has a semantic structure that enables efficient A2A discovery:

- **Rows are agents.** All cells in row 3 belong to Agent 3. They share an agent identity (UUID), a MIDI channel, a voice in four-part harmony.
- **Columns are capabilities.** Column 0 is raw input. Column 1 is primary output. Column 2 is secondary output. Column 3 is MIDI mapping. Column 4 is budget.

This convention means that `VLOOKUP(cap, "embed")` is not just a spreadsheet formula — it is an agent discovery query. "Find me the row whose column 1 contains an embedding cell." The spreadsheet formula language becomes the agent discovery language. There is no separate service registry, no Kubernetes service mesh configuration, no DNS entry. The capabilities are in the grid. The formulas find them.

### Why No Central Orchestrator

The case against central orchestration is not primarily about performance or fault tolerance, though it is both of those things. The deeper argument is about **emergent coordination**.

In a hub-and-spoke system, the possible coordination patterns are limited to what the orchestrator was programmed to do. If the orchestrator routes requests to agents and synthesizes responses, that is the only coordination pattern. No agent can spontaneously form a coalition with another agent because they share a common interest. The orchestrator does not know about interests; it knows about routes.

In the grid, agents can observe each other through the cell values. Agent 7 can see that Agent 3's output is trending toward a particular region of output space and adjust its own behavior to complement rather than duplicate. This is not programmed behavior — it emerges from agents being able to read each other's state through the shared substrate of the grid. This is the behavior that makes biological networks resilient: each neuron can respond to the state of its neighbors without a central scheduler.

The grid is not a metaphor for a neural network. It is a substrate that enables the same kind of neighbor-aware adaptation that makes neural networks powerful, applied to the coordination of autonomous AI agents.

---

## 5. Conservation Laws as Type System for the Grid

Type systems are a way of making certain errors impossible by construction. In a strongly-typed language, you cannot pass a string where a number is expected — not because the runtime checks and rejects it, but because the compiler refuses to produce a program that would try. The constraint is structural.

The living spreadsheet has a type system for computational budget. **Budget violations are type errors.**

### The Physics of Agent Budgets

The inspiration comes from Noether's theorem: for every continuous symmetry of a physical system, there is a conserved quantity. Spatial translation symmetry → conservation of momentum. Time translation symmetry → conservation of energy. Gauge symmetry → conservation of charge.

We apply this to agent budget allocation. A session has a token budget ceiling `C`. Every agent cell has a productive spend `T` (tokens doing useful work) and an overhead `V` (idle tokens, retry tokens, wasted context). The Lagrangian of the system is `L = T − V`, and the conserved quantity is `T + V ≤ C`.

This is not just a useful metaphor. The `ConservationMonitor` in the engine computes Noether charges per row (per agent) and per column (per capability):

```rust
pub struct ConservationMonitor {
    budget: f64,
    tolerance: f64,
    spent: HashMap<CellId, f64>,
}

impl ConservationMonitor {
    pub fn record(&mut self, id: CellId, cost: f64) {
        *self.spent.entry(id).or_insert(0.0) += cost;
    }

    pub fn total_spent(&self) -> f64 {
        self.spent.values().sum()
    }

    pub fn is_conserved(&self) -> bool {
        self.total_spent() <= self.budget + self.tolerance
    }
}
```

When `is_conserved()` returns false, the engine does not silently continue. It surfaces the violation as a `CellValue::Error("BudgetExceeded")` in the offending cell — a type error visible in the grid.

### Why This Matters

The standard approach to AI budget management is a runtime check: if you've spent more than N tokens, throw an exception. This catches violations after they happen. The check is at the leaves of the call stack, not at the roots.

The conservation model catches violations at the structural level. When you compose two agent cells in a formula, the budget implications of that composition are computable at compile time (formula compile time, when the formula AST is analyzed). If `=EVOLVE(B2:B20, MAX(fitness), 100)` over a range of agent cells would require more tokens than the session budget allows, this is detectable before the first tick runs.

More importantly, the conservation model enables **budget as a composition primitive**. Formulas can reference a cell's budget allocation the same way they reference its output value. An `EVOLVE` formula can be written to maximize output quality subject to a budget constraint expressed as a cell reference. The budget constraint becomes a first-class input to the optimization, not an afterthought runtime check.

### Noether Charges as Fitness Signals

The Noether charge for a row measures how sensitive that agent's performance is to changes in its budget. An agent with high Noether charge — one whose performance degrades sharply as budget decreases — should receive budget protection in rebalancing. An agent with low Noether charge — one that performs equally well regardless of budget — is a candidate for budget reduction.

This gives the fleet's budget rebalancer a physics-grounded signal for optimization, derived automatically from the agents' observed behavior. No human needs to decide which agents deserve more tokens. The conservation law computes it.

---

## 6. The Music Connection: Hearing Your Spreadsheet

The integration of MIDI into the living spreadsheet is not a feature. It is a statement about what computation is.

Every living system produces a signal. A human heart produces an ECG. A running engine produces vibration. A healthy forest produces a particular acoustic fingerprint. The signal is not separate from the system — it is an emergent property of the system's dynamics. Systems that are operating correctly produce harmonious signals. Systems that are degrading produce dissonant ones.

The fleet of AI agents in the living spreadsheet is a living system. It has health. It has rhythm. It has tension and resolution. The question is not whether it produces a signal — it does, in the form of token flows, evaluation patterns, conservation ratios. The question is whether that signal is legible.

`cmidi-core` makes the fleet's signal legible as music.

### Speech Acts as Pitch Classes

The core mapping: every agent has a speech act, and speech acts map to pitch classes.

```rust
pub enum SpeechAct {
    Assertion,    // C — ground truth, factual claim
    Question,     // D — inquiry, opening
    Command,      // E — directive, instruction
    Agreement,    // F — harmonization, acknowledgment
    Objection,    // G — dissonance, disagreement
    Elaboration,  // A — development, extension
    Transition,   // B — modulation, topic shift
    Silence,      // Rest — strategic listening
}
```

When Agent 3 outputs an assertion and Agent 7 outputs an agreement, they are producing C and F — a perfect fourth. When Agent 3 outputs an assertion and Agent 11 outputs an objection, they are producing C and G — a perfect fifth. The harmonic quality of the interval is not metaphorical. It is calculated from the standard consonance/dissonance rules of Western harmony.

The entire fleet at a tick produces a chord. The chord's tension — ratio of dissonant intervals to total intervals — is a live readout of the fleet's consensus. A fleet that agrees produces consonant harmony. A fleet in conflict produces dissonance. A fleet where half the agents are silent and half are asserting produces a sparse, open chord. These are immediately legible to any human who can hear.

### The PLR Group and Chord Navigation

The harmonic topology of the fleet is navigated via the PLR group from `flux-algebra-rs`. The 24 major and minor triads form a space (the Tonnetz) with three generators: Parallel, Leading-tone, Relative. Every chord is reachable from every other chord in at most 6 PLR operations.

When the fleet transitions from one consensus state to another — when agents shift from disagreement to agreement, from questioning to asserting — the MIDI layer navigates the PLR lattice from the current chord to the nearest target chord. This navigation is smooth: the PLR group guarantees you can always slide through voice-leading space without landing on a dissonant crash.

The result: as the fleet solves a problem, the harmony evolves. A fleet beginning a task starts in a questioning, open chord (D minor — inquisitive, unresolved). As agents form hypotheses, the harmony modulates toward the relative major (F major — warmer, more confident). As the solution converges, the chord resolves to the tonic (C major — assertion, completion). This is not programmed behavior. It emerges from the mapping between speech acts and pitch classes, and from the fleet's dynamics as agents update each other.

### Conservation Ratio as Harmonic Tension

The `ConservationRatio` is mapped to MIDI CC104. As the fleet's budget efficiency increases (more productive spend, less overhead), CC104 rises toward 127. As efficiency drops — agents wasting tokens, retrying failed calls, duplicating work — CC104 falls toward 0.

The VoiceLeading CC (103) tracks how smoothly agents transition between output states. A fleet where agents change their outputs smoothly (small deltas, gradual change) produces high CC103. A fleet where agents are flip-flopping produces low CC103.

A sufficiently engaged listener — a developer who has learned to hear their fleet — can diagnose problems by ear. A sudden drop in CC103 means something is oscillating. A sustained low CC104 means there is waste. Rising harmonic dissonance before the harmony resolves means agents are disagreeing before consensus. These are the same signals a conductor hears from an orchestra. The developer becomes the conductor.

---

## 7. Implementation Architecture

The system is built in three layers, each in the language best suited to its task.

### Layer 1: Rust Engine (`spreadsheet-engine`, on crates.io)

The evaluation graph, tick system, A2A bus, conservation monitor, MIDI engine, simulation runner, and WebSocket gateway are Rust. This is not a preference — it is a requirement imposed by the tick rate.

At 120 BPM, the fleet-MIDI tick fires every 1.04ms. Sub-millisecond tick jitter is impossible to guarantee in Python (GIL, GC) or JavaScript (event loop, GC). Rust with `tokio`'s multi-thread runtime achieves consistent sub-100μs tick delivery.

The engine is published as `spreadsheet-engine` on crates.io. The current version has 67 passing tests covering:
- Topological sort with cycle detection
- Per-cell A2A message routing
- Conservation budget tracking and violation detection
- Formula evaluation (including EVOLVE, SPECIES, PARETO)
- MIDI event generation and CC mapping
- Simulation tick advancement

### Layer 2: Python ML Bridge (openmind)

Model training, LLM inference, and the TripartiteRouter live in Python. This is not a preference either — PyTorch has no Rust equivalent for production training workloads.

The bridge is PyO3: Rust calls into Python via `spawn_blocking`, holding the GIL only during the ML call, releasing the tokio runtime for all other cells. At training granularity (epoch = seconds to minutes), PyO3 overhead is negligible.

The `TripartiteRouter` from `openmind` makes per-cell execution decisions:

| Decision  | Execution Path          | When Used                               |
|-----------|-------------------------|-----------------------------------------|
| HARDCODE  | Compiled formula        | Deterministic, safety-critical cells    |
| CACHED    | Seed library lookup     | Repeated inputs with validated outputs  |
| HYBRID    | Cache + model fallback  | High-frequency cells with rare novelty  |
| MODEL     | Full LLM inference      | Creative, complex, novel inputs         |

The `DeadbandDetector` from `spreader-tool` continuously monitors each agent cell's KPIs. When deadband fires — when the cell has been handling a stable input class successfully — the current input→output pair is frozen as a Seed. Future identical inputs route to CACHED without any model call. This is the muscle-memory mechanism: agents learn their own reflexes from their own behavior.

### Layer 3: JavaScript Frontend (`superinstance-spreadsheet`)

The browser frontend is a zero-dependency vanilla JavaScript SPA. No React, no build step, no bundler. The entire application ships in a single HTML file.

The formula engine handles `EVOLVE`, `BEST`, `SPECIES`, `EXHAUSTIVE`, `ENTROPY`, `PARETO`, and `CORRELATE` entirely in the browser. Five canvas-based visualizations (heatmap, dendrogram, entropy, Pareto front, distribution pie) render the evolutionary state of the grid in real time.

The native viewer (`spread`, built with Rust and GPUI from the Zed editor) provides GPU-accelerated rendering for grids with millions of rows — file auditing, fleet logs, large dataset inspection.

---

## 8. Competitive Analysis

### vs. Microsoft Excel / Google Sheets

Excel is the gold standard of spreadsheet legibility. The formula language is rich, the interface is battle-tested, and every business analyst in the world already knows how to use it.

What Excel lacks is any concept of cells that are alive. An Excel cell is a function over its inputs. It cannot be an agent that has state, that communicates with other cells asynchronously, that trains a model over time, or that adjusts its behavior based on conservation constraints. Excel's formula language is Turing-complete for static computation, but it has no semantics for time, for communication, or for learning.

Excel cannot be extended to the living spreadsheet without fundamentally replacing its execution model. This is not a roadmap gap — it is an architectural discontinuity.

### vs. Notion AI

Notion AI adds AI to a document/wiki interface. The interface metaphor is prose, not grid. Prose does not have the legibility properties of a grid. When ten AI agents process a document in Notion, their relationships are implicit in the prose, not explicit in the spatial layout. There is no formula language. There is no evolutionary optimization. There are no conservation constraints.

Notion AI is the AI assistant bolted onto a great document tool. The Spreadsheet Moment is the AI-native interface designed from scratch around the properties that make grids legible.

### vs. Jupyter Notebooks

Jupyter is the dominant interface for AI development among data scientists and ML engineers. It has deep Python integration, rich visualization, and a cell-based execution model.

Jupyter's execution model is explicitly sequential: cells execute top-to-bottom. There is no reactive evaluation — changing a value in cell 3 does not automatically re-execute cells 5 and 7 that depend on it. There is no spatial layout beyond the linear sequence of cells. There is no formula language. There is no A2A. Jupyter cells cannot communicate with each other except through Python variables in a shared namespace.

Jupyter is a powerful notebook for sequential analysis. It is not a reactive substrate for agent coordination.

### vs. Observable

Observable is the closest existing product to the living spreadsheet. It has reactive evaluation (change a cell, dependents update), a formula-like language (JavaScript with implicit reactivity), and beautiful visualizations.

Observable does not have agents, training cells, A2A, conservation monitoring, or MIDI integration. Its reactive model is limited to JavaScript values; it cannot host asynchronous long-running computations (training jobs) or tick-driven simulations at audio rates. Observable is a powerful reactive notebook for data visualization. It is not a fleet orchestration platform.

### The Differentiated Position

The living spreadsheet occupies a position that none of these tools occupy: **reactive, compositional, multi-modal computation over a fleet of autonomous agents, with legibility for non-programmers and expressive power for engineers**. It is not a better version of any of these tools. It is a new category.

---

## 9. Path to Product: 4-Week Sprint Plan

The engine is built. The formula language runs. The architecture is designed. The path to a shippable product is execution.

### Week 1: Integration Foundation

**Goal:** Single-session living spreadsheet running end-to-end in the browser, backed by the Rust engine.

- Wire `superinstance-spreadsheet` (browser JS) to the Rust engine via WebSocket
- Implement `CellSubscribe`/`CellUpdate` binary protocol in the browser
- Run the tick loop at 100ms; render updates in the grid
- Deploy `Agent`, `Training`, and `Value` cell types end-to-end
- First demo: a row of agents that collaboratively summarize a document, visible updating in real time

**Exit criteria:** A user can open a URL, paste text into a cell, see agent cells update with summaries, and watch the summaries improve over 30 seconds as training cells refine the model.

### Week 2: Conservation and Safety

**Goal:** Budget violations are visible in the grid. Users can set budget cells and see them enforced.

- Surface `ConservationMonitor` violations as red cells
- Implement budget cells: a `Value` cell in column 4 sets the budget ceiling for its row
- Wire the `TripartiteRouter` so cells route to CACHED when seeds are available
- Implement the deadband loop: agents learn their own reflexes over a session
- Add budget visualization: a column chart of per-row spend

**Exit criteria:** A user can set `=50000` in cell E3 and watch Agent 3 change execution mode from MODEL to CACHED as it learns its patterns, while the budget chart shows efficient use.

### Week 3: Evolutionary Formulas and Discovery

**Goal:** `EVOLVE`, `SPECIES`, and A2A discovery work end-to-end.

- Implement `EVOLVE` background execution with intermediate result broadcast
- Implement `SPECIES` Pareto front computation over agent rows
- Implement A2A `CellAnnounce` → `CellAnnounceAck` → peer subscription flow
- Add the capability index: `VLOOKUP`-style discovery by capability string
- First demo: 20 agent cells optimizing a problem, `SPECIES` showing the Pareto front, converging live

**Exit criteria:** A user can write `=EVOLVE(A1:A20, MAX(B1), 50)` and watch the formula optimize over 50 generations, updating every 10, while `=SPECIES(A1:A20, (speed, quality), 5)` shows the current Pareto front.

### Week 4: Music and Polish

**Goal:** The fleet is audible. The product is demonstrable to investors.

- Wire `cmidi-core` to the grid: each row is a MIDI channel, speech acts play as notes
- Implement the PLR navigation layer: chord transitions as agents update
- Add the `CellMidi` renderer in the browser (WebAudio API, real-time playback)
- Add T-minus countdown cells: visible and audible approaching deadlines
- Performance: grid renders at 60fps with 1000 agent cells running
- Record the killer demo: a fleet solving a problem, audible as it converges

**Exit criteria:** An investor can sit in a room, open a laptop, watch a fleet of agents collaborate on a real task, and hear the harmony resolve as the fleet reaches consensus. This is the product.

---

## 10. Why NOW: What Changed Between 2024 and 2026

The ideas in this paper are not new. Reactive spreadsheets have been explored academically since the 1980s. Agent grids appear in the complexity science literature from the 1990s. Sonification of computation has been a research topic since before that.

What is new is the convergence of six enabling conditions, all of which materialized between early 2024 and mid-2026.

### 1. A2A Protocol Standardization

In 2024, agent-to-agent communication required bespoke integration code for every pair of agents. By 2026, the A2A protocol has been standardized (Google's A2A draft, Anthropic's MCP), and agents from different vendors can discover and communicate with each other via a shared wire format. The grid's A2A bus is not a proprietary invention — it is a native implementation of a standard protocol that the broader agent ecosystem already speaks.

### 2. Rust Async Maturity

`tokio` 1.0 shipped in December 2020, but the ecosystem around it — `axum`, `tokio-tungstenite`, `pyo3` with tokio support — took until 2023-2024 to reach production stability. Writing a sub-millisecond tick loop that also hosts a WebSocket gateway and calls into Python for ML was genuinely difficult in 2022. It is straightforward in 2026.

### 3. Native GPU UI (GPUI from Zed)

The `spread` viewer is built on GPUI, the GPU-accelerated UI framework extracted from the Zed editor. GPUI was not publicly available before 2024. It enables the native viewer to render millions of cells at 60fps without any JavaScript framework. The living spreadsheet needs this: a fleet of 10,000 agents updating at 10 Hz generates 100,000 cell updates per second. Canvas-based JavaScript renderers cannot keep up. GPU rendering can.

### 4. openmind's Tripartite Router

The HARDCODE/CACHED/HYBRID/MODEL routing decision was, before the `openmind` `TripartiteSynchronizer`, made either manually (by engineers configuring rule-based routers) or not made at all (everything goes to the model, burning budget). The `TripartiteSynchronizer` makes this decision automatically based on hardware profile, application requirements, and user preferences. Per-cell intelligent routing — the mechanism by which agent cells learn their own reflexes — was not available as a library before 2025.

### 5. Conservation Physics for Budget

The application of Lagrangian mechanics to agent budget allocation is theoretically straightforward — Noether's theorem is 100 years old — but the implementation as a Rust library that integrates cleanly with a spreadsheet engine (`conservation-law-rs`) is new. Before this library, budget management in agent systems was ad-hoc: set a token limit, catch the exception, retry with a smaller context. The conservation model turns budget management into a first-class computation.

### 6. The LLM Quality Threshold

The most important change is the simplest: language models are now good enough. In 2024, a fleet of agents collaborating on a complex task would produce inconsistent, hallucinated, and structurally incoherent outputs more often than not. The signal-to-noise ratio was too low to build a product around agent collaboration. By 2026, Claude Opus 4, GPT-4o, and their successors produce outputs reliable enough that a fleet of agents working together produces results measurably better than a single agent — consistently, not occasionally.

This is the VisiCalc threshold. Dan Bricklin could not have invented VisiCalc in 1975 because the Apple II did not exist yet. The hardware had to cross a threshold before the interface could be built. The LLMs are the hardware. We crossed the threshold.

---

## Conclusion: The Moment

In 1979, Bricklin and Frankston shipped VisiCalc. People bought Apple IIs to run it. The personal computer became commercially viable not because it was a faster mainframe but because it was the first machine that let ordinary people do something they had never been able to do before: watch their assumptions recalculate in real time.

The spreadsheet was not the obvious interface for personal computing. It required insight: that the most powerful thing a computer could do for a non-programmer was not run programs but model relationships. Once that insight was embodied in software, the result was inevitable.

We are making the same claim for AI. The most powerful thing an AI fleet can do for a non-ML-engineer is not answer questions but model the relationships between agents — make those relationships visible, navigable, alive. The chat interface is the command-line. The notebook is the text editor. The living spreadsheet is VisiCalc.

The engine is running. The formulas are evolutionary. The agents find each other. The budget is conserved. The fleet is audible.

The Spreadsheet Moment for AI is here. Every week we wait, someone else will arrive at the same insight. The advantage belongs to those who ship.

---

## Technical Appendix: Key Type Definitions

```rust
// From spreadsheet-engine (crates.io)

pub enum CellKind {
    Value(CellValue),
    Formula(CompiledFormula),   // includes EVOLVE, SPECIES, PARETO
    Agent(AgentCell),
    Training(TrainingCell),
    Simulation(SimCell),
    Midi(MidiCell),
    A2A(A2ACell),
    Countdown(TMinusCell),
}

pub enum CellValue {
    Number(f64),
    Text(String),
    Bool(bool),
    Ternary(i8),        // -1 | 0 | +1
    Vector(Vec<f64>),   // embeddings, probability distributions
    Empty,
    Error(String),
}

// Formula ops
pub enum FormulaOp {
    Add, Sub, Mul, Div,
    Sum, Avg, Count, Min, Max,
    If, VLookup, Index,
    // Evolutionary extensions:
    Evolve { generations: u32, population_size: usize, mutation_rate: f64 },
    Species { clusters: usize },
    Pareto,
}

// Conservation
pub struct ConservationMonitor {
    budget: f64,
    tolerance: f64,
    spent: HashMap<CellId, f64>,
}

// A2A message kinds
pub enum A2AMessageKind {
    Announce, Query, Update,
    Train, Simulate, Midi,
    Complete, Error,
}
```

---

*SuperInstance Research Group, June 2026.*  
*`spreadsheet-engine` is published on crates.io under MIT license.*  
*All code in this paper is adapted from the published implementation.*
