# GrooveMesh Architecture

Real-time collaborative counterpoint engine. Multiple musicians share a session;
every note they play is projected into the current PLR-valid chord. The constraint is
categorical: the PLR group is closed over T₂₄ (24 triads), so by algebraic necessity
the system state is always harmonically valid — not by validation, but by structure.

---

## Core Invariant

> **At all times, the session chord state is an element of T₂₄.**
> All transitions are PLR group operations. Group closure guarantees the state
> never escapes T₂₄. No wrong note is possible — the wrong note simply doesn't
> exist in the reachable state space.

This is the fundamental design principle. Every architectural decision flows from it.

---

## System Topology

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            CLIENT LAYER                                      │
│                                                                              │
│   ┌───────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐ │
│   │ Web Browser       │  │ DAW / VST Plugin      │  │ CLI Instrument       │ │
│   │ (WebAudio API)    │  │ (MIDI over WS)        │  │ (groovemesh-cli)     │ │
│   └─────────┬─────────┘  └──────────┬────────────┘  └──────────┬───────────┘ │
│             └─────────────────────┬─┘──────────────────────────┘             │
└───────────────────────────────────│──────────────────────────────────────────┘
                                    │  WebSocket (RFC 6455)
                                    │  Binary MIDI frames + JSON control
┌───────────────────────────────────▼──────────────────────────────────────────┐
│                          GROOVEMESH SERVER                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        WebSocket Gateway                                │ │
│  │   tokio-tungstenite · per-session broadcast channels · rate limiting    │ │
│  └───────────────┬────────────────────────────────────┬────────────────────┘ │
│                  │                                    │                      │
│  ┌───────────────▼────────────────┐  ┌───────────────▼──────────────────┐   │
│  │       Session Manager          │  │      PLR Navigation Engine        │   │
│  │                                │  │                                   │   │
│  │  SessionId → SessionState      │  │  ChordState machine               │   │
│  │  ClientRoster (voice SATB)     │  │  PLRLattice (precomputed 24×3)    │   │
│  │  TickClock (MIDI sync)         │  │  VoiceLeadingPath solver          │   │
│  │  BroadcastBus                  │  │  NearestTriad (O(1) hash)         │   │
│  └───────────────┬────────────────┘  └────────────────┬─────────────────┘   │
│                  │                                     │                     │
│  ┌───────────────▼─────────────────────────────────────▼─────────────────┐  │
│  │                         MIDI Pipeline                                  │  │
│  │                                                                        │  │
│  │  InputValidator → PLRProjector → VoiceAssigner →                       │  │
│  │  CounterpointChecker → MIDIEmitter                                     │  │
│  │                                                                        │  │
│  │  Underlying types: cmidi-core CMidiEvent, Triad from flux-algebra-rs   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### PLR Navigation Engine  (`groovemesh-plr` crate)

Wraps `flux-algebra-rs::groups::{Triad, PlrGroup}`. Owns the session's harmonic position.

**Responsibilities:**
- Maintain `ChordState`: current triad + timestamp
- Expose `navigate(op: PLROp) -> PLRTransition`: apply a PLR operation, return the transition
- Expose `nearest_triad(pcs: &[u8]) -> (Triad, VoiceLeadingCost)`: O(1) lookup
- Precompute the PLR lattice at startup: 24 triads × {P, L, R} = 72 directed edges

**PLR Lattice (precomputed at init, never recomputed):**

Each node is a `Triad`. Each edge is labeled P, L, or R. The lattice is the Tonnetz
embedded as an adjacency map: `HashMap<Triad, [Triad; 3]>` keyed by (root, quality),
values are `[P(t), L(t), R(t)]`.

```
Tonnetz (first quadrant, wraps toroidally):

      ...─── Eb+ ──── Bb+ ──── F+ ──── C+ ──── G+ ──── D+ ───...
             │        │        │       │        │       │
      ...─── Eb- ──── Bb- ──── F- ─── C- ──── G- ─── D- ────...
             │        │        │       │        │       │
      ...─── Gb+ ──── Db+ ──── Ab+ ── Eb+ ──── Bb+ ─── F+ ───...

     P edges: vertical (same root, flip quality)
     R edges: horizontal (relative major↔minor)
     L edges: diagonal (leading-tone exchange)
```

**NearestTriad:** Given a set of pitch classes `pcs: &[u8]`, returns the triad minimizing
voice-leading distance `d(pcs, t) = Σᵢ min_{n ∈ t.pcs()} |pcs[i] - n| mod 12`.
Precomputed: for each of the 4096 possible 12-bit pitch-class sets, the nearest triad
is stored in a 4096-entry array. Lookup is O(1) via bitmask indexing.

---

### Session Manager  (`groovemesh-session` crate)

**SessionState:**
```
SessionState {
    id: SessionId,               // Uuid v7 (time-ordered)
    chord: ChordState,           // current triad + tick
    voices: VoiceRegistry,       // maps ClientId → Voice (S/A/T/B)
    tick: u64,                   // monotonic MIDI tick counter (480 ticks/beat)
    tempo_bpm: f32,              // shared tempo
    clients: HashMap<ClientId, ClientInfo>,
}
```

**VoiceRegistry:** SATB assignment. When a client joins, it is assigned the lowest-occupied
voice. Voice ranges (MIDI):
- Soprano: 60–84 (C4–C6)
- Alto: 53–77 (F3–F5)
- Tenor: 48–72 (C3–C5)
- Bass: 40–64 (E2–E4)

**TickClock:** Advances at `tempo_bpm * 480 / 60` ticks/second. Broadcasts `TickPulse`
every 480 ticks (one beat). Clients use this to synchronize note timing.

---

### MIDI Pipeline  (`groovemesh-midi` crate)

Five stages, each a pure function with no side effects:

```
InputValidator
  In:  RawNote { note: u8, velocity: u8, client_id: ClientId }
  Out: Result<ValidNote, MidiError>
  Rule: note ∈ [0,127], velocity ∈ [1,127]

PLRProjector
  In:  (ValidNote, ChordState)
  Out: ProjectedNote { note: u8, pc: u8, voice_hint: VoiceRange }
  Rule: Projects note's pitch class onto nearest PC in current triad.
        If note.pc ∈ chord.pcs(): pass through unchanged.
        Else: find nearest PC in chord.pcs(), preserve octave.

VoiceAssigner
  In:  (ProjectedNote, VoiceRegistry, ClientId)
  Out: VoiceAssignment { voice: Voice, note: u8, client_id: ClientId }
  Rule: Assigns note to the client's registered voice. Clamps to voice range.

CounterpointChecker
  In:  (VoiceAssignment, SessionState)
  Out: Result<VoiceAssignment, VoiceLeadingError>
  Rules (classic four-part writing):
    - No parallel perfect 5ths between any voice pair
    - No parallel octaves between any voice pair
    - No voice crossing (soprano > alto > tenor > bass in pitch)
    - No augmented intervals in a single voice
    On error: returns the nearest non-violating assignment.

MIDIEmitter
  In:  VoiceAssignment
  Out: [u8; 3]  (standard MIDI Note On: [0x90|channel, note, velocity])
```

---

## Data Flow

### Happy path: note plays in current chord

```
Client sends: {"type":"note","note":64,"velocity":90}

1. WS Gateway receives, parses → RawNote { note: 64, velocity: 90, client_id }
2. InputValidator:  64 ∈ [0,127] ✓ → ValidNote
3. PLRProjector:    current chord = C major {0,4,7}
                    note 64 = E4, pc = 4 ∈ {0,4,7} → pass through
4. VoiceAssigner:   client assigned Alto, range [53,77]
                    64 ∈ [53,77] → assign as Alto E4
5. CounterpointChecker: check against current SATB state → OK
6. MIDIEmitter:     [0x91, 64, 90]  (channel 1 = Alto)
7. BroadcastBus:    broadcast to all clients in session
```

### Navigation: note triggers chord change

When the PLR engine detects that the current note would resolve more cleanly in a
neighboring triad (voice-leading cost to neighbor < cost to current chord by threshold
`NAVIGATION_THRESHOLD = 2.0` semitones total), it fires a chord navigation:

```
1. PLREngine.navigate(op: R)   // e.g. C major → R → A minor
2. SessionManager.update_chord(session_id, A_minor)
3. BroadcastBus.broadcast ChordStateUpdate {
       prev: C_major,
       next: A_minor,
       operation: R,
       voice_assignments: [
           VoiceAssignment { voice: Soprano, note: 69 },  // A5
           VoiceAssignment { voice: Alto,    note: 64 },  // E4 (common tone)
           VoiceAssignment { voice: Tenor,   note: 60 },  // C4 (common tone)
           VoiceAssignment { voice: Bass,    note: 57 },  // A3
       ],
       tick: 4320,
   }
4. All clients animate to new chord state
```

### Continuous "slide" mode

A client can request a continuous glide through voice-leading space by sending a
`slide` message with a target triad. The server computes the shortest path in the
PLR lattice (BFS, at most O(8) hops for any pair of triads), then emits one
`ChordStateUpdate` per hop at the current tempo:

```
Client: {"type":"slide","target":{"root":9,"major":false}}  // A minor
Server: finds path C+ →R→ Am (1 hop), schedules at tick+480
```

---

## Module Dependency Graph

```
groovemesh-server (bin)
├── groovemesh-ws
│   └── tokio-tungstenite
├── groovemesh-session
│   ├── groovemesh-plr
│   │   └── flux-algebra-rs        (Triad, PlrGroup)
│   └── groovemesh-midi
│       └── cmidi-core             (CMidiEvent, SpeechAct, VoiceLeading CC)
└── groovemesh-proto               (shared message types, serde)
```

```toml
# Cargo.toml (workspace)
[workspace]
members = [
    "groovemesh-plr",
    "groovemesh-session",
    "groovemesh-midi",
    "groovemesh-ws",
    "groovemesh-proto",
    "groovemesh-server",
]

[workspace.dependencies]
flux-algebra-rs   = { path = "../../flux-algebra-rs" }
cmidi-core        = { path = "../../cmidi-core" }
tokio             = { version = "1", features = ["full"] }
tokio-tungstenite = "0.21"
serde             = { version = "1", features = ["derive"] }
serde_json        = "1"
uuid              = { version = "1", features = ["v7"] }
```

---

## Performance Targets

| Metric                         | Target     | Mechanism                                    |
|--------------------------------|------------|----------------------------------------------|
| Note-to-broadcast latency      | < 5 ms     | tokio async pipeline, pre-allocated buffers  |
| Chord navigation latency       | < 10 ms    | PLR lattice lookup O(1)                      |
| Nearest-triad projection       | < 1 μs     | 4096-entry precomputed array                 |
| Max simultaneous clients/session | 16       | SATB × 4 octaves = 16 voices                 |
| Max concurrent sessions        | 1024       | per-session tokio task, ~50KB each           |
| Tick clock jitter              | < 1 ms     | tokio::time::interval with yield_now         |

---

## Integration Points

| External System    | Integration                                              |
|--------------------|----------------------------------------------------------|
| `flux-algebra-rs`  | PLR group ops, Triad type — imported directly            |
| `cmidi-core`       | CMidiEvent output, VoiceLeading CC103 for glide depth    |
| `cmidi-conservation` | ConservationRatio CC104 for voice-leading smoothness   |
| MIDI devices       | Raw MIDI bytes via WebSocket binary frames               |
| DAW                | VST3/AU bridge connects via loopback WebSocket           |
| Web frontend       | Tone.js consumes broadcast MIDI + chord state JSON       |

---

## Failure Modes and Recovery

| Failure                         | Detection                    | Recovery                                      |
|---------------------------------|------------------------------|-----------------------------------------------|
| Client disconnect mid-session   | WS close frame / ping timeout| Remove from VoiceRegistry; redistribute voice |
| Voice-leading constraint violation | CounterpointChecker error | Return nearest-valid assignment (never error) |
| Session chord desync            | Client sends tick mismatch   | Server sends full `SessionSync` snapshot      |
| PLR lattice corrupted           | Hash mismatch on load        | Panic and restart; lattice is static          |
| Invalid PLR operation sequence  | Impossible: group closure    | N/A — all sequences valid by construction     |
