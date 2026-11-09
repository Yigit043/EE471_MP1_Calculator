# Hyperparameter search: fashion

Search: 3 epochs per candidate, scored on 10000 validation images.

| # | Settings | Validation accuracy | Time (s) |
|---|---|---|---|
| 1 | SGD lr 0.001, batch 64, hidden 512 | 61.0% | 26 |
| 2 | SGD lr 0.01, batch 64, hidden 512 | 78.8% | 27 |
| 3 | SGD lr 0.1, batch 64, hidden 512 | 81.6% | 26 |
| 4 | SGD lr 0.01, momentum 0.9, batch 64, hidden 512 | 85.4% | 28 |
| 5 | ADAM lr 0.0003, batch 64, hidden 512 | 86.7% | 58 |
| 6 | ADAM lr 0.001, batch 64, hidden 512 | 87.1% | 60 |
| 7 | ADAM lr 0.001, batch 128, hidden 512 | 86.9% | 39 |
| 8 | ADAM lr 0.001, batch 64, hidden 1024 | 87.1% | 69 |

Best: **ADAM lr 0.001, batch 64, hidden 1024**, trained 6 epochs (early stopping).

| Model | Test accuracy |
|---|---|
| Baseline (tutorial settings) | 64.9% |
| Optimized | 87.7% |
