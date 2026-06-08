# fleet-science

**Research papers, specifications, audits, and design documents for the SuperInstance ecosystem.**

This is not a software package — it's the intellectual backbone. Every crate in the ecosystem traces its design to a document here.

## What's Here

### Papers (`papers/`)
| Document | Words | What It Argues |
|----------|-------|----------------|
| [SPREADSHEET_MOMENT_WHITEPAPER.md](papers/SPREADSHEET_MOMENT_WHITEPAPER.md) | 6,174 | The "spreadsheet moment for AI" — why reactive compute grids with agent cells are the next interface paradigm |
| [THE_SYMPHONIC_FLEET.md](papers/THE_SYMPHONIC_FLEET.md) | 2,800 | Fleet as orchestra — each agent is a voice, PLR group ensures harmonic coherence, conservation law is the tempo |
| [ACADEMIC_PAPER_TROPICAL_SYNTH.md](papers/ACADEMIC_PAPER_TROPICAL_SYNTH.md) | ~3,000 | Tropical geometry as a framework for synthesizer patch design. arXiv priority claim |
| [COMPETITIVE_LANDSCAPE.md](papers/COMPETITIVE_LANDSCAPE.md) | ~2,500 | Where each crate sits in the market. Most are blue ocean — no equivalent exists on crates.io |
| [CROSS_POLLINATION_IDEAS.md](papers/CROSS_POLLINATION_IDEAS.md) | ~1,500 | 16 killer integration ideas from multi-model ideation (Gemma 4 + Hermes 405B + Claude synthesis) |

### Specifications (`specs/`)
| Document | Lines | What It Defines |
|----------|-------|-----------------|
| [ECOSYSTEM_MAP.md](specs/ECOSYSTEM_MAP.md) | 1,109 | Cross-crate developer's guide. 4-layer architecture, 18 pairwise connections, getting-started path |
| [CELLULAR_AGENT_PROTOCOL.md](specs/CELLULAR_AGENT_PROTOCOL.md) | 1,415 | UCAP — Unified Cellular Agent Protocol. Cells have membrane/metabolism/signaling/homeostasis |
| [INTEGRATION_SPEC.md](specs/INTEGRATION_SPEC.md) | 899 | How crates compose. API-level integration patterns, type flow, code examples |
| [BRIDGE_CRATE_DESIGN.md](specs/BRIDGE_CRATE_DESIGN.md) | 1,734 | Design for bridge crates connecting spreadsheet-engine to fleet ecosystem |
| [FLEET_CLI_DESIGN.md](specs/FLEET_CLI_DESIGN.md) | 971 | CLI tool design for fleet operations — inspect, publish, compose |
| [FLEET_MIDI_ARCHITECTURE.md](specs/FLEET_MIDI_ARCHITECTURE.md) | 730 | MIDI pipeline architecture — from ternary vectors to audible sound |
| [CROSS_CRATE_DEPENDENCY_MAP.md](specs/CROSS_CRATE_DEPENDENCY_MAP.md) | 520 | Which crates can depend on which. No circular deps, 4-layer stack |

### Audits (`audits/`)
| Document | What Was Audited | Finding |
|----------|-----------------|---------|
| [STUB_AUDIT.md](audits/STUB_AUDIT.md) | 200 of 300 repos | 2/3 are stubs. 30 BUILD IT specs prioritized |
| [AUDIT_TERNARY_ML.md](audits/AUDIT_TERNARY_ML.md) | 8 ternary ML repos | ALL REAL, 139 tests, 0 failures |
| [AUDIT_BROWSER_PYTHON_SPREADSHEETS.md](audits/AUDIT_BROWSER_PYTHON_SPREADSHEETS.md) | 6 browser/Python repos | 3 real, 3 stubs. Browser demo needs persistence |
| [AUDIT_RUST_SPREADSHEETS.md](audits/AUDIT_RUST_SPREADSHEETS.md) | 4 Rust spreadsheet crates | spreadsheet-engine is production-grade. Others are stubs |

### Design (`design/`)
| Document | What It Designs |
|----------|----------------|
| [groovemesh/](design/groovemesh/) | GrooveMesh — collaborative counterpoint engine. PLR group algebra ensures you can never play a wrong note. 4 docs: architecture, library spec, proof, protocol |

### Proofs (`proofs/`)
| Document | What It Proves |
|----------|----------------|
| [lewin_gmit_connection.md](proofs/lewin_gmit_connection.md) | Connection between Lewin's GIS framework and fleet conservation law |
| [z3_group_proof.md](proofs/z3_group_proof.md) | Z/3Z group structure in ternary agent coordination |

### Reviews (`reviews/`)
| Document | What It Reviews |
|----------|----------------|
| [SPREADSHEET_REVIEW.md](reviews/SPREADSHEET_REVIEW.md) | Code review + beta tester audit of the browser spreadsheet demo |

## How to Use This Repo

**For developers joining the ecosystem**: Read ECOSYSTEM_MAP.md first. It maps every crate and how they connect.

**For researchers**: Start with SPREADSHEET_MOMENT_WHITEPAPER.md for the vision, then CELLULAR_AGENT_PROTOCOL.md for the architecture.

**For auditors**: STUB_AUDIT.md tells you what exists vs what's aspirational across 200+ repos.

## Architecture Principle

The SuperInstance ecosystem has no compile-time dependencies between crates. Every crate depends only on `serde`, `thiserror`, and standard library. All integration is at the API and type level — crates compose by agreeing on data formats, not by importing each other's code.

This is intentional. It means:
- Each crate can be used independently
- Breaking changes in one crate don't cascade
- The ecosystem is a toolkit, not a framework
- New crates slot in by conforming to shared type conventions

## Related Repos

- [spreadsheet-engine](https://github.com/SuperInstance/spreadsheet-engine) — the core reactive compute grid
- [tropical-synth](https://github.com/SuperInstance/tropical-synth) — tropical geometry for synthesizer design
- [groovemesh-plr](https://github.com/SuperInstance/groovemesh-plr) — PLR group voice leading
- [fleet-ensemble](https://github.com/SuperInstance/fleet-ensemble) — multi-agent music coordination
- [construct-coordination](https://github.com/SuperInstance/construct-coordination) — I2I bottle exchange between Forgemaster and Oracle2

## Stats

- **24 documents** across 6 directories
- **696 KB** total
- **30+ crates** designed and specified here
- **30 BUILD IT specs** ready for implementation
- **18 pairwise crate connections** mapped
