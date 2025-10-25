# validator.py — ND-aware structured-claims normalizer + validator
# Extends the phenomenology schema with Nondual Core constraints (ND1–ND7).

Ω = 'Ω'

def _as_str(x):
    return x if isinstance(x, str) else str(x)

def _normalize_claims(claims):
    import json
    out, soft = [], []
    if not isinstance(claims, list):
        return [], ["claims must be a list"]
    for i, c in enumerate(claims):
        if isinstance(c, str):
            try:
                c = json.loads(c)
            except Exception:
                soft.append(f"claim[{i}] not valid JSON; skipped")
                continue
        if not isinstance(c, dict):
            soft.append(f"claim[{i}] is not an object; skipped")
            continue
        p = c.get("predicate"); a = c.get("args")
        if not isinstance(p, str):
            soft.append(f"claim[{i}] missing predicate; skipped")
            continue
        if not isinstance(a, list):
            a = [a] if a is not None else []
        a = [_as_str(x) for x in a]
        # alias omega0 => Ω in args
        a = [("Ω" if x == "omega0" else x) for x in a]
        out.append({"predicate": p, "args": a})
    return out, soft

def _collect_args(claim, idxs):
    a = claim.get("args", [])
    return [a[i] for i in idxs if i < len(a)]

def repair(payload):
    import copy
    d = copy.deepcopy(payload if isinstance(payload, dict) else {})
    claims, _ = _normalize_claims(d.get("claims", []))

    # Substrate aliasing: Substrate(omega0) -> Substrate(Ω)
    for c in claims:
        if c["predicate"] == "Substrate" and c.get("args") and c["args"][0] == "omega0":
            c["args"][0] = "Ω"

    # Auto-infer phenomena for various relations (and then inseparability)
    def add_pheno(x):
        if not any(cc for cc in claims
                   if cc["predicate"] == "Phenomenon" and len(cc["args"]) == 1 and cc["args"][0] == x):
            claims.append({"predicate": "Phenomenon", "args": [x]})

    ND_rels = {
        "CausallyPrecedes": (0, 1),
        "HasCoords": (1,),
        "ArisesFrom": (0, 1),
        "TimeOrder": (1, 2),
        "ComplexityOrder": (0, 1),
        "Physical": (1,),
        "Stationary": (1,),
        "PiEq": (0,),
        "PiDistinct": (0, 1),
        "Owns": (1,),
    }

    for c in list(claims):
        p = c["predicate"]
        if p in ND_rels:
            for idx in ND_rels[p]:
                args = c.get("args", [])
                if idx < len(args):
                    x = args[idx]
                    if x not in ("Ω",):
                        add_pheno(x)

    # Auto: Phenomenon(x) ⇒ Inseparable(x, Ω)
    phenos = {c["args"][0] for c in claims if c["predicate"] == "Phenomenon" and len(c["args"]) >= 1}
    inseps = {(c["args"][0], c["args"][1]) for c in claims
              if c["predicate"] in ("Inseparable", "NotTwo") and len(c["args"]) >= 2}
    for x in phenos:
        if (x, Ω) not in inseps:
            claims.append({"predicate": "Inseparable", "args": [x, "Ω"]})

    # Auto: Owns(a,p) ⇒ ValidConv(p)
    owned = [(c["args"][0], c["args"][1]) for c in claims if c["predicate"] == "Owns" and len(c["args"]) >= 2]
    valid = {c["args"][0] for c in claims if c["predicate"] == "ValidConv" and len(c["args"]) >= 1}
    for (_, p) in owned:
        if p not in valid:
            claims.append({"predicate": "ValidConv", "args": [p]})

    d["claims"] = claims
    return d

def _richness_check(claims):
    informative = [
        c for c in claims
        if c["predicate"] in (
            "CausallyPrecedes", "HasCoords", "Applies", "Owns",
            "ArisesFrom", "LT", "TimeOrder", "ComplexityOrder"
        )
    ]
    return len(informative) >= 1

def validate(payload):
    import copy
    errors = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]

    payload = copy.deepcopy(payload)
    claims, soft = _normalize_claims(payload.get("claims", []))
    errors.extend(soft)

    citations = payload.get("citations", [])
    if citations is None:
        citations = []
    if not isinstance(citations, list):
        citations = [citations]
    citations_text = " | ".join([str(x) for x in citations])

    P, S, I, E, H, C, O, V, A = set(), set(), set(), set(), set(), set(), set(), set(), set()

    # ND flags
    used_ND5 = False
    used_ND6 = False
    used_ND7 = False

    # Track presence for ND satisfaction
    time_orders = []          # (i,φ1,φ2)
    complexity_orders = set() # {(φ1,φ2)}
    physicals = []            # (i,φ)
    stationarys = set()       # {(i,φ)}
    pidistincts = []          # (i1,i2)
    differences = set()       # {(i1,i2)}

    for c in claims:
        p = c["predicate"]
        a = c["args"]

        if p == 'Phenomenon':
            if len(a) != 1:
                errors.append("Phenomenon expects 1 arg")
            else:
                P.add(a[0])

        elif p == 'Substrate':
            if len(a) != 1:
                errors.append("Substrate expects 1 arg")
            else:
                S.add(a[0])

        elif p in ('Inseparable', 'NotTwo'):
            if len(a) != 2:
                errors.append(f"{p} expects 2 args")
            else:
                I.add(tuple(a))

        elif p == 'Essence':
            if len(a) != 1:
                errors.append("Essence expects 1 arg")
            else:
                E.add(a[0])

        elif p == 'HasCoords':
            if len(a) != 2:
                errors.append("HasCoords expects 2 args")
            else:
                H.add(tuple(a))

        elif p == 'CausallyPrecedes':
            if len(a) != 2:
                errors.append("CausallyPrecedes expects 2 args")
            else:
                C.add(tuple(a))

        elif p == 'Owns':
            if len(a) != 2:
                errors.append("Owns expects 2 args")
            else:
                O.add(tuple(a))

        elif p == 'ValidConv':
            if len(a) != 1:
                errors.append("ValidConv expects 1 arg")
            else:
                V.add(a[0])

        elif p == 'Applies':
            if len(a) != 2:
                errors.append("Applies expects 2 args")
            else:
                A.add(tuple(a))

        elif p in ('ArisesFrom', 'LT'):
            if len(a) != 2:
                errors.append(f"{p} expects 2 args")

        # ND-specific
        elif p == 'TimeOrder':
            if len(a) != 3:
                errors.append("TimeOrder expects 3 args (i,phi1,phi2)")
            else:
                used_ND5 = True
                time_orders.append(tuple(a))

        elif p == 'ComplexityOrder':
            if len(a) != 2:
                errors.append("ComplexityOrder expects 2 args (phi1,phi2)")
            else:
                used_ND5 = True
                complexity_orders.add(tuple(a))

        elif p == 'Physical':
            if len(a) != 2:
                errors.append("Physical expects 2 args (i,phi)")
            else:
                used_ND6 = True
                physicals.append(tuple(a))

        elif p == 'Stationary':
            if len(a) != 2:
                errors.append("Stationary expects 2 args (i,phi)")
            else:
                used_ND6 = True
                stationarys.add(tuple(a))

        elif p == 'PiEq':
            if len(a) != 2:
                errors.append("PiEq expects 2 args (phi,i)")

        elif p == 'PiDistinct':
            if len(a) != 2:
                errors.append("PiDistinct expects 2 args (i1,i2)")
            else:
                used_ND7 = True
                pidistincts.append(tuple(a))

        elif p == 'DifferenceInIndexing':
            if len(a) != 2:
                errors.append("DifferenceInIndexing expects 2 args (i1,i2)")
            else:
                used_ND7 = True
                differences.add(tuple(a))

        elif p == 'HasIntrinsicProperty':
            if len(a) != 2:
                errors.append("HasIntrinsicProperty expects 2 args (x,p)")
            else:
                x = a[0]
                if x == 'Ω':
                    errors.append("ND3 violation: HasIntrinsicProperty(Ω, p) is forbidden")

        elif p == 'Valid':
            if len(a) != 1:
                errors.append("Valid expects 1 arg")

        else:
            errors.append(f"Unknown predicate {p}")

    # Unique substrate must be Ω
    for s in S:
        if s != Ω:
            errors.append(f"Only Ω may be Substrate, found {s}")

    # Non-duality & emptiness (Phenomena lack Essence; inseparable from Ω)
    for x in P:
        if (x, Ω) not in I:
            errors.append(f"{x} must be Inseparable from Ω")
        if x in E:
            errors.append(f"Phenomenon {x} cannot have Essence")

    # Causality & coords must be phenomena
    for (x, y) in C:
        if x not in P or y not in P:
            errors.append(f"CausallyPrecedes({x},{y}) only for Phenomena")
    for (f, x) in H:
        if x not in P:
            errors.append(f"HasCoords({f},{x}) only for Phenomenon")

    # Ownership conventional
    for (a0, p0) in O:
        if p0 not in P:
            errors.append(f"Owns({a0},{p0}) requires Phenomenon")
        if p0 not in V:
            errors.append(f"Owns({a0},{p0}) requires ValidConv")
        if (p0, Ω) not in I:
            errors.append(f"Owns({a0},{p0}) implies Inseparable({p0},Ω)")
        if p0 in E:
            errors.append(f"Owns({a0},{p0}) cannot ascribe Essence")

    # ND5: TimeOrder ⇒ ComplexityOrder
    for (_, p1, p2) in time_orders:
        if (p1, p2) not in complexity_orders:
            errors.append(f"ND5: TimeOrder({p1},{p2}) requires ComplexityOrder({p1},{p2})")

    # ND6: Physical ⇒ Stationary
    for pair in physicals:
        if pair not in stationarys:
            i, ph = pair
            errors.append(f"ND6: Physical({i},{ph}) requires Stationary({i},{ph})")

    # ND7: PiDistinct ⇒ DifferenceInIndexing
    for pair in pidistincts:
        if pair not in differences:
            i1, i2 = pair
            errors.append(f"ND7: PiDistinct({i1},{i2}) requires DifferenceInIndexing({i1},{i2})")

    # Soft citation checks
    if used_ND5 and ("ND5" not in citations_text):
        errors.append("CITATION: Using ND5 relations requires a citation mentioning 'ND5'.")
    if used_ND6 and ("ND6" not in citations_text):
        errors.append("CITATION: Using ND6 relations requires a citation mentioning 'ND6'.")
    if used_ND7 and ("ND7" not in citations_text):
        errors.append("CITATION: Using ND7 relations requires a citation mentioning 'ND7'.")

    if not errors and not _richness_check(claims):
        errors.append("Too-trivial: include at least one informative relation (Applies/Owns/HasCoords/CausallyPrecedes/ArisesFrom/LT/TimeOrder/ComplexityOrder).")
    return errors
