import itertools
from collections import Counter
from common import load

THRESHOLD = 0.61
BANDS = [(0.81, 'almost perfect'), (0.61, 'substantial'), (0.41, 'moderate'), (0.21, 'fair'), (0.0, 'slight'), (-1, 'poor')]


def cohen(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in ca) / n ** 2
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def fleiss_ac1(items, m):
    n, tot = len(items), Counter(x for it in items for x in it)
    pi = [v / (n * m) for v in tot.values()]
    pa = sum((sum(v * v for v in Counter(it).values()) - m) / (m * (m - 1)) for it in items) / n
    pf, pg = sum(p * p for p in pi), sum(p * (1 - p) for p in pi) / max(len(pi) - 1, 1)
    k = lambda pe: 1.0 if pe == 1 else (pa - pe) / (1 - pe)
    return k(pf), k(pg), max(pi)


def band(k):
    return next(name for t, name in BANDS if k >= t)


def analyse(path, merge):
    coders, heads, codes = load(path, merge)
    pairs = list(itertools.combinations(coders, 2))
    common = set.intersection(*map(set, codes.values()))
    rows = []
    for i, h in enumerate(heads):
        ks = [cohen([(codes[a][p][i], codes[b][p][i]) for p in codes[a].keys() & codes[b].keys()
                     if codes[a][p][i] is not None and codes[b][p][i] is not None]) for a, b in pairs]
        items = [[codes[s][p][i] for s in coders] for p in common if all(codes[s][p][i] is not None for s in coders)]
        rows.append((h, len(items), ks, *fleiss_ac1(items, len(coders))))
    return coders, pairs, rows


def report(path):
    lines = []
    for merge in (False, True):
        coders, pairs, rows = analyse(path, merge)
        tag = lambda s: s.split()[-1]
        lines.append(f"\n{'MERGED silence codes (Not addressed = None = N/A = No)' if merge else 'RAW codes'}")
        lines.append(f"{'variable':40}{'n':>4}" + ''.join(f'{tag(a) + tag(b):>7}' for a, b in pairs) + f"{'Fleiss':>8}{'AC1':>7}{'top':>6}")
        for h, n, ks, fk, ac1, top in rows:
            lines.append(f'  {h[:38]:38}{n:4}' + ''.join(f'{k:7.2f}' for k in ks)
                         + f'{fk:8.2f}{ac1:7.2f}{top:6.0%}' + ('  *' if fk < THRESHOLD else ''))
        mf, ma = sum(r[3] for r in rows) / len(rows), sum(r[4] for r in rows) / len(rows)
        for j, (a, b) in enumerate(pairs):
            ks = [r[2][j] for r in rows]
            lines.append(f'  pair {tag(a)}-{tag(b)}: mean Cohen kappa {sum(ks) / len(ks):.3f} '
                         f'({sum(k >= THRESHOLD for k in ks)}/{len(ks)} variables >= {THRESHOLD})')
        lines.append(f'  mean Fleiss kappa = {mf:.3f} ({band(mf)}, Landis & Koch 1977)  mean AC1 = {ma:.3f}  '
                     f'variables >= {THRESHOLD}: {sum(r[3] >= THRESHOLD for r in rows)}/{len(rows)}')
    return '\n'.join(lines), pairs, rows


def latex_table(pairs, rows):
    tag = lambda s: s.split()[-1]
    esc = lambda s: s.replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')
    out = ['\\begin{tabular}{@{}l' + 'r' * (4 + len(pairs)) + '@{}}', '\\toprule',
           'Variable & $n$ & ' + ' & '.join(f'$\\kappa_{{{tag(a)}{tag(b)}}}$' for a, b in pairs)
           + ' & Fleiss $\\kappa$ & AC1 & Top \\\\', '\\midrule']
    for h, n, ks, fk, ac1, top in rows:
        out.append(f'{esc(h)}{"$^{*}$" if fk < THRESHOLD else ""} & {n} & ' + ' & '.join(f'{k:.2f}' for k in ks)
                   + f' & {fk:.2f} & {ac1:.2f} & {round(top * 100)}\\% \\\\')
    return '\n'.join(out + ['\\bottomrule', '\\end{tabular}', ''])
