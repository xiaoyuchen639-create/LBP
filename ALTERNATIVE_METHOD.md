# Alternative LBP method

This experiment investigates an actual algorithm change, not a renamed version of the previous method.

## Processing

1. Local contrast normalization: `(I - Gaussian(I)) / sqrt(max(Gaussian(I*I) - Gaussian(I)**2, 0) + 1e-6)`.
2. Multiscale uniform LBP: 16 neighbors, radii 1, 2 and 3, nine regions. Each region histogram is normalized to sum to one.
3. Average chi-square region-pair costs across the three scales.
4. Match each region to itself or an immediately adjacent region, adding a Manhattan displacement penalty. Average both matching directions. This is a bidirectional nearest-region heuristic, not a one-to-one assignment.
5. Combine the new distance with the original fixed-orientation LBP distance after dividing the original raw-count distance by `30*37*9` to use comparable units.

Recognition does not rotate images and does not use a logarithmic illumination transform. Rotation is used only to generate the teacher's test conditions. Spatial tolerance is not full rotation invariance: uniform LBP orientation codes still change under rotation.

## Validation

The 30 candidates are the Cartesian product of sigmas 5 and 10, displacement penalties 0.02, 0.05 and 0.10, and alternative-distance weights 0, 0.25, 0.5, 0.75 and 1. Images 1-4 form the validation gallery and image 5 provides validation probes. Preserve validation normal and brightness accuracy, then maximize mean accuracy across seven remaining conditions. Ties choose the first candidate in the declared order.

Final evaluation restores images 1-5 as gallery and 6-10 as probes. It uses fixed selected parameters. Read `results/alternative/research_summary.md` for observed final results; do not assume success before reading the table. Prior test results were already inspected during exploratory work, so this is not an untouched holdout.

## Run

From the inner LBP directory with its environment active:

```powershell
python workshop_alternative.py
```

Outputs: `results/alternative/config.json`, `validation.csv`, `final.csv` and `research_summary.md`. Original experiments remain unchanged.
