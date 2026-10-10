# Alternative method research results

Selected configuration: {'sigma': 5.0, 'penalty': 0.02, 'alpha': 0.5}

Local mean and standard deviation normalize contrast; three LBP radii describe texture; nearby regions match with displacement penalties. The original distance is retained with weight 1-alpha. Recognition performs no corrective image rotations and uses no log transform.

| Condition | Baseline | Alternative | Gain (pp) |
| --- | ---: | ---: | ---: |
| normal | 97.5% | 97.5% | +0.0 |
| uniform_brightness | 97.5% | 97.5% | +0.0 |
| lighting_0.2 | 96.0% | 95.5% | -0.5 |
| lighting_0.4 | 94.5% | 95.5% | +1.0 |
| lighting_0.6 | 89.5% | 95.5% | +6.0 |
| lighting_0.8 | 70.5% | 93.0% | +22.5 |
| rotate_5 | 97.0% | 97.5% | +0.5 |
| rotate_10 | 92.5% | 93.0% | +0.5 |
| rotate_20 | 63.0% | 67.0% | +4.0 |

Teacher key criteria satisfied: True.

Earlier methods already inspected test data; this is exploratory, not an untouched holdout.

Parameters were selected on validation only; do not retune using the final table. A failed criterion is reported as a research finding, not a successful replacement.