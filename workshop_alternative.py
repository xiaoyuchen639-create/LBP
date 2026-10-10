"""Alternative route: local contrast normalization, multiscale LBP, and spatially tolerant matching.
No log-domain normalization and no candidate image rotations are used for recognition.
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from scipy import ndimage
from lbpface.datasets import load_orl
from lbpface.features import LBPDescriptor
from lbpface.distances import pairwise_distances
from lbpface.classify import recognition_rate

RADII = (1.0, 2.0, 3.0)
SIGMAS = (5.0, 10.0)
PENALTIES = (0.02, 0.05, 0.10)
ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)

def local_contrast(image, sigma):
    x = np.asarray(image, dtype=float)
    mean = ndimage.gaussian_filter(x, sigma=sigma, mode='reflect')
    variance = np.maximum(ndimage.gaussian_filter(x*x, sigma=sigma, mode='reflect')-mean*mean, 0)
    return (x-mean)/np.sqrt(variance+1e-6)

def conditions(images):
    yield 'normal', images
    yield 'uniform_brightness', [0.5*i+20 for i in images]
    for s in (0.2,0.4,0.6,0.8):
        yield f'lighting_{s}', [np.clip(i*(1+s*np.linspace(-1,1,i.shape[1])),0,255) for i in images]
    for a in (5,10,20):
        yield f'rotate_{a}', [ndimage.rotate(i.astype(float),a,reshape=False,order=1,mode='nearest') for i in images]

def multiscale_features(images, sigma):
    normalized = [local_contrast(i,sigma) for i in images]
    scales=[]
    for r in RADII:
        d=LBPDescriptor(P=16,R=r,window=(30,37))
        f=d.transform(normalized).reshape(len(normalized),9,243)
        f=f/f.sum(axis=-1,keepdims=True)
        scales.append(f)
    return np.stack(scales,axis=1)

def region_costs(probes,gallery):
    # Average chi-square distances across scales, for every region pair.
    result=np.empty((len(probes),len(gallery),9,9))
    for a in range(9):
        for b in range(9):
            result[:,:,a,b]=sum(pairwise_distances(probes[:,s,a],gallery[:,s,b],'chi2') for s in range(len(RADII)))/len(RADII)
    return result

def spatial_distance(costs,penalty):
    coords=np.stack(np.unravel_index(np.arange(9),(3,3)),axis=1)
    displacement=np.abs(coords[:,None]-coords[None,:]).sum(axis=-1)
    allowed=np.abs(coords[:,None]-coords[None,:]).max(axis=-1)<=1
    c=np.where(allowed,costs+penalty*displacement,np.inf)
    # Bidirectional nearest-region matching discourages one-way many-to-one matches.
    return 0.5*(c.min(axis=-1).mean(axis=-1)+c.min(axis=-2).mean(axis=-1))

def write_csv(path,header,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)

def evaluate(gallery,probes,gl,pl,configs):
    baseline_descriptor=LBPDescriptor.orl()
    base_gallery=baseline_descriptor.transform(gallery)
    gallery_cache={s:multiscale_features(gallery,s) for s in sorted(set(c['sigma'] for c in configs))}
    records=[]
    for name,images in conditions(probes):
        print('Computing '+name,flush=True)
        base=pairwise_distances(baseline_descriptor.transform(images),base_gallery,'chi2')
        # Convert raw count distance into mean chi-square distance of normalized regions.
        base_scaled=base/(30*37*9)
        cost_cache={s:region_costs(multiscale_features(images,s),gallery_cache[s]) for s in gallery_cache}
        elastic_cache={(c['sigma'],c['penalty']):spatial_distance(cost_cache[c['sigma']],c['penalty']) for c in configs}
        rates=[]
        for c in configs:
            elastic=elastic_cache[c['sigma'],c['penalty']]
            d=(1-c['alpha'])*base_scaled+c['alpha']*elastic
            rates.append(recognition_rate(d,gl,pl))
        records.append((name,recognition_rate(base,gl,pl),rates))
    return records

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data',default='data/ORL');ap.add_argument('--out',default='results/alternative')
    args=ap.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    fs=load_orl(args.data)
    if fs.images.shape!=(400,112,92):raise ValueError('Expected complete ORL dataset')
    index=np.array([int(n.replace('\\','/').split('/')[1].split('.')[0]) for n in fs.names])
    configs=[dict(sigma=s,penalty=p,alpha=a) for s in SIGMAS for p in PENALTIES for a in ALPHAS]
    train=index<=4;valid=index==5
    print('Validation: images 1-4 gallery, image 5 probe; 30 predeclared candidates',flush=True)
    val=evaluate(fs.images[train],fs.images[valid],fs.subjects[train],fs.subjects[valid],configs)
    matrix=np.array([r[2] for r in val]);baseline=np.array([r[1] for r in val])
    eligible=np.flatnonzero((matrix[0]>=baseline[0])&(matrix[1]>=baseline[1]))
    selected=int(eligible[np.argmax(matrix[2:,eligible].mean(axis=0))])
    chosen=configs[selected]
    write_csv(out/'validation.csv',['condition','baseline',*[f'candidate_{i}' for i in range(len(configs))]],[[n,b,*r] for n,b,r in val])
    config={'method':'local contrast normalization + multiscale LBP + bidirectional neighboring-region matching','radii':RADII,'selected':chosen,'candidates':configs,'dataset_fingerprint':fs.fingerprint,'selection':'preserve validation normal and uniform brightness; maximize mean remaining seven conditions; ties choose earliest candidate','limitations':'Earlier methods already inspected test data; this is exploratory, not an untouched holdout.'}
    (out/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    print('Selected on validation: '+str(chosen),flush=True)
    train=index<=5;test=index>=6
    final=evaluate(fs.images[train],fs.images[test],fs.subjects[train],fs.subjects[test],[chosen])
    rows=[[n,b,r[0],r[0]-b] for n,b,r in final]
    write_csv(out/'final.csv',['condition','baseline','alternative','change'],rows)
    for n,b,r,change in rows:print(f'{n:22} baseline={b:.3f} alternative={r:.3f} change={change:+.3f}',flush=True)
    lookup={n:(b,r) for n,b,r,_ in rows}
    meets=lookup['normal'][1]>=lookup['normal'][0] and lookup['lighting_0.8'][1]>lookup['lighting_0.8'][0] and lookup['rotate_20'][1]>lookup['rotate_20'][0]
    print('Meets teacher key criteria: '+str(meets),flush=True)
    report=['# Alternative method research results','', 'Selected configuration: '+str(chosen),'','Local mean and standard deviation normalize contrast; three LBP radii describe texture; nearby regions match with displacement penalties. The original distance is retained with weight 1-alpha. Recognition performs no corrective image rotations and uses no log transform.','','| Condition | Baseline | Alternative | Gain (pp) |','| --- | ---: | ---: | ---: |']
    report += [f'| {n} | {100*b:.1f}% | {100*r:.1f}% | {100*c:+.1f} |' for n,b,r,c in rows]
    report += ['',f'Teacher key criteria satisfied: {meets}.','',config['limitations'],'','Parameters were selected on validation only; do not retune using the final table. A failed criterion is reported as a research finding, not a successful replacement.']
    (out/'research_summary.md').write_text('\n'.join(report),encoding='utf-8')

if __name__=='__main__':main()
