# SuperInstance Understand — Rust Rewrite / Refactoring Plan

**Source target:** `Lum1104/Understand-Anything` (forked as `Egonex-AI/Understand-Anything`)  
**Output spec:** Replace the TypeScript multi-agent pipeline with SuperInstance Rust crates.  
**Deliverable:** Phased implementation plan: Phase 1 (Rust core), Phase 2 (Agent pipeline), Phase 3 (Dashboard), Phase 4 (Novel math features).

---

## 1. What Understand-Anything Does Today

The TypeScript plugin is a Claude Code extension with three layers:

| Layer | Package / Path | Responsibility |
|---|---|---|
| **Core data model** | `packages/core/src/types.ts`, `schema.ts` | `KnowledgeGraph`, `GraphNode` (21 types), `GraphEdge` (35 types), `Layer`, `TourStep`, validation, normalization |
| **Static extraction** | `packages/core/src/analyzer/*`, `skills/understand/extract-structure.mjs`, `extract-import-map.mjs` | Tree-sitter parsing, import resolution, call-graph extraction, fingerprint-based change detection |
| **LLM agents** | `agents/*.md` prompt specs + orchestrator | `project-scanner`, `file-analyzer`, `architecture-analyzer`, `tour-builder`, `graph-reviewer`, `domain-analyzer`, `article-analyzer` |
| **Context builders** | `src/context-builder.ts`, `explain-builder.ts`, `onboard-builder.ts`, `understand-chat.ts`, `diff-analyzer.ts` | RAG-style graph traversal, prompt formatting, diff impact analysis |
| **Dashboard** | `packages/dashboard/src/*` | React + Vite interactive graph explorer, search, tours, themes, persona-adaptive UI |

The product is essentially a **deterministic parser → multi-agent LLM pipeline → knowledge graph → React dashboard** loop.

---

## 2. SuperInstance Understand — Target Architecture

The rewrite keeps the same user-facing loops (`/understand`, `/understand-chat`, `/understand-diff`, `/understand-dashboard`) but replaces the implementation core with Rust crates.

### 2.1 Crate Mapping

| Original TS Component | SuperInstance Rust Crate | Role in the Rewrite |
|---|---|---|
| `packages/core` types + graph validation | New crate: `understand-core` | Serde schema, graph invariants, persistence, JSONL/JSON graph format |
| Tree-sitter extraction scripts (`extract-structure.mjs`, `extract-import-map.mjs`) | `tree-sitter` (official Rust bindings) + `understand-parser` (new wrapper crate) | Deterministic AST/CFG extraction, import resolution, call graphs |
| LLM agent orchestration | `fleet-i2i-protocol` + `conservation-protocol` | Inter-agent multicast, capability discovery, consensus, violation detection |
| React dashboard | `spreadsheet-plr-bridge` (repurposed) + Tauri/WASM frontend | Grid-based knowledge visualization; cells = nodes, formulas = derived views |
| Code similarity / duplicate detection | `spectral-fingerprint` | Eigenvalue fingerprints of per-function AST graphs |
| Graph health / spectral monitoring | `analog-spectral` (refactored to lib) or `conservation-spectral-v2` | Spectral gap, Fiedler vector, connectivity health |
| Invariant checking across graph versions | `noether-guard` (new crate wrapping `lau-calm-noether`) | Noether-style conserved quantities detect drift/regression |

### 2.2 Crate Readiness Notes

| Crate | Current State | Action Before Integration |
|---|---|---|
| `fleet-i2i-protocol` | Library-ready (`src/lib.rs`, `Transport`, `I2IMessage`, `Router`) | None — consume directly |
| `conservation-protocol` | Library-ready (`ConsensusTracker`, `GossipProtocol`, `LaplacianMatrix`, `ViolationDetector`) | None — consume directly |
| `spreadsheet-plr-bridge` | Library-ready but music-domain (chords, PLR operations) | Generalize cell/formula model to knowledge cells |
| `spectral-fingerprint` | Modules only, **no `src/lib.rs`** and no `[lib]` in `Cargo.toml` | Add `lib.rs` + `[lib]` section; expose `SpectralFingerprint`, `SimilarityIndex`, `Cluster` |
| `analog-spectral` | Binary-only (`src/main.rs`), no `lib.rs` | Refactor to `lib.rs` + thin `main.rs`; expose `DialBank`, `SpectralGapAnalysis`, `SpectralThermostat` |
| `conservation-spectral-v2` | Library-ready, hyper-optimized (SIMD, batch pipelines) | Use as drop-in for spectral graph health |
| `lau-calm-noether` | Library-ready (CALM ⟺ Noether ⟺ conserved charges) | Wrap into new `noether-guard` crate with graph-specific invariants |

---

## 3. Phase 1 — Rust Core

**Goal:** Port the deterministic, non-LLM parts of `packages/core` into a Rust workspace crate called `understand-core`.

### 3.1 `understand-core` — Data Model

Mirror the TypeScript schema in Rust with strict Serde compatibility:

```rust
pub struct KnowledgeGraph {
    pub version: String,
    pub kind: GraphKind,          // codebase | knowledge
    pub project: ProjectMeta,
    pub nodes: Vec<GraphNode>,    // 21 node types as enum variants
    pub edges: Vec<GraphEdge>,    // 35 edge types as enum variants
    pub layers: Vec<Layer>,
    pub tour: Vec<TourStep>,
}

pub enum NodeType {
    File, Function, Class, Module, Concept,
    Config, Document, Service, Table, Endpoint,
    Pipeline, Schema, Resource,
    Domain, Flow, Step,
    Article, Entity, Topic, Claim, Source,
}

pub enum EdgeType {
    Imports, Exports, Contains, Inherits, Implements,
    Calls, Subscribes, Publishes, Middleware,
    ReadsFrom, WritesTo, Transforms, Validates,
    DependsOn, TestedBy, Configures,
    Related, SimilarTo,
    // ... (all 35 variants)
}
```

Deliverables:
- `KnowledgeGraph` and subtypes with `Serialize`/`Deserialize`
- Validation pipeline equivalent to `schema.ts::validateGraph()` (sanitization → normalization → auto-fix → tiered validation → referential integrity)
- Alias normalization table ported to a `phf` static map
- Incremental persistence: `GraphStore` trait backed by `sled` or SQLite for local cache

### 3.2 `understand-parser` — Tree-Sitter Wrapper

Depend on official `tree-sitter` + language crates:

```toml
[dependencies]
tree-sitter = "0.25"
tree-sitter-typescript = "0.23"
tree-sitter-python = "0.23"
tree-sitter-go = "0.23"
tree-sitter-rust = "0.23"
tree-sitter-java = "0.23"
# ... others
```

Deliverables:
- `LanguageParser` trait: `parse(file_path, source) -> StructuralAnalysis`
- `ImportResolver` trait: language-specific import → resolved path
- `CallGraphExtractor` trait: caller/callee pairs with line numbers
- Batch driver that mirrors `extract-import-map.mjs` behavior
- Fingerprint-based change detection (hash of structural analysis) for incremental re-analysis

### 3.3 File Scanning

Rewrite `scan-project.mjs` in Rust using `ignore` crate + `git2`/`std::process::Command` for `git ls-files`:

```rust
pub struct ProjectScanner;
impl ProjectScanner {
    pub fn scan(root: &Path, ignore: &IgnoreFilter) -> ScanResult;
}
```

Outputs:
- File inventory with `language`, `file_category`, `size_lines`
- `total_files`, `filtered_by_ignore`, `estimated_complexity`

### 3.4 Phase 1 Exit Criteria

- `understand-core` and `understand-parser` compile and pass property tests
- Round-trip test: TS `schema.ts` fixture → Rust `KnowledgeGraph` → JSON → TS validation succeeds
- Parser produces identical `StructuralAnalysis` for the Understand-Anything repo itself
- CLI binary `si-understand scan ./path` writes `.understand-anything/intermediate/scan-result.json`

---

## 4. Phase 2 — Agent Pipeline

**Goal:** Replace the Markdown-prompt agent orchestration with typed Rust agents communicating over `fleet-i2i-protocol` and enforcing consistency with `conservation-protocol`.

### 4.1 Agent Roles (Mapped from Original)

| Original Agent | Rust Agent | Responsibilities |
|---|---|---|
| `project-scanner.md` | `ScannerAgent` | File inventory, language detection, manifest reading, import-map extraction |
| `file-analyzer.md` | `AnalyzerAgent` | Per-batch AST extraction + semantic node/edge emission |
| `architecture-analyzer.md` | `ArchitectAgent` | Layer assignment, architectural theme detection |
| `tour-builder.md` | `TourAgent` | Dependency-ordered learning paths |
| `graph-reviewer.md` | `ReviewerAgent` | Referential integrity, alias correction, cross-layer consistency |
| `domain-analyzer.md` | `DomainAgent` | Business domain / flow / step extraction |
| `article-analyzer.md` | `ArticleAgent` | Wiki/article knowledge graphs |

### 4.2 Messaging with `fleet-i2i-protocol`

Each agent gets an `Address`. The orchestrator uses `I2IMessage` with `PayloadType::Task` and `SpeechActKind::Request` to dispatch work.

```rust
use fleet_i2i_protocol::{Address, I2IMessage, Payload, SpeechActKind, Transport};

let task = I2IMessage::new(
    orchestrator_addr,
    Address::agent("file-analyzer", batch_id),
    Payload::Task {
        speech_act: SpeechActKind::Request,
        content: serde_json::to_value(&FileAnalysisTask { files, import_map }).unwrap(),
    },
);
transport.send(task).await?;
```

Capability discovery:
- Each agent advertises `Capability` at startup: `languages_supported`, `batch_size`, `output_schema_version`
- Orchestrator matches task requirements to agent capabilities

### 4.3 Consensus / Review with `conservation-protocol`

`ReviewerAgent` and `ArchitectAgent` participate in a `GossipProtocol` round to reach consensus on disputed graph elements:

- **Dangling edges:** edges pointing to nodes that no agent emitted
- **Conflicting layer assignments:** same node claimed by multiple layers
- **Alias normalization disputes:** e.g., `implements` vs `implemented_by` direction

```rust
use conservation_protocol::{GossipProtocol, ConsensusTracker, ViolationDetector};

let gossip = GossipProtocol::new(laplacian_from_agent_graph());
gossip.run_round(agent_states, &mut tracker)?;

let detector = ViolationDetector::new(consensus_threshold);
let violations = detector.check(&proposed_graph);
```

The Laplacian rows encode agent agreement weights. Consensus is reached when the spectral gap (λ₂) exceeds a threshold — exactly what `conservation-protocol` is designed for.

### 4.4 Context Builders in Rust

Port the five `src/*.ts` context builders to Rust modules inside `understand-core`:

```rust
pub mod context {
    pub fn build_chat_context(graph: &KnowledgeGraph, query: &str, max_nodes: usize) -> ChatContext;
    pub fn build_explain_context(graph: &KnowledgeGraph, path: &str) -> ExplainContext;
    pub fn build_diff_context(graph: &KnowledgeGraph, changed_files: &[String]) -> DiffContext;
    pub fn build_onboarding_guide(graph: &KnowledgeGraph) -> String;
    pub fn build_chat_prompt(ctx: &ChatContext) -> String;
}
```

These are pure graph-traversal functions (no LLM) and map 1:1 to the TypeScript logic:
- `buildChatContext`: SearchEngine relevance + 1-hop edge expansion + layer collection
- `buildExplainContext`: Target node lookup → child nodes via `contains` edges → connected neighbors
- `buildDiffContext`: Changed file → node mapping → 1-hop affected neighbors + impacted layers
- `buildOnboardingGuide`: Markdown generation from graph metadata, layers, tour, complexity hotspots

### 4.5 LLM Backend Abstraction

Add `si-llm-client` crate with a trait that supports OpenAI-compatible, Anthropic, and local endpoints:

```rust
#[async_trait]
pub trait LlmClient: Send + Sync {
    async fn complete(&self, prompt: Prompt) -> Result<String, LlmError>;
    async fn complete_structured<T: DeserializeOwned>(&self, prompt: Prompt, schema: &Schema) -> Result<T, LlmError>;
}
```

Agent prompts are no longer `.md` files read by a TS runtime. They become:
- `Handlebars` templates compiled at build time (`include_str!`)
- Type-safe prompt structs with `schemars` JSON schema output for structured generation

### 4.6 Phase 2 Exit Criteria

- All 7 agents run concurrently via `fleet-i2i-protocol`
- `conservation-protocol` consensus reaches agreement on a 1000-node test graph in < 5 rounds
- Context builders produce byte-identical markdown output for a fixed graph fixture
- End-to-end `/understand` command works from Rust CLI, emits valid `knowledge-graph.json`

---

## 5. Phase 3 — Dashboard

**Goal:** Replace the React/Vite dashboard with a Rust-native spreadsheet-grid visualization built on `spreadsheet-plr-bridge`.

### 5.1 Why a Spreadsheet View?

The original dashboard visualizes the graph as a force-directed node-link diagram. SuperInstance Understand treats the knowledge graph as a **living worksheet**:

- Rows = nodes (files, functions, classes, services, etc.)
- Columns = properties (name, type, complexity, layer, summary, tags, file path, line range)
- Formulas = derived views (e.g., `=DEPENDENTS(file:src/auth.ts)`, `=HEATMAP(complexity)`, `=PATH(file:A, file:B)`)

This maps naturally onto `spreadsheet-plr-bridge`'s existing cell/formula/evaluator model, generalizing it from music chords to knowledge entities.

### 5.2 Generalizing `spreadsheet-plr-bridge`

Introduce a new top-level crate `understand-sheet` that depends on `spreadsheet-plr-bridge` but replaces musical primitives:

| `spreadsheet-plr-bridge` Concept | `understand-sheet` Concept |
|---|---|
| `ChordCell` | `KnowledgeCell` (wraps a `GraphNode`) |
| `Formula` / `FormulaToken` | Reused verbatim; add graph-aware tokens |
| `Operation::P/L/R` | `GraphOp::Dependents, ::Dependencies, ::Path, ::Cluster, ::Similar |
| `VoiceLeadingBudget` | `RenderBudget` (limits expansion depth for large graphs) |
| `ConservationStatus` | `InvariantStatus` (graph validity checked by `noether-guard`) |

New formula functions:
- `DEPENDENTS(node_id)` — reverse `imports`/`calls`/`depends_on` edges
- `DEPENDENCIES(node_id)` — forward edges
- `PATH(a, b)` — shortest path between nodes
- `HEATMAP(metric)` — color cells by complexity or edge betweenness
- `SIMILAR(node_id, k)` — top-k spectral fingerprints
- `HEALTH()` — spectral graph health score from `conservation-spectral-v2`

### 5.3 Frontend Architecture

```
┌─────────────────────────────────────────┐
│  Tauri / egui / Web (WASM) frontend     │
│  - grid renderer (virtualized)          │
│  - graph overlay (force layout)         │
│  - search + filters + tours             │
├─────────────────────────────────────────┤
│  understand-sheet (Rust)                │
│  - cell store, formula evaluator        │
│  - graph → sheet projection             │
├─────────────────────────────────────────┤
│  understand-core (Rust)                 │
│  - knowledge graph, context builders    │
└─────────────────────────────────────────┘
```

Recommended frontend stack:
- **Tauri** for desktop-embedded dashboard (replaces the Vite dev-server model)
- **`egui` or `jsona/jsona-egui`** for immediate-mode grid UI
- **`d3-rs` / `force-atlas2-rs`** for optional graph-force overlay

### 5.4 Phase 3 Exit Criteria

- `understand-dashboard` opens from CLI (`/understand-dashboard`) and loads a 10k-node graph in < 2s
- Spreadsheet formulas update in < 100ms for `DEPENDENTS`/`DEPENDENCIES` queries
- Tour mode walks through cells in dependency order
- Persona adaptation (junior / senior / PM) filters columns and summary detail level

---

## 6. Phase 4 — Novel Math Features

**Goal:** Augment the knowledge graph with three mathematical capabilities from the SuperInstance crate ecosystem.

### 6.1 `spectral-fingerprint` — Eigenvalue Code Similarity

**What it does:** Compute a fixed-length eigenvalue fingerprint from each function's AST adjacency matrix. Similar functions have similar fingerprints.

**Integration:**

```rust
use spectral_fingerprint::{CodeGraph, SpectralFingerprint, SimilarityIndex};

// Inside AnalyzerAgent: for each function node, build CodeGraph from AST
let fg = CodeGraph::from_tree(ast_nodes, &parents);
let fp = SpectralFingerprint::from_graph_labeled(&fg, &function_id)?;

// Global index updated after each batch
similarity_index.add(fp);
```

**User-facing features:**
- `find_duplicates(threshold)` detects copy-pasted or near-copy code
- `query_top_k(query_fn, k)` finds similar implementations ("show me other auth handlers like this one")
- `cluster(k)` groups functions by structural family; clusters become auto-tags or suggested `similar_to` edges

**Required crate work:**
- Add `src/lib.rs` to `spectral-fingerprint`
- Add `[lib]` to `Cargo.toml`
- Re-export `fingerprint::SpectralFingerprint`, `similarity::SimilarityIndex`, `ast_matrix::CodeGraph`

### 6.2 `analog-spectral` / `conservation-spectral-v2` — Graph Health

**What it does:** Monitor the spectral properties of the knowledge graph as a proxy for architectural health.

**Integration with `conservation-spectral-v2` (primary):**

```rust
use conservation_spectral_v2::{Graph, Laplacian, LaplacianKind, EigenResult};

let graph = Graph::from_knowledge_graph(&kg);       // nodes + weighted edges
let laplacian = graph.build_laplacian(LaplacianKind::Normalized);
let eigen = laplacian.eigendecompose()?;

let health = GraphHealth {
    fiedler_value: eigen.spectral_gap(),
    num_components: eigen.zero_eigenvalue_count(),
    connectivity_score: eigen.algebraic_connectivity(),
};
```

**Integration with `analog-spectral` (optional metaphorical layer):**

Refactor `analog-spectral` from binary to library and expose:

```rust
use analog_spectral::{DialBank, SpectralGapAnalysis, SpectralThermostat};

let mut bank = DialBank::from_graph_adjacency(&adj);
bank.settle(dt, tolerance);
let ev = bank.eigenvalue_estimate();
let gap = SpectralGapAnalysis::from_eigenvalues(vec![ev]);
let action = SpectralThermostat::new(setpoint, deadband).measure(ev);
```

This provides a physically intuitive "thermostat" UI: if graph connectivity drops below the setpoint, the dashboard warns and suggests refactoring.

**User-facing features:**
- Real-time `=HEALTH()` formula in the dashboard
- Alerts when a commit increases the number of disconnected components
- "Thermostat" widget showing spectral gap and recommended action (Increase coupling / Decrease coupling / Stable)

### 6.3 `noether-guard` — Invariant Checking

**What it does:** Treat graph updates as discrete dynamical systems. Use Noether's theorem (via `lau-calm-noether`) to define conserved quantities and detect violations.

**New crate:** `noether-guard` wrapping `lau-calm-noether`.

```rust
pub struct GraphInvariants {
    pub total_nodes: usize,           // cardinality invariant
    pub edge_to_node_ratio: f64,      // density invariant (within tolerance)
    pub layer_coverage: f64,          // every layer must have ≥ 1 node
    pub orphan_threshold: usize,      // max orphans tolerated
}

pub struct NoetherGuard;
impl NoetherGuard {
    pub fn compute_invariants(kg: &KnowledgeGraph) -> ConservedCharges;
    pub fn check_update(prev: &Charges, next: &Charges) -> Vec<InvariantViolation>;
}
```

Conserved quantities map to Noether symmetries:

| Conserved Quantity | Symmetry | Meaning |
|---|---|---|
| Node count (minus intentional drops) | Time-translation invariance of scan scope | No silently lost files |
| Edge/node ratio within band | Scale invariance | No explosive dependency growth |
| Layer coverage | Permutation symmetry across layer labels | Every architectural layer remains populated |
| Max orphan count | Gauge symmetry on dangling references | Referential integrity preserved |

**Integration:**
- `noether-guard` runs as a final pass after every `/understand` and `/understand-diff` update
- Violations are surfaced as dashboard warnings and appended to `diff-analyzer` risk assessment
- Used by `ReviewerAgent` as objective acceptance criteria before consensus

### 6.4 Phase 4 Exit Criteria

- `spectral-fingerprint` is library-ready and detects > 80% of manually injected duplicate functions
- Dashboard `=HEALTH()` formula returns a score within 50ms for a 5k-node graph
- `noether-guard` catches introduced orphan nodes and layer-emptying changes
- All three math crates have unit and property tests; CI passes

---

## 7. Migration Strategy

### 7.1 Repo Layout

Create a new repo `SuperInstance/si-understand` (or a `rust/` directory in the fork):

```
si-understand/
├── Cargo.toml              # workspace
├── crates/
│   ├── understand-core/
│   ├── understand-parser/
│   ├── understand-sheet/
│   ├── understand-dashboard/
│   ├── si-llm-client/
│   └── noether-guard/
├── agents/
│   ├── scanner-agent/
│   ├── analyzer-agent/
│   ├── architect-agent/
│   ├── tour-agent/
│   ├── reviewer-agent/
│   ├── domain-agent/
│   └── article-agent/
├── cli/
│   └── src/main.rs         # /understand, /understand-chat, /understand-diff, /understand-dashboard
└── docs/
```

### 7.2 Workspace Dependencies

```toml
[workspace.dependencies]
# SuperInstance crates (path or git)
fleet-i2i-protocol = { git = "https://github.com/SuperInstance/fleet-i2i-protocol" }
conservation-protocol = { git = "https://github.com/SuperInstance/conservation-protocol" }
spreadsheet-plr-bridge = { git = "https://github.com/SuperInstance/spreadsheet-plr-bridge" }
spectral-fingerprint = { git = "https://github.com/SuperInstance/spectral-fingerprint" }
conservation-spectral-v2 = { git = "https://github.com/SuperInstance/conservation-spectral-v2" }
analog-spectral = { git = "https://github.com/SuperInstance/analog-spectral" }
lau-calm-noether = { git = "https://github.com/SuperInstance/lau-calm-noether-readme" }

# External
tree-sitter = "0.25"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
clap = { version = "4", features = ["derive"] }
```

### 7.3 Compatibility Bridge

During transition, keep the JSON format identical to the original `KnowledgeGraph` schema so that:
- Old TS dashboards can read new Rust-generated graphs
- New Rust dashboards can read legacy cached graphs
- Teams can migrate incrementally without invalidating committed `.understand-anything/knowledge-graph.json` files

### 7.4 Testing Strategy

1. **Golden fixtures:** Capture 5 representative `knowledge-graph.json` files from the TS pipeline. Rust output must match after normalization.
2. **Property tests:** `proptest` for validation invariants (no dangling edges, valid aliases, weight in [0,1]).
3. **Benchmarks:** `criterion` for parser throughput, agent consensus rounds, and dashboard formula evaluation.
4. **Integration tests:** Run the Rust CLI against the Understand-Anything repo itself and diff outputs.

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| `spectral-fingerprint` and `analog-spectral` are not library-ready | Phase 0: add `lib.rs` and `[lib]` sections before main integration; budget 2–3 days each |
| Tree-sitter Rust grammars lag behind TS/node-tree-sitter | Pin versions and add CI smoke tests for each supported language; fallback to regex-only extraction for unsupported grammars |
| LLM structured-output reliability drops in Rust vs. TS prompt templates | Use `schemars` + constrained decoding where available; keep a `PromptTest` harness that asserts JSON schema conformance |
| React dashboard has rich interactivity that is hard to replicate in Rust/Tauri | Ship Phase 3 as a hybrid: Rust backend + React frontend over a local WebSocket if Tauri UI velocity is insufficient |
| Agent consensus may deadlock on ambiguous graph edits | Set round cap and escalation path: unresolved conflicts go to human triage in the dashboard |
| Performance of 10k-node spectral computation | Use `conservation-spectral-v2` SIMD paths; compute fingerprints lazily and cache in SQLite |

---

## 9. Summary of Deliverables by Phase

| Phase | Deliverable |
|---|---|
| **Phase 0 (Prep)** | `spectral-fingerprint` lib-ready; `analog-spectral` lib-ready; new `noether-guard` crate skeleton |
| **Phase 1** | `understand-core`, `understand-parser`, `si-llm-client`; CLI `scan` and `validate` commands |
| **Phase 2** | 7 Rust agents over `fleet-i2i-protocol` + `conservation-protocol`; context builders; full `/understand` pipeline |
| **Phase 3** | `understand-sheet` + Tauri dashboard; formula engine; tour and search UX |
| **Phase 4** | Integrated `spectral-fingerprint`, `conservation-spectral-v2`, `noether-guard`; dashboard health and invariant widgets |

---

## 10. Immediate Next Steps

1. **Fork / branch:** Create `rust-rewrite` branch in the forked Understand-Anything repo.
2. **Phase 0 PRs:**
   - `SuperInstance/spectral-fingerprint`: add `src/lib.rs` + `[lib]`
   - `SuperInstance/analog-spectral`: refactor to `lib.rs` + `main.rs`
   - `SuperInstance/noether-guard`: new crate depending on `lau-calm-noether`
3. **Bootstrap workspace:** `cargo new --bin si-understand` and add `crates/understand-core` with the type schema.
4. **Validation target:** Reproduce the Understand-Anything repo's own `knowledge-graph.json` from Rust and diff against the TS output.
