# validator.py — robust normalizer + validator (with auto-repair and richness check)

Ω = 'Ω'

def _as_str(x):
    return x if isinstance(x, str) else str(x)

def _normalize_claims(claims):
    import json
    out = []
    soft_errors = []
    if not isinstance(claims, list):
        soft_errors.append("claims must be a list")
        return [], soft_errors
    for i, c in enumerate(claims):
        if isinstance(c, str):
            try:
                c = json.loads(c)
            except Exception:
                soft_errors.append(f"claim[{i}] is a string that is not valid JSON; skipping")
                continue
        if not isinstance(c, dict):
            soft_errors.append(f"claim[{i}] is not an object; skipping")
            continue
        p = c.get("predicate")
        a = c.get("args")
        if not isinstance(p, str):
            soft_errors.append(f"claim[{i}] missing/invalid 'predicate'; skipping")
            continue
        if not isinstance(a, list):
            a = [a] if a is not None else []
        a = [_as_str(x) for x in a]
        out.append({"predicate": p, "args": a})
    return out, soft_errors


def repair(payload):
    import copy
    d = payload if isinstance(payload, dict) else {}
    d = copy.deepcopy(d)
    claims = d.get("claims", [])
    claims, _ = _normalize_claims(claims)

    phenos = {c["args"][0] for c in claims if c["predicate"] == "Phenomenon" and len(c["args"]) >= 1}
    inseps = {(c["args"][0], c["args"][1]) for c in claims if c["predicate"] in ("Inseparable", "NotTwo") and len(c["args"]) >= 2}
    for x in phenos:
        if (x, Ω) not in inseps:
            claims.append({"predicate": "Inseparable", "args": [x, "Ω"]})

    owned = [(c["args"][0], c["args"][1]) for c in claims if c["predicate"] == "Owns" and len(c["args"]) >= 2]
    valid = {c["args"][0] for c in claims if c["predicate"] == "ValidConv" and len(c["args"]) >= 1}
    for (_, p) in owned:
        if p not in valid:
            claims.append({"predicate": "ValidConv", "args": [p]})

    d["claims"] = claims
    return d


def _richness_check(claims):
    informative = [c for c in claims if c["predicate"] in (
        "CausallyPrecedes", "HasCoords", "Applies", "Owns", "ArisesFrom", "LT")]
    return len(informative) >= 1


def validate(payload):
    import copy
    errors = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]

    payload = copy.deepcopy(payload)
    claims_raw = payload.get("claims", [])
    claims, soft = _normalize_claims(claims_raw)
    errors.extend(soft)

    P, S, I, E, H, C, O, V, A = set(), set(), set(), set(), set(), set(), set(), set(), set()

    for c in claims:
        p = c["predicate"]; a = c["args"]
        if p == 'Phenomenon':
            if len(a) != 1: errors.append("Phenomenon expects 1 arg")
            else: P.add(a[0])
        elif p == 'Substrate':
            if len(a) != 1: errors.append("Substrate expects 1 arg")
            else: S.add(a[0])
        elif p in ('Inseparable','NotTwo'):
            if len(a) != 2: errors.append(f"{p} expects 2 args")
            else: I.add(tuple(a))
        elif p == 'Essence':
            if len(a) != 1: errors.append("Essence expects 1 arg")
            else: E.add(a[0])
        elif p == 'HasCoords':
            if len(a) != 2: errors.append("HasCoords expects 2 args (frame, x)")
            else: H.add(tuple(a))
        elif p == 'CausallyPrecedes':
            if len(a) != 2: errors.append("CausallyPrecedes expects 2 args")
            else: C.add(tuple(a))
        elif p == 'Owns':
            if len(a) != 2: errors.append("Owns expects 2 args (agent, p)")
            else: O.add(tuple(a))
        elif p == 'ValidConv':
            if len(a) != 1: errors.append("ValidConv expects 1 arg (p)")
            else: V.add(a[0])
        elif p == 'Applies':
            if len(a) != 2: errors.append("Applies expects 2 args")
            else: A.add(tuple(a))
        elif p == 'ArisesFrom':
            if len(a) != 2: errors.append("ArisesFrom expects 2 args")
        elif p == 'LT':
            if len(a) != 2: errors.append("LT expects 2 args: 'T(x)', 'T(y)'")
        else:
            errors.append(f"Unknown predicate {p}")

    for s in S:
        if s != Ω: errors.append(f"Only Ω may be Substrate, found {s}")
    for x in P:
        if (x, Ω) not in I: errors.append(f"{x} must be Inseparable from Ω")
        if x in E: errors.append(f"Phenomenon {x} cannot have Essence")
    for (x, y) in C:
        if x not in P or y not in P: errors.append(f"CausallyPrecedes({x},{y}) only for Phenomena")
    for (f, x) in H:
        if x not in P: errors.append(f"HasCoords({f},{x}) only for Phenomenon")
    for (a, p) in O:
        if p not in P: errors.append(f"Owns({a},{p}) requires Phenomenon")
        if p not in V: errors.append(f"Owns({a},{p}) requires ValidConv")
        if (p, Ω) not in I: errors.append(f"Owns({a},{p}) implies Inseparable({p},Ω)")
        if p in E: errors.append(f"Owns({a},{p}) cannot ascribe Essence")
    for (cname, x) in A:
        if x not in P: errors.append(f"Applies({cname},{x}) requires Phenomenon")

    if not errors and not _richness_check(claims):
        errors.append("Too-trivial: include at least one informative relation (Applies/Owns/HasCoords/CausallyPrecedes/ArisesFrom/LT).")

    return errors
