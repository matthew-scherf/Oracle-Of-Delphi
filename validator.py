Ω='Ω'
def validate(payload):
    c=payload.get('claims',[]);P,S,I,E,H,C,O,V,A=set(),set(),set(),set(),set(),set(),set(),set(),set()
    err=[]
    for d in c:
        p=d['predicate'];a=d['args']
        if p=='Phenomenon':P.add(a[0])
        elif p=='Substrate':S.add(a[0])
        elif p in ('Inseparable','NotTwo'):I.add(tuple(a))
        elif p=='Essence':E.add(a[0])
        elif p=='HasCoords':H.add(tuple(a))
        elif p=='CausallyPrecedes':C.add(tuple(a))
        elif p=='Owns':O.add(tuple(a))
        elif p=='ValidConv':V.add(a[0])
        elif p=='Applies':A.add(tuple(a))
        else:err.append(f'Unknown predicate {p}')
    for s in S:
        if s!=Ω:err.append(f'Only Ω may be Substrate, found {s}')
    for x in P:
        if (x,Ω) not in I:err.append(f'{x} must be Inseparable from Ω')
        if x in E:err.append(f'Phenomenon {x} cannot have Essence')
    for (x,y) in C:
        if x not in P or y not in P:err.append(f'CausallyPrecedes({x},{y}) only for Phenomena')
    for (f,x) in H:
        if x not in P:err.append(f'HasCoords({f},{x}) only for Phenomenon')
    for (a,p) in O:
        if p not in P:err.append(f'Owns({a},{p}) requires Phenomenon')
        if p not in V:err.append(f'Owns({a},{p}) requires ValidConv')
        if (p,Ω) not in I:err.append(f'Owns({a},{p}) implies Inseparable({p},Ω)')
        if p in E:err.append(f'Owns({a},{p}) cannot ascribe Essence')
    for (c,x) in A:
        if x not in P:err.append(f'Applies({c},{x}) requires Phenomenon')
    return err
