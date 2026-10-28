# Codificaiton Analysis

Turns our coding workbook for research into inter-coder agreement statistics, the hypothesis tests, and figures to include in the research paper.

## Run it

- **Mac / Linux:** open a terminal in this folder and type `sh run.sh`
- **Windows:** right-click `run.ps1` → *Run with PowerShell*

## Output

| File | What it is |
|---|---|
| `kappa.txt` | Agreement per variable: Cohen's κ per coder pair, Fleiss' κ, Gwet's AC1, on raw codes and on merged codes |
| `kappa-table.tex` | The merged-code agreement table, ready for LaTeX |
| `hypotheses.txt` | H1, H2, H3 counts with the paper IDs behind each, the three-way ties, and the raw-vs-merged robustness check |
| `figures/*.pdf` | Figures for the paper (PNG copies to preview) |
| `figures/figure-counts.csv` | Every number drawn in the figures, with its papers |
| `coding-anonymous.xlsx` | The workbook with coder names, comments and author metadata removed; all results are computed from this copy |

## Coding rules the scripts apply

- A cell's consensus code is the one chosen by at least two of three coders; papers not coded by every coder are left out.
- Codes meaning "the paper names nothing" (*Not addressed*, *None*, *None identified*, *N/A*, *Not available*, *No*) are merged into one. `kappa.txt` reports agreement with and without this merge; `hypotheses.txt` shows the hypothesis results are the same either way.
- Agreement is computed per variable, never pooled. Threshold: κ ≥ 0.61 (Landis & Koch 1977).
- Cryptographic families: MAC, Signature, TESLA, Certificate, Encryption, Blockchain. All others are detection.