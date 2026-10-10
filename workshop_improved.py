import csv
from pathlib import Path

import numpy as np
from scipy import ndimage

from lbpface.datasets import load_orl
from lbpface.features import LBPDescriptor
from lbpface.distances import pairwise_distances
from lbpface.classify import recognition_rate


fs = load_orl("data/ORL")
desc = LBPDescriptor.orl()

is_gallery = (np.arange(len(fs.images)) % 10) < 5
gal, prb = fs.images[is_gallery], fs.images[~is_gallery]
gl, pl = fs.subjects[is_gallery], fs.subjects[~is_gallery]

# 第一版固定参数；先观察效果，不保证一定提升
SIGMA = 5.0
ANGLES = [-20, -15, -10, -5, 0, 5, 10, 15, 20]


def normalize_light(img):
    """减弱缓慢变化的光照，保留局部纹理。"""
    x = np.log1p(np.asarray(img, dtype=float))
    local_mean = ndimage.gaussian_filter(x, sigma=SIGMA)
    return x - local_mean


def rotate(img, degrees):
    if degrees == 0:
        return np.asarray(img, dtype=float)
    return ndimage.rotate(
        np.asarray(img, dtype=float),
        degrees,
        reshape=False,
        order=1,
        mode="nearest",
    )


def illum_ramp(img, strength):
    ramp = 1 + strength * np.linspace(-1, 1, img.shape[1])
    return np.clip(img * ramp, 0, 255)


# 训练图分别提取原始特征和光照归一化特征
G_raw = desc.transform(gal)
G_light = desc.transform([normalize_light(img) for img in gal])


def evaluate(images):
    images = np.asarray(images)

    raw_dist = pairwise_distances(
        desc.transform(images), G_raw, "chi2"
    )
    light_dist = pairwise_distances(
        desc.transform([normalize_light(img) for img in images]),
        G_light,
        "chi2",
    )

    # 为每一对测试图/训练图，保留所有候选角度中的最小距离
    rotation_dist = raw_dist.copy()
    combined_dist = light_dist.copy()

    for angle in ANGLES:
        if angle == 0:
            continue

        turned = [rotate(img, angle) for img in images]

        d_raw = pairwise_distances(
            desc.transform(turned), G_raw, "chi2"
        )
        d_light = pairwise_distances(
            desc.transform([normalize_light(img) for img in turned]),
            G_light,
            "chi2",
        )

        rotation_dist = np.minimum(rotation_dist, d_raw)
        combined_dist = np.minimum(combined_dist, d_light)

    return [
        recognition_rate(d, gl, pl)
        for d in [
            raw_dist,
            light_dist,
            rotation_dist,
            combined_dist,
        ]
    ]


conditions = [
    ("normal", prb),
    ("uniform_brightness", [0.5 * img + 20 for img in prb]),
]

for strength in [0.2, 0.4, 0.6, 0.8]:
    conditions.append((
        f"lighting_{strength}",
        [illum_ramp(img, strength) for img in prb],
    ))

for degrees in [5, 10, 20]:
    conditions.append((
        f"rotate_{degrees}",
        [rotate(img, degrees) for img in prb],
    ))

header = ["condition", "baseline", "light", "rotation", "combined"]
rows = []

print(
    f"{'condition':<22}"
    f"{'baseline':>10}{'light':>10}"
    f"{'rotation':>10}{'combined':>10}",
    flush=True,
)

for name, images in conditions:
    scores = evaluate(images)
    rows.append([name, *scores])
    print(
        f"{name:<22}" + "".join(f"{s:>10.3f}" for s in scores),
        flush=True,
    )

Path("results").mkdir(exist_ok=True)
output = Path("results/workshop_comparison.csv")

with output.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print(f"\nResults saved to {output}", flush=True)