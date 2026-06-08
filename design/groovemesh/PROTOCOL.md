# GrooveMesh WebSocket Protocol Specification

Version: 1.0.0

---

## Transport

- **Protocol:** WebSocket (RFC 6455), `ws://` or `wss://`
- **Subprotocol:** `groovemesh.v1`
- **Endpoint:** `ws://<host>:<port>/session/<session_id>`
- **Frame types:** Two distinct frame channels over the same connection:
  - **Text frames:** JSON control messages (session management, chord navigation)
  - **Binary frames:** Raw MIDI bytes (note events, clock pulse)

All JSON messages are UTF-8. All binary frames use the encoding in §5.

---

## §1. Session Lifecycle

### 1.1 Connection Handshake

Client opens WebSocket to `ws://<host>/session/<session_id>`. If the session does
not exist, the server returns HTTP 404 before the upgrade completes.

After the WS upgrade, the server immediately sends a `session.welcome` message:

```json
{
  "type": "session.welcome",
  "session_id": "01928a7f-...",
  "assigned_voice": "Alto",
  "voice_channel": 1,
  "chord": {
    "root": 0,
    "major": true
  },
  "tick": 4320,
  "tempo_bpm": 120.0,
  "clients": [
    { "id": "...", "name": "Alice", "voice": "Soprano" },
    { "id": "...", "name": "Bob",   "voice": "Alto"    }
  ]
}
```

The client must respond with `client.hello` within 5 seconds or the connection
is closed with code 4001 (timeout):

```json
{
  "type": "client.hello",
  "client_id": "01928b3c-...",
  "display_name": "Eve"
}
```

### 1.2 Client Join Broadcast

When a new client joins, all existing clients receive:

```json
{
  "type": "client.joined",
  "client_id": "01928b3c-...",
  "display_name": "Eve",
  "voice": "Tenor",
  "tick": 4800
}
```

### 1.3 Client Leave Broadcast

When a client disconnects (graceful or timeout):

```json
{
  "type": "client.left",
  "client_id": "01928b3c-...",
  "voice": "Tenor",
  "tick": 5760
}
```

### 1.4 Session State Sync

Any client may request a full session snapshot at any time (e.g., after reconnect):

```json
{ "type": "session.sync_request" }
```

Server responds with `session.snapshot`:

```json
{
  "type": "session.snapshot",
  "session_id": "...",
  "chord": { "root": 9, "major": false },
  "tick": 9600,
  "tempo_bpm": 120.0,
  "clients": [ ... ],
  "active_notes": [
    { "voice": "Soprano", "note": 69, "velocity": 100, "since_tick": 9120 },
    { "voice": "Bass",    "note": 45, "velocity": 90,  "since_tick": 9120 }
  ]
}
```

---

## §2. Note Events

### 2.1 Client → Server: Note Input

Clients send raw note events as JSON:

```json
{
  "type": "note.on",
  "note": 64,
  "velocity": 90,
  "tick": 9120
}
```

```json
{
  "type": "note.off",
  "note": 64,
  "tick": 9600
}
```

**Fields:**
- `note`: MIDI note number, 0–127 (required). Rejected with `error.note_invalid` if out of range.
- `velocity`: MIDI velocity, 1–127 (required for `note.on`). Rejected if 0 or > 127.
- `tick`: Client's local tick at the moment of the event. Used for jitter correction.
  Server adjusts ±20 ticks to align with its clock; discards events more than
  100 ticks out of sync (sends `error.tick_skew` to client).

### 2.2 Server → All Clients: Corrected Note Broadcast

After projecting and assigning voice, the server broadcasts as a **binary MIDI frame**
(see §5) plus a JSON metadata message:

```json
{
  "type": "note.broadcast",
  "client_id": "...",
  "voice": "Alto",
  "voice_channel": 1,
  "original_note": 64,
  "corrected_note": 64,
  "velocity": 90,
  "tick": 9120,
  "projection_cost": 0
}
```

`projection_cost` is the number of semitones the note was moved to land in the
current chord. 0 means the note was already valid.

### 2.3 Velocity to CC Mapping

GrooveMesh maps MIDI velocity to `cmidi-core` CC values for analytics:

| CC | Meaning           | Value mapping                      |
|----|-------------------|------------------------------------|
| 7  | Salience          | velocity directly                  |
| 103| VoiceLeading      | 127 − (projection_cost × 20)       |
| 104| ConservationRatio | fixed per voice: S=127,A=100,T=80,B=60 |

These CCs are attached to the broadcast MIDI event.

---

## §3. Chord Navigation

### 3.1 Client → Server: PLR Navigate

Any client may propose a PLR operation. The server applies it immediately and
broadcasts the result:

```json
{
  "type": "chord.navigate",
  "op": "R"
}
```

`op` must be one of `"P"`, `"L"`, `"R"`. Other values return `error.invalid_op`.

### 3.2 Server → All Clients: Chord State Update

```json
{
  "type": "chord.update",
  "prev_chord": { "root": 0, "major": true },
  "next_chord": { "root": 9, "major": false },
  "op": "R",
  "voice_leading_cost": 3.0,
  "voice_assignments": [
    { "voice": "Soprano", "note": 69 },
    { "voice": "Alto",    "note": 64 },
    { "voice": "Tenor",   "note": 60 },
    { "voice": "Bass",    "note": 57 }
  ],
  "tick": 9600
}
```

`voice_assignments` lists the canonical notes for the new chord in each voice.
Clients should smoothly transition sounding notes to these targets (glide or
retrigger depending on their preference).

### 3.3 Client → Server: Slide to Target

Request a BFS shortest-path glide from the current chord to a target triad.
The server emits one `chord.update` per hop, spaced `ticks_per_beat` ticks apart:

```json
{
  "type": "chord.slide",
  "target": { "root": 5, "major": true },
  "speed_beats": 1
}
```

`speed_beats`: how many beats per hop (default 1). Range: 0.25–4.0.

Server responds immediately with the full path, then fires chord updates on schedule:

```json
{
  "type": "chord.slide_plan",
  "hops": [
    { "op": "R", "triad": { "root": 9, "major": false } },
    { "op": "L", "triad": { "root": 5, "major": true  } }
  ],
  "total_beats": 2
}
```

### 3.4 Server → All: Tempo Update

```json
{
  "type": "session.tempo",
  "tempo_bpm": 140.0,
  "tick": 9600
}
```

Only the session creator may send `session.tempo_request`. All others receive
this broadcast.

---

## §4. Clock Sync

### 4.1 Server → All: Tick Pulse

Every beat (480 ticks at default tempo), the server broadcasts a binary tick pulse
(see §5.2). Clients use this to keep their local tick synchronized.

### 4.2 Client → Server: Ping

```json
{ "type": "ping", "t": 1749381234567 }
```

Server responds:

```json
{ "type": "pong", "t": 1749381234567, "server_tick": 9600 }
```

`t` is the client's Unix timestamp in milliseconds, echoed back unchanged.
`server_tick` is the server's current MIDI tick. Clients use this to compute
clock offset.

---

## §5. Binary Frame Encoding

Binary frames carry time-critical MIDI data with minimal overhead.

### 5.1 Note Event Frame (9 bytes)

```
Offset  Size  Field
──────  ────  ──────────────────────────────────────────────
0       1     frame_type = 0x01 (note event)
1       8     tick (u64, big-endian)
9       1     status byte (0x90|channel = Note On, 0x80|channel = Note Off)
10      1     note (0–127)
11      1     velocity (0–127)
```

Total: 12 bytes.

### 5.2 Tick Pulse Frame (9 bytes)

```
Offset  Size  Field
──────  ────  ──────────────────────────────────────────────
0       1     frame_type = 0x02 (tick pulse)
1       8     tick (u64, big-endian)
```

Total: 9 bytes.

### 5.3 Chord Change Frame (4 bytes)

Sent in addition to the JSON `chord.update` for low-latency rendering:

```
Offset  Size  Field
──────  ────  ──────────────────────────────────────────────
0       1     frame_type = 0x03 (chord change)
1       1     root (0–11)
2       1     quality (0 = major, 1 = minor)
3       1     op (0=P, 1=L, 2=R)
```

Total: 4 bytes.

### 5.4 MIDI CC Frame (12 bytes)

```
Offset  Size  Field
──────  ────  ──────────────────────────────────────────────
0       1     frame_type = 0x04 (CC event)
1       8     tick (u64, big-endian)
9       1     status byte (0xB0|channel)
10      1     cc_number
11      1     value
```

Total: 12 bytes.

---

## §6. Error Messages

All errors follow this envelope:

```json
{
  "type": "error",
  "code": "note_out_of_range",
  "message": "note 200 is outside MIDI range [0, 127]",
  "tick": 9600
}
```

| `code`                | Cause                                          | Client action                  |
|-----------------------|------------------------------------------------|--------------------------------|
| `note_out_of_range`   | note not in 0–127                              | Clamp to range                 |
| `velocity_out_of_range`| velocity not in 1–127                         | Clamp to range                 |
| `tick_skew`           | Client tick > 100 ticks ahead/behind server   | Re-sync via ping               |
| `invalid_op`          | PLR op not P/L/R                               | Check message format           |
| `session_full`        | All 16 voice slots occupied                    | Wait for a client to leave     |
| `session_not_found`   | Session ID doesn't exist                       | Create a new session           |
| `unknown_client`      | client_id not in session                       | Send `client.hello` again      |
| `rate_limited`        | >100 note events per second from one client    | Back off 100ms                 |
| `protocol_error`      | Malformed JSON or unknown message type         | Check protocol version         |

---

## §7. WebSocket Close Codes

| Code  | Meaning                                       |
|-------|-----------------------------------------------|
| 1000  | Normal closure                                |
| 1001  | Server shutting down                          |
| 4000  | Protocol version mismatch                     |
| 4001  | `client.hello` timeout (5 seconds)            |
| 4002  | Session eviction (idle > 30 minutes)          |
| 4003  | Banned (rate limit exceeded repeatedly)       |
| 4004  | Session full, no slot available               |

---

## §8. Rate Limits

| Limit                              | Default  | Configurable |
|------------------------------------|----------|--------------|
| Note events per client per second  | 100      | Yes          |
| PLR navigations per client per second | 10    | Yes          |
| JSON messages per client per second | 200     | Yes          |
| Max binary frame size              | 64 bytes | No           |
| Max JSON message size              | 4 KB     | No           |

Exceeding any limit triggers `error.rate_limited`. Three violations within 10 seconds
close the connection with code 4003.

---

## §9. Example Session Transcript

```
C→S  [WS connect to /session/01928a7f-...]
S→C  {"type":"session.welcome","assigned_voice":"Alto","chord":{"root":0,"major":true},...}
C→S  {"type":"client.hello","client_id":"...","display_name":"Eve"}
S→All {"type":"client.joined","display_name":"Eve","voice":"Alto",...}

C→S  {"type":"note.on","note":64,"velocity":90,"tick":480}
S→All [binary: 0x01 0x00..0x01E0 0x91 0x40 0x5A]  ← Note On, Alto ch=1, E4, vel=90
S→All {"type":"note.broadcast","voice":"Alto","corrected_note":64,"projection_cost":0,...}

C→S  {"type":"chord.navigate","op":"R"}
S→All [binary: 0x03 0x09 0x01 0x02]               ← chord change: A minor via R
S→All {"type":"chord.update","prev_chord":{"root":0,"major":true},
        "next_chord":{"root":9,"major":false},"op":"R",...}

C→S  {"type":"note.on","note":66,"velocity":80,"tick":960}
     ↑ F#4, not in A minor {A,C,E}
S→All [binary: 0x01 0x00..0x03C0 0x91 0x45 0x50]  ← corrected to A4 (note 69)
S→All {"type":"note.broadcast","original_note":66,"corrected_note":69,"projection_cost":3,...}

C→S  {"type":"note.off","note":64,"tick":1440}
S→All [binary: 0x01 0x00..0x05A0 0x81 0x40 0x00]  ← Note Off

C→S  [WS close 1000]
S→All {"type":"client.left","client_id":"...","voice":"Alto"}
```
