# Bundled Active Theory (Nondual Core)
BUNDLED_THEORY = r"""<BEGIN NONDUAL CORE>
# Nondual Core — Symbolic Logic Extraction

This document renders axioms, definitions, locale assumptions, and selected lemma/theorem statements from the uploaded Isabelle/HOL sources in symbolic notation.

## File: `Nondual_Core.thy`

### Axiomatization
- **ND1**: `∀ phi. Valid phi → (∃ i. phi = pi omega0 i)`
- **ND2**: `∀ om. om = omega0`
- **ND3**: `∀ p. ¬ HasIntrinsicProperty omega0 p`
- **ND4**: `∀ phi. Valid phi = (g phi > 0)`
- **ND5**: `∀ i phi1 phi2. Valid phi1 ∧ Valid phi2 ∧ t i phi1 < t i phi2 → c phi1 ≤ c phi2`
- **ND6**: `∀ i phi. Physical i phi → Stationary i phi`
- **ND7**: `∀ i1 i2. pi omega0 i1 ¬= pi omega0 i2 → DifferenceInIndexing i1 i2`

## File: `Schema_CICY_Hodge_Calculation.thy`

### Axiomatization
- **bott_formula**: `∀ n d p.
      line_bundle_cohomology n d p =
        (if p = 0 ∧ d ≥ 0 then
           binomial (n + nat d) n
         else if p = n ∧ d < - (int n) then
           binomial (nat (-d - 1)) n
         else 0)`

### Definitions
- **alt_sign**: `alt_sign k = (if even k then 1 else -1)`
- **koszul_term**: `koszul_term config i k = exterior_power k (dual (normal_bundle config i))`
- **euler_char_from_koszul**: `euler_char_from_koszul config =
     (let K = length config in
      sum (%k. alt_sign k * int (cohomology (koszul_term config 0 k) 0)) {0 ..< K})`
- **h11_formula_int**: `h11_formula_int config =
     (let K = length config;
          n = hd (ambient_dims config)
      in int (card {i. i < K ∧ line_bundle_cohomology n 1 1 = 0}) - int (K - 1))`
- **h11_formula**: `h11_formula config = h11_formula_int config`

### Locales (Assumptions)
- **locale CICY_1724_Reduction**
  - ambient_hd_7: `hd (ambient_dims CICY_1724_config) = 7`
  - exact_sequence_calculation: `h11_formula CICY_1724_config =
       (4 * int (binomial 8 7)) + correction_term - 3`
  - detailed_koszul_calculation: `correction_term = 28`

### Lemmas/Theorems (Statements)
- **h11_CICY_1724_numeric_local**: `h11_formula CICY_1724_config = 32 + correction_term - 3`
- **h11_CICY_1724_local**: `h11_formula CICY_1724_config = 57`

## File: `Schema_CY3_Topology.thy`
... (full content omitted here only in code comment; full string is included in the active theory)

<END NONDUAL CORE>
"""
