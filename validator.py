# validator.py — structured-claims normalizer + validator (same schema)

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
            try: c = json.loads(c)
            except Exception: soft.append(f"claim[{i}] not valid JSON; skipped"); continue
        if not isinstance(c, dict):
            soft.append(f"claim[{i}] is not an object; skipped"); continue
        p = c.get("predicate"); a = c.get("args")
        if not isinstance(p, str):
            soft.append(f"claim[{i}] missing predicate; skipped"); continue
        if not isinstance(a, list): a = [a] if a is not None else []
        a = [_as_str(x) for x in a]
        out.append({"predicate": p, "args": a})
    return out, soft

def repair(payload):
    import copy
    d = copy.deepcopy(payload if isinstance(payload, dict) else {})
    claims, _ = _normalize_claims(d.get("claims", []))

    for c in list(claims):
        if c["predicate"] == "CausallyPrecedes" and len(c["args"]) >= 2:
            for arg in c["args"]:
                if not any(cc for cc in claims
                           if cc["predicate"] == "Phenomenon" and len(cc["args"])==1 and cc["args"][0]==arg):
                    claims.append({"predicate": "Phenomenon", "args": [arg]})

    phenos = {c["args"][0] for c in claims if c["predicate"]=="Phenomenon" and len(c["args"])>=1}
    inseps = {(c["args"][0], c["args"][1]) for c in claims
              if c["predicate"] in ("Inseparable","NotTwo") and len(c["args"])>=2}
    for x in phenos:
        if (x, Ω) not in inseps:
            claims.append({"predicate": "Inseparable", "args": [x, "Ω"]})

    owned = [(c["args"][0], c["args"][1]) for c in claims if c["predicate"]=="Owns" and len(c["args"])>=2]
    valid = {c["args"][0] for c in claims if c["predicate"]=="ValidConv" and len(c["args"])>=1}
    for (_, p) in owned:
        if p not in valid:
            claims.append({"predicate": "ValidConv", "args": [p]})

    d["claims"] = claims
    return d

def _richness_check(claims):
    informative = [c for c in claims if c["predicate"] in ("CausallyPrecedes","HasCoords","Applies","Owns","ArisesFrom","LT")]
    return len(informative) >= 1

def validate(payload):
    import copy
    errors = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]

    payload = copy.deepcopy(payload)
    claims, soft = _normalize_claims(payload.get("claims", []))
    errors.extend(soft)

    P,S,I,E,H,C,O,V,A = set(),set(),set(),set(),set(),set(),set(),set(),set()

    for c in claims:
        p=c["predicate"]; a=c["args"]
        if p=='Phenomenon':
            if len(a)!=1: errors.append("Phenomenon expects 1 arg"); else: P.add(a[0])
        elif p=='Substrate':
            if len(a)!=1: errors.append("Substrate expects 1 arg"); else: S.add(a[0])
        elif p in ('Inseparable','NotTwo'):
            if len(a)!=2: errors.append(f"{p} expects 2 args"); else: I.add(tuple(a))
        elif p=='Essence':
            if len(a)!=1: errors.append("Essence expects 1 arg"); else: E.add(a[0])
        elif p=='HasCoords':
            if len(a)!=2: errors.append("HasCoords expects 2 args"); else: H.add(tuple(a))
        elif p=='CausallyPrecedes':
            if len(a)!=2: errors.append("CausallyPrecedes expects 2 args"); else: C.add(tuple(a))
        elif p=='Owns':
            if len(a)!=2: errors.append("Owns expects 2 args"); else: O.add(tuple(a))
        elif p=='ValidConv':
            if len(a)!=1: errors.append("ValidConv expects 1 arg"); else: V.add(a[0])
        elif p=='Applies':
            if len(a)!=2: errors.append("Applies expects 2 args"); else: A.add(tuple(a))
        elif p in ('ArisesFrom','LT'):
            if len(a)!=2: errors.append(f"{p} expects 2 args")
        else:
            errors.append(f"Unknown predicate {p}")

    for s in S:
        if s != Ω: errors.append(f"Only Ω may be Substrate, found {s}")

    for x in P:
        if (x, Ω) not in I: errors.append(f"{x} must be Inseparable from Ω")
        if x in E: errors.append(f"Phenomenon {x} cannot have Essence")

    for (x,y) in C:
        if x not in P or y not in P:
            errors.append(f"CausallyPrecedes({x},{y}) only for Phenomena")
    for (f,x) in H:
        if x not in P: errors.append(f"HasCoords({f},{x}) only for Phenomenon")

    for (a,p) in O:
        if p not in P: errors.append(f"Owns({a},{p}) requires Phenomenon")
        if p not in V: errors.append(f"Owns({a},{p}) requires ValidConv")
        if (p, Ω) not in I: errors.append(f"Owns({a},{p}) implies Inseparable({p},Ω)")
        if p in E: errors.append(f"Owns({a},{p}) cannot ascribe Essence")

    if not errors and not _richness_check(claims):
        errors.append("Too-trivial: include at least one informative relation (Applies/Owns/HasCoords/CausallyPrecedes/ArisesFrom/LT).")
    return errors
