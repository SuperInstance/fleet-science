# FLEET_CLI_DESIGN: openagent → `si` Fleet CLI

**File**: `/tmp/nightshift/FLEET_CLI_DESIGN.md`  
**Purpose**: Upgrade openagent into a git-native fleet CLI (`si`).  
**Source**: Based on source audit of `superinstance/`, `tool/superinstance.go`, `pipe/`, `internal/cli/cli.go`.  
**Status**: Design only — no code changed.

---

## 0. Executive Summary

openagent is currently an HTTP API server with an MCP tool layer. The `superinstance/` package has all the fleet knowledge baked in as static Go maps. The `pipe/` package has 9 battle-tested messaging adapters sitting idle for fleet use.

The upgrade:

1. Add `cmd/si/` — a Cobra-based CLI binary alongside the existing server
2. Add `internal/fleet/` — live fleet state, conservation tracking, git operations
3. Add `internal/bridge/` — JSON-over-stdin protocol to Rust crates (no CGO)
4. Wire `pipe/` adapters as fleet notification channels with priority routing
5. Add `si gateway heartbeat` to register with openclaw and drive fleet monitoring

The existing server (`openagent serve`) is untouched. `si` is a new binary built from the same module.

---

## 1. CLI Command Tree

```
si
├── fleet
│   ├── status [--json] [--full]
│   ├── watch  [--interval=30s]
│   └── export [--format=json|md|csv]
│
├── agents
│   ├── list   [--phase=INCUBATE|COMPETE|SURVIVE|SUNSET] [--json]
│   ├── show   <name>
│   ├── promote <name>        # advance to next lifecycle phase
│   └── retire  <name>        # force SUNSET
│
├── conservation
│   ├── check  [--strict]     # exit 1 if deviation > 2σ
│   ├── history [--commits=20]
│   └── gate   <command...>   # run <command> only if conservation healthy
│
├── dial
│   ├── compare <trad1> <trad2>
│   ├── nearest <h> <r> <s>   # find tradition nearest to (H, R, S) position
│   └── list                  # all known traditions with dial coordinates
│
├── repo
│   ├── audit   [--tag=<tag>] [--lang=<lang>] [--json]
│   └── status  <name>
│
├── publish
│   │  # conservation-gated release for a repo
│   ├── (implicit args: [<repo>] [--dry-run] [--force] [--tag=<semver>])
│   └── --all [--dry-run]
│
├── pipe
│   ├── list
│   ├── send    <channel> <message> [--level=LOW|MEDIUM|HIGH|CRITICAL]
│   └── test    <channel>           # sends a test ping
│
└── gateway
    ├── serve   [--port=8000]       # existing HTTP server (was default)
    └── heartbeat [--interval=60s] [--target=<openclaw-url>]
```

### 1.1 Commands in Detail

#### `si fleet status`

```
SuperInstance Fleet — 2026-06-08 15:42 UTC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agent       Role                 Phase     Gen  Trinity Avg  Status
──────────────────────────────────────────────────────────────────
CCC         Fleet I&O Officer    SURVIVE   3    0.883        active
Oracle1     Research & Synthesis SURVIVE   5    0.890        active
FM          Forgemaster          COMPETE   2    0.760        active
TurboVec    Vector Operations    COMPETE   1    0.717        active

Conservation: γ=0.812  H=0.498  Expected=0.848  Deviation=+0.64σ  ✓ OK
Fleet size V=4  σ(4)=0.140
```

Exit codes: 0=healthy, 1=conservation violation (deviation > 2σ), 2=error.

#### `si conservation check`

```
Fleet Conservation Law: γ + H = 1.283 - 0.159·log(V)

Fleet size V: 4
Expected total (γ+H): 1.283 - 0.159·log(4) = 1.283 - 0.220 = 1.062
Empirical split: γ=62% (0.659), H=38% (0.404)
σ(4): 0.28/√4 = 0.140

Observed γ (mean Trinity): 0.812
Observed H (entropy):       0.498
Observed total:             1.310

Deviation: (1.310 - 1.062) / 0.140 = +1.77σ  ← within 2σ threshold ✓
```

With `--strict`: threshold becomes 1σ instead of 2σ.

#### `si conservation gate <cmd>`

```bash
# Only publishes if conservation is healthy
si conservation gate cargo publish -p groovemesh-plr

# Usage in CI (combine with --strict for tighter gate)
si conservation check --strict && cargo publish -p spreadsheet-engine
```

Returns the exit code of `<cmd>` on success, 1 on conservation failure without running `<cmd>`.

#### `si dial compare Jazz Gamelan`

```
Dial Comparison: Jazz vs Gamelan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                   Jazz    Gamelan   Δ
Harmonic Tension   3.80    1.50      +2.30
Rhythmic Complexity 3.50   4.20      -0.70
Spectral Density   2.80    3.50      -0.70

Euclidean distance: 2.51

Nearest tradition to midpoint: Hindustani (d=0.94)
```

#### `si publish spreadsheet-plr-bridge --dry-run`

```
[DRY RUN] Publishing spreadsheet-plr-bridge v0.1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conservation gate: deviation=+1.77σ  threshold=2.00σ  ✓ PASS
Git status:        all committed  ✓ PASS
Tests:             67 passing     ✓ PASS
Cargo.toml:        version=0.1.0  ✓ OK

[DRY RUN] Would execute:
  git tag -s v0.1.0 -m "release: spreadsheet-plr-bridge v0.1.0 (γ+H=1.310, V=4)"
  cargo publish -p spreadsheet-plr-bridge
  [pipe] Slack → #fleet-releases: "📦 spreadsheet-plr-bridge v0.1.0 published"
  [pipe] Discord → fleet-builds: "📦 spreadsheet-plr-bridge v0.1.0"
```

---

## 2. Source File Changes

### 2.1 New Binary: `cmd/si/main.go`

New file. Imports Cobra, wires the command tree. Does NOT import `beego` or any HTTP-server deps — the `si` binary is a thin CLI wrapper over `internal/fleet/`, `superinstance/`, and `pipe/`.

```go
// cmd/si/main.go
package main

import (
    "github.com/the-open-agent/openagent/internal/fleet"
    "github.com/the-open-agent/openagent/internal/bridge"
    "github.com/the-open-agent/openagent/internal/si"
    "github.com/spf13/cobra"
)

func main() {
    root := si.BuildRootCmd()
    root.Execute()
}
```

### 2.2 New Package: `internal/si/`

Cobra command definitions only. Business logic lives in `internal/fleet/` and `internal/bridge/`.

```
internal/si/
├── root.go          # BuildRootCmd(), global --json / --quiet flags
├── cmd_fleet.go     # fleet status, fleet watch, fleet export
├── cmd_agents.go    # agents list, show, promote, retire
├── cmd_conservation.go  # conservation check, history, gate
├── cmd_dial.go      # dial compare, nearest, list
├── cmd_repo.go      # repo audit, status
├── cmd_publish.go   # publish (conservation-gated release)
├── cmd_pipe.go      # pipe list, send, test
└── cmd_gateway.go   # gateway serve, heartbeat
```

### 2.3 New Package: `internal/fleet/`

Live fleet state (replaces static read-only access to `superinstance.KnownAgents`).

```go
// internal/fleet/state.go

// FleetSnapshot is the result of a single fleet health check.
// All fields are JSON-serializable for --json output and heartbeat payloads.
type FleetSnapshot struct {
    Timestamp       time.Time              `json:"timestamp"`
    Agents          []superinstance.Agent  `json:"agents"`
    ConservationObs ConservationObservation `json:"conservation"`
    GitHead         string                 `json:"git_head"`   // HEAD SHA of workspace
    Version         string                 `json:"version"`    // si binary version
}

type ConservationObservation struct {
    FleetSize      int     `json:"fleet_size"`
    ObservedGamma  float64 `json:"observed_gamma"`   // mean Trinity.Average()
    ObservedH      float64 `json:"observed_h"`       // fleet entropy
    ExpectedTotal  float64 `json:"expected_total"`   // ConservationTotal(V)
    Deviation      float64 `json:"deviation_sigma"`  // ConservationDeviation(...)
    Sigma          float64 `json:"sigma"`            // conservationSigma(V)
    IsHealthy      bool    `json:"is_healthy"`       // |deviation| < 2σ
    IsStrictHealth bool    `json:"is_strict_healthy"` // |deviation| < 1σ
}

// ComputeEntropy computes Shannon entropy over agent Trinity.Average() values,
// normalized to [0,1]. Used as the H (Helmholtz) term in conservation law.
// H = -Σ p_i · log(p_i), where p_i = trinity_avg_i / Σ trinity_avg_j
func ComputeEntropy(agents []superinstance.Agent) float64

// Snapshot builds a FleetSnapshot from the current KnownAgents + git state.
func Snapshot(workspaceRoot string) (*FleetSnapshot, error)

// LoadHistory reads up to n snapshots from .si/fleet-history.jsonl
func LoadHistory(workspaceRoot string, n int) ([]FleetSnapshot, error)

// SaveSnapshot appends a snapshot to .si/fleet-history.jsonl
func SaveSnapshot(workspaceRoot string, snap *FleetSnapshot) error
```

```go
// internal/fleet/phase.go

// PromoteAgent advances an agent to the next lifecycle phase.
// Validates against PhaseTransitions() — returns error if invalid.
func PromoteAgent(name string) error

// RetireAgent forces an agent to SUNSET phase.
func RetireAgent(name string) error

// All mutations write to .si/agents.json which overrides KnownAgents at runtime.
// The static KnownAgents map in agents.go is the fallback default.
type AgentOverrides struct {
    Agents map[string]superinstance.Agent `json:"agents"`
}
```

```go
// internal/fleet/git.go

// TagRelease creates an annotated git tag with conservation metadata in the message.
// Format: v<semver> | message includes γ+H values and fleet size.
func TagRelease(workspaceRoot, repoPath, version string, snap *FleetSnapshot) error
// Runs: git tag -s v<version> -m "release: <repo> v<version> (γ+H=<obs>, V=<fleet_size>)"

// GitHead returns the current HEAD SHA for a path.
func GitHead(path string) (string, error)

// IsClean returns true if the git working tree has no uncommitted changes.
func IsClean(path string) (bool, error)

// FindRepoVersion reads the version from Cargo.toml or pyproject.toml or go.mod.
func FindRepoVersion(repoPath string) (string, error)
```

### 2.4 New Package: `internal/bridge/`

JSON-over-stdin bridge to Rust crates. Enables `si` to invoke `groovemesh-plr`, `spreadsheet-engine`, `noether-guard` logic without requiring CGO.

```go
// internal/bridge/bridge.go

// BridgeRequest is the JSON envelope sent to the Rust bridge subprocess.
type BridgeRequest struct {
    Command string          `json:"command"` // "conservation_check", "plr_snap", "dial_distance"
    Payload json.RawMessage `json:"payload"`
}

// BridgeResponse is the JSON envelope returned from the Rust bridge subprocess.
type BridgeResponse struct {
    OK      bool            `json:"ok"`
    Result  json.RawMessage `json:"result,omitempty"`
    Error   string          `json:"error,omitempty"`
}

// Bridge is a handle to the Rust bridge subprocess.
// The subprocess is `si-rust-bridge` (a thin Rust binary in cmd/si-rust-bridge/).
type Bridge struct {
    binPath string       // path to si-rust-bridge binary
    timeout time.Duration
}

// NewBridge creates a Bridge. binPath defaults to finding si-rust-bridge in $PATH.
func NewBridge(binPath string) *Bridge

// Call spawns si-rust-bridge, sends req as JSON on stdin,
// reads response from stdout, returns the parsed BridgeResponse.
// Each call is a fresh subprocess (stateless, ~20ms spawn cost).
// For batch operations, use CallBatch to amortize startup.
func (b *Bridge) Call(ctx context.Context, req BridgeRequest) (*BridgeResponse, error)

// CallBatch sends multiple requests in a single subprocess session.
// Reads newline-delimited JSON responses (one per request).
func (b *Bridge) CallBatch(ctx context.Context, reqs []BridgeRequest) ([]*BridgeResponse, error)
```

#### Bridge Commands and Payloads

```go
// ConservationCheckRequest — wraps spreadsheet-engine conservation monitor.
type ConservationCheckRequest struct {
    Agents []BridgeAgent `json:"agents"`  // gamma + eta + budget per agent
}
type BridgeAgent struct {
    AgentID string  `json:"agent_id"`
    Gamma   float64 `json:"gamma"`
    Eta     float64 `json:"eta"`
    Budget  float64 `json:"budget"`
}
type ConservationCheckResult struct {
    Health     float64  `json:"health"`      // 0.0–1.0
    Violations []string `json:"violations"`  // agent IDs that violated
    Trend      string   `json:"trend"`       // "Improving", "Stable", "Degrading"
}

// PLRSnapRequest — wraps groovemesh-plr nearest_plr_triad.
type PLRSnapRequest struct {
    CurrentRoot    int    `json:"current_root"`    // 0–11
    CurrentQuality string `json:"current_quality"` // "Major" or "Minor"
    PitchClasses   []int  `json:"pitch_classes"`   // 0–11
}
type PLRSnapResult struct {
    Root    int    `json:"root"`
    Quality string `json:"quality"`
    PLROp   string `json:"plr_op"`  // "P", "L", "R", or "none"
}

// DialDistanceRequest — wraps superinstance.DialDistance Go logic
// (this is purely Go-side, not Rust; no bridge needed, but keeping here for completeness)
// See: superinstance.DialDistance() is already in Go.
```

#### Why JSON-over-stdin, not CGO

| Concern | CGO | JSON-stdin |
|---------|-----|-----------|
| goreleaser `CGO_ENABLED=0` | Requires `CGO_ENABLED=1`, separate build per platform | No change needed |
| Cross-compilation | Breaks for GOOS=linux from darwin | Works — Rust binary is separate artifact |
| Startup cost | Zero | ~15–25ms per cold call (negligible for CLI) |
| Debugging | Segfaults are opaque in Go | Clear stdout/stderr from subprocess |
| Distribution | Embed `.so` in binary (complex) | Ship `si-rust-bridge` alongside `si` |

The Rust bridge binary (`si-rust-bridge`) is a thin `clap`-driven CLI:

```toml
# cmd/si-rust-bridge/Cargo.toml
[package]
name = "si-rust-bridge"
version = "0.1.0"

[dependencies]
spreadsheet-plr-bridge = { path = "../../" }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
clap = { version = "4", features = ["derive"] }
```

```rust
// cmd/si-rust-bridge/src/main.rs
// Reads newline-delimited JSON BridgeRequests from stdin,
// writes newline-delimited JSON BridgeResponses to stdout.
// Dispatches on BridgeRequest::command.
fn main() {
    let stdin = io::stdin();
    let stdout = io::stdout();
    for line in stdin.lock().lines() {
        let req: BridgeRequest = serde_json::from_str(&line?)?;
        let resp = dispatch(req);
        serde_json::to_writer(&stdout, &resp)?;
        writeln!(&stdout)?;
    }
}
```

### 2.5 Changes to `superinstance/agents.go`

**Add `Gamma` and `Eta` fields** to `Agent` so live conservation monitoring can track per-agent budget usage (paralleling `AgentCell` in spreadsheet-engine):

```go
// Agent represents an agent in the SuperInstance fleet.
// CHANGED: added Gamma, Eta, Budget for conservation monitoring.
type Agent struct {
    Name       string       `json:"name"`
    Role       string       `json:"role"`
    Trinity    TrinityScore `json:"trinity"`
    Phase      string       `json:"phase"`
    Generation int          `json:"generation"`
    Status     string       `json:"status"`

    // Conservation fields — 0-valued if not tracked (backward-compatible).
    Gamma  float64 `json:"gamma,omitempty"`  // compute spend
    Eta    float64 `json:"eta,omitempty"`    // memory usage
    Budget float64 `json:"budget,omitempty"` // total allowed
}

// ConservationError returns |Gamma + Eta - Budget|. Returns 0 if Budget == 0.
func (a *Agent) ConservationError() float64 {
    if a.Budget == 0 {
        return 0
    }
    return math.Abs(a.Gamma+a.Eta-a.Budget)
}
```

**Deprecate `KnownAgents` as the sole truth source.** The fleet package's `AgentOverrides` (.si/agents.json) takes precedence at runtime, with `KnownAgents` as fallback. No change to the static map — it remains the compile-time default.

### 2.6 Changes to `superinstance/fleet_conservation.go`

Add `ConservationStatus` method that returns a structured result (used by `si conservation check`):

```go
// ConservationStatus wraps ConservationDeviation with a named result type.
// This avoids callers needing to reconstruct the check inline.
type ConservationStatus struct {
    FleetSize    int     `json:"fleet_size"`
    ExpectedSum  float64 `json:"expected_sum"`
    ObservedSum  float64 `json:"observed_sum"`
    Sigma        float64 `json:"sigma"`
    Deviation    float64 `json:"deviation_sigma"`
    IsHealthy    bool    `json:"is_healthy"`    // |deviation| < 2σ
    IsStrict     bool    `json:"is_strict"`     // |deviation| < 1σ
}

func CheckConservation(fleetSize int, observedGamma, observedH float64) ConservationStatus {
    expected := ConservationTotal(fleetSize)
    sigma := conservationSigma(fleetSize)
    observed := observedGamma + observedH
    dev := ConservationDeviation(fleetSize, observedGamma, observedH)
    return ConservationStatus{
        FleetSize:   fleetSize,
        ExpectedSum: expected,
        ObservedSum: observed,
        Sigma:       sigma,
        Deviation:   dev,
        IsHealthy:   math.Abs(dev) < 2.0,
        IsStrict:    math.Abs(dev) < 1.0,
    }
}
```

### 2.7 New File: `.si/config.yaml` (per-workspace)

```yaml
# .si/config.yaml — created by `si init`, gitignored
workspace_root: /home/phoenix/.openclaw/workspace
openclaw_gateway: http://localhost:8000
heartbeat_interval: 60s

# Conservation thresholds
conservation:
  threshold_sigma: 2.0    # default gate threshold
  strict_sigma: 1.0       # for --strict mode
  history_file: .si/fleet-history.jsonl

# Rust bridge
bridge:
  bin_path: ""            # auto-discover from $PATH if empty
  timeout: 5s

# Pipes (fleet notification channels)
# Each entry maps to a pipe adapter in the pipe/ package.
pipes:
  - name: fleet-slack
    type: Slack
    token: "${SLACK_BOT_TOKEN}"
    signing_secret: "${SLACK_SIGNING_SECRET}"
    chat_id: "C_FLEET_STATUS"  # channel ID
    levels: [MEDIUM, HIGH, CRITICAL]

  - name: fleet-discord
    type: Discord
    token: "${DISCORD_BOT_TOKEN}"
    secret_key: "${DISCORD_PUBLIC_KEY}"
    chat_id: "1234567890"
    levels: [LOW, MEDIUM, HIGH, CRITICAL]

  - name: fleet-telegram
    type: Telegram
    token: "${TELEGRAM_BOT_TOKEN}"
    chat_id: "${TELEGRAM_CHAT_ID}"
    levels: [HIGH, CRITICAL]
```

---

## 3. Fleet-Aware Git Operations

### 3.1 Conservation-Gated Publishing (`si publish`)

The publish command wraps `cargo publish` / `pip publish` / `go release` with a three-stage gate:

```
Stage 1: Pre-flight
  ├── Git working tree clean?          (git status --porcelain)
  ├── HEAD is tagged or on main?       (git branch --show-current)
  └── Tests passing?                   (cargo test / pytest / go test)

Stage 2: Conservation Gate
  ├── Compute fleet snapshot           (internal/fleet.Snapshot)
  ├── ComputeEntropy(agents) → H
  ├── Mean Trinity.Average() → γ
  └── CheckConservation(V, γ, H).IsHealthy ?
      ✓ PASS → proceed
      ✗ FAIL → print deviation, exit 1 (unless --force)

Stage 3: Publish + Tag
  ├── cargo publish -p <repo>          (or pip / go as appropriate)
  ├── git tag -s v<version>            (TagRelease with conservation metadata)
  ├── git push origin v<version>
  └── [pipe broadcast] fleet channels → conservation-stamped release note
```

The git tag message embeds the conservation snapshot:

```
release: groovemesh-plr v0.1.0

Fleet conservation at release:
  γ+H = 1.310 (expected 1.062, deviation +1.77σ)
  Fleet size V=4, σ(4)=0.140
  Trinity scores: CCC=0.883, Oracle1=0.890, FM=0.760, TurboVec=0.717
  
Published by si v0.1.0 at 2026-06-08T15:42:00Z
```

This embeds provenance in the git history. Any `git log --show-notes` or `git tag -l -n10` shows the fleet health at release time.

### 3.2 Git Hook: `pre-push`

`si init` installs a `pre-push` hook:

```bash
#!/bin/sh
# .git/hooks/pre-push — installed by `si init`
# Warns (does not block) on conservation degradation before push.
if command -v si >/dev/null 2>&1; then
    si conservation check --quiet || {
        echo "WARNING: Fleet conservation deviation exceeds 2σ."
        echo "Run 'si conservation check' for details."
        echo "Use 'git push --no-verify' to override."
        exit 1
    }
fi
```

This is a warning hook, not a hard block — `--no-verify` always escapes. The CI publish pipeline uses `--strict` with no escape hatch.

### 3.3 GitHub Actions Integration (`.github/workflows/si-fleet.yml`)

```yaml
name: Fleet Conservation Gate

on:
  push:
    tags: ['v*']

jobs:
  conservation-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Download si
        run: |
          curl -sL https://github.com/SuperInstance/openagent/releases/latest/download/si_linux_x86 -o si
          chmod +x si
      - name: Conservation check
        run: ./si conservation check --strict
      - name: Publish (on pass)
        run: cargo publish -p ${{ github.event.repository.name }}
        env:
          CARGO_REGISTRY_TOKEN: ${{ secrets.CARGO_REGISTRY_TOKEN }}
```

### 3.4 Auto-Versioning via Conservation Phase

Optional: `si publish --auto-semver` derives the semantic version bump from the conservation trend:

| Trend | Semver bump | Rationale |
|-------|-------------|-----------|
| Improving (deviation shrinking) | minor | Fleet growing stronger → feature release |
| Stable | patch | Maintenance release |
| Degrading (deviation growing) | patch + `-rc` | Prerelease only; warn operator |

---

## 4. Openclaw Gateway Integration

### 4.1 Architecture

```
openclaw gateway (existing HTTP server at :8000)
    ↑ heartbeat POST /api/fleet/heartbeat (every 60s)
    │ ← receives: FleetSnapshot JSON
    │ → returns: FleetAck { warnings, broadcasts }
    │
si gateway heartbeat
    ├── loads .si/config.yaml
    ├── starts ticker (default 60s)
    ├── each tick: internal/fleet.Snapshot() → POST to openclaw
    └── on FleetAck.broadcasts: routes through pipe/

openclaw gateway (existing HTTP server)
    ├── receives heartbeat from all si instances
    ├── stores fleet-wide history
    ├── exposes MCP tools (existing superinstance_fleet tool)
    └── computes cross-instance fleet conservation (V = sum of all registered agents)
```

### 4.2 New Gateway Endpoints (add to existing HTTP server)

These are additions to the existing beego-based HTTP server, not to the `si` binary:

```go
// controllers/fleet.go (new file, beego controller)

// POST /api/fleet/heartbeat
// Body: FleetSnapshot JSON
// Response: FleetAck JSON
type HeartbeatController struct {
    beego.Controller
}

type FleetAck struct {
    ReceivedAt  time.Time `json:"received_at"`
    InstanceID  string    `json:"instance_id"`
    GlobalV     int       `json:"global_v"`       // sum of agents across all instances
    GlobalDeviation float64 `json:"global_deviation_sigma"`
    Warnings    []string  `json:"warnings"`       // non-empty if conservation degrading
    Broadcasts  []FleetBroadcast `json:"broadcasts"` // messages to route through pipes
}

type FleetBroadcast struct {
    Level   string `json:"level"`   // LOW/MEDIUM/HIGH/CRITICAL
    Message string `json:"message"`
    Channel string `json:"channel,omitempty"` // empty = all channels at this level
}

// GET /api/fleet/status
// Returns the most recent snapshot from each registered si instance.

// GET /api/fleet/history?n=20
// Returns the last n global fleet snapshots.
```

### 4.3 `si gateway heartbeat` Implementation

```go
// internal/si/cmd_gateway.go (heartbeat subcommand)

func runHeartbeat(cfg *Config) error {
    ticker := time.NewTicker(cfg.HeartbeatInterval)
    defer ticker.Stop()
    log.Printf("heartbeat: registered with %s (interval=%s)", cfg.OpenclawGateway, cfg.HeartbeatInterval)
    for range ticker.C {
        snap, err := fleet.Snapshot(cfg.WorkspaceRoot)
        if err != nil {
            log.Printf("heartbeat: snapshot failed: %v", err)
            continue
        }
        ack, err := postHeartbeat(cfg.OpenclawGateway, snap)
        if err != nil {
            log.Printf("heartbeat: POST failed: %v", err)
            continue
        }
        for _, bc := range ack.Broadcasts {
            if err := routeBroadcast(cfg, bc); err != nil {
                log.Printf("heartbeat: broadcast failed: %v", err)
            }
        }
    }
    return nil
}

func postHeartbeat(gatewayURL string, snap *fleet.FleetSnapshot) (*fleet.FleetAck, error) {
    body, _ := json.Marshal(snap)
    resp, err := http.Post(gatewayURL+"/api/fleet/heartbeat", "application/json", bytes.NewReader(body))
    // ... parse FleetAck response
}
```

### 4.4 Local-Only Mode (no openclaw gateway)

When `openclaw_gateway` is absent from `.si/config.yaml`, `si gateway heartbeat` writes snapshots to `.si/fleet-history.jsonl` only. The gateway is optional — all local commands (`si fleet status`, `si conservation check`, etc.) work without it.

---

## 5. Pipe Adapters as Fleet Notification Channels

### 5.1 Priority Routing Table

The 9 pipe adapters map to fleet notification priority levels. Operators configure which adapters receive which levels in `.si/config.yaml`.

| Priority | Condition | Default Channels | Delivery SLA |
|----------|-----------|------------------|-------------|
| CRITICAL | Conservation deviation > 3σ, agent SUNSET | All configured channels | Immediate |
| HIGH | Conservation deviation > 2σ, publish failure | Telegram, Slack, Discord | Immediate |
| MEDIUM | Phase transitions, successful publishes | Slack, Discord | Best-effort |
| LOW | Routine heartbeats, status updates | Discord | Best-effort |

Default channel assignments by pipe type:

| Pipe | Suggested Fleet Role | Rationale |
|------|---------------------|-----------|
| Telegram | CRITICAL + HIGH | Real-time mobile push; reliable delivery |
| Slack | HIGH + MEDIUM | Team workspace; thread-able for follow-up |
| Discord | LOW + MEDIUM + HIGH | Community visibility; can be muted easily |
| WhatsApp | CRITICAL only | Personal device; maximum interrupt cost |
| X DM | HIGH | Public incident signal (sender controls audience) |
| Threads | MEDIUM | Community broadcast for releases |
| Facebook Messenger | MEDIUM | Secondary team channel |
| WeChat | CRITICAL + HIGH | Regional deployment channel |
| Snapchat | LOW | Ephemeral status; 24h TTL natural expiry |

### 5.2 New Package: `internal/notify/`

Wraps `pipe/` with priority routing. This is the only package that imports `pipe/` from the `si` binary; the server uses `pipe/` directly.

```go
// internal/notify/router.go

// PipeConfig maps a configured pipe name to its pipe.Pipe instance and level filter.
type PipeConfig struct {
    Name   string
    Impl   pipe.Pipe
    Levels []NotifyLevel // which levels this channel receives
}

type NotifyLevel int
const (
    LevelLow      NotifyLevel = 0
    LevelMedium   NotifyLevel = 1
    LevelHigh     NotifyLevel = 2
    LevelCritical NotifyLevel = 3
)

// Router dispatches fleet notifications to configured pipe channels.
type Router struct {
    channels []PipeConfig
}

// NewRouter builds a Router from the .si/config.yaml pipes section.
// It calls pipe.Get() for each configured pipe entry.
func NewRouter(cfgPipes []PipeConfigEntry) (*Router, error)

// Broadcast sends a message to all channels at or above the given level.
func (r *Router) Broadcast(ctx context.Context, level NotifyLevel, msg string) []error

// BroadcastTo sends a message to a specific named channel, bypassing level filter.
func (r *Router) BroadcastTo(ctx context.Context, name string, msg string) error

// Format helpers — fleet-aware message templates.
func FormatConservationAlert(snap *fleet.FleetSnapshot) string
func FormatPublishSuccess(repo, version string, snap *fleet.FleetSnapshot) string
func FormatAgentPhaseChange(name, from, to string) string
func FormatHeartbeatSummary(snap *fleet.FleetSnapshot) string
```

### 5.3 Fleet Event Messages

Standard message formats emitted by `si` commands:

```
# Conservation CRITICAL
⚠️ Fleet conservation CRITICAL: deviation=+3.21σ (threshold=3.00σ)
  γ=0.912  H=0.389  Expected=0.848  Fleet V=4
  Run `si conservation check` for details.

# Successful publish (MEDIUM)
📦 groovemesh-plr v0.1.0 published (SuperInstance/openagent#42)
  Conservation at release: deviation=+1.77σ ✓  Fleet V=4

# Agent phase transition (MEDIUM)
🔄 Agent FM promoted: COMPETE → SURVIVE (Gen 2)
  Trinity: Ethos=0.75 Pathos=0.65 Logos=0.88 Avg=0.760

# Heartbeat summary (LOW, periodic)
💚 Fleet heartbeat 2026-06-08 15:42 UTC
  4 active agents · deviation=+1.77σ · V=4 · head=fb4a5fae
```

### 5.4 `si pipe` Command Implementation

```go
// cmd_pipe.go

// si pipe list — shows configured channels with level filters
func runPipeList(cfg *Config) error {
    // Reads .si/config.yaml pipes section
    // Prints: Name | Type | Levels | Status (reachable/unreachable)
}

// si pipe send <channel> <message> --level=<level>
func runPipeSend(cfg *Config, channelName, message string, level NotifyLevel) error {
    router, _ := notify.NewRouter(cfg.Pipes)
    if channelName == "all" {
        errs := router.Broadcast(ctx, level, message)
        // report errors per channel
    } else {
        return router.BroadcastTo(ctx, channelName, message)
    }
}

// si pipe test <channel> — sends "Fleet pipe test: <timestamp>" at MEDIUM
func runPipeTest(cfg *Config, channelName string) error
```

---

## 6. Build System Changes

### 6.1 Dual Binary Build

Add `si` as a second binary in the goreleaser config. CGO remains disabled for both.

```yaml
# .goreleaser.yaml additions

builds:
  - id: openagent
    # ... existing config unchanged

  - id: si
    main: ./cmd/si
    binary: si
    env:
      - CGO_ENABLED=0
    flags:
      - -trimpath
    ldflags:
      - -s -w
      - -X github.com/the-open-agent/openagent/internal/cli.Version={{ .Version }}
      - -X github.com/the-open-agent/openagent/internal/cli.Commit={{ .Commit }}
      - -X github.com/the-open-agent/openagent/internal/cli.BuildDate={{ .Date }}
    goos: [linux, windows, darwin]
    goarch: [amd64, arm64]
```

### 6.2 Rust Bridge Binary

The `si-rust-bridge` binary is built separately via the Rust workspace and included in goreleaser archives as an extra file:

```yaml
# .goreleaser.yaml additions

extra_files:
  - glob: target/release/si-rust-bridge*   # bundled alongside si
```

The Rust workspace CI builds `si-rust-bridge` before goreleaser runs.

### 6.3 New Direct Dependency

Add `cobra` (or `urfave/cli`) to `go.mod`. Cobra is already the de-facto standard in Go CLI tooling and has zero runtime dependencies beyond `pflag`. Since goreleaser uses `CGO_ENABLED=0`, any new dep must also be CGO-free.

```
require (
    github.com/spf13/cobra v1.8.0
    github.com/spf13/viper v1.19.0  // for .si/config.yaml loading
)
```

---

## 7. Implementation Order

The following sequence minimizes risk and allows incremental testing:

### Phase 1: Core CLI skeleton (1–2 days)

1. Add `github.com/spf13/cobra` to `go.mod`
2. Create `cmd/si/main.go` + `internal/si/root.go`
3. Wire `si fleet status` using existing `superinstance.ActiveAgents()` and `superinstance.KnownAgents`
4. Wire `si conservation check` using existing `fleet_conservation.go` functions
5. Wire `si dial compare` and `si dial nearest` using existing `dial_theory.go`
6. Wire `si agents list` and `si repo audit` using existing `superinstance.Repos`

No new packages needed yet — Phase 1 just surfaces existing Go logic as CLI commands.

### Phase 2: Mutable fleet state (1 day)

1. Add `internal/fleet/` with `Snapshot()`, `LoadHistory()`, `SaveSnapshot()`
2. Add `AgentOverrides` (.si/agents.json)
3. Wire `si agents promote` and `si agents retire`
4. Add `si conservation history` reading `.si/fleet-history.jsonl`
5. Add `.si/config.yaml` loading via viper

### Phase 3: Notification routing (1 day)

1. Add `internal/notify/Router` wrapping `pipe/`
2. Wire `si pipe list`, `si pipe send`, `si pipe test`
3. Add `notify.BroadcastTo()` calls in `si publish` and `si agents promote`

### Phase 4: Git operations (1 day)

1. Add `internal/fleet/git.go` — `TagRelease()`, `IsClean()`, `FindRepoVersion()`
2. Wire `si publish` with the three-stage gate
3. Add `si conservation gate` as a thin wrapper
4. Install `pre-push` hook via `si init`

### Phase 5: Gateway heartbeat + Rust bridge (2 days)

1. Add `internal/bridge/` package + `si-rust-bridge` Rust crate
2. Add `controllers/fleet.go` to openagent server (heartbeat endpoint)
3. Wire `si gateway heartbeat`
4. Wire bridge commands for advanced conservation queries

### Phase 6: goreleaser + CI integration (1 day)

1. Add `si` build target to `.goreleaser.yaml`
2. Add `.github/workflows/si-fleet.yml`
3. Add UPX config for `si` binary (same as openagent binary)

---

## 8. Key Design Decisions

### Why not embed Rust code directly in openagent?

The existing goreleaser config has `CGO_ENABLED=0` and builds for `linux/darwin/windows × amd64/arm64` — that's 6 platform targets. Enabling CGO would require cross-compilation toolchains for each target, substantially complicating the build. The JSON-over-stdin bridge adds ~20ms per call — negligible for a CLI, acceptable for heartbeat (60s interval), and easily cacheable.

### Why not a separate `si` repo?

`si` needs `superinstance/`, `pipe/`, and `internal/cli/` — already in openagent. A separate repo would require either duplicating these or creating a shared library. The shared-module approach (two binaries from one module) is simpler and keeps fleet knowledge co-located with the agent runtime that generates it.

### Conservation as a publish gate, not a hard block

Conservation is a _signal_, not a lock. The `--force` flag always overrides. In practice, a deviation > 2σ usually means a new agent was just added (V changed) or the fleet is in transition. Blocking releases during fleet expansion would be self-defeating. The gate provides visibility, not veto power.

### Fleet entropy (H) computation

The conservation law uses H as a Helmholtz term. For a fleet of agents, H is Shannon entropy over normalized Trinity.Average() values:

```
p_i = Trinity.Average(agent_i) / Σ Trinity.Average(agent_j)
H = -Σ p_i · log2(p_i)
```

A uniform fleet (all agents equal) maximizes H. A fleet dominated by one agent (e.g., V=4, Oracle1 at 0.890 vs others near 0.75) has lower H. The conservation law says γ + H = f(V): as fleet grows, the split between mean performance and diversity is constrained.

This mirrors the spreadsheet-engine's `ConservationMonitor` (γ + η = budget) but at the fleet level rather than the cell level — a fractal conservation structure across scales.

---

## 9. Open Questions

1. **`si-rust-bridge` binary distribution**: Should it be a goreleaser extra file, or embedded as `//go:embed` bytes and extracted at runtime? The embed approach makes `si` fully self-contained at the cost of a larger binary.

2. **`.si/` directory gitignored or committed?** `fleet-history.jsonl` grows unboundedly — should be gitignored. `agents.json` (overrides) should probably be committed. `config.yaml` contains tokens — gitignored. Recommend: `.si/agents.json` committed, all others gitignored.

3. **Multi-workspace heartbeat**: openclaw gateway currently assumes one workspace. If the user has multiple workspaces (e.g., `/tmp/groovemesh` + main workspace), each `si gateway heartbeat` instance should register with a unique `instance_id`. Global V = sum across all registered instances.

4. **Pipe token security**: `.si/config.yaml` supports `${ENV_VAR}` substitution. This is Viper's default behavior. Tokens never appear in `.si/config.yaml` in plaintext — only env var references.

5. **`si conservation history` visualization**: ASCII sparkline is sufficient for terminal output. For richer visualization, `si conservation history --export` could write to `.si/conservation.svg` using a pure-Go SVG library (zero new deps).
