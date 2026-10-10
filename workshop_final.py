import csv
import json
from pathlib import Path
import numpy as np
from scipy import ndimage
from lbpface.datasets import load_orl
from lbpface.features import LBPDescriptor
from lbpface.distances import pairwise_distances
from lbpface.classify import recognition_rate

ANGLES = [-20, -15, -10, -5, 0, 5, 10, 15, 20]
WEIGHTS = np.linspace(0, 1, 21)
SIGMA = 5.0

def rotate(img, angle):
    return np.asarray(img, dtype=float) if angle == 0 else ndimage.rotate(np.asarray(img, dtype=float), angle, reshape=False, order=1, mode='nearest')

def light(img):
    x = np.log1p(np.asarray(img, dtype=float))
    return x - ndimage.gaussian_filter(x, sigma=SIGMA)

def conditions(images):
    yield 'normal', images
    yield 'uniform_brightness', [0.5*i+20 for i in images]
    for s in [0.2, 0.4, 0.6, 0.8]:
        yield f'lighting_{s}', [np.clip(i*(1+s*np.linspace(-1,1,i.shape[1])),0,255) for i in images]
    for a in [5,10,20]:
        yield f'rotate_{a}', [rotate(i,a) for i in images]

def distances(images, gallery, desc):
    raw_gallery = desc.transform(gallery)
    light_gallery = desc.transform([light(i) for i in gallery])
    for name, probes in conditions(images):
        print('Computing '+name, flush=True)
        raw, norm = [], []
        for a in ANGLES:
            turned = [rotate(i,a) for i in probes]
            raw.append(pairwise_distances(desc.transform(turned),raw_gallery,'chi2'))
            norm.append(pairwise_distances(desc.transform([light(i) for i in turned]),light_gallery,'chi2'))
        yield name, np.stack(raw), np.stack(norm)

def fusion(raw,norm,weight):
    # Fuse at each common angle before taking the minimum over angles.
    return ((1-weight)*raw+weight*norm).min(axis=0)

def main():
    fs=load_orl('data/ORL')
    assert fs.images.shape == (400,112,92)
    index=np.array([int(n.split('/')[1].split('.')[0]) for n in fs.names])
    desc=LBPDescriptor.orl()
    train=index<=4
    valid=index==5
    score_table=[]
    baseline=[]
    names=[]
    for name,raw,norm in distances(fs.images[valid],fs.images[train],desc):
        names.append(name)
        baseline.append(recognition_rate(raw[ANGLES.index(0)],fs.subjects[train],fs.subjects[valid]))
        score_table.append([recognition_rate(fusion(raw,norm,w),fs.subjects[train],fs.subjects[valid]) for w in WEIGHTS])
    scores=np.asarray(score_table)
    eligible=np.flatnonzero((scores[0]>=baseline[0]) & (scores[1]>=baseline[1]))
    if eligible.size==0:
        raise RuntimeError('No candidate preserves validation normal/brightness accuracy; do not evaluate test for parameter selection.')
    # Maximize mean accuracy across changed conditions; ties prefer less normalization.
    selected=int(eligible[np.argmax(scores[2:,eligible].mean(axis=0))])
    weight=float(WEIGHTS[selected])
    out=Path('results'); out.mkdir(exist_ok=True)
    with (out/'workshop_validation.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f); writer.writerow(['condition','baseline',*[f'weight_{w:.2f}' for w in WEIGHTS]])
        writer.writerows([[n,b,*r] for n,b,r in zip(names,baseline,scores)])
    config={'weight':weight,'sigma':SIGMA,'angles':ANGLES,'dataset_fingerprint':fs.fingerprint,'selection':'images 1-4 gallery, image 5 validation; preserve normal and uniform brightness, maximize mean other conditions','limitation':'test results were already inspected during earlier exploratory experiments; not a fully untouched holdout'}
    (out/'workshop_selected_config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    print(f'Selected weight on validation: {weight:.2f}',flush=True)
    train=index<=5; test=index>=6
    rows=[]
    for name,raw,norm in distances(fs.images[test],fs.images[train],desc):
        b=recognition_rate(raw[ANGLES.index(0)],fs.subjects[train],fs.subjects[test])
        r=recognition_rate(fusion(raw,norm,weight),fs.subjects[train],fs.subjects[test])
        rows.append([name,b,r,r-b])
        print(f'{name:22} baseline={b:.3f} fusion={r:.3f} change={r-b:+.3f}',flush=True)
    with (out/'workshop_final.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f); writer.writerow(['condition','baseline','fusion','change']); writer.writerows(rows)
    lookup={row[0]:row for row in rows}
    passed=lookup['normal'][2]>=lookup['normal'][1] and lookup['lighting_0.8'][2]>lookup['lighting_0.8'][1] and lookup['rotate_20'][2]>lookup['rotate_20'][1]
    print('Teacher key criteria satisfied: '+str(passed),flush=True)

if __name__=='__main__':
    main()
