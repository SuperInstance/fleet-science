# 🔬 fleet-science

**The science behind the SuperInstance ternary system — papers, experiments, proofs.**

Every mathematical claim in the fleet is proven here. Every experiment is documented with
reproducible steps. Every paper is summarized with its connection to the fleet.

## Papers

| Paper | Connection | Experiment |
|-------|-----------|------------|
| Lewin, *GMIT* (1987) | Group theory foundation for interval mapping | Run `python experiments/gmit_proof.py` |
| Cohn, *Audacious Euphony* (2012) | Hexatonic cycles = conservation pairs | Run `python experiments/hexatonic.py` |
| Tymoczko, *Geometry of Music* (2011) | Chord space = state vector space | Run `python experiments/geometry.py` |
| *MusicVAE* (2018) | Latent space interpolation = vector morph | See experiments/musicvae.md |
| *DDSP* (2020) | MIDI→realistic audio rendering | Run `python experiments/ddsp_bridge.py` |

## Experiments

| Experiment | Reproduces | How to run |
|-----------|-----------|------------|
| Ternary group closure | The group axioms | `python proofs/group_closure.py` |
| Conservation law | +1 + (-1) = 0 in music | `python proofs/conservation.py` |
| 10-language verification | Same output across all langs | `bash run_all.sh` |
| Markov style preservation | Vocabulary preserved across generations | `python proofs/markov_preservation.py` |

## Proofs

All proofs runnable in Python, with implementations in Rust, C, C++, Go, JS, WASM, Mojo, Chapel, CUDA.
