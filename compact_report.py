from pathlib import Path
import re
p=Path(__file__).resolve().parent / 'LBP_One_Page_Report.tex'
s=p.read_text(encoding='utf-8-sig')
tables=re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',s,re.S)
assert len(tables)==3
header=r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=14mm]{geometry}
\usepackage{booktabs,array}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{3pt}
\setlength{\tabcolsep}{8pt}
\renewcommand{\arraystretch}{1.0}
\begin{document}
{\centering\Large\bfseries Improving LBP Face Recognition Robustness\par}
\vspace{4pt}
\textbf{Protocol.} ORL: 40 subjects, 10 images each ($92\times112$ pixels). Images 1--5 form the gallery; 6--10 form the 200-image test set. Baseline: uniform LBP (16 neighbors, radius 2), nine regions, 2187 features, chi-square matching. A separate 100-random-split run achieved 98.26\% mean accuracy (SD 0.96 percentage points).

\textbf{Conditions.} Only probes are changed: brightness $0.5I+20$; side lighting $I[1+s\,\mathrm{linspace}(-1,1,W)]$, clipped to $[0,255]$; rotations retain dimensions with bilinear interpolation and nearest boundary handling. All accuracies below are percentages.
'''
def block(title,table):
    return '\n\\begin{minipage}{\\linewidth}\n\\centering\n\\textbf{'+title+'}\\par\\vspace{2pt}\n{\\fontsize{9}{10.5}\\selectfont\n'+table+'}\n\\end{minipage}\n\\par\\vspace{3pt}\n'
text=header+block('Table 1. Original baseline',tables[0])
text+=r'''\textbf{Initial methods.} Light: $\log(1+I)$ minus its Gaussian local mean ($\sigma=5$). Rotation: search $-20^\circ$ to $20^\circ$ in $5^\circ$ steps. Combined: rotation search on normalized features only. Its normal accuracy drops to 96.5\%, motivating fusion.
'''
text+=block('Table 2. Initial enhancement comparison',tables[1])
text+=r'''\textbf{Final method.} Fuse $D=(1-w)D_{\mathrm{raw}}+wD_{\mathrm{light}}$ at each angle, then minimize over angles. Select $w$ using images 1--4 as gallery and image 5 as validation: test 21 weights from 0 to 1; preserve normal/brightness accuracy, then maximize mean accuracy on the other seven conditions. Selected $w=0.50$ is fixed for final testing.
'''
text+=block('Table 3. Final fusion results',tables[2])
text+=r'''\textbf{Conclusion.} Normal accuracy is preserved (98.0\%); strong lighting improves by 24.5 percentage points and $20^\circ$ rotation by 25.0. No tested condition falls below baseline. ``pp'' means percentage points.

\textbf{Limitations.} Angle search adds computation. Test results were viewed during earlier exploration; this is not an untouched holdout. Statistical significance and generalization to new data remain unverified.
\end{document}
'''
p.write_text(text,encoding='utf-8')
print('Updated report; all 27 condition rows retained in three unbreakable tables.')
