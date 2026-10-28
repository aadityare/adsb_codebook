import os, csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib import font_manager
from common import load, consensus, families, key, THIRD_PARTY

SPEC, UNSPEC, SILENT, TIE = '#184f95', '#6da7ec', '#e4e3df', '#ffffff'
ORANGE, ORANGE_L, INK, INK2, DOT = '#eb6834', '#f3a07c', '#0b0b0b', '#52514e', '#c3c2b7'
FONTS = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams.update({'font.family': next(f for f in ('Liberation Serif', 'Times New Roman', 'DejaVu Serif') if f in FONTS), 'font.size': 7.5,
                     'pdf.fonttype': 42, 'axes.edgecolor': INK2, 'axes.linewidth': 0.5, 'xtick.color': INK2,
                     'hatch.linewidth': 0.4, 'hatch.color': INK2})
STATES = ['spec', 'unspec', 'tie', 'silent']
LABEL = {'spec': 'Supplier or mechanism named', 'unspec': 'Needed, none named',
         'tie': 'Coders split (pending)', 'silent': 'Silent'}
FILL = {'spec': SPEC, 'unspec': UNSPEC, 'tie': TIE, 'silent': SILENT}


def state(v, spec=None, unspec=('Unspecified',), prefix=None):
    if v == 'TIE':
        return 'tie'
    if prefix:
        return 'spec' if v and v.startswith(prefix) else 'silent'
    if v in unspec:
        return 'unspec'
    if spec is not None:
        return 'spec' if v in spec else 'silent'
    return 'silent' if v in ('NONE', None, 'Not needed') else 'spec'


FUNCTIONS = [
    ('Trust', 'Credential issuer', 'Root of Trust', lambda v: state(v)),
    ('Trust', 'Credential distribution', 'Credential Distribution', lambda v: state(v)),
    ('Trust', 'Acceptance by foreign receivers', 'Cross-certification between states', lambda v: state(v)),
    ('Trust', 'Revocation (ground or airborne)', 'Revocation reaches airborne verifiers', lambda v: state(v)),
    ('Trust', 'Common time source', 'Time sync Authority', lambda v: state(v, unspec=('Needed, but not addressed',))),
    ('Coordination', 'Standards change (MOPS/SARP)', 'Standards Change', lambda v: state(v, spec={'MOPS', 'SARP', 'Both'}, unspec=())),
    ('Data sharing', 'Third-party receiver network', 'Receiver network', lambda v: state(v, prefix=THIRD_PARTY)),
    ('Data sharing', 'Cross-border raw data', 'Cross-border raw-data sharing', lambda v: state(v, unspec=('Required but not addressed',))),
    ('Data sharing', 'Reference-data custody', 'Reference database custody', lambda v: state(v)),
    ('Data sharing', 'Cross-border personal data', 'Cross-border route the personal data takes', lambda v: state(v)),
    ('Operations', 'ATC action on a flag', 'Operational Procedure', lambda v: state(v)),
    ('Operations', 'Wrongly rejected aircraft', 'What happens to a legitimate aircraft the scheme wrongly rejects', lambda v: state(v)),
    ('Operations', 'Aircraft revoked in flight', 'What happens to an aircraft whose credential is revoked in flight', lambda v: state(v)),
    ('Enforcement', 'Enforcement channel', 'Enforcement', lambda v: state(v)),
    ('Enforcement', 'Liability assigned', 'Whether the paper assigns liability for either case', lambda v: state(v, spec={'Yes'}, unspec=())),
]


def save(fig, out, name):
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(out, f'{name}.{ext}'), dpi=300)
    plt.close(fig)


def run(path, out):
    os.makedirs(out, exist_ok=True)
    coders, heads, codes = load(path, merge=True)
    papers, cons, _ = consensus(coders, codes)
    col = {key(h): i for i, h in enumerate(heads)}
    code = lambda p, c: cons[p][col[c]]
    cell = lambda p, f: f[3](code(p, f[2]))
    crypto, detect = families(cons, heads, papers)

    counts = {}
    with open(os.path.join(out, 'figure-counts.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['set', 'function', 'state', 'n', 'papers'])
        for setname, ps in (('cryptographic', crypto), ('detection', detect)):
            for f in FUNCTIONS:
                by = {s: [p for p in ps if cell(p, f) == s] for s in STATES}
                counts[(setname, f[1])] = {s: len(v) for s, v in by.items()}
                for s in STATES:
                    w.writerow([setname, f[1], s, len(by[s]), ' '.join(by[s])])

    rows = []
    for grp in dict.fromkeys(f[0] for f in FUNCTIONS):
        rows += [('header', grp)] + [('fn', f[1]) for f in FUNCTIONS if f[0] == grp]
    Y = {r: len(rows) - 1 - i for i, r in enumerate(rows)}

    def bars(ax, setname, n, title):
        for kind, lab in rows:
            if kind == 'header':
                continue
            y, left = Y[(kind, lab)], 0
            for s in STATES:
                k = counts[(setname, lab)][s]
                if not k:
                    continue
                ax.barh(y, k - 0.14, left=left + 0.07, height=0.7, color=FILL[s], linewidth=0.5,
                        edgecolor=INK2 if s == 'tie' else 'none', hatch='//////' if s == 'tie' else None)
                if k >= 2 or s == 'spec':
                    ax.text(left + k / 2, y, str(k), ha='center', va='center', fontsize=6.5,
                            color='white' if s == 'spec' else INK,
                            bbox=dict(boxstyle='square,pad=0.08', fc='white', ec='none') if s == 'tie' else None)
                left += k
        ax.set_xlim(0, n)
        ax.set_ylim(-0.6, len(rows) - 0.4)
        ax.set_xticks([0, n / 2, n])
        ax.set_xticklabels(['0', f'{n / 2:g}\n(half)', str(n)])
        ax.tick_params(axis='x', length=2, labelsize=6.5)
        ax.tick_params(axis='y', length=0)
        for sp in ('top', 'right', 'left'):
            ax.spines[sp].set_visible(False)
        ax.set_title(title, fontsize=8, loc='left', color=INK)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 3.3), sharey=True, gridspec_kw={'wspace': 0.05})
    bars(a1, 'cryptographic', len(crypto), f'Cryptographic schemes ($n={len(crypto)}$)')
    bars(a2, 'detection', len(detect), f'Detection schemes ($n={len(detect)}$)')
    a1.set_yticks([Y[r] for r in rows])
    a1.set_yticklabels([lab for _, lab in rows], fontsize=7)
    for t, (kind, _) in zip(a1.get_yticklabels(), rows):
        if kind == 'header':
            t.set_fontweight('bold'); t.set_color(INK2); t.set_fontsize(6.8)
    fig.legend(handles=[Patch(facecolor=FILL[s], edgecolor=INK2 if s == 'tie' else 'none',
                              hatch='//////' if s == 'tie' else None, linewidth=0.5, label=LABEL[s]) for s in STATES],
               loc='lower center', ncol=4, frameon=False, fontsize=6.8, bbox_to_anchor=(0.6, 0.0), handlelength=1.4)
    fig.subplots_adjust(left=0.24, right=0.99, top=0.93, bottom=0.17)
    save(fig, out, 'fig-rq2-functions')

    rn = 'Receiver network'
    segs = [('Research network', lambda v: v.startswith('Research'), ORANGE, 'white', -0.42),
            ('Crowdsourced', lambda v: v == 'Crowdsourced', ORANGE_L, INK, -0.80),
            ('ANSP-owned', lambda v: v == 'ANSP-owned', SPEC, 'white', -0.42),
            ('Single receiver', lambda v: v.startswith('Single'), UNSPEC, INK, -0.80),
            ('Not stated', lambda v: v in ('NONE', 'TIE'), SILENT, INK, -0.42)]
    groups = [[p for p in detect if test(code(p, rn))] for _, test, *_ in segs]
    fig, ax = plt.subplots(figsize=(3.33, 1.3))
    left = 0
    for (lab, _, color, tcolor, ylab), ps in zip(segs, groups):
        k = len(ps)
        if not k:
            continue
        ax.barh(0, k - 0.14, left=left + 0.07, height=0.55, color=color, edgecolor='none')
        ax.text(left + k / 2, 0, str(k), ha='center', va='center', fontsize=7, color=tcolor)
        ax.text(left + k / 2, ylab, lab, ha='center', va='top', fontsize=6.3, color=INK2)
        left += k
    third, half = len(groups[0]) + len(groups[1]), len(detect) / 2
    ax.plot([half, half], [0.32, 0.95], color=INK, lw=0.7, ls=(0, (2, 2)))
    ax.text(half + 0.25, 0.62, f'majority threshold ({half:g})', ha='left', va='center', fontsize=6.3, color=INK)
    ax.annotate('', xy=(0, 0.48), xytext=(third, 0.48), arrowprops=dict(arrowstyle='<->', color=ORANGE, lw=0.6))
    ax.text(third / 2, 0.55, 'may include foreign receivers', ha='center', va='bottom', fontsize=6.3, color=INK2)
    ax.set_xlim(0, len(detect)); ax.set_ylim(-1.15, 1.0); ax.axis('off')
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    save(fig, out, 'fig-rq2-receivers')

    short = {'Certificate': 'Cert.', 'Encryption': 'Encr.', 'Cross-Check': 'Cross-check',
             'Doppler': 'Dopp.', 'RF-Fingerprint': 'RF'}
    fam = lambda p: code(p, 'Family')
    order = sorted(crypto, key=lambda p: (fam(p), int(p[1:]))) + sorted(detect, key=lambda p: (fam(p), int(p[1:])))
    marks = {'spec': dict(s=16, color=SPEC), 'unspec': dict(s=16, color=UNSPEC),
             'tie': dict(s=14, facecolor='white', edgecolor=INK2, linewidths=0.6), 'silent': dict(s=2.5, color=DOT)}
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    for x, p in enumerate(order):
        for i, f in enumerate(FUNCTIONS):
            s = cell(p, f)
            ax.scatter(x, len(FUNCTIONS) - 1 - i, **({'linewidths': 0} | marks[s]))
    start = 0
    for x in range(1, len(order) + 1):
        if x == len(order) or fam(order[x]) != fam(order[start]):
            f = fam(order[start])
            ax.text((start + x - 1) / 2, len(FUNCTIONS) - 0.2 + (0.4 if x - start == 1 else 0), short.get(f, f),
                    ha='center', va='bottom', fontsize=5.6, color=INK2)
            if x < len(order):
                edge = x == len(crypto)
                ax.axvline(x - 0.5, color=INK2 if edge else SILENT, lw=0.6 if edge else 0.4, zorder=0)
            start = x
    ax.text((len(crypto) - 1) / 2, len(FUNCTIONS) + 0.75, f'Cryptographic ($n={len(crypto)}$)', ha='center', fontsize=7)
    ax.text(len(crypto) + (len(detect) - 1) / 2, len(FUNCTIONS) + 0.75, f'Detection ($n={len(detect)}$)', ha='center', fontsize=7)
    ax.set_yticks(range(len(FUNCTIONS)))
    ax.set_yticklabels([f[1] for f in FUNCTIONS][::-1], fontsize=6.5)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order, rotation=90, fontsize=5.2)
    ax.set_xlim(-0.8, len(order) - 0.2); ax.set_ylim(-0.6, len(FUNCTIONS) + 1.3)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    fig.legend(handles=[Line2D([], [], marker='o', ls='', color=SPEC, markersize=4, label=LABEL['spec']),
                        Line2D([], [], marker='o', ls='', color=UNSPEC, markersize=4, label=LABEL['unspec']),
                        Line2D([], [], marker='o', ls='', markerfacecolor='white', markeredgecolor=INK2,
                               markersize=3.8, label=LABEL['tie']),
                        Line2D([], [], marker='o', ls='', color=DOT, markersize=1.6, label=LABEL['silent'])],
               loc='lower center', ncol=4, frameon=False, fontsize=6.5, bbox_to_anchor=(0.6, -0.01))
    fig.subplots_adjust(left=0.2, right=0.995, top=0.97, bottom=0.2)
    save(fig, out, 'fig-rq2-matrix')
