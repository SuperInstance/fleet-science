# Lewin's Generalized Interval Systems — Direct Implementation

## The Insight
David Lewin's *Generalized Musical Intervals and Transformations* (1987)
defines a GIS as (S, IVLS, int) where:
- S is a set of musical objects
- IVLS is a group of intervals
- int: S × S → IVLS is an interval function

Our implementation:
- S = {-1, 0, +1}ⁿ (all ternary vectors of length n)
- IVLS = Z₃ (the cyclic group of order 3)
- int(v₁, v₂) = v₂ - v₁ (element-wise, modulo 3 with conservation)

This is a valid GIS. And because our interval group is Z₃,
every transformation corresponds to a Neo-Riemannian operation.

## Key Paper
Lewin, D. (1987). *Generalized Musical Intervals and Transformations.*
Yale University Press.
