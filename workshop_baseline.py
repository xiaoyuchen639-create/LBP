import numpy as np
from scipy import ndimage

from lbpface.datasets import load_orl
from lbpface.features import LBPDescriptor
from lbpface.distances import pairwise_distances
from lbpface.classify import recognition_rate


fs = load_orl("data/ORL")
desc = LBPDescriptor.orl()

# 数据按每个人的图片编号排序：前5张训练，后5张测试
is_gallery = (np.arange(len(fs.images)) % 10) < 5
gal = fs.images[is_gallery]
prb = fs.images[~is_gallery]
gl = fs.subjects[is_gallery]
pl = fs.subjects[~is_gallery]

G = desc.transform(gal)


def score(probe_images):
    features = desc.transform(probe_images)
    distances = pairwise_distances(features, G, "chi2")
    return recognition_rate(distances, gl, pl)


def illum_ramp(img, strength):
    ramp = 1 + strength * np.linspace(-1, 1, img.shape[1])
    return np.clip(img * ramp, 0, 255)


def rotate(img, degrees):
    return ndimage.rotate(
        img.astype(float),
        degrees,
        reshape=False,
        order=1,
        mode="nearest",
    )


print("baseline           ", score(prb))
print("uniform brightness ", score([0.5 * img + 20 for img in prb]))

for strength in [0.2, 0.4, 0.6, 0.8]:
    print(
        "lighting ramp", strength,
        score([illum_ramp(img, strength) for img in prb]),
    )

for degrees in [5, 10, 20]:
    print(
        "rotate", degrees, "deg",
        score([rotate(img, degrees) for img in prb]),
    )