# theory_map.py
# Raw symbolic logic provided by the user. You can parse or map it further if needed.
SYMBOLIC_LOGIC_MD = r"""# Symbolic Logic Conversion

## Domain

E: entities  
Ω: unique substrate

## Predicates

- Φ(x): x is phenomenon
- Σ(x): x is substrate  
- P(x,y): x presents y
- I(x,y): x inseparable from y
- C(x,y): x causally precedes y
- Ess(x): x has essence
- A(x,y): x arises from y
- O(a,x): agent a owns x
- V(x): x valid convention
- Ap(c,x): concept c applies to x

## Core Axioms

A1: ∃s. Σ(s)

A2: ∀a,b. Σ(a) ∧ Σ(b) → a = b

A3: ∀x. Φ(x) ∨ Σ(x)

A4: ∀p,s. Φ(p) ∧ Σ(s) → P(p,s)

A5: ∀x,y. I(x,y) ↔ (∃s. Σ(s) ∧ P(x,s) ∧ y = s)

## Theorems

T1 (Unique substrate): ∃!s. Σ(s)

T2 (Substrate is Ω): Σ(Ω)

T3 (Only Ω): Σ(s) → s = Ω

T4 (Non-duality): ∀p. Φ(p) → I(p,Ω)

## Causality

C1: ∀x,y. C(x,y) → Φ(x) ∧ Φ(y)

C2: ∀x. Φ(x) → ¬C(x,x)

C3: ∀x,y,z. C(x,y) ∧ C(y,z) → C(x,z)

T5: C(x,y) → I(x,Ω) ∧ I(y,Ω)

## Spacetime

f: frame, r: coordinates

S1: coord(f,x) = Some(r) → Φ(x)

S2: GaugeRel(f,g) → (coord(f,x) = None ↔ coord(g,x) = None)

T6: coord(f,x) ≠ None → I(x,Ω)

## Emptiness

E1: ∀x. Φ(x) → ¬Ess(x)

## Dependent Arising

D1: ∀p,q. A(p,q) → Φ(p) ∧ Φ(q)

D2: ∀p,q. A(p,q) → (∃s. Σ(s) ∧ P(p,s) ∧ P(q,s))

D3: ∀p,q. A(p,q) → ¬(∃z. ¬Φ(z) ∧ ¬Σ(z))

## Ownership

O1: ∀a,p. O(a,p) → Φ(p) ∧ V(p)

O2: ∀a,p. O(a,p) → I(p,Ω) ∧ ¬Ess(p)

## Gauge Symmetry

g: group element, act(g,x): action

G1: ∀g,x. Φ(x) → Φ(act(g,x))

G2: ∀g,x. P(x,Ω) → P(act(g,x),Ω)

T7: Φ(x) → I(act(g,x),Ω)

## Concepts

C1: ∀c,x. Ap(c,x) → Φ(x)

T8: Ap(c,x) → I(x,Ω)

## Information

Q: quantity type, Info(x): information quantity

I1: ∀x. Φ(x) → Nonneg(Info(x))

T9: Φ(x) → I(x,Ω)

## Time

T(x): time index, LT(q₁,q₂): q₁ < q₂

T1: ∀q. ¬LT(q,q)

T2: ∀a,b,c. LT(a,b) ∧ LT(b,c) → LT(a,c)

T3: ∀x,y. C(x,y) → LT(T(x),T(y))

T10: Φ(x) → I(x,Ω)

## Two Levels

L1: ∀x. V(x) → Φ(x)

L2: Coherent(Ω)

## Alternative Notation

NotTwo(x,y) ≝ I(x,y)

T11: Φ(p) → NotTwo(p,Ω)

T12: Φ(x) → NotTwo(x,Ω)
"""
