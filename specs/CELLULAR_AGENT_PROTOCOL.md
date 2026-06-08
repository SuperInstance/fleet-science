# Unified Cellular Agent Protocol (UCAP)

> **Version:** 1.0.0  
> **Status:** Draft  
> **Scope:** Defines how cells in the living spreadsheet communicate, discover, route, execute, and conserve resources.  
> **Unifies:** openmind (tripartite execution + cellular computation), agent-grid (mesh/ring/star/tree topologies), Google A2A (agent discovery + task delegation).

---

## 1. Overview

The Unified Cellular Agent Protocol (UCAP) treats every computational unit — a spreadsheet cell, a grid node, an agent process — as a **living cell**. Like biological cells, each agent-cell has:

- **Membrane** (interface / input-output contract)
- **Metabolism** (resource-adaptive execution: HARDCODE / CACHED / HYBRID / MODEL)
- **Signaling** (message passing over negotiated topologies)
- **Homeostasis** (conservation monitoring and budget enforcement)

UCAP unifies three existing systems:

| System | Contribution | UCAP Integration |
|--------|-----------|------------------|
| **openmind** | Tripartite execution model, resource probing, muscle memory | Execution tier selection, cell metabolism, `@cell` decorator semantics |
| **agent-grid** | Mesh/ring/star/tree topologies, node health, workload dispatch | Topology negotiation, routing, failure detection, load balancing |
| **Google A2A** | Agent discovery, task delegation, status streaming, artifact exchange | Discovery protocol, `Task`/`Artifact` schemas, `send/receive` semantics |

### 1.1 Design Principles

1. **Cell as Unit of Execution** — Every cell has a budget, a tier, and a topology role.
2. **Topology is Negotiated** — Cells do not assume a fixed wiring; they vote on it.
3. **Tier is Contextual** — The same cell may execute as HARDCODE on a server and CACHED on a Raspberry Pi.
4. **Conservation is First-Class** — Budget checks happen before every task dispatch.
5. **A2A-Native** — Cells speak A2A to the outside world and UCAP to their neighbors.

---

## 2. Core Abstractions

### 2.1 Execution Tier

From openmind's `Decision` enum and `MetabolicPath`:

```rust
/// How a cell metabolizes a task.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExecutionTier {
    /// Compiled/fast path. Spinal reflex. 0 tokens. <1 ms.
    Hardcode,
    /// Pre-computed replay. Cerebellar pattern. 0 tokens. <1 ms.
    Cached,
    /// Cache first, model fallback. Basal ganglia habit. ~50 tokens. ~50 ms.
    Hybrid,
    /// LLM inference. Prefrontal deliberation. ~500 tokens. ~500 ms.
    Model,
}
```

### 2.2 Cell Status

From agent-grid's `NodeStatus`, extended with IDLE:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CellStatus {
    Offline,
    Idle,
    Active,
    Suspect,
    Failed,
}
```

### 2.3 Topology Kind

From agent-grid's topology system:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TopologyKind {
    Mesh,
    Ring,
    Star,
    Tree,
}
```

### 2.4 Conservation Budget

From openmind's `cell_from_capability.py` default budgets and conservation-law:

```rust
/// Computational currency for a cell. Every task spend is deducted here.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct ConservationBudget {
    pub gpu_seconds: f64,
    pub compute_seconds: f64,
    pub memory_mb: f64,
    pub api_calls: u32,
}

impl ConservationBudget {
    pub const ZERO: Self = Self {
        gpu_seconds: 0.0,
        compute_seconds: 0.0,
        memory_mb: 0.0,
        api_calls: 0,
    };

    pub fn covers(&self, cost: &Self) -> bool {
        self.gpu_seconds >= cost.gpu_seconds
            && self.compute_seconds >= cost.compute_seconds
            && self.memory_mb >= cost.memory_mb
            && self.api_calls >= cost.api_calls
    }

    pub fn deduct(&self, cost: &Self) -> Self {
        Self {
            gpu_seconds: (self.gpu_seconds - cost.gpu_seconds).max(0.0),
            compute_seconds: (self.compute_seconds - cost.compute_seconds).max(0.0),
            memory_mb: (self.memory_mb - cost.memory_mb).max(0.0),
            api_calls: self.api_calls.saturating_sub(cost.api_calls),
        }
    }
}
```

### 2.5 The Cell Struct

```rust
use std::collections::HashSet;

/// A living cell in the spreadsheet grid.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Cell {
    pub cell_id: String,
    pub name: String,
    pub layer: String,               // "protocol", "foundation", "decomposition", "application"
    pub capabilities: Vec<String>,
    pub interface: CellInterface,
    pub budget: ConservationBudget,
    pub execution_tier: ExecutionTier,
    pub topology_role: TopologyRole,
    pub status: CellStatus,
    pub neighbors: HashSet<String>,
    pub last_heartbeat: u64,         // Unix millis
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CellInterface {
    pub input_schema: serde_json::Value,
    pub output_schema: serde_json::Value,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TopologyRole {
    Leaf,
    Hub,
    Root,
    Relay,
}
```

---

## 3. Message Protocol

All inter-cell messages use the **CellMessage** envelope. Messages are typed, routed, TTL-limited, and budget-aware.

### 3.1 CellMessage Envelope

```rust
use serde::{Serialize, Deserialize};
use serde_json::Value;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CellMessage {
    pub msg_type: CellMessageType,
    pub sender: String,              // cell_id
    pub receiver: String,            // cell_id, "BROADCAST", or "DIRECTORY"
    pub payload: Value,
    pub message_id: String,
    pub timestamp: u64,              // Unix millis
    pub ttl: u8,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub budget_hint: Option<ConservationBudget>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tier_hint: Option<ExecutionTier>,
}

impl CellMessage {
    pub fn new(msg_type: CellMessageType, sender: &str, receiver: &str, payload: Value) -> Self {
        Self {
            msg_type,
            sender: sender.to_string(),
            receiver: receiver.to_string(),
            payload,
            message_id: uuid::Uuid::new_v4().to_string(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_millis() as u64,
            ttl: 16,
            budget_hint: None,
            tier_hint: None,
        }
    }

    pub fn is_broadcast(&self) -> bool {
        self.receiver == "BROADCAST"
    }

    pub fn forward(&mut self, next_hop: &str) -> Result<(), CellBusError> {
        if self.ttl == 0 {
            return Err(CellBusError::TtlExpired);
        }
        self.ttl -= 1;
        self.receiver = next_hop.to_string();
        Ok(())
    }
}
```

### 3.2 CellMessageType

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CellMessageType {
    // ── Discovery (A2A + openmind) ──
    IdentityBroadcast,
    IdentityAck,
    AlignmentQuery,
    AlignmentResponse,

    // ── Topology (agent-grid) ──
    TopologyPropose,
    TopologyAccept,
    TopologyReject,
    TopologyRebuild,
    Heartbeat,

    // ── Task Execution (A2A + openmind) ──
    TaskRoute,
    TaskAck,
    TaskResult,
    TaskFail,
    TaskStatusUpdate,       // A2A streaming status
    TaskCancel,

    // ── Muscle Memory (openmind) ──
    ChordRequest,
    ChordOffer,
    ReflexExecute,

    // ── Conservation (conservation-law + a2a-conservation) ──
    BudgetReserve,
    BudgetCommit,
    BudgetReject,
    ConservationCheck,
    ConservationReport,

    // ── A2A Artifacts ──
    ArtifactPush,
    ArtifactPull,
}
```

### 3.3 Payload Schemas

#### Discovery

```rust
// IDENTITY_BROADCAST
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IdentityBroadcastPayload {
    pub cell: Cell,
    pub spectral_hash: String,       // Structural fingerprint of capabilities
}

// ALIGNMENT_QUERY
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlignmentQueryPayload {
    pub capability: String,
    pub min_alignment: f64,
}

// ALIGNMENT_RESPONSE
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlignmentResponsePayload {
    pub candidates: Vec<AlignmentCandidate>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlignmentCandidate {
    pub cell_id: String,
    pub alignment_score: f64,
    pub latency_ms_estimate: u32,
}
```

#### Topology

```rust
// TOPOLOGY_PROPOSE
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TopologyProposePayload {
    pub kind: TopologyKind,
    pub adjacency: std::collections::HashMap<String, Vec<String>>,
    pub diameter: usize,
    pub redundancy_factor: f64,
}

// TOPOLOGY_ACCEPT / TOPOLOGY_REJECT
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TopologyVotePayload {
    pub accepted: bool,
    pub reason: Option<String>,
    pub counter_proposal: Option<TopologyKind>,
}

// HEARTBEAT
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeartbeatPayload {
    pub cell_id: String,
    pub status: CellStatus,
    pub load: u32,
    pub capacity: u32,
    pub budget_remaining: ConservationBudget,
}
```

#### Task Execution

```rust
// TASK_ROUTE (A2A SendTask + openmind task routing)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskRoutePayload {
    pub task_id: String,
    pub task_name: String,
    pub parameters: Value,
    pub latency_requirement_ms: f64,
    pub safety_critical: bool,
    pub deterministic: bool,
    pub wants_creativity: f64,
    pub wants_consistency: f64,
}

// TASK_ACK
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskAckPayload {
    pub task_id: String,
    pub accepted: bool,
    pub estimated_cost: ConservationBudget,
    pub chosen_tier: ExecutionTier,
}

// TASK_RESULT
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskResultPayload {
    pub task_id: String,
    pub status: TaskCompletionStatus,
    pub output: Value,
    pub actual_cost: ConservationBudget,
    pub tier_used: ExecutionTier,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TaskCompletionStatus {
    Success,
    Cached,
    Failed,
    Cancelled,
}

// TASK_STATUS_UPDATE (A2A streaming)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskStatusUpdatePayload {
    pub task_id: String,
    pub state: TaskState,
    pub message: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TaskState {
    Submitted,
    Working,
    AwaitingInput,
    Completed,
    Canceled,
}
```

#### Muscle Memory

```rust
// CHORD_REQUEST
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChordRequestPayload {
    pub intent: String,
    pub top_k: usize,
}

// CHORD_OFFER
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChordOfferPayload {
    pub intent: String,
    pub chord_name: String,
    pub decision: ExecutionTier,
    pub confidence: f64,
    pub docstring_summary: String,
}

// REFLEX_EXECUTE
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReflexExecutePayload {
    pub chord_name: String,
    pub arguments: Value,
    pub exec_strategy: String,       // "direct" | "cached" | "generate" | "hybrid"
}
```

#### Conservation

```rust
// BUDGET_RESERVE
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BudgetReservePayload {
    pub task_id: String,
    pub cost: ConservationBudget,
}

// BUDGET_COMMIT / BUDGET_REJECT
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BudgetResultPayload {
    pub task_id: String,
    pub approved: bool,
    pub remaining: ConservationBudget,
    pub reason: Option<String>,
}

// CONSERVATION_CHECK
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConservationCheckPayload {
    pub collaboration_id: String,
    pub alignment_threshold: f64,
}

// CONSERVATION_REPORT
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConservationReportPayload {
    pub collaboration_id: String,
    pub healthy: bool,
    pub alignment: f64,
    pub conservation_ratio: f64,
    pub predicted_success: f64,
    pub action: Option<String>,
}
```

#### Artifacts (A2A)

```rust
// ARTIFACT_PUSH / ARTIFACT_PULL
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArtifactPayload {
    pub artifact_id: String,
    pub name: String,
    pub mime_type: String,
    pub parts: Vec<ArtifactPart>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArtifactPart {
    pub content_type: String,        // "text", "file", "data"
    pub content: Value,
}
```

---

## 4. CellBus Transport

`CellBus` is the message transport layer. It abstracts over in-memory channels, WebSockets, HTTP/2, or Unix sockets. Every cell holds a `CellBus` handle.

### 4.1 Trait Definition

```rust
use async_trait::async_trait;

#[derive(Debug, Clone, thiserror::Error)]
pub enum CellBusError {
    #[error("TTL expired")]
    TtlExpired,
    #[error("No route to {0}")]
    NoRoute(String),
    #[error("Transport error: {0}")]
    Transport(String),
    #[error("Budget exceeded")]
    BudgetExceeded,
}

#[async_trait]
pub trait CellBus: Send + Sync {
    /// Send a message. The bus handles routing based on the receiver field.
    async fn send(&self, msg: CellMessage) -> Result<(), CellBusError>;

    /// Receive the next message addressed to this cell.
    async fn recv(&self) -> Result<CellMessage, CellBusError>;

    /// Broadcast to all neighbors (topology-aware flood).
    async fn broadcast(&self, msg: CellMessage) -> Result<(), CellBusError>;

    /// Register this cell with the directory.
    async fn register(&self, cell: &Cell) -> Result<(), CellBusError>;

    /// Graceful shutdown.
    async fn close(&self) -> Result<(), CellBusError>;
}
```

### 4.2 In-Memory Implementation

```rust
use tokio::sync::mpsc;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

pub struct InMemoryCellBus {
    cell_id: String,
    directory: Arc<RwLock<HashMap<String, mpsc::UnboundedSender<CellMessage>>>>,
    inbox: mpsc::UnboundedReceiver<CellMessage>,
}

#[async_trait]
impl CellBus for InMemoryCellBus {
    async fn send(&self, msg: CellMessage) -> Result<(), CellBusError> {
        let dir = self.directory.read().await;
        let tx = dir.get(&msg.receiver).ok_or_else(|| {
            CellBusError::NoRoute(msg.receiver.clone())
        })?;
        tx.send(msg).map_err(|_| CellBusError::Transport("closed".into()))?;
        Ok(())
    }

    async fn recv(&self) -> Result<CellMessage, CellBusError> {
        // In a real implementation this would require &mut self or interior mutability.
        // Simplified here for illustration.
        unimplemented!("use split inbox pattern")
    }

    async fn broadcast(&self, msg: CellMessage) -> Result<(), CellBusError> {
        let dir = self.directory.read().await;
        for (id, tx) in dir.iter() {
            if id != &self.cell_id {
                let mut m = msg.clone();
                m.receiver = id.clone();
                let _ = tx.send(m);
            }
        }
        Ok(())
    }

    async fn register(&self, _cell: &Cell) -> Result<(), CellBusError> {
        Ok(())
    }

    async fn close(&self) -> Result<(), CellBusError> {
        Ok(())
    }
}
```

---

## 5. A2A Discovery Protocol

UCAP implements a two-phase discovery protocol compatible with Google A2A:

1. **Agent Card Resolution** — HTTP GET `/.well-known/agent.json` returns metadata.
2. **Directory Registration** — Cells broadcast identities to a `CellDirectory`.
3. **Alignment Scoring** — Cells query the directory for collaborators by spectral similarity.

### 5.1 Agent Card (A2A-Compatible)

```rust
/// A2A Agent Card — exposed at `/.well-known/agent.json`
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentCard {
    pub name: String,
    pub description: String,
    pub url: String,
    pub provider: Option<AgentProvider>,
    pub version: String,
    pub documentation_url: Option<String>,
    pub capabilities: AgentCapabilities,
    pub authentication: Option<AgentAuthentication>,
    pub default_input_modes: Vec<String>,
    pub default_output_modes: Vec<String>,
    pub skills: Vec<AgentSkill>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentCapabilities {
    pub streaming: bool,
    pub push_notifications: bool,
    pub state_transition_history: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSkill {
    pub id: String,
    pub name: String,
    pub description: String,
    pub tags: Vec<String>,
    pub examples: Option<Vec<String>>,
    pub input_modes: Vec<String>,
    pub output_modes: Vec<String>,
}
```

### 5.2 Directory Service

```rust
#[async_trait]
pub trait CellDirectory: Send + Sync {
    /// Register a cell after receiving IdentityBroadcast.
    async fn register(&self, cell: Cell, spectral_hash: String);

    /// Find cells that provide a given capability, sorted by alignment.
    async fn find_collaborators(
        &self,
        requester_id: &str,
        capability: &str,
        min_alignment: f64,
    ) -> Vec<AlignmentCandidate>;

    /// Get the current negotiated topology.
    async fn current_topology(&self) -> Option<(TopologyKind, HashMap<String, Vec<String>>)>;

    /// Propose a new topology and collect votes.
    async fn propose_topology(
        &self,
        kind: TopologyKind,
    ) -> Result<TopologyKind, CellBusError>;
}
```

### 5.3 Discovery Flow

```
Cell A                          Directory / Well-Known
  │ ──GET /.well-known/agent.json────────> │
  │ <─AgentCard────────────────────────────│
  │
  │ ──IDENTITY_BROADCAST───────> CellDirectory
  │    {cell, spectral_hash}               │──index──┐
  │ <─IDENTITY_ACK─────────────────────────│<────────┘
  │
  │ ──ALIGNMENT_QUERY──────────> CellDirectory
  │    {capability: "sum", min_alignment: 0.5}
  │ <─ALIGNMENT_RESPONSE───────────────────│
  │    [{cell_id: "B", alignment: 0.92}, ...]
```

---

## 6. Topology-Aware Routing

UCAP adopts agent-grid's topology system with a routing cache per cell.

### 6.1 Topology Trait

```rust
pub trait Topology: Send + Sync {
    /// Given a list of node IDs, return an adjacency map.
    fn connect(&self, node_ids: &[String]) -> HashMap<String, HashSet<String>>;

    /// BFS shortest-path between src and dst.
    fn route(
        &self,
        adjacency: &HashMap<String, HashSet<String>>,
        src: &str,
        dst: &str,
    ) -> Vec<String>;

    /// Longest shortest-path across all node pairs.
    fn diameter(&self, adjacency: &HashMap<String, HashSet<String>>) -> usize;
}
```

### 6.2 Topology Implementations

```rust
pub struct MeshTopology;
impl Topology for MeshTopology {
    fn connect(&self, node_ids: &[String]) -> HashMap<String, HashSet<String>> {
        node_ids.iter().map(|id| {
            let neighbors: HashSet<String> = node_ids.iter()
                .filter(|n| *n != id)
                .cloned()
                .collect();
            (id.clone(), neighbors)
        }).collect()
    }

    fn route(&self, adj: &HashMap<String, HashSet<String>>, src: &str, dst: &str) -> Vec<String> {
        if src == dst { return vec![src.to_string()]; }
        vec![src.to_string(), dst.to_string()]
    }

    fn diameter(&self, _adj: &HashMap<String, HashSet<String>>) -> usize { 1 }
}

pub struct RingTopology;
impl Topology for RingTopology {
    fn connect(&self, node_ids: &[String]) -> HashMap<String, HashSet<String>> {
        let mut adj: HashMap<String, HashSet<String>> = node_ids.iter()
            .map(|id| (id.clone(), HashSet::new()))
            .collect();
        let n = node_ids.len();
        for (i, id) in node_ids.iter().enumerate() {
            adj.get_mut(id).unwrap().insert(node_ids[(i + n - 1) % n].clone());
            adj.get_mut(id).unwrap().insert(node_ids[(i + 1) % n].clone());
        }
        adj
    }

    fn route(&self, adj: &HashMap<String, HashSet<String>>, src: &str, dst: &str) -> Vec<String> {
        if src == dst { return vec![src.to_string()]; }
        let mut visited = HashSet::new();
        let mut queue = std::collections::VecDeque::new();
        queue.push_back((src.to_string(), vec![src.to_string()]));
        while let Some((current, path)) = queue.pop_front() {
            if let Some(neighbors) = adj.get(&current) {
                for neighbor in neighbors {
                    if neighbor == dst {
                        let mut p = path.clone();
                        p.push(neighbor.clone());
                        return p;
                    }
                    if visited.insert(neighbor.clone()) {
                        let mut p = path.clone();
                        p.push(neighbor.clone());
                        queue.push_back((neighbor.clone(), p));
                    }
                }
            }
        }
        vec![]
    }

    fn diameter(&self, adj: &HashMap<String, HashSet<String>>) -> usize {
        let n = adj.len();
        if n == 0 { return 0; }
        n / 2
    }
}

pub struct StarTopology {
    pub hub_id: Option<String>,
}
impl Topology for StarTopology {
    fn connect(&self, node_ids: &[String]) -> HashMap<String, HashSet<String>> {
        let mut adj: HashMap<String, HashSet<String>> = node_ids.iter()
            .map(|id| (id.clone(), HashSet::new()))
            .collect();
        let hub = self.hub_id.clone()
            .or_else(|| node_ids.first().cloned())
            .unwrap_or_default();
        for id in node_ids {
            if id != &hub {
                adj.get_mut(id).unwrap().insert(hub.clone());
                adj.get_mut(&hub).unwrap().insert(id.clone());
            }
        }
        adj
    }

    fn route(&self, adj: &HashMap<String, HashSet<String>>, src: &str, dst: &str) -> Vec<String> {
        if src == dst { return vec![src.to_string()]; }
        let hub = self.hub_id.clone().unwrap_or_else(|| src.to_string());
        if src == hub || dst == hub {
            vec![src.to_string(), dst.to_string()]
        } else {
            vec![src.to_string(), hub, dst.to_string()]
        }
    }

    fn diameter(&self, _adj: &HashMap<String, HashSet<String>>) -> usize { 2 }
}

pub struct TreeTopology {
    pub branching_factor: usize,
}
impl Topology for TreeTopology {
    fn connect(&self, node_ids: &[String]) -> HashMap<String, HashSet<String>> {
        let mut adj: HashMap<String, HashSet<String>> = node_ids.iter()
            .map(|id| (id.clone(), HashSet::new()))
            .collect();
        if node_ids.is_empty() { return adj; }
        let mut queue = std::collections::VecDeque::new();
        queue.push_back(node_ids[0].clone());
        let mut idx = 1usize;
        while let Some(parent) = queue.pop_front() {
            for _ in 0..self.branching_factor {
                if idx >= node_ids.len() { break; }
                let child = node_ids[idx].clone();
                adj.get_mut(&parent).unwrap().insert(child.clone());
                adj.get_mut(&child).unwrap().insert(parent.clone());
                queue.push_back(child);
                idx += 1;
            }
        }
        adj
    }

    fn route(&self, adj: &HashMap<String, HashSet<String>>, src: &str, dst: &str) -> Vec<String> {
        if src == dst { return vec![src.to_string()]; }
        let mut visited = HashSet::new();
        let mut queue = std::collections::VecDeque::new();
        queue.push_back((src.to_string(), vec![src.to_string()]));
        while let Some((current, path)) = queue.pop_front() {
            if let Some(neighbors) = adj.get(&current) {
                for neighbor in neighbors {
                    if neighbor == dst {
                        let mut p = path.clone();
                        p.push(neighbor.clone());
                        return p;
                    }
                    if visited.insert(neighbor.clone()) {
                        let mut p = path.clone();
                        p.push(neighbor.clone());
                        queue.push_back((neighbor.clone(), p));
                    }
                }
            }
        }
        vec![]
    }

    fn diameter(&self, adj: &HashMap<String, HashSet<String>>) -> usize {
        let ids: Vec<String> = adj.keys().cloned().collect();
        let mut max_d = 0usize;
        for (i, src) in ids.iter().enumerate() {
            for dst in ids.iter().skip(i + 1) {
                let d = self.route(adj, src, dst).len().saturating_sub(1);
                if d > max_d { max_d = d; }
            }
        }
        max_d
    }
}
```

### 6.3 Topology Negotiation

```rust
pub struct TopologyNegotiator;

impl TopologyNegotiator {
    pub fn negotiate(cells: &[Cell]) -> (TopologyKind, Box<dyn Topology>) {
        let n = cells.len();
        if n <= 12 {
            (TopologyKind::Mesh, Box::new(MeshTopology))
        } else if n <= 50 {
            (TopologyKind::Star, Box::new(StarTopology { hub_id: None }))
        } else {
            (TopologyKind::Tree, Box::new(TreeTopology { branching_factor: 3 }))
        }
    }
}
```

---

## 7. Execution Tier Selection (Tripartite Synchronizer)

When a cell receives a `TaskRoute`, it selects an execution tier using an extended version of openmind's `TripartiteSynchronizer`.

### 7.1 Execution Context

```rust
#[derive(Debug, Clone)]
pub struct ExecutionContext {
    // Hardware (from openmind::cellular::ResourceSnapshot)
    pub gpu_available: bool,
    pub api_available: bool,
    pub memory_gb: f64,
    pub battery_level: Option<f64>,
    pub device_type: String, // "desktop", "laptop", "server", "edge"

    // Application (from task payload)
    pub latency_requirement_ms: f64,
    pub accuracy_requirement: f64,
    pub safety_critical: bool,
    pub deterministic: bool,
    pub scale: u32,

    // User / Policy
    pub wants_creativity: f64,
    pub wants_consistency: f64,
    pub preference_override: Option<ExecutionTier>,

    // Network / Grid (NEW in UCAP)
    pub neighbor_count: usize,
    pub grid_load: f64,
    pub is_hub: bool,

    // Conservation (NEW in UCAP)
    pub budget_remaining: ConservationBudget,
    pub task_estimated_cost: ConservationBudget,
}
```

### 7.2 Tier Selector

```rust
pub struct ExecutionTierSelector;

impl ExecutionTierSelector {
    pub fn select(&self, ctx: &ExecutionContext) -> ExecutionTier {
        // 1. User override (absolute)
        if let Some(tier) = ctx.preference_override {
            return tier;
        }

        // 2. Conservation budget gate
        if !ctx.budget_remaining.covers(&ctx.task_estimated_cost) {
            if ctx.budget_remaining.compute_seconds < ctx.task_estimated_cost.compute_seconds {
                if ctx.budget_remaining.compute_seconds < 1.0 {
                    return ExecutionTier::Cached;
                }
                return ExecutionTier::Hybrid;
            }
        }

        // 3. Safety-critical -> Hardcode
        if ctx.safety_critical {
            return ExecutionTier::Hardcode;
        }

        // 4. Deterministic required -> Hardcode
        if ctx.deterministic {
            return ExecutionTier::Hardcode;
        }

        // 5. Ultra-low latency -> Hardcode or Cached
        if ctx.latency_requirement_ms < 10.0 {
            if ctx.device_type == "edge" {
                return ExecutionTier::Cached;
            }
            return ExecutionTier::Hardcode;
        }

        // 6. Network congestion -> avoid Model (too chatty)
        if ctx.grid_load > 0.85 && !ctx.gpu_available {
            return ExecutionTier::Cached;
        }

        // 7. Hub in STAR topology -> prefer fast tiers
        if ctx.is_hub && ctx.latency_requirement_ms < 100.0 {
            return ExecutionTier::Hardcode;
        }

        // 8. High creativity -> Model or Hybrid
        if ctx.wants_creativity > 0.7 {
            if ctx.gpu_available || ctx.api_available {
                return ExecutionTier::Model;
            }
            return ExecutionTier::Hybrid;
        }

        // 9. High consistency -> Hardcode or Cached
        if ctx.wants_consistency > 0.8 {
            return ExecutionTier::Hardcode;
        }

        // 10. Edge + low battery -> Cached
        if ctx.device_type == "edge" {
            if let Some(bat) = ctx.battery_level {
                if bat < 0.3 {
                    return ExecutionTier::Cached;
                }
            }
        }

        // 11. High accuracy + high scale -> Hybrid
        if ctx.accuracy_requirement > 0.9 && ctx.scale > 100 {
            return ExecutionTier::Hybrid;
        }

        // 12. Default -> Hybrid
        ExecutionTier::Hybrid
    }
}
```

---

## 8. Conservation Budget System

Every cell carries a `ConservationBudget`. The protocol enforces budget gates at three points:

1. **Reserve** — Before execution, the estimated cost is reserved.
2. **Commit** — After execution, the actual cost is committed (refund over-reserve).
3. **Reject** — If the budget is insufficient, the task is rejected with a `BudgetReject` message.

### 8.1 Budget Manager

```rust
use std::sync::Arc;
use tokio::sync::Mutex;

pub struct BudgetManager {
    cell_id: String,
    budget: Arc<Mutex<ConservationBudget>>,
}

impl BudgetManager {
    pub fn new(cell_id: String, initial: ConservationBudget) -> Self {
        Self {
            cell_id,
            budget: Arc::new(Mutex::new(initial)),
        }
    }

    /// Attempt to reserve budget. Returns false if insufficient.
    pub async fn reserve(&self, cost: &ConservationBudget) -> bool {
        let mut b = self.budget.lock().await;
        if b.covers(cost) {
            *b = b.deduct(cost);
            true
        } else {
            false
        }
    }

    /// Commit actual spend. Refund the difference between reserved and actual.
    pub async fn commit(&self, reserved: &ConservationBudget, actual: &ConservationBudget) {
        let mut b = self.budget.lock().await;
        // refund = reserved - actual
        let refund = ConservationBudget {
            gpu_seconds: (reserved.gpu_seconds - actual.gpu_seconds).max(0.0),
            compute_seconds: (reserved.compute_seconds - actual.compute_seconds).max(0.0),
            memory_mb: (reserved.memory_mb - actual.memory_mb).max(0.0),
            api_calls: reserved.api_calls.saturating_sub(actual.api_calls),
        };
        *b = ConservationBudget {
            gpu_seconds: b.gpu_seconds + refund.gpu_seconds,
            compute_seconds: b.compute_seconds + refund.compute_seconds,
            memory_mb: b.memory_mb + refund.memory_mb,
            api_calls: b.api_calls + refund.api_calls,
        };
    }

    pub async fn snapshot(&self) -> ConservationBudget {
        *self.budget.lock().await
    }
}
```

### 8.2 Conservation Hooks Trait

```rust
#[async_trait]
pub trait ConservationHooks: Send + Sync {
    /// Called when a TASK_ROUTE arrives. Return a reject message to block.
    async fn on_task_received(
        &self,
        cell: &Cell,
        msg: &CellMessage,
    ) -> Option<CellMessage>;

    /// Called periodically during long-running tasks.
    async fn on_conservation_check(
        &self,
        cell: &Cell,
        task_id: &str,
    ) -> ConservationReportPayload;

    /// Called when spectral alignment with a peer drops.
    async fn on_alignment_drift(
        &self,
        cell: &Cell,
        peer_id: &str,
        old_alpha: f64,
        new_alpha: f64,
    ) -> Option<CellMessage>;
}
```

---

## 9. The CellAgent Trait

`CellAgent` is the unifying trait that any entity must implement to participate in UCAP — whether it is a Jupyter cell, an ESP32 firmware module, a grid worker, or an A2A agent.

```rust
#[async_trait]
pub trait CellAgent: Send + Sync {
    /// Unique identity in the cell grid.
    fn cell_id(&self) -> &str;

    /// Human-readable name (e.g., "A1", "sum-range", "worker-3").
    fn name(&self) -> &str;

    /// Current status in the state machine.
    fn status(&self) -> CellStatus;

    /// Available computational budget.
    async fn budget(&self) -> ConservationBudget;

    /// The cell bus used for transport.
    fn bus(&self) -> &dyn CellBus;

    /// ── Discovery ──

    /// Produce an A2A-compatible Agent Card for external discovery.
    fn agent_card(&self) -> AgentCard;

    /// Produce a spectral fingerprint for alignment-based collaboration.
    fn spectral_fingerprint(&self) -> String;

    /// ── Topology ──

    /// Update neighbor set after topology negotiation.
    async fn set_neighbors(&mut self, neighbors: HashSet<String>);

    /// Return current neighbors.
    fn neighbors(&self) -> &HashSet<String>;

    /// ── Execution ──

    /// Handle an incoming task. The implementation should:
    /// 1. Check conservation budget.
    /// 2. Select execution tier.
    /// 3. Execute.
    /// 4. Emit TaskResult or TaskFail.
    async fn handle_task(&mut self, msg: CellMessage) -> Result<CellMessage, CellBusError>;

    /// Recall a chord by intent (openmind muscle memory).
    async fn recall_chord(&self, intent: &str, top_k: usize) -> Vec<ChordOfferPayload>;

    /// Flex a muscle — get execution plan for an intent.
    async fn flex(&self, intent: &str) -> Option<ReflexExecutePayload>;

    /// ── Conservation ──

    /// Reserve budget for a task.
    async fn reserve_budget(&self, cost: &ConservationBudget) -> bool;

    /// Commit actual spend.
    async fn commit_budget(&self, reserved: &ConservationBudget, actual: &ConservationBudget);

    /// ── Lifecycle ──

    /// Activate the cell (OFFLINE -> IDLE).
    async fn activate(&mut self);

    /// Heartbeat — called periodically to report health.
    async fn heartbeat(&mut self) -> HeartbeatPayload;

    /// Graceful shutdown.
    async fn shutdown(&mut self);
}
```

### 9.1 Blanket Implementation Notes

- `handle_task` must invoke `ExecutionTierSelector` and `ConservationHooks`.
- `recall_chord` and `flex` delegate to an embedded `MuscleMemory` store (openmind).
- `heartbeat` must include `budget_remaining` so the directory can make load-aware routing decisions.

---

## 10. Example: A Spreadsheet Cell Implementing CellAgent

```rust
use async_trait::async_trait;
use std::collections::HashSet;

pub struct SpreadsheetCell {
    cell: Cell,
    bus: Box<dyn CellBus>,
    budget_mgr: BudgetManager,
    tier_selector: ExecutionTierSelector,
    muscle_memory: HashMap<String, ReflexExecutePayload>, // openmind chord store
}

#[async_trait]
impl CellAgent for SpreadsheetCell {
    fn cell_id(&self) -> &str { &self.cell.cell_id }
    fn name(&self) -> &str { &self.cell.name }
    fn status(&self) -> CellStatus { self.cell.status }

    async fn budget(&self) -> ConservationBudget {
        self.budget_mgr.snapshot().await
    }

    fn bus(&self) -> &dyn CellBus { self.bus.as_ref() }

    fn agent_card(&self) -> AgentCard {
        AgentCard {
            name: self.cell.name.clone(),
            description: format!("UCAP spreadsheet cell {}", self.cell.name),
            url: format!("cell://{}", self.cell.cell_id),
            provider: None,
            version: "1.0.0".to_string(),
            documentation_url: None,
            capabilities: AgentCapabilities {
                streaming: false,
                push_notifications: true,
                state_transition_history: true,
            },
            authentication: None,
            default_input_modes: vec!["text/plain".to_string()],
            default_output_modes: vec!["text/plain".to_string(), "application/json".to_string()],
            skills: self.cell.capabilities.iter().map(|cap| AgentSkill {
                id: cap.clone(),
                name: cap.clone(),
                description: format!("Provides {}", cap),
                tags: vec![cap.clone()],
                examples: None,
                input_modes: vec!["text/plain".to_string()],
                output_modes: vec!["application/json".to_string()],
            }).collect(),
        }
    }

    fn spectral_fingerprint(&self) -> String {
        // Deterministic hash of capabilities
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        let mut hasher = DefaultHasher::new();
        self.cell.capabilities.hash(&mut hasher);
        format!("{:x}", hasher.finish())
    }

    async fn set_neighbors(&mut self, neighbors: HashSet<String>) {
        self.cell.neighbors = neighbors;
    }

    fn neighbors(&self) -> &HashSet<String> { &self.cell.neighbors }

    async fn handle_task(&mut self, msg: CellMessage) -> Result<CellMessage, CellBusError> {
        let payload: TaskRoutePayload = serde_json::from_value(msg.payload)
            .map_err(|e| CellBusError::Transport(e.to_string()))?;

        // 1. Budget gate
        let estimated = msg.budget_hint.unwrap_or(ConservationBudget {
            compute_seconds: 1.0, ..ConservationBudget::ZERO
        });
        if !self.reserve_budget(&estimated).await {
            return Ok(CellMessage::new(
                CellMessageType::BudgetReject,
                &self.cell.cell_id,
                &msg.sender,
                serde_json::to_value(BudgetResultPayload {
                    task_id: payload.task_id.clone(),
                    approved: false,
                    remaining: self.budget().await,
                    reason: Some("insufficient_budget".to_string()),
                }).unwrap(),
            ));
        }

        // 2. Tier selection
        let ctx = ExecutionContext {
            gpu_available: false,
            api_available: false,
            memory_gb: 4.0,
            battery_level: None,
            device_type: "server".to_string(),
            latency_requirement_ms: payload.latency_requirement_ms,
            accuracy_requirement: 0.95,
            safety_critical: payload.safety_critical,
            deterministic: payload.deterministic,
            scale: 1,
            wants_creativity: payload.wants_creativity,
            wants_consistency: payload.wants_consistency,
            preference_override: msg.tier_hint,
            neighbor_count: self.cell.neighbors.len(),
            grid_load: 0.5,
            is_hub: false,
            budget_remaining: self.budget().await,
            task_estimated_cost: estimated,
        };
        let tier = self.tier_selector.select(&ctx);

        // 3. Execute (simplified)
        let result_value = match payload.task_name.as_str() {
            "sum" => {
                let ops: Vec<f64> = serde_json::from_value(
                    payload.parameters.get("operands").cloned().unwrap_or_default()
                ).unwrap_or_default();
                serde_json::to_value(ops.iter().sum::<f64>()).unwrap()
            }
            "value" => payload.parameters.get("value").cloned().unwrap_or_default(),
            _ => Value::Null,
        };

        let actual_cost = ConservationBudget { compute_seconds: 0.5, ..ConservationBudget::ZERO };
        self.commit_budget(&estimated, &actual_cost).await;

        // 4. Return result
        Ok(CellMessage::new(
            CellMessageType::TaskResult,
            &self.cell.cell_id,
            &msg.sender,
            serde_json::to_value(TaskResultPayload {
                task_id: payload.task_id,
                status: TaskCompletionStatus::Success,
                output: result_value,
                actual_cost,
                tier_used: tier,
            }).unwrap(),
        ))
    }

    async fn recall_chord(&self, intent: &str, top_k: usize) -> Vec<ChordOfferPayload> {
        let mut matches: Vec<_> = self.muscle_memory.iter()
            .filter(|(k, _)| k.contains(intent))
            .map(|(name, reflex)| ChordOfferPayload {
                intent: intent.to_string(),
                chord_name: name.clone(),
                decision: ExecutionTier::Hardcode,
                confidence: 0.9,
                docstring_summary: reflex.exec_strategy.clone(),
            })
            .collect();
        matches.truncate(top_k);
        matches
    }

    async fn flex(&self, intent: &str) -> Option<ReflexExecutePayload> {
        self.muscle_memory.get(intent).cloned()
    }

    async fn reserve_budget(&self, cost: &ConservationBudget) -> bool {
        self.budget_mgr.reserve(cost).await
    }

    async fn commit_budget(&self, reserved: &ConservationBudget, actual: &ConservationBudget) {
        self.budget_mgr.commit(reserved, actual).await;
    }

    async fn activate(&mut self) {
        self.cell.status = CellStatus::Idle;
        self.bus.register(&self.cell).await.ok();
    }

    async fn heartbeat(&mut self) -> HeartbeatPayload {
        HeartbeatPayload {
            cell_id: self.cell.cell_id.clone(),
            status: self.cell.status,
            load: self.cell.neighbors.len() as u32,
            capacity: 10,
            budget_remaining: self.budget().await,
        }
    }

    async fn shutdown(&mut self) {
        self.cell.status = CellStatus::Offline;
        self.bus.close().await.ok();
    }
}
```

---

## 11. Protocol Compliance Checklist

An implementation is UCAP-compliant if it supports:

| # | Requirement | Source System |
|---|-------------|---------------|
| 1 | `CellMessage` envelope with `msg_type`, `sender`, `receiver`, `payload`, `ttl`, `budget_hint`, `tier_hint` | UCAP |
| 2 | All 22 `CellMessageType` variants | UCAP |
| 3 | Rust struct schemas for all payloads | UCAP |
| 4 | `CellBus` trait with `send`, `recv`, `broadcast`, `register`, `close` | UCAP |
| 5 | A2A `AgentCard` with capabilities and skills | Google A2A |
| 6 | `CellDirectory` trait with register, find_collaborators, propose_topology | UCAP |
| 7 | Four topologies: `Mesh`, `Ring`, `Star`, `Tree` with BFS routing | agent-grid |
| 8 | Topology negotiation with voting | UCAP |
| 9 | `ExecutionTierSelector` with 12 priority rules | openmind |
| 10 | `ConservationBudget` with reserve, commit, deduct | openmind + conservation-law |
| 11 | `ConservationHooks` for task gating, mid-flight checks, alignment drift | a2a-conservation |
| 12 | `CellAgent` trait with discovery, topology, execution, conservation, lifecycle | UCAP |
| 13 | Heartbeat-based failure detection (HEALTHY / SUSPECT / FAILED / OFFLINE) | agent-grid |
| 14 | Muscle memory: `recall_chord` and `flex` methods | openmind |
| 15 | Task status streaming (`TaskStatusUpdate` with `TaskState`) | Google A2A |
| 16 | Artifact push/pull for data exchange | Google A2A |

---

## 12. References

| System | File | Role in UCAP |
|--------|------|--------------|
| openmind | `openmind/induction/synchronizer.py` | Tripartite decision engine, tier definitions, scoring rules |
| openmind | `openmind/cellular.py` | Resource probing, metabolic pathways (`FULL_TRAIN`, `TRANSFER`, `CLOUD`, `MUSCLE_MEMORY`, `HARDWARE_LOOP`) |
| openmind | `openmind/muscle.py` | `Chord`, `Reflex`, `MuscleMemory`, `flex()`, `recall()` |
| openmind | `openmind/flex.py` | One-shot convenience API (`quick_flex`, `load_and_flex`) |
| openmind | `si/cell_from_capability.py` | Cell creation from `CAPABILITY.toml`, default budget allocation |
| agent-grid | `agent_grid/topology.py` | `MeshTopology`, `RingTopology`, `StarTopology`, `TreeTopology` |
| agent-grid | `agent_grid/grid.py` | Node management, adjacency, `rebuild_topology()`, `route()` |
| agent-grid | `agent_grid/node.py` | `GridNode`, `NodeStatus`, heartbeat, utilization |
| agent-grid | `agent_grid/dispatch.py` | `WorkDispatcher`, `Task`, dispatch strategies |
| agent-grid | `agent_grid/failure.py` | `FailureDetector`, heartbeat timeouts, `SUSPECT`/`FAILED` transitions |
| Google A2A | [github.com/google/A2A](https://github.com/google/A2A) | `AgentCard`, `Task`, `Artifact`, `Part`, streaming status |

---

*End of Protocol Specification*
