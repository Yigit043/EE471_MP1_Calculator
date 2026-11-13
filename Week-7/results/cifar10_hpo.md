# Hyperparameter search: cifar10

Search: 3 epochs per candidate, scored on 5000 validation images.

| # | Settings | Validation accuracy | Time (s) |
|---|---|---|---|
| 1 | SGD lr 0.001, momentum 0.9, batch 4, width 1 | 58.3% | 133 |
| 2 | SGD lr 0.01, momentum 0.9, batch 32, width 1 | 56.5% | 50 |
| 3 | ADAM lr 0.001, batch 64, width 1 | 57.3% | 53 |
| 4 | ADAM lr 0.001, batch 64, width 2 | 61.7% | 61 |
| 5 | ADAM lr 0.001, batch 64, width 2, augmentation | 58.3% | 77 |
| 6 | ADAM lr 0.002, batch 128, width 2, augmentation | 59.7% | 72 |

Best: **ADAM lr 0.001, batch 64, width 2**, trained 8 epochs (early stopping).

| Model | Test accuracy |
|---|---|
| Baseline (tutorial settings) | 53.5% |
| Optimized | 67.5% |
