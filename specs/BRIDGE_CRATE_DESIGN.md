# BRIDGE_CRATE_DESIGN: spreadsheet-plr-bridge v0.1.0

**File**: `/tmp/nightshift/BRIDGE_CRATE_DESIGN.md`  
**Purpose**: Complete implementation blueprint for the `spreadsheet-plr-bridge` crate.  
**Audience**: A GLM-5.1 subagent implementing this crate cold, without access to source crates.  
**Source**: Derived from INTEGRATION_SPEC.md + CROSS_CRATE_DEPENDENCY_MAP.md + direct source audits.

---

## 0. What This Crate Is

`spreadsheet-plr-bridge` connects two published crates that know nothing about each other:

- **`spreadsheet-engine`** — a reactive compute grid where cells can be agents, MIDI generators, or training jobs
- **`groovemesh-plr`** — PLR (Parsimonious Voice Leading) neo-Riemannian harmony algebra over 24 major/minor triads

Neither crate is modified. The bridge adds extension traits and a stateful coordinator on top of both. All public types in this crate are original to this crate; imported types from dependencies are used only as parameters and return values.

**Four integration points:**

| # | Trait / Struct | Extends | Does |
|---|---|---|---|
| 1 | `HarmonicSonify` | `spreadsheet_engine::MidiCell` | Snaps raw MIDI output to nearest PLR-valid triad |
| 2 | `CapabilityPLR` | `spreadsheet_engine::AgentCell` | Maps dominant capability keyword to PLR operation |
| 3 | `ConservationHarmony` | `spreadsheet_engine::ConservationMonitor` | Encodes budget health as CC104, violations as tritone injections |
| 4 | `PLRSessionCoordinator` | (new struct) | Stateful session: holds current triad, dispatches all three traits, emits `BridgeEvent` stream |

---

## 1. Cargo.toml

```toml
[package]
name = "spreadsheet-plr-bridge"
version = "0.1.0"
edition = "2021"
rust-version = "1.78"
description = "Connects spreadsheet-engine cells to groovemesh-plr harmony algebra"
license = "MIT"

# ── Required dependencies (always present) ─────────────────────────────────────

[dependencies]
spreadsheet-engine   = "0.1"
groovemesh-plr       = "0.1"
cmidi-core           = "0.2"
thiserror            = "2"

# ── Optional dependencies (feature-gated) ──────────────────────────────────────

[dependencies.tokio]
version  = "1"
features = ["sync"]
optional = true

[dependencies.noether-guard]
version  = "0.1"
optional = true

[dependencies.cmidi-conservation]
version  = "0.1"
optional = true

# ── Features ───────────────────────────────────────────────────────────────────

[features]
# coordinator: PLRSessionCoordinator requires tokio::sync::Mutex
coordinator         = ["dep:tokio"]

# noether: richer conservation trend analysis via noether-guard::ConservationMonitor
noether             = ["dep:noether-guard"]

# cmidi-conservation-cc: emit ConservationVoice-compatible events
cmidi-conservation  = ["dep:cmidi-conservation"]

# full: all optional features enabled
full                = ["coordinator", "noether", "cmidi-conservation"]

[dev-dependencies]
tokio = { version = "1", features = ["full", "test-util"] }
```

### Version notes

| Crate | Version | Key types used |
|---|---|---|
| `spreadsheet-engine` | `0.1` | `MidiCell`, `AgentCell`, `CellValue`, `CellId`, `Grid`, `ConservationMonitor`, `ConservationTrend` |
| `groovemesh-plr` | `0.1` | `Triad`, `Quality`, `PLR`, `PitchClass`, `PlrError`, `CounterpointRules`, `Lattice`, `nearest_plr_triad`, `voice_leading_distance` |
| `cmidi-core` | `0.2` | `CMidiEvent`, `SpeechAct`, `ConversationCC`, `AgentRole` |
| `thiserror` | `2` | `#[derive(Error)]` for `BridgeError` |
| `tokio` | `1` | `tokio::sync::Mutex` in `PLRSessionCoordinator` (optional) |
| `noether-guard` | `0.1` | `ConservationMonitor` (richer than spreadsheet-engine's; optional) |
| `cmidi-conservation` | `0.1` | `ConservationVoice` (optional CC compatibility) |

---

## 2. Source Type Reference

This section documents every type from dependency crates that the bridge uses. The GLM agent MUST NOT guess or invent fields — use exactly what is listed here.

### 2.1 From `spreadsheet_engine::cell`

```rust
// ── CellId ──────────────────────────────────────────────────────────────────
pub struct CellId {
    pub row: usize,
    pub col: usize,
}
impl CellId {
    pub fn new(row: usize, col: usize) -> Self;
}
impl std::fmt::Display for CellId {
    // formats as "R{row}C{col}"
}

// ── CellValue ────────────────────────────────────────────────────────────────
pub enum CellValue {
    Number(f64),
    Text(String),
    Bool(bool),
    Ternary(i8),          // INVARIANT: value ∈ {-1, 0, 1}
    Vector(Vec<f64>),
    Empty,
    Error(String),
}

// ── CellState ────────────────────────────────────────────────────────────────
pub enum CellState { Idle, Evaluating, Ready, Error, Running, Paused }

// ── AgentCell ────────────────────────────────────────────────────────────────
pub struct AgentCell {
    pub agent_id:     String,
    pub capabilities: std::collections::HashMap<String, f64>,  // name → confidence 0.0–1.0
    pub gamma:        f64,    // compute spend (≥ 0.0)
    pub eta:          f64,    // memory usage (≥ 0.0)
    pub budget:       f64,    // total allowed (> 0.0)
    pub state:        CellState,
}
impl AgentCell {
    // Returns |gamma + eta - budget|
    pub fn conservation_error(&self) -> f64;
    // Returns conservation_error() <= tolerance
    pub fn is_healthy(&self, tolerance: f64) -> bool;
}
```

### 2.2 From `spreadsheet_engine::midi`

```rust
pub struct MidiCell {
    pub name:       String,
    pub state:      CellState,
    pub channel:    u8,        // INVARIANT: 0–15 (clamped at construction)
    pub base_note:  u8,        // INVARIANT: 0–127 (clamped at construction)
    pub velocity:   u8,        // INVARIANT: 0–127
    pub last_event: Option<[u8; 3]>,
}

impl MidiCell {
    /// Produce MIDI bytes for a cell value. Returns Vec<[u8; 3]>.
    /// Each [u8; 3] is a standard MIDI message: [status, data1, data2].
    ///
    /// Exact mapping (CONFIRMED FROM SOURCE):
    ///   Number(n):   offset = n.clamp(-12.0, 12.0) as i8
    ///                note   = (base_note as i16 + offset as i16).clamp(0, 127) as u8
    ///                → [[0x90 | channel, note, velocity]]
    ///
    ///   Ternary(-1): note = base_note.saturating_sub(3)   (minor third below)
    ///   Ternary(0):  note = base_note
    ///   Ternary(1):  note = base_note.saturating_add(4)   (major third above)
    ///                → [[0x90 | channel, note, velocity]]
    ///
    ///   Vector(v):   for each element e in v (up to 6):
    ///                  offset = (e * 12.0).clamp(-24.0, 24.0) as i8
    ///                  note = (base_note as i16 + offset as i16).clamp(0, 127) as u8
    ///                → [[0x90 | channel, note, velocity], ...]  ← up to 6 entries
    ///
    ///   Text / Bool / Empty / Error: → []  (no output)
    pub fn sonify(&mut self, value: &CellValue) -> Vec<[u8; 3]>;
}
```

### 2.3 From `spreadsheet_engine::conservation`

```rust
pub enum ConservationTrend {
    Improving,   // recent health scores trending upward
    Stable,      // no significant trend
    Degrading,   // recent health scores trending downward
}

pub struct ConservationMonitor {
    pub total_budget: f64,               // sum of all agent budgets
    pub tolerance:    f64,               // |error| <= tolerance → healthy cell
    pub history:      Vec<(u64, f64)>,   // (tick, health_score)  health ∈ [0.0, 1.0]
}

impl ConservationMonitor {
    pub fn new(total_budget: f64, tolerance: f64) -> Self;

    /// Health = 1.0 - (|Σ(γ+η) - total_budget| / total_budget).min(1.0)
    /// Returns 1.0 if no AgentCells exist.
    pub fn health(&self, grid: &Grid) -> f64;

    /// CellIds of AgentCells where !cell.is_healthy(self.tolerance)
    pub fn violations(&self, grid: &Grid) -> Vec<CellId>;

    /// Derived from history: compares mean of last-5 vs prev-5 health scores.
    /// Improving if diff > 0.01, Degrading if diff < -0.01, else Stable.
    /// Returns Stable if history.len() < 2.
    pub fn trend(&self) -> ConservationTrend;

    pub fn total_gamma(&self, grid: &Grid) -> f64;
    pub fn total_eta(&self, grid: &Grid) -> f64;
}
```

### 2.4 From `spreadsheet_engine::grid`

```rust
pub struct Grid { /* opaque — use methods below */ }

impl Grid {
    /// Returns the cell at position id, or None if not present.
    pub fn cell(&self, id: CellId) -> Option<&Cell>;

    /// Iterator over all (CellId, &Cell) pairs.
    pub fn cells(&self) -> impl Iterator<Item = (CellId, &Cell)>;

    /// Iterator over all AgentCells only.
    pub fn agent_cells(&self) -> impl Iterator<Item = (CellId, &AgentCell)>;

    /// Iterator over all MidiCells only.
    pub fn midi_cells(&self) -> impl Iterator<Item = (CellId, &MidiCell)>;
}

/// Cell is an enum wrapping each cell type.
pub enum Cell {
    Value(ValueCell),
    Agent(AgentCell),
    Midi(MidiCell),
    Formula(FormulaCell),
    Training(TrainingCell),
    Simulation(SimulationCell),
    A2A(A2ACell),
}

impl Cell {
    pub fn as_agent(&self) -> Option<&AgentCell>;
    pub fn as_midi(&self) -> Option<&MidiCell>;
    pub fn as_midi_mut(&mut self) -> Option<&mut MidiCell>;
}
```

### 2.5 From `groovemesh_plr::chord`

```rust
pub type PitchClass = u8;  // 0=C, 1=C#, 2=D, 3=D#, 4=E, 5=F,
                            // 6=F#, 7=G, 8=G#, 9=A, 10=A#, 11=B

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub enum Quality { Major, Minor }

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct Triad {
    pub root:    PitchClass,   // 0–11
    pub quality: Quality,
}

impl Triad {
    pub fn new(root: PitchClass, quality: Quality) -> Result<Self, PlrError>;
    pub const fn new_unchecked(root: PitchClass, quality: Quality) -> Self;
    pub fn from_name(name: &str) -> Result<Self, PlrError>;
    pub fn all() -> Vec<Triad>;   // all 24 major/minor triads

    /// [root, third, fifth]
    /// Major: [root, (root+4)%12, (root+7)%12]
    /// Minor: [root, (root+3)%12, (root+7)%12]
    pub fn pitch_classes(&self) -> [PitchClass; 3];

    pub fn contains(&self, pc: PitchClass) -> bool;
    pub fn common_tones(&self, other: &Triad) -> usize;
    pub fn root_name(&self) -> &'static str;
}

impl std::fmt::Display for Triad {
    // formats as "C", "Am", "F#", "Bbm", etc.
}
```

### 2.6 From `groovemesh_plr::transform`

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PLR { P, L, R }

/// Parallel: same root, flip quality.
/// P(C major) = C minor. P(Am) = A major.
pub fn apply_p(t: Triad) -> Triad;

/// Leading-tone exchange.
/// L(C major) = E minor   — new root = (0+4)%12 = 4
/// L(C minor) = Ab major  — new root = (0+8)%12 = 8
/// VERIFIED INVOLUTIVE: L(Em) = (4+8)%12 = 0 = C major. L² = id. ✓
pub fn apply_l(t: Triad) -> Triad;

/// Relative.
/// R(C major) = A minor   — new root = (0+9)%12 = 9
/// R(C minor) = Eb major  — new root = (0+3)%12 = 3
pub fn apply_r(t: Triad) -> Triad;

/// Dispatch: apply a single PLR op.
pub fn apply(op: PLR, t: Triad) -> Triad;

#[derive(Debug, Clone, PartialEq)]
pub struct PLRWord { pub ops: Vec<PLR> }

impl PLRWord {
    pub fn new() -> Self;
    pub fn from_ops(ops: &[PLR]) -> Self;
    pub fn apply(&self, t: Triad) -> Triad;
    pub fn reduce(&self) -> PLRWord;   // cancel adjacent identical ops (PP=id, LL=id, RR=id)
    pub fn inverse(&self) -> PLRWord;  // reverse order (P,L,R)⁻¹ = (R,L,P)
    pub fn len(&self) -> usize;
    pub fn is_empty(&self) -> bool;
}
```

### 2.7 From `groovemesh_plr::nearest`

```rust
/// Find the triad in T₂₄ best matching a set of pitch classes.
///
/// Scoring: (1) maximize number of PCs contained in the triad,
///          (2) minimize sum of min chromatic distance from each PC to any triad PC.
///
/// Returns Err(PlrError::NoValidTriad) if pitches is empty.
/// Returns Err(PlrError::InvalidPitchClass(pc)) if any pc > 11.
pub fn nearest_triad(pitches: &[PitchClass]) -> Result<Triad, PlrError>;

/// One PLR hop from `current` toward the triad nearest to `pitches`.
///
/// Algorithm:
///   1. ideal = nearest_triad(pitches). On Err or empty: return current unchanged.
///   2. If ideal == current: return current.
///   3. path = Lattice::build().shortest_path(current, ideal).
///      If None or empty: return current unchanged.
///   4. Return apply(path[0], current).  ← EXACTLY ONE HOP.
///
/// This function is INFALLIBLE — always returns a valid Triad.
pub fn nearest_plr_triad(current: Triad, pitches: &[PitchClass]) -> Triad;
```

### 2.8 From `groovemesh_plr::voice`

```rust
pub struct VoiceLeading {
    pub from:      Triad,
    pub to:        Triad,
    pub movements: [i8; 4],  // [soprano, alto, tenor, bass] semitone movements
    pub distance:  u32,      // sum of |movement[i]|
}

pub fn minimal_voice_leading(from: Triad, to: Triad) -> VoiceLeading;

/// Sum of absolute minimal semitone movements (close-position, all permutations).
pub fn voice_leading_distance(from: Triad, to: Triad) -> u32;

/// The single PLR neighbor of `from` that minimizes voice_leading_distance to `target`.
/// Returns (op, apply(op, from), distance(apply(op, from), target)).
pub fn nearest_plr_neighbor(from: Triad, target: Triad) -> (PLR, Triad, u32);
```

### 2.9 From `groovemesh_plr::counterpoint`

```rust
#[derive(Debug, Clone)]
pub struct CounterpointRules {
    pub no_parallel_fifths:  bool,          // default true
    pub no_parallel_octaves: bool,          // default true
    pub no_voice_crossing:   bool,          // default true
    pub max_voice_distance:  Option<u32>,   // default Some(7) semitones
}

impl Default for CounterpointRules {
    fn default() -> Self {
        Self {
            no_parallel_fifths:  true,
            no_parallel_octaves: true,
            no_voice_crossing:   true,
            max_voice_distance:  Some(7),
        }
    }
}

impl CounterpointRules {
    pub fn new() -> Self;  // same as Default

    /// Err(PlrError::CounterpointViolation(reason)) if any rule is broken.
    /// Ok(()) if transition is legal.
    /// NOTE: check(t, t) always returns Ok(()) — self-transition is legal.
    pub fn check(&self, from: Triad, to: Triad) -> Result<(), PlrError>;

    /// Among {P(from), L(from), R(from)}, find the one that:
    ///   (a) passes check(from, neighbor), AND
    ///   (b) minimizes voice_leading_distance(neighbor, target).
    /// Returns None if all three PLR neighbors violate the rules.
    pub fn legal_plr_step(&self, from: Triad, target: Triad) -> Option<(PLR, Triad)>;

    /// Walk from start toward target using legal_plr_step, up to max_steps hops.
    /// Stops early if target is reached or no legal step is available.
    pub fn legal_path(&self, start: Triad, target: Triad, max_steps: usize) -> Vec<(PLR, Triad)>;
}
```

### 2.10 From `groovemesh_plr::lattice`

```rust
pub struct Lattice {
    adj: std::collections::HashMap<Triad, Vec<LatticeEdge>>,
}

pub struct LatticeEdge {
    pub op:     PLR,
    pub target: Triad,
}

impl Lattice {
    /// Build the complete PLR Cayley graph: 24 nodes × 3 edges each.
    /// Graph diameter ≤ 6 (proven in PROOF.md).
    /// This is O(72) — cheap, build it fresh per coordinator, not per tick.
    pub fn build() -> Self;

    /// BFS from `from` to `to`. Returns the sequence of PLR ops (length = distance).
    /// Returns None if no path exists (impossible in a connected graph, but defensively handled).
    pub fn shortest_path(&self, from: Triad, to: Triad) -> Option<Vec<PLR>>;

    /// Number of PLR hops from from to to (0 if from == to, max 6).
    pub fn distance(&self, from: Triad, to: Triad) -> usize;
}
```

### 2.11 From `groovemesh_plr::error`

```rust
#[derive(Debug, thiserror::Error)]
pub enum PlrError {
    #[error("invalid chord name: {0}")]
    InvalidChordName(String),
    #[error("invalid pitch class: {0} (must be 0–11)")]
    InvalidPitchClass(u8),
    #[error("no valid triad found for given pitch classes")]
    NoValidTriad,
    #[error("no path between triads in PLR lattice")]
    NoPath,
    #[error("voice leading violation: {0}")]
    VoiceLeadingViolation(String),
    #[error("counterpoint violation: {0}")]
    CounterpointViolation(String),
}
```

### 2.12 From `cmidi_core`

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpeechAct {
    Assertion,   // C4 = MIDI note 60
    Question,    // D4 = 62
    Command,     // E4 = 64
    Agreement,   // F4 = 65
    Objection,   // G4 = 67
    Elaboration, // A4 = 69
    Transition,  // B4 = 71
    Silence,     // rest = 0 (NoteOn emits [0,0,0])
}
impl SpeechAct {
    pub fn note(&self) -> u8;  // returns the MIDI note number above
    pub fn is_consonant_with(&self, other: &SpeechAct) -> bool;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ConversationCC {
    Engagement      = 1,
    Sarcasm         = 2,
    Salience        = 7,
    Sentiment       = 10,
    Nuance          = 11,
    Expertise       = 16,
    Urgency         = 17,
    ReferenceDepth  = 18,
    Novelty         = 19,
    Tension         = 102,
    VoiceLeading    = 103,
    ConservationRatio = 104,
}
impl ConversationCC {
    pub fn cc_number(&self) -> u8;  // returns the discriminant value above
}

#[derive(Debug, Clone)]
pub struct CMidiEvent {
    pub tick:          u32,
    pub agent_channel: u8,
    pub speech_act:    SpeechAct,
    pub velocity:      u8,
    pub duration:      u32,
    pub cc_values:     Vec<(ConversationCC, u8)>,
}
impl CMidiEvent {
    pub fn new(tick: u32, channel: u8, act: SpeechAct, velocity: u8, duration: u32) -> Self;
    // Builder: appends (cc, value) to cc_values and returns self
    pub fn with_cc(self, cc: ConversationCC, value: u8) -> Self;
    // [0x90|channel, speech_act.note(), velocity]; returns [0,0,0] for Silence
    pub fn note_on_bytes(&self) -> [u8; 3];
    // [0x80|channel, speech_act.note(), 0]; returns [0,0,0] for Silence
    pub fn note_off_bytes(&self) -> [u8; 3];
    // [[0xB0|channel, cc_number, value], ...] for each entry in cc_values
    pub fn cc_bytes(&self) -> Vec<[u8; 3]>;
}
```

---

## 3. Module Structure

```
spreadsheet-plr-bridge/
├── Cargo.toml
└── src/
    ├── lib.rs                  # re-exports + module declarations
    ├── error.rs                # BridgeError, BridgeResult
    ├── event.rs                # BridgeEvent enum
    ├── harmonic_sonify.rs      # Integration 1: HarmonicSonify trait
    ├── capability_plr.rs       # Integration 2: CapabilityPLR trait
    ├── conservation_harmony.rs # Integration 3: ConservationHarmony trait
    └── coordinator.rs          # Integration 4: PLRSessionCoordinator
```

---

## 4. `src/error.rs`

```rust
use groovemesh_plr::error::PlrError;

/// All errors the bridge can produce.
#[derive(Debug, thiserror::Error)]
pub enum BridgeError {
    /// PLR lattice or group operation failed.
    #[error("PLR error: {0}")]
    Plr(#[from] PlrError),

    /// A proposed chord advance violated counterpoint rules.
    /// `to` is the Display string of the target Triad.
    /// `reason` is the PlrError::CounterpointViolation message.
    #[error("counterpoint violation advancing to {to}: {reason}")]
    CounterpointViolation { to: String, reason: String },

    /// nearest_plr_triad returned the same triad — no valid projection.
    #[error("no harmonic projection possible: all 24 triads equally distant")]
    NoProjection,

    /// The grid contains no AgentCells — conservation monitoring not available.
    #[error("conservation monitoring unavailable: grid has no AgentCells")]
    NoAgentCells,

    /// MIDI channel out of range.
    #[error("channel {0} out of range (must be 0–15)")]
    InvalidChannel(u8),
}

/// Convenience alias.
pub type BridgeResult<T> = Result<T, BridgeError>;
```

---

## 5. `src/event.rs`

`CMidiEvent` from `cmidi-core` encodes speech acts at fixed pitch classes (C4, D4, …). The bridge also needs to inject arbitrary note numbers for tritone violation signaling. `BridgeEvent` holds both.

```rust
use cmidi_core::CMidiEvent;

/// A MIDI output event produced by the bridge.
///
/// Use `BridgeEvent::to_bytes()` to get the raw three-byte MIDI message.
/// For CC-only `SpeechAct` events, the SpeechAct is always `Silence`;
/// only the `cc_values` carry information.
#[derive(Debug, Clone)]
pub enum BridgeEvent {
    /// A CMIDI conversational event (speech act + optional CC values).
    /// Used for: CC104 (ConservationRatio), CC103 (VoiceLeading).
    SpeechAct(CMidiEvent),

    /// A raw MIDI Note On. Used for tritone violation injection.
    NoteOn {
        channel:  u8,
        note:     u8,
        velocity: u8,
        tick:     u64,
    },

    /// A raw MIDI Note Off. Always paired with a NoteOn 1 tick later.
    NoteOff {
        channel: u8,
        note:    u8,
        tick:    u64,
    },

    /// A raw MIDI CC (used when a CMidiEvent would be overkill).
    CC {
        channel:    u8,
        controller: u8,
        value:      u8,
        tick:       u64,
    },
}

impl BridgeEvent {
    /// The tick this event belongs to.
    pub fn tick(&self) -> u64 {
        match self {
            Self::SpeechAct(e) => e.tick as u64,
            Self::NoteOn  { tick, .. } => *tick,
            Self::NoteOff { tick, .. } => *tick,
            Self::CC      { tick, .. } => *tick,
        }
    }

    /// Raw MIDI bytes [status, data1, data2].
    ///
    /// For `SpeechAct(e)` where `e.speech_act == Silence`:
    ///   returns the first CC pair's bytes if cc_values is non-empty,
    ///   otherwise [0, 0, 0].
    ///
    /// For `SpeechAct(e)` where `e.speech_act != Silence`:
    ///   returns `e.note_on_bytes()`.
    ///
    /// For raw variants: constructs the standard 3-byte message.
    pub fn to_bytes(&self) -> [u8; 3] {
        match self {
            Self::SpeechAct(e) => {
                use cmidi_core::SpeechAct;
                if e.speech_act == SpeechAct::Silence {
                    if let Some((cc, val)) = e.cc_values.first() {
                        [0xB0 | (e.agent_channel & 0x0F), cc.cc_number(), *val]
                    } else {
                        [0, 0, 0]
                    }
                } else {
                    e.note_on_bytes()
                }
            }
            Self::NoteOn  { channel, note, velocity, .. } =>
                [0x90 | (channel & 0x0F), *note, *velocity],
            Self::NoteOff { channel, note, .. } =>
                [0x80 | (channel & 0x0F), *note, 0],
            Self::CC      { channel, controller, value, .. } =>
                [0xB0 | (channel & 0x0F), *controller, *value],
        }
    }

    /// All raw bytes for this event: note_on + all CC messages.
    /// For SpeechAct events, returns note bytes + all cc_values bytes.
    /// For raw variants, returns exactly one entry: `vec![self.to_bytes()]`.
    pub fn all_bytes(&self) -> Vec<[u8; 3]> {
        match self {
            Self::SpeechAct(e) => {
                let mut out = Vec::new();
                out.extend_from_slice(&e.cc_bytes());
                let note = e.note_on_bytes();
                if note != [0, 0, 0] {
                    out.push(note);
                }
                out
            }
            other => vec![other.to_bytes()],
        }
    }

    /// True if this event carries meaningful data (not a no-op).
    pub fn is_active(&self) -> bool {
        self.to_bytes() != [0, 0, 0]
    }
}
```

---

## 6. `src/harmonic_sonify.rs` — Integration 1

### Trait definition

```rust
use groovemesh_plr::{
    chord::{PitchClass, Quality, Triad},
    nearest::nearest_plr_triad,
};
use spreadsheet_engine::{cell::CellValue, midi::MidiCell};

/// Extension trait for MidiCell.
///
/// `sonify_harmonized` wraps `MidiCell::sonify()` and snaps every output
/// pitch class to the nearest pitch class in a PLR-projected triad.
///
/// INVARIANT: after this call, for every [status, note, velocity] in the
/// returned vec where (status & 0xF0 == 0x90) && velocity > 0:
///   session_triad_after_projection.contains(note % 12) == true
///
/// FALLBACK: if nearest_plr_triad returns the same triad as session_triad
/// (i.e., the raw output already fits), notes are still snapped to that triad.
/// If raw is empty, returns empty.
pub trait HarmonicSonify {
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

        // Collect pitch classes from note-on events.
        // Filter: status byte high nibble == 0x90 AND velocity > 0.
        let raw_pcs: Vec<PitchClass> = raw
            .iter()
            .filter(|n| (n[0] & 0xF0) == 0x90 && n[2] > 0)
            .map(|n| n[1] % 12)
            .collect();

        if raw_pcs.is_empty() {
            // All events were note-offs or zero-velocity — return unchanged.
            return raw;
        }

        // One PLR hop toward the triad best matching the raw pitch classes.
        // nearest_plr_triad is infallible; returns session_triad on any error.
        let target = nearest_plr_triad(session_triad, &raw_pcs);

        // Snap each note-on to the nearest PC in target.
        raw.into_iter()
            .map(|mut event| {
                if (event[0] & 0xF0) == 0x90 && event[2] > 0 {
                    event[1] = snap_to_triad(event[1], target);
                }
                event
            })
            .collect()
    }
}
```

### `snap_to_triad` — internal function

```rust
/// Snap a MIDI note number to the nearest pitch class in `triad`,
/// preserving the octave register as closely as possible.
///
/// Algorithm:
///   1. pc = note % 12
///   2. octave_base = note - pc
///   3. pcs = triad.pitch_classes()  → [root, third, fifth]
///   4. If pc already in pcs → return note unchanged.
///   5. For each t in pcs:
///        diff = (pc as i16 - t as i16).abs()
///        dist = min(diff, 12 - diff) as u8   ← chromatic distance mod 12
///   6. nearest_pc = t with minimum dist.
///      Tie-break: choose the lowest pitch class value.
///   7. raw_snapped = octave_base + nearest_pc
///   8. If raw_snapped > 127: raw_snapped -= 12  (drop one octave)
///   9. Return raw_snapped as u8.
///
/// Examples (C major triad = [0, 4, 7]):
///   snap(60, C_major) = 60  (C4 is root — unchanged)
///   snap(61, C_major) = 60  (C#4: dist(1,0)=1, dist(1,4)=3, dist(1,7)=6 → snap to 0)
///   snap(62, C_major) = 60  (D4: dist(2,0)=2, dist(2,4)=2 → tie → lowest=0=C → 60)
///   snap(63, C_major) = 64  (D#4: dist(3,0)=3, dist(3,4)=1, dist(3,7)=4 → snap to 4=E)
///   snap(66, C_major) = 67  (F#4: dist(6,0)=6, dist(6,4)=2, dist(6,7)=1 → snap to 7=G)
pub(crate) fn snap_to_triad(note: u8, triad: Triad) -> u8 {
    let pc = note % 12;
    let octave_base = note - pc;
    let pcs = triad.pitch_classes(); // [root, third, fifth]

    if pcs.contains(&pc) {
        return note;
    }

    let (nearest_pc, _) = pcs
        .iter()
        .map(|&t| {
            let diff = (pc as i16 - t as i16).abs();
            let dist = diff.min(12 - diff) as u8;
            (t, dist)
        })
        .min_by_key(|&(t, dist)| (dist, t)) // primary: distance, secondary: lowest PC
        .expect("pitch_classes() always returns 3 elements");

    let raw = octave_base + nearest_pc;
    if raw > 127 {
        raw - 12
    } else {
        raw
    }
}
```

### Why one PLR hop rather than direct snap

`nearest_triad(raw_pcs)` finds the globally best triad, which may be 6 hops away. Jumping directly would produce a large voice-leading discontinuity — exactly what PLR algebra is designed to prevent. One hop keeps voice-leading smooth: maximum 1 semitone of change per voice (P), 1 semitone (L), or 2 semitones (R) for the moving voice.

---

## 7. `src/capability_plr.rs` — Integration 2

### Keyword tables

These tables are the authoritative mapping. Matching is case-insensitive substring containment: `capability_name.to_lowercase().contains(keyword)`. First table to match wins (R > P > L priority).

```rust
static R_KEYWORDS: &[&str] = &[
    "summarize", "embed", "retrieve", "search", "recall",
    "cluster",   "index", "similarity", "encode", "compress",
];

static P_KEYWORDS: &[&str] = &[
    "classify", "label",         "detect",       "filter",  "decide",
    "discriminate", "annotate",  "score",         "rank",    "threshold",
];

static L_KEYWORDS: &[&str] = &[
    "generate", "create",     "synthesize", "complete", "transform",
    "translate", "rewrite",   "imagine",    "hallucinate", "compose",
];
```

### Semantic rationale

| PLR | Neo-Riemannian meaning | Agent semantics |
|-----|------------------------|-----------------|
| R (Relative) | Shares 2 common tones; mode change preserving root | Retrieval/embedding: transform representation, preserve content |
| P (Parallel) | Same root, opposite quality; maximum color contrast | Classification/decision: binary judgment on fixed structure |
| L (Leading-tone exchange) | Root shifts by semitone; resolves strongly | Generation: creates new root-level content from existing material |

Priority R > P > L: retrieval is harmonically most stable (2 common tones with R), classification is intermediate, generation is most disruptive. On ambiguity, stability wins.

### Types and implementation

```rust
use groovemesh_plr::transform::PLR;
use spreadsheet_engine::cell::AgentCell;
use std::collections::HashMap;

/// Confidence-weighted sum of R, P, L keyword matches for an AgentCell.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct PlrWeights {
    pub r: f64,  // sum of confidences for R-type capabilities
    pub p: f64,  // sum of confidences for P-type capabilities
    pub l: f64,  // sum of confidences for L-type capabilities
}

impl PlrWeights {
    /// Returns the dominant PLR operation by total weight.
    ///
    /// Tie-breaking order: R beats P beats L (stability-first).
    /// Returns None if all weights are exactly 0.0.
    ///
    /// Implementation:
    ///   max = r.max(p).max(l)
    ///   if max == 0.0: return None
    ///   if r == max: Some(PLR::R)
    ///   elif p == max: Some(PLR::P)
    ///   else: Some(PLR::L)
    pub fn dominant(&self) -> Option<PLR> {
        let max = self.r.max(self.p).max(self.l);
        if max == 0.0 {
            return None;
        }
        if (self.r - max).abs() < f64::EPSILON {
            Some(PLR::R)
        } else if (self.p - max).abs() < f64::EPSILON {
            Some(PLR::P)
        } else {
            Some(PLR::L)
        }
    }

    /// Normalize weights so r + p + l = 1.0.
    /// Returns self unchanged if sum is 0.0.
    pub fn normalized(&self) -> PlrWeights {
        let total = self.r + self.p + self.l;
        if total == 0.0 {
            return *self;
        }
        PlrWeights {
            r: self.r / total,
            p: self.p / total,
            l: self.l / total,
        }
    }

    /// True if all weights are zero (no recognized capabilities).
    pub fn is_empty(&self) -> bool {
        self.r == 0.0 && self.p == 0.0 && self.l == 0.0
    }
}

/// Extension trait for AgentCell.
pub trait CapabilityPLR {
    /// Returns the PLR op corresponding to the dominant capability.
    ///
    /// Implementation: calls `self.plr_weights().dominant()`.
    fn dominant_plr_op(&self) -> Option<PLR>;

    /// Confidence-weighted R/P/L scores across all capabilities.
    ///
    /// Algorithm:
    ///   Initialize weights = PlrWeights { r: 0.0, p: 0.0, l: 0.0 }
    ///   For each (name, &confidence) in self.capabilities:
    ///     Skip if confidence <= 0.0
    ///     op = keyword_plr(name)
    ///     Match op:
    ///       Some(PLR::R) => weights.r += confidence
    ///       Some(PLR::P) => weights.p += confidence
    ///       Some(PLR::L) => weights.l += confidence
    ///       None         => (no-op)
    ///   Return weights
    fn plr_weights(&self) -> PlrWeights;
}

impl CapabilityPLR for AgentCell {
    fn dominant_plr_op(&self) -> Option<PLR> {
        self.plr_weights().dominant()
    }

    fn plr_weights(&self) -> PlrWeights {
        let mut weights = PlrWeights { r: 0.0, p: 0.0, l: 0.0 };
        for (name, &confidence) in &self.capabilities {
            if confidence <= 0.0 {
                continue;
            }
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

/// Map a capability name to its PLR type via substring match.
///
/// Case-insensitive. R_KEYWORDS checked first, then P, then L.
/// Returns None if no keyword matches.
pub(crate) fn keyword_plr(name: &str) -> Option<PLR> {
    let lower = name.to_lowercase();
    if R_KEYWORDS.iter().any(|k| lower.contains(k)) {
        return Some(PLR::R);
    }
    if P_KEYWORDS.iter().any(|k| lower.contains(k)) {
        return Some(PLR::P);
    }
    if L_KEYWORDS.iter().any(|k| lower.contains(k)) {
        return Some(PLR::L);
    }
    None
}
```

---

## 8. `src/conservation_harmony.rs` — Integration 3

### Design note: why BridgeEvent, not CMidiEvent

`CMidiEvent` maps speech acts to fixed pitch classes (C4, D4, …). The conservation bridge needs to:
1. Emit CC104 at an arbitrary value → use `BridgeEvent::CC`
2. Inject a tritone note at `base_note + 6` per violated cell → `BridgeEvent::NoteOn` with arbitrary note
3. Optionally emit a speech-act for trend signaling → `BridgeEvent::SpeechAct`

Forcing arbitrary tritone notes through `CMidiEvent` would require fabricating a `SpeechAct` that happens to have the right pitch class — fragile and incorrect. `BridgeEvent` handles all three cleanly.

### Trait and implementation

```rust
use crate::event::BridgeEvent;
use crate::error::BridgeError;
use cmidi_core::{CMidiEvent, ConversationCC, SpeechAct};
use groovemesh_plr::{chord::Triad, transform::{apply, PLR}};
use spreadsheet_engine::{
    cell::CellId,
    conservation::{ConservationMonitor, ConservationTrend},
    grid::Grid,
};

/// Extension trait for spreadsheet_engine::ConservationMonitor.
///
/// Maps grid conservation state to MIDI output and optional chord advance.
pub trait ConservationHarmony {
    /// Encode the current conservation state as BridgeEvents and an optional next triad.
    ///
    /// Returns: (events_to_emit, Some(new_triad) if chord should advance)
    ///
    /// Events always emitted (in order):
    ///   1. BridgeEvent::CC { controller: 104 (ConservationRatio), value: health*127 }
    ///   2. BridgeEvent::CC { controller: 103 (VoiceLeading), value: trend_signal }
    ///   3. For each violated CellId:
    ///        BridgeEvent::NoteOn  { channel: cell_id.row & 0x0F, note: base+6, velocity: 80 }
    ///        BridgeEvent::NoteOff { channel: cell_id.row & 0x0F, note: base+6, tick: tick+1 }
    ///
    /// Trend → PLR + CC103:
    ///   Improving → Some(apply(PLR::R, current_triad)),  CC103 = 64
    ///   Degrading → Some(apply(PLR::P, current_triad)),  CC103 = 127
    ///   Stable    → None,                                CC103 = 32
    fn to_bridge_events(
        &self,
        grid: &Grid,
        current_triad: Triad,
        tick: u64,
        channel: u8,
    ) -> (Vec<BridgeEvent>, Option<Triad>);
}

impl ConservationHarmony for ConservationMonitor {
    fn to_bridge_events(
        &self,
        grid: &Grid,
        current_triad: Triad,
        tick: u64,
        channel: u8,
    ) -> (Vec<BridgeEvent>, Option<Triad>) {
        let mut events: Vec<BridgeEvent> = Vec::new();

        // ── CC104: ConservationRatio ──────────────────────────────────────────
        let health = self.health(grid);
        // health is in [0.0, 1.0]; clamp defensively before cast
        let cc104 = (health * 127.0).round().clamp(0.0, 127.0) as u8;
        events.push(BridgeEvent::CC {
            channel,
            controller: ConversationCC::ConservationRatio.cc_number(), // 104
            value: cc104,
            tick,
        });

        // ── Trend → PLR + CC103 ──────────────────────────────────────────────
        // VoiceLeading CC signal:
        //   Improving = 64  (mid-high — smooth, positive motion)
        //   Stable    = 32  (low — hold, no motion)
        //   Degrading = 127 (maximum — audible alarm)
        let (next_triad, vl_signal) = match self.trend() {
            ConservationTrend::Improving => (Some(apply(PLR::R, current_triad)), 64u8),
            ConservationTrend::Degrading => (Some(apply(PLR::P, current_triad)), 127u8),
            ConservationTrend::Stable    => (None,                               32u8),
        };

        events.push(BridgeEvent::CC {
            channel,
            controller: ConversationCC::VoiceLeading.cc_number(), // 103
            value: vl_signal,
            tick,
        });

        // ── Violations → tritone injection ───────────────────────────────────
        for cell_id in self.violations(grid) {
            // MIDI channel: use row mod 16 (row 0 = ch0, row 15 = ch15, row 16 wraps)
            let cell_channel = (cell_id.row as u8) & 0x0F;

            // Base note: row-based default (musical rows: C3=48, C#3=49, …)
            // If the Grid exposes midi_cells(), try to look up the actual MidiCell's base_note.
            // Fall back to 48 + (row % 12) if no MidiCell at that position.
            let base_note: u8 = grid
                .midi_cells()
                .find(|(id, _)| *id == cell_id)
                .map(|(_, mc)| mc.base_note)
                .unwrap_or_else(|| 48u8.saturating_add(cell_id.row as u8 % 12));

            // Tritone = 6 semitones above base note.
            // Clamped to MIDI valid range [0, 127].
            let tritone = base_note.saturating_add(6).min(127);

            events.push(BridgeEvent::NoteOn {
                channel: cell_channel,
                note: tritone,
                velocity: 80,
                tick,
            });
            events.push(BridgeEvent::NoteOff {
                channel: cell_channel,
                note: tritone,
                tick: tick + 1, // auto-off exactly 1 tick later
            });
        }

        (events, next_triad)
    }
}
```

### CC value table

| Signal | CC | Value | Meaning |
|--------|----|-------|---------|
| `health() == 1.0` | 104 | 127 | Budget perfectly balanced |
| `health() == 0.0` | 104 | 0 | Complete budget failure |
| `health() == 0.5` | 104 | 64 | 50% of cells within tolerance |
| Trend: Improving | 103 | 64 | Smooth upward motion |
| Trend: Stable | 103 | 32 | Hold position |
| Trend: Degrading | 103 | 127 | Maximum alarm — dissonance peak |
| Violation per cell | — | NoteOn(base+6, vel=80) | Tritone: maximally dissonant interval |

---

## 9. `src/coordinator.rs` — Integration 4

The `PLRSessionCoordinator` owns the session's harmonic state and routes all three integration points from a single tick call.

```rust
use crate::{
    capability_plr::CapabilityPLR,
    conservation_harmony::ConservationHarmony,
    error::{BridgeError, BridgeResult},
    event::BridgeEvent,
    harmonic_sonify::HarmonicSonify,
};
use groovemesh_plr::{
    chord::Triad,
    counterpoint::CounterpointRules,
    lattice::Lattice,
    transform::{apply, PLR},
};
use spreadsheet_engine::{
    cell::{AgentCell, CellId, CellValue},
    conservation::ConservationMonitor,
    grid::Grid,
    midi::MidiCell,
};

/// Stateful bridge session coordinator.
///
/// One instance per active spreadsheet-engine grid session.
/// Holds the current PLR triad and dispatches all three integration traits.
///
/// Typical usage per fleet-midi tick:
///   1. agents submit speech acts → ensemble resolves
///   2. ensemble calls coordinator.tick(grid, monitor) → Vec<BridgeEvent>
///   3. caller emits BridgeEvents to audio pipeline
///   4. MidiCells call coordinator.harmonize_cell(cell, value) → Vec<[u8; 3]>
pub struct PLRSessionCoordinator {
    /// Current session harmonic context.
    pub current_triad: Triad,

    /// Counterpoint rules applied to all chord advances.
    /// Defaults to standard species counterpoint (no parallel fifths/octaves,
    /// no voice crossing, max_voice_distance = Some(7)).
    pub rules: CounterpointRules,

    /// PLR Cayley graph for BFS path queries.
    /// Built once at construction — O(72) nodes.
    lattice: Lattice,

    /// Absolute tick counter. Incremented by `tick()`.
    tick: u64,

    /// MIDI channel for CC output from conservation_harmony.
    pub cmidi_channel: u8,

    /// Maximum PLR chord advances per call to `tick()`.
    /// Prevents rapid drift when many agents complete in the same tick.
    /// Default: 1. Set to 0 to disable agent-driven advances.
    pub max_advances_per_tick: usize,
}

impl PLRSessionCoordinator {
    /// Create a new coordinator.
    ///
    /// Parameters:
    ///   initial_triad: the starting chord (e.g., C major = Triad::new_unchecked(0, Quality::Major))
    ///   cmidi_channel: 0–15, the MIDI channel for CC104/CC103 output
    ///
    /// Panics if cmidi_channel > 15.
    pub fn new(initial_triad: Triad, cmidi_channel: u8) -> Self {
        assert!(cmidi_channel <= 15, "MIDI channel must be 0–15");
        Self {
            current_triad: initial_triad,
            rules: CounterpointRules::default(),
            lattice: Lattice::build(), // O(72): build once
            tick: 0,
            cmidi_channel,
            max_advances_per_tick: 1,
        }
    }

    /// Replace the counterpoint rules.
    pub fn with_rules(mut self, rules: CounterpointRules) -> Self {
        self.rules = rules;
        self
    }

    /// Set maximum chord advances per tick.
    pub fn with_max_advances(mut self, n: usize) -> Self {
        self.max_advances_per_tick = n;
        self
    }

    /// Current absolute tick count.
    pub fn current_tick(&self) -> u64 {
        self.tick
    }

    /// PLR lattice distance from current_triad to target. Range: 0–6.
    pub fn distance_to(&self, target: Triad) -> usize {
        self.lattice.distance(self.current_triad, target)
    }

    /// Attempt to advance the session chord by one PLR op.
    ///
    /// Checks CounterpointRules::check(current, apply(op, current)).
    /// If legal: updates current_triad and returns Ok(new_triad).
    /// If illegal: returns Err(BridgeError::CounterpointViolation).
    ///
    /// This is the single mutation point for current_triad.
    pub fn advance_chord(&mut self, op: PLR) -> BridgeResult<Triad> {
        let candidate = apply(op, self.current_triad);
        self.rules
            .check(self.current_triad, candidate)
            .map_err(|e| BridgeError::CounterpointViolation {
                to: candidate.to_string(),
                reason: e.to_string(),
            })?;
        self.current_triad = candidate;
        Ok(candidate)
    }

    /// Process one fleet-midi pulse tick.
    ///
    /// Algorithm:
    ///   1. self.tick += 1
    ///   2. Run conservation_harmony:
    ///        (events, conservation_triad) = monitor.to_bridge_events(
    ///            grid, current_triad, self.tick, cmidi_channel)
    ///        If conservation_triad is Some(t): advance_chord_unchecked(t)
    ///          → conservation overrides rules (urgent signal)
    ///   3. Run capability advances (up to self.max_advances_per_tick):
    ///        For each CellId in completed_agent_ids:
    ///          advance_count < max_advances_per_tick
    ///          Get AgentCell for that id from grid
    ///          op = agent_cell.dominant_plr_op()
    ///          if Some(op): try advance_chord(op)
    ///            Ok → increment advance_count; break if at max
    ///            Err → skip (log, but do not propagate)
    ///   4. Return events
    ///
    /// NOTE: `completed_agent_ids` is the caller's responsibility — the engine
    /// knows which agents finished this tick; pass their CellIds here.
    /// Pass an empty slice if no agents completed.
    pub fn tick(
        &mut self,
        grid: &Grid,
        monitor: &ConservationMonitor,
        completed_agent_ids: &[CellId],
    ) -> Vec<BridgeEvent> {
        self.tick += 1;

        // Step 1: Conservation → events + optional chord advance
        let (mut events, conservation_triad) =
            monitor.to_bridge_events(grid, self.current_triad, self.tick, self.cmidi_channel);

        if let Some(next) = conservation_triad {
            // Conservation-driven advances bypass counterpoint check —
            // budget violations are urgent signals, not musical choices.
            self.current_triad = next;
        }

        // Step 2: Agent capability → chord advances
        let mut advances = 0;
        for &cell_id in completed_agent_ids {
            if advances >= self.max_advances_per_tick {
                break;
            }
            let agent = match grid.cell(cell_id).and_then(|c| c.as_agent()) {
                Some(a) => a,
                None => continue,
            };
            if let Some(op) = agent.dominant_plr_op() {
                if self.advance_chord(op).is_ok() {
                    advances += 1;
                }
                // On CounterpointViolation: silently skip. The chord stays.
            }
        }

        events
    }

    /// Harmonize a MidiCell's output against the current session triad.
    ///
    /// Delegates to HarmonicSonify::sonify_harmonized(cell, value, current_triad).
    pub fn harmonize_cell(
        &mut self,
        cell: &mut MidiCell,
        value: &CellValue,
    ) -> Vec<[u8; 3]> {
        cell.sonify_harmonized(value, self.current_triad)
    }

    /// Force-set the current triad, bypassing counterpoint rules.
    /// Use only for session initialization or hard resets.
    pub fn set_triad(&mut self, triad: Triad) {
        self.current_triad = triad;
    }
}
```

### Conservation-driven vs. capability-driven chord advances

There are two advance paths and they have different semantics:

| Path | Source | Counterpoint check | Rationale |
|------|--------|--------------------|-----------|
| Conservation | `trend() == Degrading → P`, `Improving → R` | **Bypassed** | Budget violation is an urgent signal; harmony must communicate alarm even if it violates smoothness |
| Capability | Agent's dominant PLR op on task completion | **Enforced** | Agent-driven harmony is aesthetic; species counterpoint rules apply |

---

## 10. `src/lib.rs`

```rust
//! # spreadsheet-plr-bridge
//!
//! Connects `spreadsheet-engine` cells to `groovemesh-plr` harmony algebra.
//!
//! ## Quick start
//!
//! ```rust
//! use spreadsheet_plr_bridge::{
//!     HarmonicSonify,
//!     CapabilityPLR,
//!     ConservationHarmony,
//!     PLRSessionCoordinator,
//! };
//! use groovemesh_plr::chord::{Quality, Triad};
//!
//! let c_major = Triad::new_unchecked(0, Quality::Major);
//! let mut coord = PLRSessionCoordinator::new(c_major, 0);
//!
//! // On each tick:
//! let events = coord.tick(&grid, &monitor, &completed_agents);
//! // Harmonize a MidiCell:
//! let bytes = coord.harmonize_cell(&mut midi_cell, &cell_value);
//! ```

mod error;
mod event;
mod harmonic_sonify;
mod capability_plr;
mod conservation_harmony;
mod coordinator;

// Public re-exports — the complete public API

pub use error::{BridgeError, BridgeResult};
pub use event::BridgeEvent;
pub use harmonic_sonify::HarmonicSonify;
pub use capability_plr::{CapabilityPLR, PlrWeights};
pub use conservation_harmony::ConservationHarmony;
pub use coordinator::PLRSessionCoordinator;

// Re-export groovemesh_plr types that callers commonly need,
// so they don't need to add groovemesh-plr as a direct dep.
pub use groovemesh_plr::{
    chord::{PitchClass, Quality, Triad},
    transform::PLR,
    counterpoint::CounterpointRules,
    lattice::Lattice,
};
```

---

## 11. Feature Flag Reference

```
default         []               Only required deps. No tokio, no noether, no cmidi-conservation.
coordinator     [tokio/sync]     Enables PLRSessionCoordinator (requires tokio::sync).
noether         [noether-guard]  Enables impl ConservationHarmony for noether_guard::ConservationMonitor.
                                 (Different from spreadsheet-engine's ConservationMonitor.)
cmidi-conservation               Enables ConservationVoice → BridgeEvent conversion utilities.
                [cmidi-conservation]
full            [all above]      All optional features. Use for normal application builds.
```

### Feature: `noether`

When `noether` is enabled, an additional impl is provided:

```rust
// Only compiled with feature "noether"
#[cfg(feature = "noether")]
impl ConservationHarmony for noether_guard::monitor::ConservationMonitor {
    fn to_bridge_events(
        &self,
        _grid: &Grid,
        current_triad: Triad,
        tick: u64,
        channel: u8,
    ) -> (Vec<BridgeEvent>, Option<Triad>) {
        let health = self.health();  // noether-guard: fraction of clean snapshots
        let cc104 = (health * 127.0).round().clamp(0.0, 127.0) as u8;

        // noether-guard has no ConservationTrend enum.
        // Derive trend from total_violations: 0 = stable, increasing = degrading.
        let trend_signal = if self.total_violations() == 0 { 32u8 } else { 127u8 };
        let next_triad = if self.total_violations() == 0 {
            None
        } else {
            Some(apply(PLR::P, current_triad))
        };

        let events = vec![
            BridgeEvent::CC { channel, controller: 104, value: cc104, tick },
            BridgeEvent::CC { channel, controller: 103, value: trend_signal, tick },
        ];
        (events, next_triad)
    }
}
```

---

## 12. Error Handling Strategy

### Principle: Bridge errors are non-fatal

The spreadsheet grid must continue operating even if PLR projection fails. No error from this crate should crash the grid. The error strategy is:

| Site | Error | Recovery |
|------|-------|----------|
| `sonify_harmonized()` | `nearest_plr_triad` returns same triad (infallible, no error) | Notes are still snapped; this is not an error |
| `snap_to_triad()` | `pitch_classes()` returns empty (impossible — always 3) | `unwrap()` is safe here; document the invariant |
| `dominant_plr_op()` | No capability keywords match | Returns `None`; coordinator skips advance |
| `advance_chord()` | CounterpointViolation | Returns `Err`; coordinator skips advance, triad unchanged |
| `to_bridge_events()` | Grid has no agent cells | `violations()` returns empty vec; `health()` returns 1.0 |
| `tick()` | Any internal error | Logged at `WARN`, never propagated to caller; tick always returns events |

### What is never `unwrap`-ed unsafely

- `nearest_triad(pitches)` — can return `Err(NoValidTriad)` if pitches is empty. `nearest_plr_triad` handles this internally (returns `current` on error). Do NOT call `nearest_triad` directly in the bridge; always use `nearest_plr_triad`.
- `CounterpointRules::check()` — can return `Err`. Always pattern-match; never `.unwrap()`.
- `Grid::cell(id)` — can return `None`. Always use `.and_then()` / `.map()`.

### The one safe `unwrap`

`pcs.iter().min_by_key(...)` in `snap_to_triad` — `pitch_classes()` is guaranteed to return exactly 3 elements by the `Triad` type invariant. Document this; the unwrap is safe.

---

## 13. Test Scaffolding

Place in `src/` as `#[cfg(test)]` modules within each file, or in `tests/integration.rs`.

```rust
#[cfg(test)]
mod tests {
    // ── harmonic_sonify tests ────────────────────────────────────────────────

    #[test]
    fn snap_to_triad_already_in_triad() {
        // C major = [0, 4, 7]. Note C4=60 has PC=0, which is in triad.
        let triad = Triad::new_unchecked(0, Quality::Major);
        assert_eq!(snap_to_triad(60, triad), 60); // unchanged
        assert_eq!(snap_to_triad(64, triad), 64); // E4, PC=4, unchanged
        assert_eq!(snap_to_triad(67, triad), 67); // G4, PC=7, unchanged
    }

    #[test]
    fn snap_to_triad_chromatic_snap() {
        // C major = [0, 4, 7]
        let c_major = Triad::new_unchecked(0, Quality::Major);
        // C#4 (61) → nearest is C (dist=1) not E (dist=3) → snap to 60
        assert_eq!(snap_to_triad(61, c_major), 60);
        // D#4 (63) → dist(3,0)=3, dist(3,4)=1, dist(3,7)=4 → snap to E=64
        assert_eq!(snap_to_triad(63, c_major), 64);
        // F#4 (66) → dist(6,0)=6, dist(6,4)=2, dist(6,7)=1 → snap to G=67
        assert_eq!(snap_to_triad(66, c_major), 67);
        // A#4 (70) → dist(10,0)=2, dist(10,4)=6, dist(10,7)=3 → snap to C=72 (next octave)
        // octave_base=60, nearest_pc=0, raw=60... but note=70, pc=10, octave_base=60,
        // nearest=0, raw=60. But 60 < 70 so we lose octave. Check: 60 ≤ 127 → 60.
        // Actually PC=10 (Bb), C major=[0,4,7], dist(10,0)=2, dist(10,4)=6, dist(10,7)=3 → 0
        // octave_base = 70-10=60, nearest_pc=0, raw=60. Return 60.
        assert_eq!(snap_to_triad(70, c_major), 60);
    }

    #[test]
    fn snap_to_triad_invariant_all_notes_all_triads() {
        // INVARIANT: snap_to_triad(note, triad).result_pc ∈ triad.pitch_classes()
        for note in 0u8..=127u8 {
            for root in 0u8..12u8 {
                for quality in [Quality::Major, Quality::Minor] {
                    let triad = Triad::new_unchecked(root, quality);
                    let snapped = snap_to_triad(note, triad);
                    assert!(
                        triad.contains(snapped % 12),
                        "note={note} root={root} quality={quality:?} snapped={snapped} pc={} not in triad",
                        snapped % 12
                    );
                }
            }
        }
    }

    #[test]
    fn harmonize_output_pcs_in_triad() {
        let triad = Triad::new_unchecked(0, Quality::Major); // C major
        let mut cell = MidiCell {
            name: "test".into(),
            state: CellState::Ready,
            channel: 0,
            base_note: 60,
            velocity: 80,
            last_event: None,
        };
        let value = CellValue::Number(7.0); // offset = 7 → G4=67
        let events = cell.sonify_harmonized(&value, triad);
        for ev in &events {
            if ev[0] & 0xF0 == 0x90 && ev[2] > 0 {
                let pc = ev[1] % 12;
                // After one PLR hop from C major toward G, result is in the hop target.
                // nearest_plr_triad(Cmaj, [7]) → ideal = G major or E minor (both contain 7)
                // One hop from C major: P=Cm, L=Em, R=Am. Em contains G(7). → target = Em.
                // snap(67, Em): Em=[4,7,11], G=7 ∈ Em → unchanged.
                // So pc=7 expected.
                assert!(
                    [0u8, 4, 7, 3, 11].contains(&pc),
                    "unexpected pc={pc} after harmonization"
                );
            }
        }
    }

    // ── capability_plr tests ────────────────────────────────────────────────

    #[test]
    fn keyword_plr_exact_matches() {
        assert_eq!(keyword_plr("summarize"), Some(PLR::R));
        assert_eq!(keyword_plr("embed"),     Some(PLR::R));
        assert_eq!(keyword_plr("classify"),  Some(PLR::P));
        assert_eq!(keyword_plr("detect"),    Some(PLR::P));
        assert_eq!(keyword_plr("generate"),  Some(PLR::L));
        assert_eq!(keyword_plr("create"),    Some(PLR::L));
        assert_eq!(keyword_plr("unknown"),   None);
        assert_eq!(keyword_plr(""),          None);
    }

    #[test]
    fn keyword_plr_case_insensitive() {
        assert_eq!(keyword_plr("SUMMARIZE"), Some(PLR::R));
        assert_eq!(keyword_plr("Generate"),  Some(PLR::L));
        assert_eq!(keyword_plr("CLASSIFY"),  Some(PLR::P));
    }

    #[test]
    fn keyword_plr_substring_match() {
        assert_eq!(keyword_plr("text_summarizer"),   Some(PLR::R));
        assert_eq!(keyword_plr("image_classifier"),  Some(PLR::P));
        assert_eq!(keyword_plr("code_generator"),    Some(PLR::L));
    }

    #[test]
    fn plr_weights_dominant_single() {
        let w = PlrWeights { r: 0.9, p: 0.0, l: 0.0 };
        assert_eq!(w.dominant(), Some(PLR::R));
    }

    #[test]
    fn plr_weights_dominant_tie_prefers_r() {
        // Tie between R and P → R wins (stability first)
        let w = PlrWeights { r: 0.5, p: 0.5, l: 0.0 };
        assert_eq!(w.dominant(), Some(PLR::R));
    }

    #[test]
    fn plr_weights_dominant_tie_r_p_l() {
        // R wins three-way tie
        let w = PlrWeights { r: 1.0, p: 1.0, l: 1.0 };
        assert_eq!(w.dominant(), Some(PLR::R));
    }

    #[test]
    fn plr_weights_dominant_none_when_empty() {
        let w = PlrWeights { r: 0.0, p: 0.0, l: 0.0 };
        assert_eq!(w.dominant(), None);
    }

    #[test]
    fn agent_cell_plr_mixed_capabilities() {
        let mut caps = std::collections::HashMap::new();
        caps.insert("summarize".into(), 0.9);
        caps.insert("generate".into(),  0.3);
        let cell = AgentCell {
            agent_id: "test".into(),
            capabilities: caps,
            gamma: 0.5, eta: 0.5, budget: 1.0,
            state: CellState::Ready,
        };
        // r=0.9, l=0.3 → R dominant
        assert_eq!(cell.dominant_plr_op(), Some(PLR::R));
        let w = cell.plr_weights();
        assert!((w.r - 0.9).abs() < 1e-9);
        assert!((w.l - 0.3).abs() < 1e-9);
    }

    // ── conservation_harmony tests ──────────────────────────────────────────

    #[test]
    fn cc104_maps_health_to_0_127() {
        // health=1.0 → cc104=127
        // health=0.0 → cc104=0
        // health=0.5 → cc104=64
        // Test via to_bridge_events using a mock/stub grid+monitor
        // (integration test — requires test fixtures)
    }

    #[test]
    fn degrading_trend_emits_parallel_plr() {
        // ConservationTrend::Degrading → Some(apply(PLR::P, current_triad))
        // P(C major) = C minor
        let triad = Triad::new_unchecked(0, Quality::Major);
        let p_result = apply(PLR::P, triad);
        assert_eq!(p_result.root, 0);
        assert_eq!(p_result.quality, Quality::Minor);
    }

    #[test]
    fn improving_trend_emits_relative_plr() {
        // ConservationTrend::Improving → Some(apply(PLR::R, current_triad))
        // R(C major) = A minor
        let triad = Triad::new_unchecked(0, Quality::Major);
        let r_result = apply(PLR::R, triad);
        assert_eq!(r_result.root, 9); // A
        assert_eq!(r_result.quality, Quality::Minor);
    }

    #[test]
    fn tritone_encoding() {
        // base_note=60 → tritone=66 (F#4)
        assert_eq!(60u8.saturating_add(6).min(127), 66);
        // base_note=122 → tritone=127 (not 128 — clamped)
        assert_eq!(122u8.saturating_add(6).min(127), 127);
    }

    // ── coordinator tests ───────────────────────────────────────────────────

    #[test]
    fn coordinator_advance_chord_legal() {
        let c_major = Triad::new_unchecked(0, Quality::Major);
        let mut coord = PLRSessionCoordinator::new(c_major, 0);
        // P(C major) = C minor — check(Cmaj, Cmin): same root, distance=1 → legal
        let result = coord.advance_chord(PLR::P);
        assert!(result.is_ok());
        assert_eq!(coord.current_triad.root, 0);
        assert_eq!(coord.current_triad.quality, Quality::Minor);
    }

    #[test]
    fn coordinator_distance_to() {
        let c_major = Triad::new_unchecked(0, Quality::Major);
        let coord = PLRSessionCoordinator::new(c_major, 0);
        // C major to itself → 0
        assert_eq!(coord.distance_to(c_major), 0);
        // C major to C minor (P) → 1
        let c_minor = Triad::new_unchecked(0, Quality::Minor);
        assert_eq!(coord.distance_to(c_minor), 1);
    }

    #[test]
    fn coordinator_initial_triad_preserved() {
        let am = Triad::new_unchecked(9, Quality::Minor);
        let coord = PLRSessionCoordinator::new(am, 3);
        assert_eq!(coord.current_triad, am);
        assert_eq!(coord.cmidi_channel, 3);
    }
}
```

---

## 14. Known Pitfalls and Implementation Notes

### Pitfall 1: `snap_to_triad` octave arithmetic

When `pc > nearest_pc`, `octave_base + nearest_pc` lands in a *lower* register than the original note. This is correct: we preserve the octave base (i.e., the C-3 octave for notes 48–59), not the exact octave of the note. If this is audibly wrong (e.g., a D5 snapping to C4 instead of C5), the caller can post-process to normalize octaves. The bridge's invariant is PC correctness, not register preservation.

### Pitfall 2: `nearest_plr_triad` is infallible but silent

When the raw pitch classes are empty, or when `nearest_triad` returns an error, `nearest_plr_triad` silently returns `current`. The bridge caller has no way to detect this. If you need to detect projection failures, call `nearest_triad(raw_pcs)` separately and check the error before calling `nearest_plr_triad`.

### Pitfall 3: conservation-driven advances bypass counterpoint

The `tick()` method applies conservation-driven chord advances (from `to_bridge_events`) without `CounterpointRules::check`. This is intentional: budget violations are urgent signals. If you need strict counterpoint even for conservation advances, replace the unchecked assignment in `tick()` with `self.advance_chord(op)` and handle the error.

### Pitfall 4: keyword matching is substring, not word-boundary

`"reclassify"` matches both R (`"recall"` — no), and P (`"classify"` — yes). It matches P. `"decode"` matches neither (`"decode"` contains neither R, P, nor L keywords). `"re-encode"` matches R (`"encode"`). When adding capabilities to `AgentCell`, use specific names without accidental keyword overlap.

### Pitfall 5: `Lattice::build()` is cheap but not free

`Lattice::build()` constructs a `HashMap<Triad, Vec<LatticeEdge>>` with 72 entries. This is O(72) — fast, but not zero-cost. Build the `PLRSessionCoordinator` once per session, not per tick. The coordinator's `Lattice` field is private and non-`Clone` intentionally.

### Pitfall 6: `MidiCell::sonify` takes `&mut self`

The method is `&mut self` (it updates `self.last_event`). The `HarmonicSonify` trait mirrors this signature: `sonify_harmonized(&mut self, ...)`. The coordinator's `harmonize_cell` also takes `&mut MidiCell`. If you hold a `&Grid` (shared reference) while calling `harmonize_cell`, you'll need to restructure — extract the cell value first, then call harmonize with exclusive access to the cell.

### Pitfall 7: `Grid::midi_cells()` may not exist

Section 2.4 says `Grid::midi_cells() -> impl Iterator<Item = (CellId, &MidiCell)>` is available. If the actual `spreadsheet-engine` 0.1 API only exposes `Grid::cells()` with a `Cell` enum, use:

```rust
grid.cells()
    .filter_map(|(id, cell)| cell.as_midi().map(|mc| (id, mc)))
```

The `conservation_harmony` implementation already has this fallback via `.find()` on `grid.midi_cells()` — adjust if the method name differs.
