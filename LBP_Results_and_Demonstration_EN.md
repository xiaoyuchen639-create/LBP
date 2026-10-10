# LBP Face Recognition Results and Demonstration Guide

This experiment first reproduces the supplied LBP face recognition baseline, then improves robustness using illumination normalization, rotation search, and distance fusion. The final method increases accuracy from 97.5% to 98.0% on normal images, from 70.5% to 95.0% under strong side lighting, and from 63.0% to 88.0% under a 20-degree rotation. Final accuracy is at least as high as the baseline in all nine specified conditions.

## 1 Assignment objectives and completion

The assignment asks us to read the supplied code, reproduce the baseline using its exact data split and test conditions, and improve performance under uneven illumination and rotation without reducing accuracy on normal images. We completed data verification, random-split reproduction, fixed-split baseline evaluation, separate enhancement experiments, and final fusion evaluation.

These conclusions apply to the specified ORL data and transformations. The message Teacher key criteria satisfied: True is a check implemented in our script: normal-image accuracy must not decrease, strong-lighting accuracy must improve, and 20-degree rotation accuracy must improve. It is not a teacher-issued grade or external certification.

## 2 What LBP does

LBP stands for Local Binary Pattern. It extracts local texture information and converts a face image into numerical features that can be compared with faces of known identity.

For each central pixel, the algorithm compares its intensity with neighbors sampled on a circle. A neighbor greater than or equal to the center is encoded as 1; otherwise it is encoded as 0. The resulting binary pattern describes local texture. The implementation uses uniform LBP: circular patterns with at most two transitions between 0 and 1 receive separate labels, while all remaining patterns share one label.

The ORL descriptor uses 16 neighbors at a radius of 2 pixels. Each 92-by-112 image is divided into a 3-by-3 arrangement of 30-by-37-pixel windows. Each region has a 243-bin histogram, giving 9 x 243 = 2187 features per image. Keeping separate regional histograms retains approximate spatial information.

Recognition pipeline: grayscale face → LBP encoding → regional histograms → 2187-dimensional feature vector → chi-square distance comparison → nearest known identity. No neural network is trained. The gallery stores features and labels of known faces. Ties between identities are treated as incorrect by the project's accuracy calculation.

LBP compares relative intensities, so it often tolerates a uniform monotonic brightness change. Uneven illumination, clipping, and rotation can still change local codes or the correspondence between regions. This explains why the baseline remains stable under uniform brightness changes but drops under strong side lighting and large rotations.

## 3 Dataset verification and original experiment reproduction

The dataset check reports 400 images of 40 subjects, with 10 images per subject. Image width is 92 pixels and height is 112 pixels. The fingerprint is a SHA-256 identifier computed from file paths and contents. It identifies the dataset copy; it is not an accuracy score.

Dataset fingerprint: 9972801133ec8ba8b06221a0f2c7c087c2e2a8d99a5fdd0ddfbf90beb82d5ac3

The original experiment randomly selects five gallery images and five probe images per subject, repeats the split 100 times with seed 0, and uses the original LBP descriptor with chi-square distance.

| Output | Value | Interpretation |
| --- | --- | --- |
| mean recognition rate | 0.9826 | Mean recognition accuracy across 100 random splits: 98.26% |
| std | 0.0096 | Sample standard deviation of split accuracies: about 0.96 percentage points |
| 95% interval | 0.962 to 1.000 | Empirical 2.5th to 97.5th percentiles of split accuracies: approximately 96.2% to 100% |
| paper reports | mean 0.9800, std 0.0120 | Reference reported by the supplied code: mean 98.0%, standard deviation 1.2 percentage points |
| feature length | 2187 | Number of descriptor components for each face |
| features+distances | 4.2 seconds | Feature and distance computation time in this baseline run; not the final fusion runtime |

The reproduced mean of 98.26% is close to the reference mean of 98.0%. The printed 95% interval describes the distribution of random-split accuracies. It is not a confidence interval for population mean accuracy and does not establish a 95% probability of achieving a particular accuracy.

Results are stored in results/orl_seed0.json. The digest is a checksum of the results, not a performance measure.

## 4 Fixed protocol for the workshop

The workshop uses images 1–5 of each subject as the gallery, giving 200 gallery images. Images 6–10 are the probes, giving 200 test images. Gallery images stay unchanged; transformations are applied only to the probes.

| Condition | Exact transformation |
| --- | --- |
| Normal | Original probe images |
| Uniform brightness | 0.5 x pixel intensity + 20 |
| Lighting ramp | Multiply each column by 1 + s x linspace(-1, 1, width), then clip to 0–255; s = 0.2, 0.4, 0.6, 0.8 |
| Rotation | scipy.ndimage.rotate at 5, 10, or 20 degrees, with reshape=False, order=1, and mode='nearest' |

At lighting strength 0.8, the left edge is multiplied by 0.2 and the right edge by 1.8, simulating a dark left side and bright right side. Bright values may be clipped at 255. Rotations retain image dimensions, so edge content can be lost. These conditions are generated transformations, not separately captured photographs.

The fixed-split baseline achieves 97.5% on normal images, 70.5% under the strongest lighting ramp, and 63.0% at 20 degrees. The latter two values match the assignment examples. The fixed-split 97.5% and random-split mean of 98.26% come from different protocols and are not an improvement comparison.

## 5 Initial enhancement results

light means illumination normalization alone. rotation uses original features with angle search. combined applies angle search to illumination-normalized features, without fusing original features.

| Condition | Baseline | Light | Rotation | Combined |
| --- | --- | --- | --- | --- |
| Normal | 97.5% | 96.0% | 97.5% | 96.5% |
| Uniform brightness | 97.5% | 96.0% | 97.5% | 95.5% |
| Lighting 0.2 | 96.0% | 96.0% | 96.0% | 96.5% |
| Lighting 0.4 | 94.5% | 96.0% | 94.5% | 96.5% |
| Lighting 0.6 | 89.5% | 95.5% | 89.5% | 96.0% |
| Lighting 0.8 | 70.5% | 96.5% | 70.0% | 96.5% |
| Rotation 5 degrees | 97.0% | 95.0% | 97.0% | 95.5% |
| Rotation 10 degrees | 92.5% | 91.0% | 94.0% | 91.5% |
| Rotation 20 degrees | 63.0% | 68.5% | 87.0% | 79.5% |

Illumination normalization greatly improves strong-lighting accuracy, but reduces normal-image accuracy to 96.0%. Rotation search improves 20-degree accuracy to 87.0% while preserving normal-image accuracy. The initial combined method still reduces normal-image accuracy to 96.5%, so it does not meet the preservation objective. The final method therefore fuses distances to retain useful information from the original descriptor.

## 6 Final method and parameter selection

Illumination normalization computes x = log(1 + image), then subtracts a Gaussian-smoothed local mean, using a fixed sigma of 5.0. The resulting floating-point image is passed directly to LBP, without additional conversion to an 8-bit image. Gallery and probe images receive the same normalization.

The candidate correction angles are -20, -15, -10, -5, 0, 5, 10, 15, and 20 degrees. The recognizer searches all candidates. It does not receive the true rotation angle or condition label as recognition input.

For each probe–gallery pair at a common candidate angle a, compute the original-feature distance D_raw(a) and normalized-feature distance D_light(a). Fuse them as D(a) = (1 - w) x D_raw(a) + w x D_light(a). Take the minimum over candidate angles, then identify the nearest subject. Fusion happens at the same angle before angle minimization.

Weight selection uses only the original training portion: images 1–4 per subject form a 160-image gallery, and image 5 per subject provides 40 validation probes. The same nine transformations are applied to validation probes. There are 21 candidate weights from 0.00 to 1.00 in steps of 0.05.

The selection rule first requires validation accuracy on both normal and uniform-brightness images to be at least their baseline values. Among eligible candidates, maximize mean accuracy across the other seven conditions. Ties favor a smaller normalization weight. The selected weight is 0.50, so the two distances contribute equally. This weight combines descriptor distances; it is not a spatial-region weight.

Sigma and candidate angles are fixed in this experiment; only the fusion weight is selected on validation data. After selection, images 1–5 are restored as the gallery, and images 6–10 are evaluated with fixed parameters. The final test results are not used to adjust the selected weight.

## 7 Final results and interpretation

| Condition | Original LBP | Final fusion | Gain in percentage points |
| --- | --- | --- | --- |
| Normal | 97.5% | 98.0% | 0.5 |
| Uniform brightness | 97.5% | 98.0% | 0.5 |
| Lighting 0.2 | 96.0% | 97.0% | 1.0 |
| Lighting 0.4 | 94.5% | 96.5% | 2.0 |
| Lighting 0.6 | 89.5% | 97.5% | 8.0 |
| Lighting 0.8 | 70.5% | 95.0% | 24.5 |
| Rotation 5 degrees | 97.0% | 97.0% | 0.0 |
| Rotation 10 degrees | 92.5% | 96.0% | 3.5 |
| Rotation 20 degrees | 63.0% | 88.0% | 25.0 |

Each condition has 200 probes, so 0.5 percentage points corresponds to one image. Correct identifications increase from 195 to 196 on normal images, from 141 to 190 under strong lighting, and from 126 to 176 at 20 degrees. These are net increases in correct totals; individual corrected and newly incorrect images have not been analyzed separately.

Final fusion is not the best intermediate method in every condition. Its strong-lighting accuracy of 95.0% is below the light-only result of 96.5%, but fusion preserves normal accuracy and also handles rotation. The objective is one method that meets the assignment goals, rather than choosing a different best method after observing each test condition.

Limitations: images 6–10 were already inspected during earlier exploratory experiments, so this is not a completely untouched holdout. No statistical significance test of accuracy differences has been performed. Angle search adds computation, and final total runtime has not been measured separately. Results support effectiveness under the specified conditions, not arbitrary rotations or all real lighting environments.

## 8 Live demonstration sequence

Open the PyCharm project, the final CSV, and this guide in advance. The terminal should show (.venv) and use the inner LBP directory. While fusion runs, explain the method and show saved results rather than waiting silently for computation to finish.

Working directory: C:\Users\pc\Desktop\resume\872\LBP\LBP

Step 1. Verify the dataset. Explain the image count, subject count, dimensions, and fingerprint.

python -m lbpface.datasets data/ORL

Step 2. Reproduce the random-split experiment. Explain the 100 repetitions and 98.26% mean. If time is limited, show the saved JSON or terminal screenshot.

python -m experiments.orl --data data/ORL --seed 0 --n-perm 100 --out results/orl_seed0.json

Step 3. Run the fixed-split baseline. Highlight 97.5%, 70.5%, and 63.0%.

python workshop_baseline.py

Step 4. Show the initial comparison table to explain why fusion was introduced. Run this intermediate experiment only if time permits.

python workshop_improved.py

Step 5. Run final fusion. The first group of Computing messages is validation. Selected weight on validation: 0.50 reports the selected weight. The second group is the final test evaluation.

python workshop_final.py

Final results are in results/workshop_final.csv; validation results are in results/workshop_validation.csv; parameters and dataset fingerprint are in results/workshop_selected_config.json. Earlier experiment outputs remain available. Re-running the final script recomputes and overwrites its corresponding result files.

## 9 Two-minute presentation script

I first checked the ORL dataset, which contains 400 images of 40 subjects. The original method uses LBP with 16 neighbors and a radius of 2 pixels. It divides each face into nine regions, constructs a 2187-dimensional feature vector, and recognizes identity using nearest-neighbor matching with chi-square distance.

I reproduced the original experiment using five random gallery images and five probe images per subject over 100 splits. Mean accuracy was 98.26%, close to the reported 98%. I then used the workshop's fixed split: images 1–5 for the gallery and images 6–10 for testing. Baseline accuracy was 97.5% on normal images, 70.5% under strong side lighting, and 63% at a 20-degree rotation. The two challenging-condition results matched the assignment examples.

I tested illumination normalization and rotation search separately. Normalization improved lighting robustness but reduced normal-image accuracy. Rotation search improved rotated-image recognition. To combine their benefits, I fused distances from original and normalized LBP features at each candidate angle, then selected the minimum distance across angles.

I selected the fusion weight using validation images from the original training portion. The selected weight was 0.50. With parameters fixed, final accuracy reached 98% on normal images, 95% under strong side lighting, and 88% at 20 degrees. These are gains of 0.5, 24.5, and 25 percentage points. None of the nine specified conditions performed worse than the baseline.

The method meets the workshop objectives under these conditions. However, angle search costs more computation, and test images were already viewed during earlier exploration. Further evaluation should use new independent data.

## 10 Likely questions and answers

Q: Why are 98.26% and 97.5% different?
A: The first is the mean over 100 random splits; the second is one fixed workshop split. Different protocols produce different results, so these are not a before-and-after comparison.

Q: Does recognition receive the correct identity or true rotation angle?
A: No. Matching uses images and known gallery features, searching candidate angles automatically. Probe labels are used only to calculate accuracy; condition names are used for reporting.

Q: How was 0.50 selected?
A: Images 1–4 form the validation gallery and image 5 is the validation probe for each subject. The script compares 21 weights using a predefined selection rule, chooses 0.50, and fixes it before evaluating images 6–10.

Q: Why not use the light-only method, which reaches 96.5% under strong lighting?
A: It reduces normal accuracy to 96.0% and achieves only 68.5% at 20 degrees. Final fusion preserves normal accuracy while improving both lighting and rotation performance.

Q: What model was trained?
A: No neural network was trained. LBP is a fixed feature extractor, gallery images provide reference features, and validation selects the distance-fusion weight.

Q: Does a change of 0.245 mean an increase of 0.245%?
A: No. Multiplying 0.245 by 100 gives 24.5 percentage points: for example, 70.5% to 95.0%.

Q: Are the improvements statistically significant?
A: These are observed accuracy changes. No paired significance test has been performed, so statistical significance has not been established.
