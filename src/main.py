import os
from common import find_xlsx
from anonymize import anonymize
import kappa, hypotheses, figures

OUT = 'output'
os.makedirs(OUT, exist_ok=True)

src = find_xlsx('data')
data = src if src.endswith('coding-anonymous.xlsx') else anonymize(src, os.path.join(OUT, 'coding-anonymous.xlsx'))
print(f'1/4  input: {src}\n     anonymized copy: {data}')

text, pairs, rows = kappa.report(data)
open(os.path.join(OUT, 'kappa.txt'), 'w').write(text)
open(os.path.join(OUT, 'kappa-table.tex'), 'w').write(kappa.latex_table(pairs, rows))
print('2/4  agreement:  output/kappa.txt, output/kappa-table.tex')
print('\n'.join(l for l in text.splitlines() if 'mean Fleiss' in l))

open(os.path.join(OUT, 'hypotheses.txt'), 'w').write(hypotheses.report(data))
print('3/4  hypotheses: output/hypotheses.txt')

figures.run(data, os.path.join(OUT, 'figures'))
print('4/4  figures:    output/figures/ (PDF for LaTeX, PNG to look at, figure-counts.csv)')
