from common import load, consensus, families, key, THIRD_PARTY


def test(path, merge=True):
    coders, heads, codes = load(path, merge)
    papers, cons, ties = consensus(coders, codes)
    col = {key(h): i for i, h in enumerate(heads)}
    g = lambda p, c: cons[p][col[c]]
    said = lambda v: v not in ('NONE', None) and str(v).lower() not in ('not addressed', 'none', 'n/a', 'na', 'no')
    tp = lambda v: v not in (None, 'TIE') and v.startswith(THIRD_PARTY)
    crypto, detect = families(cons, heads, papers)
    h1 = lambda p: (said(g(p, 'Root of Trust')) or said(g(p, 'Credential Distribution'))
                    or said(g(p, 'Cross-certification between states'))
                    or g(p, 'Revocation reaches airborne verifiers') in ('Datalink push', 'Broadcast CRL'))
    h2 = lambda p: tp(g(p, 'Receiver network')) or said(g(p, 'Cross-border raw-data sharing'))
    N = [p for p in papers if not (h1(p) or h2(p))]
    strict = [p for p in N if p in detect and g(p, 'Standards Change') not in ('MOPS', 'SARP', 'Both')]
    return dict(papers=papers, ties=ties, heads=heads, crypto=crypto, detect=detect,
                H1=[p for p in crypto if h1(p)],
                H2=[p for p in detect if tp(g(p, 'Receiver network'))],
                H2_any_vote=[p for p in detect if any(tp(codes[s][p][col['Receiver network']]) for s in coders)],
                N=N, strict=strict)


def report(path):
    r, raw = test(path, True), test(path, False)
    line = lambda label, ps: f'{label:58}{len(ps):3}  {" ".join(ps)}'
    out = [line('papers coded by all coders', r['papers']),
           line('cryptographic', r['crypto']), line('detection', r['detect']),
           f"three-way ties: {len(r['ties'])} of {len(r['papers']) * 20} cells",
           *[f"  {p} {r['heads'][i][:40]}: {v}" for p, i, v in r['ties']],
           '', line(f"H1 support (holds if > {len(r['crypto']) / 2:g})", r['H1']),
           line(f"H2 upper bound, third-party receivers (holds if > {len(r['detect']) / 2:g})", r['H2']),
           line('H2 if any single coder vote counts', r['H2_any_vote']),
           line('H3 N: no H1 or H2 function stated', r['N']),
           line('H3 detection schemes in N with no standards change', r['strict']),
           '  (also set aside by hand in the paper: P02 jamming, P09 ownship GNSS)', '',
           'robustness, raw vs merged codes: '
           + ('identical' if all(r[k] == raw[k] for k in ('H1', 'H2', 'N')) else 'DIFFERENT, check')]
    return '\n'.join(out)
