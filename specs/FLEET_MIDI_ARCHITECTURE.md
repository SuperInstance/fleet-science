# Fleet MIDI Architecture

**File**: `/tmp/nightshift/FLEET_MIDI_ARCHITECTURE.md`  
**Scope**: All crates in the fleet-midi layer, grounded in the STUB_AUDIT.md build queue  
**Status**: Engineering spec — all APIs are implementation-ready

---

## Ecosystem Map

```
External AI Models              Fleet Protocol Layer              Audio Output
─────────────────               ──────────────────────────        ──────────────
fleet-diffrhythm-connector ─┐   cmidi-core (KEEP)                fleet-sound-toolkit
fleet-rave-connector ────────┤   cmidi-conservation (KEEP)            FluidSynth
fleet-maidi-connector ───────┘   fleet-i2i-protocol (BUILD)          SuperCollider
                              │                                        RustFM (no_std)
                              ▼                                    fleet-midi-synth
                        ┌─────────────┐                               Web Audio API
   fleet-midi-pulse ───►│fleet-ensemble│──────────────────────►       WASM
   (clock/timing)       └──────┬──────┘                           fleet-midi-studio
                               │                                       React/Vite DAW
                        fleet-midi-harmonizer
                        (four-part harmony,
                         PLR validation)
```

**Crates with code today**: `cmidi-core` (33 KB), `cmidi-conservation` (20 KB)  
**Crates to build (P0)**: `fleet-midi-pulse`, `fleet-midi-harmonizer`, `fleet-ensemble`, `fleet-i2i-protocol`  
**Crates to build (P1)**: `fleet-midi-studio`, `fleet-sound-toolkit`, `fleet-midi-synth`  
**Crates to build (P3)**: `fleet-diffrhythm-connector`, `fleet-rave-connector`, `fleet-maidi-connector`

---

## Section 1: Crate Registry

### 1.1 Foundation — Already Exists

#### `cmidi-core`

The protocol kernel. Maps multi-agent discourse to symbolic MIDI.

**Key types (source-confirmed)**:
- `SpeechAct` — 8 variants → pitch classes: `Assertion=C4(60)`, `Question=D4(62)`, `Command=E4(64)`, `Agreement=F4(65)`, `Objection=G4(67)`, `Elaboration=A4(69)`, `Transition=B4(71)`, `Silence=rest`
- `ConversationCC` — 12 CC mappings: `Engagement=1`, `Sarcasm=2`, `Salience=7`, `Sentiment=10`, `Nuance=11`, `Tension=102`, `VoiceLeading=103`, `ConservationRatio=104`
- `AgentRole` — 8 roles → GM programs: `Researcher=68(Oboe)`, `Builder=42(Cello)`, `Critic=56(Trumpet)`, `Integrator=0(Piano)`, `Explorer=65(AltoSax)`, `Conductor=48(Strings)`, `Guardian=47(Timpani)`, `Narrator=52(Choir)`
- `CMAgent` — `{ id: String, channel: u8, role: AgentRole, confidence: u8 }`
- `CMidiEvent` — `{ tick: u32, agent_channel: u8, speech_act: SpeechAct, velocity: u8, duration: u32, cc_values: Vec<(ConversationCC, u8)> }`
- `Conversation` — multi-track session with `to_midi_bytes() -> Vec<u8>` (Format 0 MIDI)
- `FakeBook` — chord progression schema (`FakeBookSection` with AABA/ABB form)

#### `cmidi-conservation`

Fleet health sonification. Encodes `ConservationMonitor` state as CC104 and harmonic corrections. (Source: `/home/phoenix/.openclaw/workspace/cmidi-conservation/`)

---

### 1.2 Build Queue: 10 Crates

#### `fleet-i2i-protocol`

**Purpose**: Inter-Agent Interaction protocol over MIDI SysEx. Foundation layer — no dependencies within fleet-midi.

**Dependency**: `cmidi-core`  
**Feature flags**: `networking` (Tokio + WebSocket), `no_std` (SysEx encoding only)

```rust
/// I2I/1.0 — Inter-Agent Interaction protocol
pub trait I2IAgent: Send + Sync {
    fn agent_id(&self) -> &str;
    fn capabilities(&self) -> I2ICapabilities;
    /// Called by router when a message arrives for this agent.
    fn handle(&self, msg: I2IMessage) -> impl Future<Output = Option<I2IMessage>> + Send;
}

pub struct I2ICapabilities {
    pub speech_acts: Vec<SpeechAct>,
    pub cc_controllers: Vec<u8>,
    pub accepts_commands: bool,
}

#[derive(Debug, Clone)]
pub struct I2IMessage {
    pub version: u8,           // 1
    pub from: AgentId,
    pub to: I2IDest,
    pub reply_to: Option<AgentId>,
    pub payload: I2IPayload,
}

pub type AgentId = String;

pub enum I2IDest {
    Unicast(AgentId),
    Multicast(Vec<AgentId>),
    Anycast(String),           // first available agent matching group name
    Broadcast,
}

pub enum I2IPayload {
    SpeechAct {
        act: SpeechAct,
        cc_values: Vec<(ConversationCC, u8)>,
    },
    CCUpdate { controller: u8, value: u8 },
    RoleChange { new_role: AgentRole },
    Ping { nonce: u64 },
    Pong { nonce: u64, latency_us: u32 },
}

pub struct I2IRouter {
    agents: HashMap<AgentId, Arc<dyn I2IAgent>>,
}

impl I2IRouter {
    pub fn new() -> Self;
    pub fn register(&mut self, agent: Arc<dyn I2IAgent>);
    pub fn unregister(&mut self, id: &str);

    /// Dispatch a message to its destination.
    pub async fn dispatch(&self, msg: I2IMessage);

    /// Encode an I2IMessage as MIDI SysEx bytes.
    /// Format: F0 7D <version> <from_len> <from_bytes> <payload_type> <payload_bytes> F7
    pub fn encode_sysex(msg: &I2IMessage) -> Vec<u8>;
    pub fn decode_sysex(bytes: &[u8]) -> Result<I2IMessage, I2IError>;

    /// Serve WebSocket endpoint (requires `networking` feature).
    pub async fn serve_ws(&self, addr: &str) -> Result<(), I2IError>;
}

pub enum I2IError {
    InvalidSysEx,
    UnknownAgent(AgentId),
    CapabilityDenied { agent: AgentId, act: SpeechAct },
    Transport(String),
}
```

**no_std surface** (feature `no_std`): `encode_sysex`, `decode_sysex`, `I2IMessage`, `I2IPayload` — no networking, no `Box<dyn Trait>`.

---

#### `fleet-midi-pulse`

**Purpose**: The fleet heartbeat. Single source of timing truth. Agents subscribe, receive `TickEvent`.

**Dependency**: `tokio` (default), `wasm-bindgen` (wasm feature)  
**Feature flags**: `std` (default, tokio + SCHED_FIFO), `wasm` (requestAnimationFrame), `no_std` (bare `tick()` fn, no broadcast)

```rust
#[derive(Debug, Clone, Copy)]
pub struct PulseConfig {
    pub bpm: f64,
    pub ticks_per_beat: u32,   // Standard: 480
    pub time_signature: (u8, u8),
    pub swing: SwingFeel,
}

impl Default for PulseConfig {
    fn default() -> Self {
        Self { bpm: 120.0, ticks_per_beat: 480, time_signature: (4, 4), swing: SwingFeel::None }
    }
}

#[derive(Debug, Clone, Copy)]
pub enum SwingFeel {
    None,
    Soft,    // 54/46 ratio
    Medium,  // 58/42 ratio
    Hard,    // 66/34 ratio (strong triplet feel)
}

#[derive(Debug, Clone, Copy)]
pub struct TickEvent {
    pub tick: u64,              // absolute tick counter
    pub beat: u32,              // beat within bar (0-based)
    pub bar: u32,               // bar number (0-based)
    pub phase: f64,             // 0.0–1.0 within current beat
    pub is_downbeat: bool,      // tick == bar start
}

impl TickEvent {
    /// Microseconds per tick at current BPM.
    pub fn tick_duration_us(bpm: f64, ticks_per_beat: u32) -> u64 {
        (60_000_000.0 / (bpm * ticks_per_beat as f64)) as u64
    }
}

pub struct Pulse {
    config: PulseConfig,
    tick: Arc<AtomicU64>,
    sender: tokio::sync::broadcast::Sender<TickEvent>,
}

impl Pulse {
    pub fn new(config: PulseConfig) -> Self;

    /// Subscribe to receive every tick.
    pub fn subscribe(&self) -> tokio::sync::broadcast::Receiver<TickEvent>;

    /// Current tick (lockless read).
    pub fn current_tick(&self) -> u64;

    /// Drive the pulse loop. Runs until the future is dropped.
    /// On Linux, elevates thread priority to SCHED_FIFO.
    pub async fn run(&self);

    /// Quantize an arbitrary tick to the nearest grid position.
    pub fn quantize(&self, tick: u64, grid: QuantizeGrid) -> u64;

    /// Gradually change BPM over `duration_beats`.
    pub fn ramp_bpm(&mut self, target_bpm: f64, duration_beats: u32);

    /// Pause all ticking (fermata).
    pub fn pause(&self);
    pub fn resume(&self);

    /// Lock to external MIDI clock (MIDI clock byte = 0xF8, 24 per beat).
    /// Requires `networking` feature and a MIDI input port.
    pub async fn lock_to_external_midi_clock(
        &mut self,
        port: &str,
    ) -> Result<(), PulseError>;
}

pub enum QuantizeGrid {
    Whole,
    Half,
    Quarter,
    Eighth,
    Sixteenth,
    Triplet(u32),  // triplet subdivision of given note value
}

pub enum PulseError {
    MidiPortNotFound(String),
    ClockLockFailed,
    AlreadyLocked,
}
```

**Merged from `fleet-midi-quantizer`**: The `quantize()` method above.

**Tick math**:
- At 120 BPM, 480 ticks/beat: 1 tick = 1,041.67 µs ≈ 1 ms
- At 120 BPM: 1 bar (4/4) = 1920 ticks = 2.0s
- At 120 BPM: 1 second ≈ 960 ticks

---

#### `fleet-midi-harmonizer`

**Purpose**: Four-part harmony engine. Validates and corrects chord voicings. Absorbs `fleet-midi-arpeggiator` and `fleet-midi-morph`.

**Dependencies**: `cmidi-core`, `groovemesh-plr` (or `flux-algebra-rs`)  
**Feature flags**: `groovemesh` (enables PLR group operations), `no_std` (voice-leading tables only)

```rust
#[derive(Debug, Clone, Copy)]
pub struct HarmonicContext {
    pub key_root: u8,          // pitch class 0–11 (C=0)
    pub mode: Mode,
    pub tension_budget: f64,   // 0.0=pure consonance, 1.0=atonal
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode { Major, Minor, Dorian, Mixolydian, Phrygian, Lydian, Locrian }

#[derive(Debug, Clone, Copy)]
pub enum VoiceRole { Soprano, Alto, Tenor, Bass }

#[derive(Debug, Clone, Copy)]
pub struct Voice {
    pub role: VoiceRole,
    pub agent_channel: u8,
    pub note: u8,    // MIDI note 0–127
    pub velocity: u8,
}

impl Voice {
    // SATB ranges (MIDI)
    pub const SOPRANO_RANGE: (u8, u8) = (60, 84);  // C4–C6
    pub const ALTO_RANGE:    (u8, u8) = (55, 79);  // G3–G5
    pub const TENOR_RANGE:   (u8, u8) = (48, 72);  // C3–C5
    pub const BASS_RANGE:    (u8, u8) = (40, 64);  // E2–E4
}

#[derive(Debug, Clone)]
pub struct Chord {
    pub voices: [Voice; 4],
    pub duration_ticks: u32,
    pub tension: f64,          // measured tension (0.0–1.0)
}

pub struct HarmonizerConfig {
    pub no_parallel_fifths: bool,       // default true
    pub no_parallel_octaves: bool,      // default true
    pub no_voice_crossing: bool,        // default true
    pub resolve_leading_tone: bool,     // default true
    pub max_voice_distance_semitones: u8, // default 7
}

impl Default for HarmonizerConfig {
    fn default() -> Self {
        Self {
            no_parallel_fifths: true,
            no_parallel_octaves: true,
            no_voice_crossing: true,
            resolve_leading_tone: true,
            max_voice_distance_semitones: 7,
        }
    }
}

// ── Merged from fleet-midi-arpeggiator ──────────────────────────────

#[derive(Debug, Clone)]
pub struct ArpPattern {
    pub order: ArpOrder,
    pub rhythm: Vec<u32>,     // tick durations per step
    pub gate: f32,             // 0.0–1.0 (1.0 = full legato)
}

pub enum ArpOrder { Up, Down, UpDown, Random, AsPlayed }

// ── Merged from fleet-midi-morph ───────────────────────────────────

pub struct MorphConfig {
    pub steps: u32,            // number of intermediate voicings
    pub interpolation: MorphInterpolation,
}

pub enum MorphInterpolation {
    Linear,                    // direct semitone interpolation
    VoiceLeading,              // minimize total movement at each step
    Glissando,                 // continuous pitch slide
}

// ── Core Harmonizer ────────────────────────────────────────────────

pub struct Harmonizer {
    pub context: HarmonicContext,
    pub config: HarmonizerConfig,
}

impl Harmonizer {
    pub fn new(context: HarmonicContext) -> Self;
    pub fn with_config(self, config: HarmonizerConfig) -> Self;

    /// Build a 4-voice chord from a set of simultaneous speech acts.
    /// Input: [(agent_channel, SpeechAct)] — one entry per active agent.
    /// Assigns agents to voices by role priority, corrects voicing violations.
    pub fn harmonize(
        &self,
        acts: &[(u8, SpeechAct)],
        channel_roles: &HashMap<u8, AgentRole>,
    ) -> Result<Chord, HarmonizerError>;

    /// Correct a chord that violates counterpoint rules.
    /// Returns a minimally-adjusted chord satisfying all rules.
    pub fn correct(&self, chord: &Chord) -> Chord;

    /// Check if a chord satisfies all counterpoint rules.
    pub fn is_valid(&self, chord: &Chord) -> bool;

    /// Voice-leading cost between two chords (sum of absolute semitone movements).
    pub fn voice_leading_cost(&self, from: &Chord, to: &Chord) -> u32;

    /// Build a chord from a ternary {-1, 0, 1} state vector.
    /// Negative components → flatten voice, positive → raise, zero → hold.
    pub fn from_ternary(&self, state: &[i8; 4]) -> Result<Chord, HarmonizerError>;

    // ── Arpeggiator (from fleet-midi-arpeggiator) ──

    /// Expand a Chord into an arpeggio — a sequence of (tick_offset, Voice) events.
    pub fn arpeggiate(&self, chord: &Chord, pattern: &ArpPattern) -> Vec<(u32, Voice)>;

    // ── Morph (from fleet-midi-morph) ──

    /// Generate `config.steps` intermediate voicings from `from` to `to`.
    /// Returned vec has length `steps + 2` (including endpoints).
    pub fn morph(&self, from: &Chord, to: &Chord, config: &MorphConfig) -> Vec<Chord>;
}

pub enum HarmonizerError {
    NoValidVoicing,
    TooFewAgents { have: usize, need: usize },
    KeyNotSet,
    ViolatesHardConstraint(String),
}

/// Map AgentRole to SATB voice assignment by priority.
/// Conductor/Guardian → Bass (anchor), Builder → Tenor,
/// Researcher/Critic → Alto, Explorer/Narrator/Integrator → Soprano
pub fn role_to_voice(role: AgentRole) -> VoiceRole;
```

---

#### `fleet-ensemble`

**Purpose**: Multi-agent music coordinator. The conductor. Absorbs `fleet-midi-gateway`, `fleet-midi-conductor`, `fleet-midi-router`.

**Dependencies**: `cmidi-core`, `fleet-midi-pulse`, `fleet-midi-harmonizer`, `fleet-i2i-protocol`  
**Feature flags**: `gateway` (WebSocket server), `recording` (Conversation export), `no_std` (tick-only mode)

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EnsembleMode {
    /// First species counterpoint: one speech act per agent per tick.
    Synchronous,
    /// Second species: agents may buffer and emit on weak beats.
    Asynchronous,
    /// Fifth species: free counterpoint within harmonic constraints.
    Improvisational,
}

pub enum ConflictResolution {
    /// Strict priority: Conductor > Guardian > Critic > Builder > Researcher > Explorer > Integrator > Narrator
    RolePriority,
    /// Prefer the speech act that minimizes voice-leading movement.
    VoiceLeading,
    /// Majority vote when three or more agents agree.
    Democratic,
}

/// Agent role priority. Lower = higher priority (0 = highest).
pub fn role_priority(role: AgentRole) -> u8 {
    match role {
        AgentRole::Conductor => 0,
        AgentRole::Guardian  => 1,
        AgentRole::Critic    => 2,
        AgentRole::Builder   => 3,
        AgentRole::Researcher => 4,
        AgentRole::Explorer  => 5,
        AgentRole::Integrator => 6,
        AgentRole::Narrator  => 7,
    }
}

pub struct AgentRegistration {
    pub agent: CMAgent,
    pub patch_override: Option<u8>,
    pub muted: bool,
    pub solo: bool,
    /// If false: adversarial agent. Will be muted if consistently dissonant.
    pub accepts_direction: bool,
}

pub struct EnsembleConfig {
    pub mode: EnsembleMode,
    pub conflict_resolution: ConflictResolution,
    pub harmonic_context: HarmonicContext,
    pub max_agents: usize,      // default 16 (MIDI channel limit)
    pub dissonance_threshold: f64, // 0.0–1.0; agents above this are warned then muted
}

pub struct EnsembleSnapshot {
    pub tick: u64,
    pub active_agents: Vec<AgentId>,
    pub current_chord: Option<Chord>,
    pub tension: f64,
}

pub struct Ensemble {
    config: EnsembleConfig,
    registrations: HashMap<AgentId, AgentRegistration>,
    harmonizer: Harmonizer,
    pending: HashMap<AgentId, (SpeechAct, Vec<(ConversationCC, u8)>)>,
    conversation_log: Conversation,
    tick: u64,

    // Merged from fleet-midi-gateway:
    ws_clients: Vec<WsClientHandle>,

    // Merged from fleet-midi-conductor + fleet-midi-router:
    router: I2IRouter,
}

impl Ensemble {
    pub fn new(config: EnsembleConfig) -> Self;

    pub fn register(&mut self, reg: AgentRegistration);
    pub fn unregister(&mut self, id: &AgentId);
    pub fn mute(&mut self, id: &AgentId);
    pub fn unmute(&mut self, id: &AgentId);
    pub fn solo(&mut self, id: &AgentId);
    pub fn clear_solo(&mut self);

    /// An agent submits a pending speech act for the next tick.
    /// Thread-safe — can be called from any agent thread.
    pub fn submit(&self, from: &AgentId, act: SpeechAct, cc: Vec<(ConversationCC, u8)>);

    /// Process one tick of the pulse clock.
    /// Collects all pending speech acts, resolves conflicts,
    /// harmonizes via Harmonizer, logs to Conversation.
    /// Returns all CMidiEvents to emit this tick.
    pub fn tick(&mut self, event: TickEvent) -> Vec<CMidiEvent>;

    /// Run the ensemble, driven by a Pulse. Returns an event stream.
    pub async fn run(
        &mut self,
        pulse: &Pulse,
    ) -> impl Stream<Item = Vec<CMidiEvent>>;

    /// Current snapshot (lock-free read).
    pub fn snapshot(&self) -> EnsembleSnapshot;

    /// Export the recorded conversation as a CMIDI Conversation.
    pub fn export_conversation(&self) -> Conversation;

    /// Export to standard MIDI file bytes (SMF Format 0).
    pub fn export_midi(&self) -> Vec<u8>;

    // ── Gateway (merged from fleet-midi-gateway) ──

    /// Open a WebSocket server that external clients can connect to.
    /// Clients receive every CMidiEvent as a JSON or binary frame.
    /// Clients can submit speech acts via the WS connection.
    /// Requires `gateway` feature.
    pub async fn serve_gateway(&mut self, addr: &str) -> Result<(), EnsembleError>;
}

pub enum EnsembleError {
    AgentNotFound(AgentId),
    ChannelExhausted,
    HarmonizerError(HarmonizerError),
    GatewayError(String),
}
```

---

#### `fleet-sound-toolkit`

**Purpose**: Audio synthesis backend. Bridges validated CMidiEvent streams to PCM audio.

**Dependencies**: optional `fluidsynth` (sys crate), optional `supercollider` (OSC), always-available `rust-fm`  
**Feature flags**: `fluidsynth`, `supercollider`, `cpal` (local audio device), `no_std` (rust-fm only)

```rust
pub enum SynthBackend {
    FluidSynth {
        soundfont_path: std::path::PathBuf,
        sample_rate: u32,
    },
    SuperCollider {
        osc_port: u16,
        osc_host: std::net::IpAddr,
    },
    RustFM,   // Pure Rust FM synth — no external deps, WASM/embedded safe
}

pub trait AudioRenderer: Send {
    fn play_event(&mut self, event: &CMidiEvent) -> Result<(), SoundError>;
    fn play_raw(&mut self, note_on: [u8; 3], duration_ticks: u32) -> Result<(), SoundError>;
    fn set_patch(&mut self, channel: u8, program: u8) -> Result<(), SoundError>;
    fn set_reverb(&mut self, channel: u8, send: u8);
    fn silence_all(&mut self);

    /// Render a batch of events to PCM (offline, for export).
    fn render_to_pcm(
        &self,
        events: &[CMidiEvent],
        sample_rate: u32,
        ticks_per_beat: u32,
        bpm: f64,
    ) -> Result<Vec<[f32; 2]>, SoundError>;
}

pub struct SoundToolkit {
    backend: SynthBackend,
    channel_patches: [u8; 16],
    reverb_sends: [u8; 16],
    polyphony_limit: u32,      // default 64 voices
    master_volume: f32,        // 0.0–1.0
}

impl SoundToolkit {
    /// Auto-detect best backend: FluidSynth if sf2 available, else RustFM.
    pub fn auto(sf2_path: Option<&std::path::Path>) -> Result<Self, SoundError>;

    pub fn with_fluidsynth(sf2_path: &std::path::Path) -> Result<Self, SoundError>;
    pub fn with_supercollider(host: std::net::IpAddr, port: u16) -> Self;
    pub fn with_rust_fm() -> Self;  // zero deps — always available

    /// Auto-assign GM program numbers from AgentRole.
    pub fn configure_from_roles(&mut self, roles: &[(u8, AgentRole)]);

    /// Stream stereo PCM via CPAL (local speaker output).
    /// Requires `cpal` feature.
    pub fn stream_to_speakers(&self) -> Result<cpal::Stream, SoundError>;

    /// Render a Conversation to a WAV file.
    pub fn render_wav(
        &self,
        conversation: &Conversation,
        output_path: &std::path::Path,
    ) -> Result<(), SoundError>;
}

impl AudioRenderer for SoundToolkit { /* dispatches to backend */ }

/// RustFM synthesizer — pure Rust, no external dependencies.
/// Implements 4-operator FM synthesis.
pub struct RustFMSynth {
    voices: [FMVoice; 32],
    sample_rate: u32,
}

impl RustFMSynth {
    pub fn note_on(&mut self, channel: u8, note: u8, velocity: u8);
    pub fn note_off(&mut self, channel: u8, note: u8);
    pub fn process(&mut self, out_l: &mut [f32], out_r: &mut [f32]);
}

struct FMVoice {
    operators: [FMOperator; 4],
    envelope: ADSR,
    active: bool,
    channel: u8,
    note: u8,
}

pub enum SoundError {
    BackendNotAvailable(String),
    SoundFontLoadError(String),
    PCMRenderError(String),
    PolyphonyExhausted,
}
```

---

#### `fleet-midi-synth`

**Purpose**: Web Audio API synthesis engine. Runs in-browser via WASM.

**Dependencies**: `wasm-bindgen`, `web-sys` (AudioContext, AudioNode), connects to `fleet-midi-pulse` WS  
**Feature flags**: `wasm` (default), `cpal` (native audio output for testing)

```rust
// The WASM-exported surface (annotated with #[wasm_bindgen])

#[wasm_bindgen]
pub struct SynthConfig {
    pub sample_rate: u32,      // default 44100
    pub voice_count: u32,      // default 32 (voice stealing beyond this)
    pub attack_ms: f32,        // ADSR
    pub decay_ms: f32,
    pub sustain_level: f32,    // 0.0–1.0
    pub release_ms: f32,
}

#[wasm_bindgen]
pub struct WavetableSynth {
    voices: Vec<SynthVoice>,
    lfo: LFO,
    context: web_sys::AudioContext,
    gain_node: web_sys::GainNode,
}

#[wasm_bindgen]
impl WavetableSynth {
    #[wasm_bindgen(constructor)]
    pub fn new(config: SynthConfig) -> WavetableSynth;

    pub fn note_on(&mut self, channel: u8, note: u8, velocity: u8);
    pub fn note_off(&mut self, channel: u8, note: u8);
    pub fn cc(&mut self, channel: u8, controller: u8, value: u8);

    /// Connect to a fleet-midi-pulse WebSocket URL.
    /// Incoming TickEvents and CMidiEvents are dispatched to note_on/off/cc.
    pub fn connect_pulse(&mut self, ws_url: &str);

    /// Disconnect from pulse WS.
    pub fn disconnect_pulse(&mut self);

    /// Offline render: returns a Float32Array (interleaved stereo).
    pub fn render_offline(
        events_json: &str,
        duration_seconds: f32,
        sample_rate: u32,
    ) -> js_sys::Float32Array;

    pub fn set_master_volume(&mut self, volume: f32);
    pub fn set_reverb(&mut self, send: f32);
}

struct SynthVoice {
    note: u8,
    channel: u8,
    oscillator: web_sys::OscillatorNode,
    envelope: web_sys::GainNode,
    filter: web_sys::BiquadFilterNode,
    age: u32,  // for voice stealing (oldest = highest age)
}

struct LFO {
    rate_hz: f32,
    depth: f32,
    target: LFOTarget,
}

pub enum LFOTarget { Pitch, FilterCutoff, Volume }

// Wavetable: 256-sample periodic waveforms for GM instrument families
// (Piano, Strings, Brass, Woodwind, Percussion)
pub fn wavetable_for_role(role: AgentRole) -> [f32; 256];
```

---

#### `fleet-midi-studio`

**Purpose**: Browser-based DAW. The human interface. Absorbs `fleet-midi-monitor`, `fleet-midi-sequencer`, `fleet-midi-looper`, `fleet-midi-recorder`, `fleet-midi-composer`, `fleet-midi-remapper`.

**Language**: TypeScript/React/Vite (not a Rust crate — a web application)  
**Communication**: WebSocket to `fleet-ensemble` gateway, Web Audio API via `fleet-midi-synth` (WASM)

```typescript
// Studio component architecture

interface StudioProps {
  ensembleWsUrl: string;      // fleet-ensemble WebSocket gateway
  pulseWsUrl: string;         // fleet-midi-pulse WebSocket
}

// Piano Roll — renders Conversation events (color-coded by SpeechAct)
// Assertion=blue, Objection=red, Question=yellow, Command=orange
// Agreement=green, Elaboration=purple, Transition=cyan, Silence=gray
interface PianoRollProps {
  conversation: Conversation;
  ticksPerBeat: number;       // 480
  zoomLevel: number;
  selectedChannel?: number;
}

// Agent Rack — registered fleet agents with mute/solo/arm
interface AgentRackProps {
  agents: AgentRegistration[];
  onMute: (id: string) => void;
  onSolo: (id: string) => void;
  onPatchChange: (id: string, program: number) => void;
}

// Mixer — per-channel routing to FluidSynth or WebAudio
interface MixerProps {
  channels: ChannelStrip[];
  masterVolume: number;
}

interface ChannelStrip {
  channel: number;
  label: string;
  volume: number;
  pan: number;               // CC10 (Sentiment)
  reverbSend: number;
  outputBus: 'fluidsynth' | 'webaudio';
}

// Compose Panel — ternary input sliders → fleet-midi-harmonizer
interface ComposePanelProps {
  onHarmonize: (ternaryState: [number, number, number, number]) => void;
  harmonicContext: HarmonicContext;
}

// Monitor Panel (merged from fleet-midi-monitor)
// Real-time oscilloscope of cmidi-conservation dissonance (CC104)
interface MonitorPanelProps {
  bufferSize: number;         // samples to display
  sampleRateHz: number;       // 10Hz = one CC104 per 100ms
}

// Step Sequencer (merged from fleet-midi-sequencer)
interface SequencerProps {
  steps: number;              // 16 or 32
  stepResolution: QuantizeGrid;
  pattern: SequencerPattern;
}

// Transport bar (includes looper, recorder, play/stop/export)
// Merged from: fleet-midi-looper, fleet-midi-recorder
interface TransportProps {
  isPlaying: boolean;
  isRecording: boolean;
  isLooping: boolean;
  loopStart: number;          // ticks
  loopEnd: number;            // ticks
  onPlay: () => void;
  onRecord: () => void;
  onLoop: (start: number, end: number) => void;
  onExportMid: () => void;
  onExportWav: () => void;    // offline render via OfflineAudioContext
}

// MIDI Remapper (merged from fleet-midi-remapper)
// Route incoming notes/CC from one channel to another, transpose, remap CC
interface RemapperConfig {
  fromChannel: number;
  toChannel: number;
  transposeOctaves: number;
  ccMap: Record<number, number>;   // source CC → destination CC
}
```

---

#### `fleet-diffrhythm-connector`

**Purpose**: Bridge to DiffRhythm full-song generation.

**Dependencies**: `cmidi-core`, `reqwest` (HTTP client), `serde_json`  
**Runtime**: sidecar service (not embedded in ensemble)

```rust
pub struct DiffRhythmConnector {
    pub endpoint: url::Url,
    pub timeout: std::time::Duration,
    client: reqwest::Client,
}

pub struct DiffRhythmRequest {
    pub style: String,           // "jazz", "classical", "ambient"
    pub duration_seconds: f32,
    pub temperature: f32,        // creativity 0.0–1.0
    // Encoded from Conversation:
    pub melodic_contour: Vec<f32>, // normalized pitch contour [0.0, 1.0]
    pub harmonic_rhythm: Vec<f32>, // chord change timestamps in seconds
    pub lyrical_theme: LyricalTheme,
}

pub enum LyricalTheme {
    Declarative,    // from Assertion-heavy conversation
    Interrogative,  // from Question-heavy conversation
    Contrasting,    // from Objection-heavy conversation
    Narrative,      // mixed
}

pub struct GeneratedAudio {
    pub format: AudioFormat,
    pub data: Vec<u8>,     // MP3 or WAV bytes
    pub duration_seconds: f32,
    pub bpm: f32,
    pub key: String,
}

pub enum AudioFormat { MP3, WAV, OGG }

impl DiffRhythmConnector {
    pub fn new(endpoint: url::Url) -> Self;

    /// Convert a Conversation to a DiffRhythm request.
    /// Extracts melodic contour from SpeechAct note sequence,
    /// harmonic rhythm from chord changes,
    /// LyricalTheme from dominant speech act.
    pub fn encode_conversation(conversation: &Conversation) -> DiffRhythmRequest;

    pub async fn generate(
        &self,
        req: DiffRhythmRequest,
    ) -> Result<GeneratedAudio, ConnectorError>;

    /// Convenience: one call from Conversation to audio bytes.
    pub async fn generate_from_conversation(
        &self,
        conversation: &Conversation,
        style: &str,
        duration_seconds: f32,
    ) -> Result<GeneratedAudio, ConnectorError>;
}
```

---

#### `fleet-rave-connector`

**Purpose**: Bridge to RAVE neural audio synthesis.

```rust
pub struct RaveConnector {
    pub model_zoo: std::path::PathBuf,  // directory of .ts (TorchScript) RAVE models
    pub latency_budget_ms: u32,
    pub device: RaveDevice,
}

pub enum RaveDevice { CPU, CUDA(u32) }

pub struct RaveConfig {
    /// Map MIDI channel → RAVE model name (e.g., channel 0 → "piano.ts").
    pub channel_models: std::collections::HashMap<u8, String>,
    /// Number of latent dimensions (depends on model, typically 8–64).
    pub latent_dims: usize,
}

impl RaveConnector {
    pub fn new(model_zoo: &std::path::Path, latency_budget_ms: u32) -> Result<Self, ConnectorError>;
    pub fn load_model(&mut self, channel: u8, model_name: &str) -> Result<(), ConnectorError>;

    /// Convert MIDI events (pitch, velocity, CC) to RAVE latent codes.
    /// Encoding: note → pitch latent (harmonic dimension),
    ///           velocity → amplitude latent,
    ///           CC103 (VoiceLeading) → timbre latent.
    pub fn midi_to_latent(
        &self,
        events: &[CMidiEvent],
        channel: u8,
    ) -> Result<Vec<f32>, ConnectorError>;

    /// Decode latent codes to stereo PCM.
    pub fn render(
        &self,
        latent_codes: &[f32],
        channel: u8,
    ) -> Result<Vec<[f32; 2]>, ConnectorError>;

    /// Real-time inference path (streaming, uses ring buffer).
    /// Latency ≤ `latency_budget_ms` ms on GPU, ≤ 50ms on CPU.
    pub async fn stream(
        &self,
        events: impl Stream<Item = CMidiEvent>,
        channel: u8,
    ) -> impl Stream<Item = [f32; 2]>;
}
```

---

#### `fleet-maidi-connector`

**Purpose**: Bridge to M(AI)DI transformer. Acts as a "ghost player" — AI agent listening and improvising.

```rust
pub struct MaidiConnector {
    pub context_window_ticks: u32,  // how many recent ticks to use as prompt
    pub temperature: f32,
    pub style_bias: String,          // "jazz", "baroque", "minimalist"
    pub fleet_alignment: f32,        // 0.0=full novelty, 1.0=strict follow
    model: MaidiModel,
}

pub struct MaidiModel {
    pub vocab_size: usize,
    pub max_sequence_len: usize,
    pub checkpoint_path: std::path::PathBuf,
}

pub struct MaidiToken {
    pub token_type: MaidiTokenType,
    pub value: u8,
    pub time_shift_ticks: u32,
}

pub enum MaidiTokenType {
    NoteOn, NoteOff, Velocity, TimeShift, ProgramChange
}

impl MaidiConnector {
    pub fn new(model: MaidiModel, temperature: f32) -> Result<Self, ConnectorError>;

    /// Encode recent CMidiEvents as M(AI)DI token sequence.
    pub fn encode_context(events: &[CMidiEvent]) -> Vec<MaidiToken>;

    /// Decode M(AI)DI tokens back to CMidiEvents.
    pub fn decode_tokens(tokens: &[MaidiToken], channel: u8) -> Vec<CMidiEvent>;

    /// Generate a continuation of the fleet's current musical context.
    /// Returns suggested speech acts for the next N ticks.
    pub async fn generate_continuation(
        &self,
        context: &[CMidiEvent],
        n_ticks: u32,
    ) -> Result<Vec<CMidiEvent>, ConnectorError>;

    /// Run as a ghost-player agent: subscribe to ensemble, emit suggestions.
    /// The ghost player submits its suggestions back to the ensemble via I2I.
    pub async fn run_as_ghost_player(
        &self,
        ensemble: &Ensemble,
        agent_id: &str,
        channel: u8,
    );
}

pub enum ConnectorError {
    ModelNotFound(std::path::PathBuf),
    InferenceError(String),
    ContextTooLong { max: usize, got: usize },
    NetworkError(String),
}
```

---

## Section 2: Data Flow — Speech Act to Speakers

### 2.1 Complete Pipeline Trace

```
╔══════════════════════════════════════════════════════════════════════╗
║  AGENT LAYER                                                         ║
║                                                                      ║
║  Agent decides to speak:                                             ║
║    speech_act = SpeechAct::Objection                                 ║
║    cc_values  = [(ConversationCC::Urgency, 127),                     ║
║                  (ConversationCC::Tension, 90)]                      ║
║    agent_channel = 1  (Critic → Trumpet, GM program 56)             ║
║                                                    │                 ║
╚════════════════════════════════════════════════════╪═════════════════╝
                                                     │ Ensemble::submit()
                                                     ▼
╔══════════════════════════════════════════════════════════════════════╗
║  TIMING LAYER  (fleet-midi-pulse)                                    ║
║                                                                      ║
║  Pulse::run() fires every 1,041 µs (120 BPM, 480 ticks/beat)       ║
║    → TickEvent { tick: 1440, beat: 2, bar: 0, phase: 0.0 }          ║
║    → broadcast to Ensemble via tokio::broadcast::Sender<TickEvent>  ║
║                                                    │                 ║
╚════════════════════════════════════════════════════╪═════════════════╝
                                                     │ pulse_rx.recv()
                                                     ▼
╔══════════════════════════════════════════════════════════════════════╗
║  ORCHESTRATION LAYER  (fleet-ensemble)                               ║
║                                                                      ║
║  Ensemble::tick(tick_event):                                         ║
║    1. Drain pending queue → collected_acts:                          ║
║         [(ch=0, Assertion), (ch=1, Objection), (ch=2, Question)]    ║
║                                                                      ║
║    2. Conflict resolution (RolePriority):                            ║
║         ch=0 Researcher (priority 4)                                 ║
║         ch=1 Critic     (priority 2)  ← wins on same pitch class    ║
║         ch=2 Explorer   (priority 5)                                 ║
║         All pass (different pitch classes, no conflict)              ║
║                                                                      ║
║    3. Forward to Harmonizer:                                         ║
║         harmonizer.harmonize(&collected_acts, &channel_roles)       ║
║                                                    │                 ║
╚════════════════════════════════════════════════════╪═════════════════╝
                                                     │
                                                     ▼
╔══════════════════════════════════════════════════════════════════════╗
║  HARMONY LAYER  (fleet-midi-harmonizer)                              ║
║                                                                      ║
║  Harmonizer::harmonize():                                            ║
║    1. Assign voices by role:                                         ║
║         Critic → Alto   (note=67, G4 = Objection)                   ║
║         Researcher → Soprano (note=62, D4 = Question)               ║
║         Explorer → Tenor   (note=60, C4 = Assertion)                ║
║         [Bass auto-filled from harmonic context C major]             ║
║                                                                      ║
║    2. Check counterpoint rules:                                      ║
║         G4-D4 = P5 ✓   no parallel fifths (no prior chord)         ║
║         D4-C4 = M2 ✗   voice crossing check: C4 < D4 ✓             ║
║         Max voice distance: Bass(C3=48) to Soprano(D4=62) = 14 semi ║
║         → exceeds max_voice_distance_semitones=7                    ║
║                                                                      ║
║    3. Correct: Harmonizer::correct()                                 ║
║         → spread voices: Bass=C3, Tenor=G3, Alto=D4, Soprano=G4    ║
║         → tension = 0.15 (some dissonance, within budget)           ║
║                                                                      ║
║    Returns: Chord { voices: [Soprano=G4, Alto=D4,                   ║
║                               Tenor=G3, Bass=C3],                   ║
║                     tension: 0.15 }                                  ║
║                                                    │                 ║
╚════════════════════════════════════════════════════╪═════════════════╝
                                                     │ Vec<CMidiEvent>
                                                     ▼
╔══════════════════════════════════════════════════════════════════════╗
║  BACK IN ENSEMBLE                                                    ║
║                                                                      ║
║  Ensemble::tick() continues:                                         ║
║    4. Flatten Chord → Vec<CMidiEvent>:                               ║
║         CMidiEvent { tick: 1440, channel: 1, act: Objection, vel:127, ║
║                      cc: [(Urgency,127),(Tension,90),(VL,45)] }      ║
║         CMidiEvent { tick: 1440, channel: 2, act: Question, vel:100 }║
║         CMidiEvent { tick: 1440, channel: 0, act: Assertion, vel:90 }║
║                                                                      ║
║    5. Log to conversation_log (for Conversation export)             ║
║                                                                      ║
║    6. Broadcast via WS gateway to studio clients                    ║
║                                                                      ║
║    Returns: Vec<CMidiEvent>                                          ║
║                                                    │                 ║
╚════════════════════════════════════════════════════╪═════════════════╝
                                      ┌─────────────┤
                                      │             │
                                      ▼             ▼
╔═══════════════════════════╗  ╔══════════════════════════════════════╗
║  LOCAL SYNTHESIS          ║  ║  BROWSER SYNTHESIS                   ║
║  (fleet-sound-toolkit)    ║  ║  (fleet-midi-synth WASM)             ║
║                           ║  ║                                      ║
║  AudioRenderer::          ║  ║  WavetableSynth::note_on()           ║
║    play_event(event)      ║  ║  → wavetable oscillator triggered    ║
║    → FluidSynth           ║  ║  → ADSR envelope applied            ║
║      GM program 56        ║  ║  → resonant LPF (vel → cutoff)      ║
║      (Trumpet)            ║  ║  → stereo panner (CC10 Sentiment)   ║
║    → stereo PCM to CPAL   ║  ║  → Web Audio output node           ║
║    → speakers             ║  ║  → speakers                         ║
╚═══════════════════════════╝  ╚══════════════════════════════════════╝
```

### 2.2 CC Propagation

CC events emitted by agents travel alongside note events and modulate synthesis in real time:

| CC | Name | Range | Effect at Synth |
|----|------|--------|-----------------|
| 1 | Engagement | 0–127 | Mod wheel → vibrato depth |
| 2 | Sarcasm | 0–127 | Breath controller → filter cutoff |
| 7 | Salience | 0–127 | Volume (main fader) |
| 10 | Sentiment | 0–127 | Pan: 0=left(objection) → 127=right(endorsement) |
| 11 | Nuance | 0–127 | Expression → amplitude envelope scale |
| 102 | Tension | 0–127 | Distortion/overdrive in RustFM; reverb in FluidSynth |
| 103 | VoiceLeading | 0–127 | Filter resonance — higher = more sinuous transitions |
| 104 | ConservationRatio | 0–127 | Master limiter ceiling: 0=silence, 127=full level |

---

## Section 3: Merge Targets

Three crates absorb the most legacy repos. Their merged scope is specified here.

### 3.1 `fleet-ensemble` absorbs 3

| Source | Absorbed as |
|--------|-------------|
| `fleet-midi-gateway` | `Ensemble::serve_gateway()` — WS server, protocol handling |
| `fleet-midi-conductor` | `Ensemble::tick()` priority queue + conflict resolution logic |
| `fleet-midi-router` | `I2IRouter` embedded in `Ensemble`, routes I2I messages between agents |

The gateway was a standalone HTTP/WS server. The conductor was event dispatch logic. The router was routing tables. All three are stateful subsystems of the ensemble — there is no scenario where they operate independently.

**Structural consequence**: `fleet-ensemble` depends on `fleet-i2i-protocol`. The router is `I2IRouter` from that crate, not a custom re-implementation.

### 3.2 `fleet-midi-harmonizer` absorbs 2

| Source | Absorbed as |
|--------|-------------|
| `fleet-midi-arpeggiator` | `Harmonizer::arpeggiate(chord, pattern) -> Vec<(tick_offset, Voice)>` |
| `fleet-midi-morph` | `Harmonizer::morph(from, to, config) -> Vec<Chord>` |

Both operations are transformations on `Chord` — the harmonizer's core type. Arpeggiating a chord is pattern-based voice extraction; morphing is interpolating between two chord voicings. Neither needs a separate crate; both are 50–150 line implementations on top of the existing harmonizer data structures.

**Structural consequence**: `fleet-midi-harmonizer::Harmonizer` gains two new methods with no new dependencies.

### 3.3 `fleet-midi-studio` absorbs 5 (+1 monitor)

| Source | Absorbed as |
|--------|-------------|
| `fleet-midi-sequencer` | `<Sequencer>` component — step grid with per-step mute/pitch/velocity |
| `fleet-midi-looper` | `<Transport>` `onLoop()` + loop region in PianoRoll |
| `fleet-midi-recorder` | `<Transport>` `onRecord()` + live capture to Conversation |
| `fleet-midi-composer` | `<ComposePanel>` — ternary input → harmonizer → piano roll preview |
| `fleet-midi-remapper` | `<RemapperConfig>` panel — per-channel MIDI effect insert |
| `fleet-midi-monitor` | `<MonitorPanel>` — real-time CC104 oscilloscope |

All six are UI panels or transport controls. The studio is a single-page application where these appear as dockable panes. No panel has backend logic that can't be handled by the studio's WS connection to the ensemble.

---

## Section 4: Deployment Targets

### 4.1 Local (CLI)

```
fleet-midi-pulse        → OS daemon thread (SCHED_FIFO on Linux)
fleet-ensemble          → tokio multi-thread runtime, Unix socket + WS gateway
fleet-sound-toolkit     → FluidSynth backend via libfluidsynth-dev, CPAL output
fleet-midi-studio       → browser pointed at ws://localhost:4747
fleet-i2i-protocol      → WS server on port 4748

Cargo features:
  fleet-midi-pulse/std
  fleet-ensemble/gateway,recording
  fleet-sound-toolkit/fluidsynth,cpal
```

**CLI binary** (`fleet-midi` crate):

```rust
// src/main.rs
#[tokio::main]
async fn main() {
    let pulse_config = PulseConfig::default();
    let pulse = Pulse::new(pulse_config);

    let harmonic_ctx = HarmonicContext { key_root: 0, mode: Mode::Major, tension_budget: 0.3 };
    let ensemble_config = EnsembleConfig {
        mode: EnsembleMode::Synchronous,
        conflict_resolution: ConflictResolution::RolePriority,
        harmonic_context: harmonic_ctx,
        max_agents: 8,
        dissonance_threshold: 0.7,
    };

    let mut ensemble = Ensemble::new(ensemble_config);
    ensemble.serve_gateway("0.0.0.0:4747").await.unwrap();

    let mut toolkit = SoundToolkit::with_fluidsynth(Path::new("GeneralUser.sf2")).unwrap();
    toolkit.stream_to_speakers().unwrap();

    let event_stream = ensemble.run(&pulse).await;
    pin_mut!(event_stream);
    while let Some(events) = event_stream.next().await {
        for event in events {
            toolkit.play_event(&event).ok();
        }
    }
}
```

### 4.2 Browser (WASM)

```
fleet-midi-pulse        → NOT compiled to WASM; pulse timing comes from WS connection
fleet-ensemble          → NOT compiled to WASM; runs server-side or in Node.js
fleet-midi-synth        → wasm-pack → ES module (fleet_midi_synth.js, ~50 KB gzip)
cmidi-core              → wasm-pack (for Conversation type, serialize/deserialize)
fleet-i2i-protocol      → wasm-pack (encode_sysex / decode_sysex only)

Cargo features:
  fleet-midi-synth/wasm
  cmidi-core/wasm (serde + wasm-bindgen)
  fleet-i2i-protocol/no_std (SysEx codec only)
```

**Browser initialization** (TypeScript):

```typescript
import init, { WavetableSynth, SynthConfig } from './fleet_midi_synth.js';

await init();

const synth = new WavetableSynth({
    sample_rate: 44100,
    voice_count: 32,
    attack_ms: 10,
    decay_ms: 50,
    sustain_level: 0.8,
    release_ms: 200,
});

synth.connect_pulse('ws://localhost:4747');  // connects to fleet-midi-pulse WS endpoint

// Studio mounts and routes CMidiEvent JSON from ensemble WS → synth
document.addEventListener('cmidi-event', (e: CustomEvent) => {
    const { channel, note, velocity } = e.detail;
    synth.note_on(channel, note, velocity);
});
```

**no_std surface available in WASM**: `SpeechAct`, `ConversationCC`, `CMidiEvent` (no alloc features), `encode_sysex` / `decode_sysex`.

### 4.3 Embedded (no_std)

Target: RP2040, STM32, ESP32 running `embassy` or bare-metal.

```
fleet-midi-pulse        → feature `no_std`: bare tick counter, no broadcast
fleet-sound-toolkit     → feature `no_std`: RustFMSynth only (no FluidSynth, no CPAL)
cmidi-core              → feature `no_std` + `no_alloc`: SpeechAct, CMidiEvent (no Vec, uses arrayvec)
fleet-i2i-protocol      → feature `no_std`: encode_sysex/decode_sysex with fixed-size buffers
```

**`no_std` constraints**:

```rust
// cmidi-core/src/lib.rs (no_std mode)
#![cfg_attr(not(feature = "std"), no_std)]
#[cfg(not(feature = "std"))]
extern crate alloc;

// CMidiEvent in no_alloc mode uses arrayvec:
#[cfg(feature = "no_alloc")]
pub struct CMidiEvent {
    pub tick: u32,
    pub agent_channel: u8,
    pub speech_act: SpeechAct,
    pub velocity: u8,
    pub duration: u32,
    pub cc_values: arrayvec::ArrayVec<(ConversationCC, u8), 8>,  // max 8 CC per event
}

// Pulse in no_std mode: just the tick counter + tick duration math
#[cfg(feature = "no_std")]
pub struct Pulse {
    tick: core::sync::atomic::AtomicU64,
    tick_duration_us: u64,
}

#[cfg(feature = "no_std")]
impl Pulse {
    pub fn new(bpm: f64, ticks_per_beat: u32) -> Self;
    pub fn tick(&self) -> TickEvent;   // called from timer ISR
    pub fn current_tick(&self) -> u64;
}
```

**UART / DIN MIDI output** on embedded: `fleet-i2i-protocol::encode_sysex()` → write bytes to UART1 at 31250 baud.

---

## Section 5: Cargo Workspace Structure

```toml
# Cargo.toml (workspace root)
[workspace]
members = [
    "cmidi-core",
    "cmidi-conservation",
    "fleet-i2i-protocol",
    "fleet-midi-pulse",
    "fleet-midi-harmonizer",
    "fleet-ensemble",
    "fleet-sound-toolkit",
    "fleet-midi-synth",           # WASM crate, separate wasm-pack build
    "fleet-diffrhythm-connector",
    "fleet-rave-connector",
    "fleet-maidi-connector",
    # Math foundation (for harmonizer):
    "groovemesh-plr",             # already exists at /tmp/nightshift/
    # Bridge:
    "spreadsheet-plr-bridge",     # already spec'd at /tmp/nightshift/
]
resolver = "2"

[workspace.dependencies]
cmidi-core       = { path = "cmidi-core",       version = "0.1" }
cmidi-conservation = { path = "cmidi-conservation", version = "0.1" }
groovemesh-plr   = { path = "groovemesh-plr",   version = "0.1" }
tokio            = { version = "1", features = ["full"] }
serde            = { version = "1", features = ["derive"] }
serde_json       = "1"
arrayvec         = { version = "0.7", default-features = false }
```

### Dependency graph (directed, acyclic)

```
cmidi-core          (no internal deps)
fleet-i2i-protocol  → cmidi-core
fleet-midi-pulse    → (none — pure timing)
groovemesh-plr      → (none — pure math)
fleet-midi-harmonizer → cmidi-core, groovemesh-plr
fleet-ensemble      → cmidi-core, fleet-midi-pulse, fleet-midi-harmonizer, fleet-i2i-protocol
cmidi-conservation  → cmidi-core
fleet-sound-toolkit → cmidi-core, [fluidsynth-sys], [cpal]
fleet-midi-synth    → cmidi-core, [wasm-bindgen], [web-sys]
fleet-midi-studio   → (TypeScript, not Rust)
fleet-diffrhythm-connector → cmidi-core, reqwest
fleet-rave-connector        → cmidi-core, torch (optional, via libtorch-sys)
fleet-maidi-connector       → cmidi-core
spreadsheet-plr-bridge      → cmidi-core, groovemesh-plr, spreadsheet-engine
```

No cycles. `cmidi-core` and `fleet-midi-pulse` are the only crates with zero internal dependencies.

---

## Section 6: P0 Build Sequence

Per STUB_AUDIT.md priority queue. All four P0 crates can be partially parallelized:

```
Week 1-2 (parallel):
    fleet-midi-pulse     — timing layer, standalone
    groovemesh-plr       — PLR math, standalone (already started at /tmp/nightshift/)
    fleet-i2i-protocol   — messaging layer, depends only on cmidi-core

Week 3-4 (parallel):
    fleet-midi-harmonizer — depends on cmidi-core + groovemesh-plr
    fleet-ensemble        — depends on pulse + i2i-protocol

Week 5:
    Integration test: 4-agent ensemble, synchronized debate, .mid export

P0 Exit Criteria (from audit):
    4 agents hold a synchronized debate in 4/4 at 120 BPM.
    Harmonizer corrects dissonant speech acts in real time.
    Output exports to a valid .mid file playable in any DAW.
```

---

## Section 7: Open Questions

1. **PLR vs. key-based harmonization**: The harmonizer spec uses a key + mode model (C major, A minor, etc.). The `groovemesh-plr` crate uses PLR group operations on triads. These are compatible but distinct: PLR operates locally (one chord to adjacent chord), key-based operates globally (all notes evaluated against a scale). Recommended: harmonizer uses key-based rules for initial chord assignment, then calls `groovemesh-plr::CounterpointRules::check()` for validation. Both layers active.

2. **Embedded tick source**: On RP2040, `fleet-midi-pulse` in `no_std` mode needs a hardware timer ISR calling `pulse.tick()` at 1 ms intervals. The crate should not dictate the ISR binding — it should expose `Pulse::tick()` as a callable from any timer interrupt handler.

3. **RAVE model format**: The RAVE connector calls TorchScript (`.ts`) models via `libtorch`. This adds a ~200 MB C++ dependency. Alternative: export RAVE to ONNX and use `ort` (ONNX Runtime, ~20 MB). Recommend ONNX path for portability.

4. **M(AI)DI ghost player conflict**: The ghost player submits to the ensemble via `Ensemble::submit()`. If the ghost player is assigned `AgentRole::Explorer` (priority 5), its suggestions are low-priority and easily overridden by human agents. This is the intended behavior — the ghost player should suggest, not override. Confirm this priority assignment is correct before implementation.

5. **Fleet-midi-studio WS protocol**: The studio communicates with the ensemble gateway via WebSocket. The message format (binary vs. JSON vs. MIDI bytes) should be decided before the gateway is implemented. Recommendation: binary for performance-critical streams (CMidiEvent at 480 ticks/beat × 16 channels), JSON for control (agent registration, mute/solo, config changes).
