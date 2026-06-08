# GrooveMesh Library Specification

Rust API for `groovemesh-plr`, `groovemesh-session`, `groovemesh-midi`.
All crates are `no_std`-compatible except `groovemesh-session` (requires `std::collections`).

---

## Crate: `groovemesh-plr`

Wraps `flux-algebra-rs` and adds the precomputed lattice and nearest-triad table.

### Structs

```rust
// Re-export from flux-algebra-rs
pub use flux_algebra_rs::groups::{Triad, PlrGroup};

/// The three PLR generators.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PLROp {
    P,  // Parallel
    L,  // Leading-tone exchange
    R,  // Relative
}

impl PLROp {
    pub fn apply(self, t: Triad) -> Triad;
    pub fn inverse(self) -> PLROp;  // All ops are involutions: inverse == self
    pub fn name(self) -> &'static str;
}

/// A transition between two triads via a PLR operation.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct PLRTransition {
    pub from: Triad,
    pub to: Triad,
    pub op: PLROp,
    pub voice_leading_cost: f32,  // total semitone motion
}

/// The current harmonic state of a session.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct ChordState {
    pub triad: Triad,
    pub tick: u64,  // MIDI tick when this chord was established
}

impl ChordState {
    pub fn new(triad: Triad, tick: u64) -> Self;
    pub fn apply(&self, op: PLROp, tick: u64) -> (ChordState, PLRTransition);
}

/// A sequence of PLR operations forming a path through the Tonnetz.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VoiceLeadingPath {
    pub start: Triad,
    pub steps: Vec<(PLROp, Triad)>,  // (operation, resulting triad)
}

impl VoiceLeadingPath {
    pub fn len(&self) -> usize;
    pub fn cost(&self) -> f32;  // total voice-leading cost of all steps
    pub fn end(&self) -> Triad;
}
```

### The PLR Lattice

```rust
/// Precomputed PLR graph over T₂₄.
/// Built once at startup; immutable thereafter.
pub struct PLRLattice {
    // Internal: [Triad; 24], adjacency [Triad; 3] per node (P, L, R neighbors)
    // Laid out as flat array for cache efficiency.
}

impl PLRLattice {
    /// Build the lattice. Called once at startup; O(24) time.
    pub fn build() -> PLRLattice;

    /// Apply a single PLR operation. O(1).
    pub fn step(&self, from: Triad, op: PLROp) -> PLRTransition;

    /// BFS shortest path between two triads. O(24) worst case (constant).
    pub fn shortest_path(&self, from: Triad, to: Triad) -> VoiceLeadingPath;

    /// All neighbors of a triad (P, L, R results). O(1).
    pub fn neighbors(&self, t: Triad) -> [(PLROp, Triad); 3];

    /// Diameter of the Tonnetz graph (precomputed = 6). O(1).
    pub fn diameter(&self) -> usize { 6 }
}
```

### Nearest-Triad Table

```rust
/// O(1) projection from arbitrary pitch classes to nearest triad.
/// Precomputed 4096-entry table (4 KB, fits in L1 cache).
pub struct NearestTriadTable {
    // internal: [u8; 4096] — index by 12-bit PC bitmask, value = triad index
}

impl NearestTriadTable {
    /// Build the table. O(4096 × 24) time at startup; called once.
    pub fn build() -> NearestTriadTable;

    /// Find nearest triad to a set of pitch classes. O(1).
    ///
    /// `pcs`: slice of pitch classes (values 0–11)
    pub fn nearest(&self, pcs: &[u8]) -> Triad;

    /// Voice-leading distance from pcs to a specific triad. O(1).
    pub fn distance(&self, pcs: &[u8], t: Triad) -> f32;

    /// Project a single note (0–127) onto the nearest PC in triad t. O(1).
    pub fn project_note(&self, note: u8, t: Triad) -> u8;
}
```

### Traits

```rust
/// Anything that can navigate the PLR lattice.
pub trait PLRNavigator {
    fn current_chord(&self) -> ChordState;
    fn navigate(&mut self, op: PLROp) -> PLRTransition;
    fn navigate_to(&mut self, target: Triad) -> VoiceLeadingPath;
}

/// Anything that can be projected onto a valid chord.
pub trait HarmonicProjection {
    /// Project input pitch classes onto the given triad. Returns corrected PCs.
    fn project(&self, pcs: &[u8], onto: Triad) -> Vec<u8>;
}
```

---

## Crate: `groovemesh-session`

Manages multi-client sessions, voice assignment, and clock sync.

### Type Aliases and Ids

```rust
use uuid::Uuid;

pub type SessionId = Uuid;  // v7 (time-ordered)
pub type ClientId  = Uuid;  // v7
pub type Tick      = u64;   // monotonic MIDI ticks (480 ticks/beat)
```

### Structs

```rust
/// A participant's voice in SATB counterpoint.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Voice {
    Soprano,  // MIDI 60–84
    Alto,     // MIDI 53–77
    Tenor,    // MIDI 48–72
    Bass,     // MIDI 40–64
}

impl Voice {
    pub fn midi_range(self) -> (u8, u8);
    pub fn midi_channel(self) -> u8;  // S=0, A=1, T=2, B=3
    pub fn clamp_note(self, note: u8) -> u8;
}

/// Per-client state within a session.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientInfo {
    pub id: ClientId,
    pub voice: Voice,
    pub display_name: String,
    pub joined_at: Tick,
}

/// Full state of one collaborative session.
#[derive(Debug)]
pub struct SessionState {
    pub id: SessionId,
    pub chord: ChordState,
    pub clients: HashMap<ClientId, ClientInfo>,
    pub tick: Tick,
    pub tempo_bpm: f32,
    pub ticks_per_beat: u32,  // default 480
}

impl SessionState {
    pub fn new(id: SessionId, initial_chord: Triad, tempo_bpm: f32) -> Self;
    pub fn add_client(&mut self, client_id: ClientId, name: &str) -> Result<Voice, SessionError>;
    pub fn remove_client(&mut self, client_id: ClientId) -> Option<ClientInfo>;
    pub fn voice_of(&self, client_id: ClientId) -> Option<Voice>;
    pub fn advance_tick(&mut self, ticks: u64);
    pub fn seconds_per_tick(&self) -> f64;
}

/// Snapshot of session state for sync broadcasts.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionSnapshot {
    pub session_id: SessionId,
    pub chord: ChordState,
    pub clients: Vec<ClientInfo>,
    pub tick: Tick,
    pub tempo_bpm: f32,
}

impl SessionSnapshot {
    pub fn from_state(state: &SessionState) -> Self;
}
```

### Session Manager

```rust
/// Manages the map of active sessions.
/// Thread-safe: sessions are stored behind tokio::sync::RwLock.
pub struct SessionManager {
    // internal: Arc<RwLock<HashMap<SessionId, SessionState>>>
    plr_lattice: Arc<PLRLattice>,
    nearest_triad: Arc<NearestTriadTable>,
}

impl SessionManager {
    pub fn new() -> Self;

    pub async fn create_session(
        &self,
        initial_chord: Triad,
        tempo_bpm: f32,
    ) -> SessionId;

    pub async fn join_session(
        &self,
        session_id: SessionId,
        client_id: ClientId,
        name: &str,
    ) -> Result<(Voice, SessionSnapshot), SessionError>;

    pub async fn leave_session(
        &self,
        session_id: SessionId,
        client_id: ClientId,
    ) -> Result<(), SessionError>;

    pub async fn apply_plr(
        &self,
        session_id: SessionId,
        op: PLROp,
    ) -> Result<PLRTransition, SessionError>;

    pub async fn navigate_to(
        &self,
        session_id: SessionId,
        target: Triad,
    ) -> Result<VoiceLeadingPath, SessionError>;

    pub async fn snapshot(&self, session_id: SessionId) -> Result<SessionSnapshot, SessionError>;
}
```

---

## Crate: `groovemesh-midi`

MIDI pipeline: validates, projects, assigns voice, checks counterpoint, emits bytes.

### Structs

```rust
/// A raw note event from a client before validation.
#[derive(Debug, Clone, Copy)]
pub struct RawNote {
    pub note: u8,
    pub velocity: u8,
    pub client_id: ClientId,
    pub tick: Tick,
}

/// A note that has passed range validation.
#[derive(Debug, Clone, Copy)]
pub struct ValidNote {
    pub note: u8,       // 0–127
    pub velocity: u8,   // 1–127
    pub pc: u8,         // note % 12
    pub octave: u8,     // note / 12
    pub client_id: ClientId,
    pub tick: Tick,
}

/// A note projected onto the current triad's pitch classes.
#[derive(Debug, Clone, Copy)]
pub struct ProjectedNote {
    pub note: u8,           // corrected MIDI note (may differ from input)
    pub pc: u8,             // pitch class (always in current triad's pcs)
    pub original_note: u8,  // input note before correction
    pub voice_hint: Voice,  // suggested voice based on register
    pub semitones_moved: u8, // voice-leading cost of this projection
}

/// A note with voice assignment confirmed.
#[derive(Debug, Clone, Copy)]
pub struct VoiceAssignment {
    pub voice: Voice,
    pub note: u8,
    pub velocity: u8,
    pub client_id: ClientId,
    pub tick: Tick,
}

impl VoiceAssignment {
    /// Standard MIDI Note On bytes.
    pub fn note_on(&self) -> [u8; 3];
    /// Standard MIDI Note Off bytes.
    pub fn note_off(&self) -> [u8; 3];
}
```

### Pipeline Functions

```rust
/// Stage 1: Validate raw input.
pub fn validate(raw: RawNote) -> Result<ValidNote, MidiError>;

/// Stage 2: Project onto current chord.
pub fn project(note: ValidNote, chord: &ChordState, table: &NearestTriadTable) -> ProjectedNote;

/// Stage 3: Assign to a voice.
pub fn assign_voice(
    note: ProjectedNote,
    registry: &HashMap<ClientId, Voice>,
    client_id: ClientId,
) -> VoiceAssignment;

/// Stage 4: Check counterpoint rules.
///
/// Returns the validated assignment, or a corrected assignment if a rule was violated.
/// Never returns Err — if a rule fires, it repairs the assignment in place.
pub fn check_counterpoint(
    incoming: VoiceAssignment,
    active: &[VoiceAssignment],  // currently sounding notes
) -> (VoiceAssignment, Vec<VoiceLeadingWarning>);

/// Stage 5: Emit MIDI bytes.
pub fn emit(assignment: &VoiceAssignment) -> [u8; 3];

/// Run all five stages in sequence.
pub fn process_note(
    raw: RawNote,
    state: &SessionState,
    active_notes: &[VoiceAssignment],
    table: &NearestTriadTable,
) -> Result<([u8; 3], Vec<VoiceLeadingWarning>), MidiError>;
```

### Counterpoint Rules

```rust
/// A violated counterpoint rule.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum VoiceLeadingWarning {
    ParallelFifths { voices: (Voice, Voice) },
    ParallelOctaves { voices: (Voice, Voice) },
    VoiceCrossing { upper: Voice, lower: Voice },
    AugmentedInterval { voice: Voice, interval: i8 },
}

/// Check for parallel perfect 5ths between two voice pairs.
pub fn parallel_fifths(
    prev: &[(Voice, u8)],   // (voice, note) before
    next: &[(Voice, u8)],   // (voice, note) after
) -> Vec<(Voice, Voice)>;

/// Check for parallel octaves.
pub fn parallel_octaves(
    prev: &[(Voice, u8)],
    next: &[(Voice, u8)],
) -> Vec<(Voice, Voice)>;

/// Check voice crossing (voices should maintain ordering S > A > T > B).
pub fn voice_crossing(assignments: &[VoiceAssignment]) -> Vec<(Voice, Voice)>;
```

---

## Error Types

```rust
/// Errors from the MIDI pipeline.
#[derive(Debug, thiserror::Error)]
pub enum MidiError {
    #[error("note {note} out of MIDI range [0,127]")]
    NoteOutOfRange { note: u8 },

    #[error("velocity {velocity} out of range [1,127]")]
    VelocityOutOfRange { velocity: u8 },

    #[error("client {client_id} not registered in session")]
    UnknownClient { client_id: ClientId },
}

/// Errors from session management.
#[derive(Debug, thiserror::Error)]
pub enum SessionError {
    #[error("session {session_id} not found")]
    SessionNotFound { session_id: SessionId },

    #[error("session {session_id} is full (max 16 clients)")]
    SessionFull { session_id: SessionId },

    #[error("client {client_id} not in session {session_id}")]
    ClientNotInSession { client_id: ClientId, session_id: SessionId },

    #[error("no path found from {from:?} to {to:?}")]
    NoPathFound { from: Triad, to: Triad },
    // Note: NoPathFound is unreachable in practice (Corollary 4.4),
    // but included for API completeness.
}

/// Errors from PLR operations (none expected at runtime).
#[derive(Debug, thiserror::Error)]
pub enum PLRError {
    #[error("invalid triad index {index} (must be < 24)")]
    InvalidTriadIndex { index: usize },
}
```

---

## Trait Summary

```rust
// groovemesh-plr
pub trait PLRNavigator { ... }
pub trait HarmonicProjection { ... }

// groovemesh-session
// (SessionManager implements PLRNavigator for a given SessionId via async methods)

// groovemesh-midi
// Pipeline is intentionally stateless pure functions, not traits.
// Callers compose the stages themselves for flexibility.
```

---

## Fix Required: `flux-algebra-rs` L Operation

The current `groups.rs:52` implementation:
```rust
// CURRENT (wrong for canonical PLR group):
Triad::major((t.root as i8 - 1).rem_euclid(12) as u8)

// REQUIRED (involutive, canonical neo-Riemannian L):
Triad::major((t.root as i8 - 4).rem_euclid(12) as u8)
```

**Impact:** Changing `−1` to `−4` makes L an involution (L² = id), reduces the
generated group from order 96 to order 24 (D₁₂), and aligns with the classical
Tonnetz. All existing tests still pass except `test_r` which tests R (unaffected).
The `test_plr_roundtrip` test should be updated to verify `PlrGroup::l(PlrGroup::l(t)) == t`.
