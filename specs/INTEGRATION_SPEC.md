# INTEGRATION_SPEC: spreadsheet-engine ↔ groovemesh-plr

**File**: `/tmp/nightshift/INTEGRATION_SPEC.md`  
**Status**: Engineering spec — implementation-ready  
**Crates involved**: `spreadsheet-engine` (on crates.io), `groovemesh-plr`, `spreadsheet-plr-bridge` (new)

---

## Overview

`spreadsheet-engine` produces MIDI events and tracks conservation budgets. `groovemesh-plr` enforces PLR-group harmony over 24 triads. Neither crate is modified. All integration lives in a new bridge crate: `spreadsheet-plr-bridge`.

Four integration points:

| # | From | To | What |
|---|------|----|------|
| 1 | `MidiCell::sonify()` | `groovemesh_plr::nearest::nearest_plr_triad()` | Snap raw MIDI output to nearest valid harmony via one PLR hop |
| 2 | `AgentCell::capabilities` | `groovemesh_plr::transform::PLR` | Map dominant capability to PLR operation; advance session chord on agent completion |
| 3 | `ConservationMonitor::{health,trend,violations}` | `cmidi_core::CMidiEvent` + PLR navigation | Encode budget health as CC104, trend as PLR chord movement, violations as tritone injection |
| 4 | `PLRSessionCoordinator` | All three above | Stateful coordinator holds `current_triad: Triad`, dispatches to integration points 1–3, emits `CMidiEvent` stream |

---

## 1. MidiCell → Harmonic Projection

### Problem

`MidiCell::sonify()` produces unconstrained MIDI:

```rust
// spreadsheet-engine/src/midi.rs
pub fn sonify(&mut self, value: &CellValue) -> Vec<[u8; 3]> {
    match value {
        CellValue::Number(n) => {
            let offset = n.clamp(-12.0, 12.0) as i8;
            let note = (self.base_note as i16 + offset as i16).clamp(0, 127) as u8;
            vec![[0x90 | self.channel, note, self.velocity]]
        }
        // ... Ternary, Vector variants also unconstrained
    }
}
```

A cell with `Number(7.0)` on `base_note=60` (C4) emits G4. If the session is in C minor, G is diatonic — fine. If the session is in Ab major, G is an avoid note. There is no guard.

### Solution

Extension trait `HarmonicSonify` wraps `sonify()` output with PLR projection:

```rust
// spreadsheet-plr-bridge/src/harmonic_sonify.rs

use groovemesh_plr::{
    nearest::{nearest_plr_triad, nearest_triad},
    chord::{PitchClass, Triad},
};
use spreadsheet_engine::midi::MidiCell;
use spreadsheet_engine::cell::CellValue;

pub trait HarmonicSonify {
    /// Like sonify(), but snaps every output note to the nearest pitch class
    /// in the PLR-projected triad closest to the raw output.
    fn sonify_harmonized(
        &mut self,
        value: &CellValue,
        session_triad: Triad,
    ) -> Vec<[u8; 3]>;
}

impl HarmonicSonify for MidiCell {
    fn sonify_harmonized(
        &mut self,
        value: &CellValue,
        session_triad: Triad,
    ) -> Vec<[u8; 3]> {
        let raw = self.sonify(value);
        if raw.is_empty() {
            return raw;
        }

        // Extract pitch classes from raw note-on events
        let raw_pcs: Vec<PitchClass> = raw.iter()
            .filter(|n| n[0] & 0xF0 == 0x90 && n[2] > 0)  // note-on, velocity > 0
            .map(|n| n[1] % 12)
            .collect();

        if raw_pcs.is_empty() {
            return raw;
        }

        // One PLR hop toward the triad best matching the raw output
        let target_triad = nearest_plr_triad(session_triad, &raw_pcs);

        // Snap each note to the nearest PC in target_triad, preserving octave
        raw.into_iter()
            .map(|mut event| {
                if event[0] & 0xF0 == 0x90 && event[2] > 0 {
                    event[1] = snap_to_triad(event[1], target_triad);
                }
                event
            })
            .collect()
    }
}

/// Snap MIDI note number to the nearest pitch class in `triad`, preserving octave register.
///
/// If the note's PC is already in the triad, it is unchanged.
/// Otherwise, find the triad PC with minimum chromatic distance (ties broken toward lower PC).
fn snap_to_triad(note: u8, triad: Triad) -> u8 {
    let pc = note % 12;
    let octave_base = note - pc;
    let triad_pcs = triad.pitch_classes();

    if triad_pcs.contains(&pc) {
        return note;
    }

    let (nearest_pc, _dist) = triad_pcs
        .iter()
        .map(|&t| {
            let diff = (pc as i16 - t as i16).abs();
            let dist = diff.min(12 - diff) as u8;
            (t, dist)
        })
        .min_by_key(|&(_, d)| d)
        .unwrap();

    // Maintain octave: if snapping crosses the octave boundary, adjust
    let raw_snapped = octave_base + nearest_pc;
    if raw_snapped > 127 { raw_snapped - 12 } else { raw_snapped }
}
```

### Behavior invariant

After `sonify_harmonized`, every output note's pitch class is contained in `target_triad.pitch_classes()`. This is guaranteed because `snap_to_triad` always returns a PC from the triad, and `nearest_plr_triad` always returns a valid member of T₂₄.

### Data flow

```
CellValue
    │
    ▼
MidiCell::sonify()          ← raw, unconstrained [u8; 3] events
    │
    ├─ extract PCs (n[1] % 12 for each note-on)
    │
    ▼
nearest_plr_triad(session_triad, raw_pcs)
    │                       ← internally: nearest_triad(raw_pcs) finds ideal;
    │                         Lattice::shortest_path(current, ideal) takes one BFS hop
    ▼
target_triad: Triad         ← PLR-adjacent to session_triad, closest to raw output
    │
    ▼
snap_to_triad(note, target_triad)  ← per note, min chromatic distance snap
    │
    ▼
Vec<[u8; 3]>                ← all PCs ∈ target_triad.pitch_classes()
```

### Why one PLR hop rather than snapping to ideal

`nearest_triad()` finds the globally best triad for the raw pitches, which may be 6 hops away from the session triad. A direct snap to a distant triad would produce a large voice-leading jump — exactly what PLR algebra is designed to prevent. One hop preserves the "no wrong note" guarantee while maintaining smooth voice-leading continuity.

---

## 2. AgentCell Capabilities → PLR Group Operations

### Problem

`AgentCell.capabilities: HashMap<String, f64>` describes what an agent can do and how confidently. The grid's harmonic context has no way to reflect what kind of cognitive work is happening in each cell.

### Semantic Mapping

PLR operations have natural semantic analogues for agent capabilities:

| PLR | Neo-Riemannian meaning | Agent domain |
|-----|----------------------|--------------|
| **R** (Relative) | Shares 2 common tones; changes mode while preserving root relationships | Retrieval, summarization, embedding — transform representation, preserve content |
| **P** (Parallel) | Same root, flips quality; maximum contrast in color | Classification, detection, decision — binary quality judgment on fixed structure |
| **L** (Leading-tone exchange) | Root moves by semitone; high tension, resolves strongly | Generation, synthesis, transformation — creates new content from existing structure |

### Capability Keyword Tables

These tables are the authoritative mapping. Case-insensitive substring match.

**R-type (Retrieval / Embedding):**
`summarize`, `embed`, `retrieve`, `search`, `recall`, `cluster`, `index`, `similarity`, `encode`, `compress`

**P-type (Classification / Decision):**
`classify`, `label`, `detect`, `filter`, `decide`, `discriminate`, `annotate`, `score`, `rank`, `threshold`

**L-type (Generation / Synthesis):**
`generate`, `create`, `synthesize`, `complete`, `transform`, `translate`, `rewrite`, `imagine`, `hallucinate`, `compose`

### Trait and Implementation

```rust
// spreadsheet-plr-bridge/src/capability_plr.rs

use std::collections::HashMap;
use groovemesh_plr::transform::PLR;
use spreadsheet_engine::cell::AgentCell;

pub trait CapabilityPLR {
    /// Returns the PLR operation corresponding to this cell's dominant capability.
    /// Returns None if no capability exceeds 0.0 or no keyword matches.
    fn dominant_plr_op(&self) -> Option<PLR>;

    /// Confidence-weighted centroid: weighted average of R/P/L scores.
    /// Used when multiple capabilities compete.
    fn plr_weights(&self) -> PlrWeights;
}

#[derive(Debug, Clone, Copy)]
pub struct PlrWeights {
    pub r: f64,
    pub p: f64,
    pub l: f64,
}

impl PlrWeights {
    /// The dominant PLR operation by weight.
    pub fn dominant(&self) -> Option<PLR> {
        let max = self.r.max(self.p).max(self.l);
        if max == 0.0 { return None; }
        if self.r == max { Some(PLR::R) }
        else if self.p == max { Some(PLR::P) }
        else { Some(PLR::L) }
    }
}

static R_KEYWORDS: &[&str] = &[
    "summarize","embed","retrieve","search","recall",
    "cluster","index","similarity","encode","compress",
];
static P_KEYWORDS: &[&str] = &[
    "classify","label","detect","filter","decide",
    "discriminate","annotate","score","rank","threshold",
];
static L_KEYWORDS: &[&str] = &[
    "generate","create","synthesize","complete","transform",
    "translate","rewrite","imagine","hallucinate","compose",
];

fn keyword_plr(name: &str) -> Option<PLR> {
    let lower = name.to_lowercase();
    if R_KEYWORDS.iter().any(|k| lower.contains(k)) { return Some(PLR::R); }
    if P_KEYWORDS.iter().any(|k| lower.contains(k)) { return Some(PLR::P); }
    if L_KEYWORDS.iter().any(|k| lower.contains(k)) { return Some(PLR::L); }
    None
}

impl CapabilityPLR for AgentCell {
    fn dominant_plr_op(&self) -> Option<PLR> {
        self.plr_weights().dominant()
    }

    fn plr_weights(&self) -> PlrWeights {
        let mut weights = PlrWeights { r: 0.0, p: 0.0, l: 0.0 };
        for (name, &confidence) in &self.capabilities {
            if confidence <= 0.0 { continue; }
            match keyword_plr(name) {
                Some(PLR::R) => weights.r += confidence,
                Some(PLR::P) => weights.p += confidence,
                Some(PLR::L) => weights.l += confidence,
                None => {}
            }
        }
        weights
    }
}
```

### Session Chord Advancement Protocol

When an `AgentCell` completes a task (transitions from `CellState::Running` to `CellState::Ready`), the `PLRSessionCoordinator` advances the session chord:

```
agent_cell.capabilities → dominant_plr_op() → PLR op
                                                 │
                                                 ▼
CounterpointRules::legal_plr_step(current_triad, apply(op, current_triad))
                                                 │
                                  ┌──────────────┴──────────────┐
                            Some((op, next))              None (illegal)
                                  │                             │
                                  ▼                             ▼
                    current_triad = next               keep current_triad
                                                    (emit PlrError::CounterpointViolation
                                                     as CC103 value 0)
```

This means the session harmony evolves with the cognitive work happening in the grid. A grid full of generation tasks walks through L operations (tension, resolution). A grid doing retrieval walks through R operations (stable, similar-sounding progressions).

---

## 3. ConservationMonitor → cmidi-conservation

### Problem

`ConservationMonitor` tracks whether `Σ(γ + η) ≈ total_budget` across all cells. This is a live budget health signal. Currently it has no audio representation.

### Three-Channel Mapping

```rust
// spreadsheet-plr-bridge/src/conservation_harmony.rs

use groovemesh_plr::{
    chord::Triad,
    transform::{apply, PLR},
};
use spreadsheet_engine::{
    conservation::{ConservationMonitor, ConservationTrend},
    grid::Grid,
    cell::CellId,
};
use cmidi_core::{CMidiEvent, ConversationCC};

pub trait ConservationHarmony {
    /// Map conservation state to MIDI events and an optional new triad.
    ///
    /// Returns: (events to emit this tick, Some(new_triad) if chord should advance)
    fn to_midi_events(
        &self,
        grid: &Grid,
        current_triad: Triad,
        tick: u64,
        channel: u8,
    ) -> (Vec<CMidiEvent>, Option<Triad>);
}

impl ConservationHarmony for ConservationMonitor {
    fn to_midi_events(
        &self,
        grid: &Grid,
        current_triad: Triad,
        tick: u64,
        channel: u8,
    ) -> (Vec<CMidiEvent>, Option<Triad>) {
        let mut events = Vec::new();

        // CC104 = ConservationRatio: health (0.0–1.0) → 0–127
        let cc104_value = (self.health() * 127.0).round() as u8;
        events.push(CMidiEvent::ControlChange {
            channel,
            controller: ConversationCC::ConservationRatio as u8,  // 104
            value: cc104_value,
            tick,
        });

        // Trend → PLR navigation
        let next_triad = match self.trend() {
            ConservationTrend::Improving => {
                // R: relative shift — preserves 2 common tones, signaling smooth improvement
                Some(apply(PLR::R, current_triad))
            }
            ConservationTrend::Degrading => {
                // P: parallel flip — same root, flipped quality — harmonic alarm signal
                Some(apply(PLR::P, current_triad))
            }
            ConservationTrend::Stable => None,
        };

        // CC103 = VoiceLeading: encode trend direction as voice-leading distance from current
        let vl_signal = match self.trend() {
            ConservationTrend::Improving => 64u8,  // neutral-high
            ConservationTrend::Stable => 32u8,      // low
            ConservationTrend::Degrading => 127u8,  // maximum — audible alarm
        };
        events.push(CMidiEvent::ControlChange {
            channel,
            controller: ConversationCC::VoiceLeading as u8,  // 103
            value: vl_signal,
            tick,
        });

        // Violations → tritone injection per violated cell
        for cell_id in self.violations(grid) {
            let base = grid.cell(cell_id)
                .and_then(|c| c.as_midi_cell())
                .map(|m| m.base_note)
                .unwrap_or(60u8);

            // Tritone = maximally dissonant interval — unambiguous violation signal
            let tritone_note = base.saturating_add(6).min(127);
            let cell_channel = (cell_id.row as u8) & 0x0F;

            events.push(CMidiEvent::NoteOn {
                channel: cell_channel,
                note: tritone_note,
                velocity: 80,
                tick,
            });
            // Auto-off after one tick
            events.push(CMidiEvent::NoteOff {
                channel: cell_channel,
                note: tritone_note,
                velocity: 0,
                tick: tick + 1,
            });
        }

        (events, next_triad)
    }
}
```

### Mapping Table

| Source field | Value range | MIDI mapping | Semantic |
|---|---|---|---|
| `health()` | `0.0–1.0` | CC104 = `(v * 127) as u8` | 0 = broke, 127 = perfectly balanced |
| `trend()::Improving` | enum variant | PLR::R advance; CC103 = 64 | Move toward relative — smooth, stable |
| `trend()::Stable` | enum variant | No PLR advance; CC103 = 32 | Hold current chord |
| `trend()::Degrading` | enum variant | PLR::P advance; CC103 = 127 | Parallel flip = audible alarm |
| `violations(grid)` | `Vec<CellId>` | NoteOn(base+6, vel=80) per violated cell | Tritone per violator |

---

## 4. PLRSessionCoordinator

Central stateful bridge struct. One instance per active grid session.

```rust
// spreadsheet-plr-bridge/src/coordinator.rs

use std::sync::Arc;
use tokio::sync::Mutex;
use groovemesh_plr::{
    chord::Triad,
    transform::{apply, PLR},
    counterpoint::CounterpointRules,
    lattice::Lattice,
};
use spreadsheet_engine::{
    grid::Grid,
    cell::{CellId, CellKind},
    conservation::ConservationMonitor,
};
use cmidi_core::CMidiEvent;

pub struct PLRSessionCoordinator {
    pub current_triad: Triad,
    pub rules: CounterpointRules,
    lattice: Lattice,
    tick: u64,
    pub cmidi_channel: u8,
}

impl PLRSessionCoordinator {
    pub fn new(initial_triad: Triad, cmidi_channel: u8) -> Self {
        Self {
            current_triad: initial_triad,
            rules: CounterpointRules::default(),
            lattice: Lattice::build(),
            tick: 0,
            cmidi_channel,
        }
    }

    /// Called each fleet-midi tick (480 ticks/beat).
    /// Returns all MIDI events to emit this tick.
    pub fn tick(
        &mut self,
        grid: &Grid,
        monitor: &ConservationMonitor,
    ) -> Vec<CMidiEvent> {
        self.tick += 1;
        let mut events = Vec::new();

        // 1. Conservation → MIDI + optional triad advance
        use crate::conservation_harmony::ConservationHarmony;
        let (conservation_events, conservation_triad) =
            monitor.to_midi_events(grid, self.current_triad, self.tick, self.cmidi_channel);
        events.extend(conservation_events);

        // Apply conservation-driven chord change if legal
        if let Some(next) = conservation_triad {
            if self.rules.check(self.current_triad, next).is_ok() {
                self.current_triad = next;
            }
        }

        // 2. Agent capability-driven chord advances (one per completed agent this tick)
        use crate::capability_plr::CapabilityPLR;
        for cell_id in grid.completed_agents_this_tick() {
            if let Some(agent) = grid.cell(cell_id).and_then(|c| c.as_agent_cell()) {
                if let Some(op) = agent.dominant_plr_op() {
                    let candidate = apply(op, self.current_triad);
                    if self.rules.check(self.current_triad, candidate).is_ok() {
                        self.current_triad = candidate;
                        break; // One chord advance per tick — prevents rapid drift
                    }
                }
            }
        }

        events
    }

    /// Harmonize a MidiCell's output against the current session triad.
    pub fn harmonize_cell(
        &mut self,
        cell: &mut spreadsheet_engine::midi::MidiCell,
        value: &spreadsheet_engine::cell::CellValue,
    ) -> Vec<[u8; 3]> {
        use crate::harmonic_sonify::HarmonicSonify;
        cell.sonify_harmonized(value, self.current_triad)
    }

    /// How many PLR hops from current_triad to a target triad.
    pub fn distance_to(&self, target: Triad) -> usize {
        self.lattice.distance(self.current_triad, target)
    }

    pub fn current_tick(&self) -> u64 {
        self.tick
    }
}
```

---

## 5. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        spreadsheet-engine                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                         Grid                                 │  │
│  │                                                              │  │
│  │  ┌──────────┐  CellValue  ┌────────────┐  HashMap<String,f64│  │
│  │  │ EvalGraph├────────────►│  MidiCell  │  ┌─────────────┐   │  │
│  │  │ (DAG,    │             │  .sonify() │  │  AgentCell  │   │  │
│  │  │  Kahn's) │             │  base_note │  │.capabilities│   │  │
│  │  └──────────┘             │  channel   │  │  gamma,eta  │   │  │
│  │                           └─────┬──────┘  └──────┬──────┘   │  │
│  └─────────────────────────────────┼─────────────────┼──────────┘  │
│                                    │                 │              │
│  ┌──────────────────────────┐      │                 │              │
│  │  ConservationMonitor     │      │                 │              │
│  │  .health() → f64         │      │                 │              │
│  │  .trend() → Trend enum   │      │                 │              │
│  │  .violations() → CellIds │      │                 │              │
│  └──────────┬───────────────┘      │                 │              │
└─────────────┼────────────────────── ┼ ────────────────┼─────────────┘
              │                       │                 │
              │         spreadsheet-plr-bridge          │
              │                       │                 │
              ▼                       ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PLRSessionCoordinator                           │
│                     current_triad: Triad                            │
│                                                                     │
│  ConservationHarmony::to_midi_events()                              │
│    health → CC104 value                                             │
│    Improving → apply(R, current)   ───────────────────────────┐    │
│    Degrading → apply(P, current)   ──────────────────────────┐│    │
│    violations → NoteOn(base+6)                               ││    │
│                                                              ││    │
│  CapabilityPLR::dominant_plr_op()                            ││    │
│    max(capabilities) → keyword match → PLR op                ││    │
│    CounterpointRules::check(current, apply(op, current))     ││    │
│      → if ok: current_triad = apply(op, current)  ──────────┘│    │
│                                                               │    │
│  HarmonicSonify::sonify_harmonized()                          │    │
│    sonify() → raw notes                                       │    │
│    raw_pcs → nearest_plr_triad(current, pcs)  ────────────────┘    │
│    → target_triad (one PLR hop)                                     │
│    snap_to_triad(note, target_triad)                                │
│                                                                     │
└──────────────┬──────────────────────┬──────────────────────────────┘
               │                      │
               ▼                      ▼
┌─────────────────────┐  ┌────────────────────────────────────────────┐
│   groovemesh-plr    │  │              cmidi-core                    │
│                     │  │                                            │
│  nearest_plr_triad  │  │  CMidiEvent::ControlChange(CC104, health)  │
│  Lattice::BFS       │  │  CMidiEvent::ControlChange(CC103, vl_dist) │
│  CounterpointRules  │  │  CMidiEvent::NoteOn (harmonized)          │
│  voice_leading_     │  │  CMidiEvent::NoteOn (tritone, violations)  │
│    distance         │  │                                            │
└─────────────────────┘  └──────────────┬───────────────────────────┘
                                         │
                                         ▼
                              fleet-midi-pulse (WebSocket)
                              → audio output / fleet health
```

---

## 6. Rust Trait Signatures — Complete Reference

All traits live in `spreadsheet-plr-bridge`. None modify either source crate.

```rust
// ── harmonic_sonify.rs ─────────────────────────────────────────────

pub trait HarmonicSonify {
    fn sonify_harmonized(
        &mut self,
        value: &CellValue,
        session_triad: Triad,
    ) -> Vec<[u8; 3]>;
}

impl HarmonicSonify for MidiCell { ... }

fn snap_to_triad(note: u8, triad: Triad) -> u8;

// ── capability_plr.rs ──────────────────────────────────────────────

#[derive(Debug, Clone, Copy)]
pub struct PlrWeights { pub r: f64, pub p: f64, pub l: f64 }

impl PlrWeights {
    pub fn dominant(&self) -> Option<PLR>;
    pub fn normalized(&self) -> PlrWeights;
}

pub trait CapabilityPLR {
    fn dominant_plr_op(&self) -> Option<PLR>;
    fn plr_weights(&self) -> PlrWeights;
}

impl CapabilityPLR for AgentCell { ... }

fn keyword_plr(name: &str) -> Option<PLR>;

// ── conservation_harmony.rs ────────────────────────────────────────

pub trait ConservationHarmony {
    fn to_midi_events(
        &self,
        grid: &Grid,
        current_triad: Triad,
        tick: u64,
        channel: u8,
    ) -> (Vec<CMidiEvent>, Option<Triad>);
}

impl ConservationHarmony for ConservationMonitor { ... }

// ── coordinator.rs ─────────────────────────────────────────────────

pub struct PLRSessionCoordinator {
    pub current_triad: Triad,
    pub rules: CounterpointRules,
    lattice: Lattice,          // private — built once
    tick: u64,
    pub cmidi_channel: u8,
}

impl PLRSessionCoordinator {
    pub fn new(initial_triad: Triad, cmidi_channel: u8) -> Self;

    pub fn tick(
        &mut self,
        grid: &Grid,
        monitor: &ConservationMonitor,
    ) -> Vec<CMidiEvent>;

    pub fn harmonize_cell(
        &mut self,
        cell: &mut MidiCell,
        value: &CellValue,
    ) -> Vec<[u8; 3]>;

    pub fn distance_to(&self, target: Triad) -> usize;
    pub fn current_tick(&self) -> u64;
}
```

---

## 7. Bridge Crate Structure

### `Cargo.toml`

```toml
[package]
name = "spreadsheet-plr-bridge"
version = "0.1.0"
edition = "2021"

[dependencies]
spreadsheet-engine = "0.1"
groovemesh-plr = { path = "../groovemesh-plr" }
cmidi-core = "0.1"
tokio = { version = "1", features = ["sync"] }
```

### `src/lib.rs`

```rust
pub mod harmonic_sonify;
pub mod capability_plr;
pub mod conservation_harmony;
pub mod coordinator;

// Re-export the four primary integration surfaces
pub use harmonic_sonify::HarmonicSonify;
pub use capability_plr::{CapabilityPLR, PlrWeights};
pub use conservation_harmony::ConservationHarmony;
pub use coordinator::PLRSessionCoordinator;
```

### Directory layout

```
spreadsheet-plr-bridge/
├── Cargo.toml
└── src/
    ├── lib.rs
    ├── harmonic_sonify.rs      # Integration point 1
    ├── capability_plr.rs       # Integration point 2
    ├── conservation_harmony.rs # Integration point 3
    └── coordinator.rs          # Integration point 4 (PLRSessionCoordinator)
```

---

## 8. CellMidi Wire Format Change

The existing `CellMidi` message (from `CELL_PROTOCOL.md`, type `0x09`, 13 bytes) adds one field:

```
Offset  Size  Field
0       1     type = 0x09
1       4     cell_id (row u16 + col u16)
5       1     channel (0–15)
6       1     base_note (0–127)
7       1     velocity (0–127)
8       1     plr_hint — NEW: encodes target triad as (root << 1) | quality_bit
                          root: 0–11, quality_bit: 0=Major 1=Minor
                          0xFF = no hint (use session default)
9       4     tick (u32, big-endian)
```

Total: 13 bytes → 14 bytes (one byte added at offset 8; tick shifts to offset 9).

The `plr_hint` byte lets the receiver skip `nearest_plr_triad()` if the sender already computed it, enabling zero-copy fast paths in the MIDI output pipeline.

Encoding:

```rust
fn encode_triad_hint(t: Option<Triad>) -> u8 {
    match t {
        None => 0xFF,
        Some(tr) => {
            let q = match tr.quality { Quality::Major => 0, Quality::Minor => 1 };
            (tr.root << 1) | q
        }
    }
}

fn decode_triad_hint(b: u8) -> Option<Triad> {
    if b == 0xFF { return None; }
    let root = b >> 1;
    let quality = if b & 1 == 1 { Quality::Minor } else { Quality::Major };
    Triad::new(root, quality).ok()
}
```

---

## 9. Error Handling

All integration errors are non-fatal by design. The grid must keep running even if PLR projection fails.

| Error condition | Source | Recovery |
|---|---|---|
| `PlrError::NoValidTriad` | `nearest_triad()` on empty `raw_pcs` | Return raw (unharmonized) notes from `sonify()` |
| `PlrError::NoPath` | `Lattice::shortest_path()` unreachable | Keep `current_triad` unchanged; log at WARN |
| `PlrError::CounterpointViolation` | `CounterpointRules::check()` | Skip chord advance; emit CC103=0 to signal blocked step |
| No capability keyword match | `capability_to_plr()` returns `None` | Skip chord advance; triad unchanged |
| `health()` returns NaN | Division by zero in empty history | Clamp to 0.0; emit CC104=0 |

```rust
// All integration points return non-panicking values:
// HarmonicSonify: falls back to raw sonify() output
// CapabilityPLR: returns None (caller skips advance)
// ConservationHarmony: returns empty events vec on monitor error
// PLRSessionCoordinator::tick: always returns Vec<CMidiEvent>, may be empty
```

---

## 10. Test Plan

Tests belong in `spreadsheet-plr-bridge/tests/integration.rs`.

```rust
// Test: snap_to_triad always produces a PC in the target triad
#[test]
fn snap_is_in_triad() {
    for note in 0u8..=127 {
        for root in 0u8..12 {
            let triad = Triad::new_unchecked(root, Quality::Major);
            let snapped = snap_to_triad(note, triad);
            assert!(triad.contains(snapped % 12),
                "note={note} root={root} snapped={snapped} not in triad");
        }
    }
}

// Test: sonify_harmonized output PCs are all in target triad
#[test]
fn harmonized_output_in_triad() {
    let mut cell = MidiCell { base_note: 60, channel: 0, velocity: 80, ..Default::default() };
    let triad = Triad::new_unchecked(0, Quality::Major); // C major
    let value = CellValue::Number(7.0); // raw: G4
    let events = cell.sonify_harmonized(&value, triad);
    // After one PLR hop toward G, result PC should be in the target triad
    for ev in &events {
        if ev[0] & 0xF0 == 0x90 {
            // Either in C major (0,4,7) or in a PLR-adjacent triad
            // The invariant: snap_to_triad guarantees containment
            let pc = ev[1] % 12;
            // The target triad is nearest_plr_triad(C_major, [7])
            // nearest_triad([7]) → G major or E minor (G is in both)
            // one hop from C → P(C)=Cm, L(C)=Em, R(C)=Am
            // Em contains G(7) — so target = Em, and pc=7 stays
            assert!(pc == 7 || pc == 4 || pc == 11, "unexpected pc={pc}");
        }
    }
}

// Test: capability → PLR mapping
#[test]
fn capability_to_plr_mapping() {
    let mut caps = HashMap::new();
    caps.insert("summarize".to_string(), 0.9);
    let cell = AgentCell { capabilities: caps, ..Default::default() };
    assert_eq!(cell.dominant_plr_op(), Some(PLR::R));

    let mut caps2 = HashMap::new();
    caps2.insert("classify".to_string(), 0.8);
    caps2.insert("generate".to_string(), 0.3);
    let cell2 = AgentCell { capabilities: caps2, ..Default::default() };
    assert_eq!(cell2.dominant_plr_op(), Some(PLR::P)); // P wins on weight

    let mut caps3 = HashMap::new();
    caps3.insert("generate".to_string(), 0.95);
    let cell3 = AgentCell { capabilities: caps3, ..Default::default() };
    assert_eq!(cell3.dominant_plr_op(), Some(PLR::L));
}

// Test: conservation health maps to CC104
#[test]
fn health_maps_to_cc104() {
    let mut monitor = ConservationMonitor::new(100.0, 1.0);
    // Inject healthy history
    // ...
    let (events, _) = monitor.to_midi_events(&grid, triad, 1, 0);
    let cc104 = events.iter().find(|e| matches!(e, CMidiEvent::ControlChange { controller: 104, .. }));
    assert!(cc104.is_some());
}

// Test: degrading trend → P operation
#[test]
fn degrading_trend_applies_parallel() {
    // Setup monitor with degrading history
    let triad = Triad::new_unchecked(0, Quality::Major); // C major
    let (_, next) = monitor.to_midi_events(&grid, triad, 1, 0);
    // P(C major) = C minor
    assert_eq!(next, Some(Triad::new_unchecked(0, Quality::Minor)));
}

// Test: triad hint encoding round-trips
#[test]
fn triad_hint_roundtrip() {
    for root in 0u8..12 {
        for quality in [Quality::Major, Quality::Minor] {
            let t = Triad::new_unchecked(root, quality);
            let encoded = encode_triad_hint(Some(t));
            let decoded = decode_triad_hint(encoded);
            assert_eq!(decoded, Some(t));
        }
    }
    assert_eq!(decode_triad_hint(0xFF), None);
}
```

---

## Open Questions

1. **Tick rate for chord advancement**: The coordinator allows at most one PLR chord advance per grid tick. At 480 ticks/beat and 120 BPM, that is 960 potential advances per second — far too fast for audible harmony. Recommend: gate chord advances to at most one per beat (480 ticks), configurable.

2. **Capability keyword conflict**: An agent with both `"generate"` (L-type) and `"embed"` (R-type) at equal confidence produces tied `PlrWeights`. The current impl returns `R` (first in `dominant()` comparator). This should probably be explicit: document that ties favor R over P over L (stability over tension).

3. **Grid method `completed_agents_this_tick()`**: The `PLRSessionCoordinator::tick()` call requires this method on `Grid`. It is not currently in the published `spreadsheet-engine` API. Either: (a) add it to `spreadsheet-engine`'s `Grid`, or (b) have the caller pass the list explicitly. Option (b) avoids modifying the source crate.

4. **Conservation trend stability**: `ConservationMonitor::trend()` is not in the published API of the `spreadsheet-engine::conservation` module as read — only `health()` and `violations()` are confirmed. Verify `trend()` exists before implementing `ConservationHarmony`. If absent, implement trend detection in the bridge crate from the `history: Vec<(u64, f64)>` field directly.
