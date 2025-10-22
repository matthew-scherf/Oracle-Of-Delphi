Ω = 'Ω'

def repair(d):
    """Auto-complete safe claims before validation."""
    claims = d.get("claims", [])
    phenos = {c["args"][0] for c in claims if c["predicate"] == "Phenomenon"}
    inseps = {(c["args"][0], c["args"][1]) for c in claims if c["predicate"] in ("Inseparable", "NotTwo")}
    for x in phenos:
        if (x, Ω) not in inseps:
            claims.append({"predicate": "Inseparable", "args": [x, "Ω"]})
    for c in list(claims):
        if c["predicate"] == "Owns":
            _, p = c["args"]
            if not any(cc["predicate"] == "ValidConv" and cc["args"][0] == p for cc in claims):
                claims.append({"predicate": "ValidConv", "args": [p]})
    d["claims"] = claims
    return d


def richness_check(claims):
    informative = [c for c in claims if c["predicate"] in (
        "CausallyPrecedes", "HasCoords", "Applies", "Owns", "ArisesFrom", "LT")]
    return len(informative) >= 1


def validate(payload):
    payload = repair(payload)
    claims = payload.get('claims', [])
    P, S, I, E, H, C, O, V, A = set(), set(), set(), set(), set(), set(), set(), set(), set()
    errors = []

    for c in claims:
        p = c['predicate']
        a = c['args']
        if p == 'Phenomenon': P.add(a[0])
        elif p == 'Substrate': S.add(a[0])
        elif p in ('Inseparable', 'NotTwo'): I.add(tuple(a))
        elif p == 'Essence': E.add(a[0])
        elif p == 'HasCoords': H.add(tuple(a))
        elif p == 'CausallyPrecedes': C.add(tuple(a))
        elif p == 'Owns': O.add(tuple(a))
        elif p == 'ValidConv': V.add(a[0])
        elif p == 'Applies': A.add(tuple(a))
        else: errors.append(f'Unknown predicate {p}')

    for s in S:
        if s != Ω: errors.append(f'Only Ω may be Substrate, found {s}')
    for x in P:
        if (x, Ω) not in I: errors.append(f'{x} must be Inseparable from Ω')
        if x in E: errors.append(f'Phenomenon {x} cannot have Essence')
    for (x, y) in C:
        if x not in P or y not in P:
            errors.append(f'CausallyPrecedes({x},{y}) only for Phenomena')
    for (f, x) in H:
        if x not in P: errors.append(f'HasCoords({f},{x}) only for Phenomenon')
    for (a, p) in O:
        if p not in P: errors.append(f'Owns({a},{p}) requires Phenomenon')
        if p not in V: errors.append(f'Owns({a},{p}) requires ValidConv')
        if (p, Ω) not in I: errors.append(f'Owns({a},{p}) implies Inseparable({p},Ω)')
        if p in E: errors.append(f'Owns({a},{p}) cannot ascribe Essence')
    for (c, x) in A:
        if x not in P: errors.append(f'Applies({c},{x}) requires Phenomenon')

    if not errors and not richness_check(claims):
        errors.append("Too-trivial: include at least one informative relation "
                      "(Applies/Owns/HasCoords/CausallyPrecedes/ArisesFrom/LT).")

    return errors
