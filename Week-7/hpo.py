"""Hyperparameter optimization: find better training settings, then train the optimized model.

    python hpo.py fashion
    python hpo.py cifar10

The test set is never used to choose settings (that would be cheating). Instead:
  1. The training images are split into a training part and a validation part.
  2. Search: every candidate below trains for a few epochs and is scored on validation accuracy.
  3. The best candidate trains for longer, with early stopping on validation accuracy:
     we keep the epoch with the best validation accuracy and stop when it stops improving.
  4. Only this final model is measured once on the test set and saved to cog/<dataset>-optimized/.
All results go to results/<dataset>_hpo.md (a table for the report) and .json.
"""
import copy
import json
import sys
import time
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset

from models import build_model, load_datasets
from train import BASELINE, HERE, evaluate, make_optimizer, save_model, train_one_epoch

VALIDATION_SIZE = {"fashion": 10_000, "cifar10": 5_000}
SEARCH_EPOCHS = 3          # short runs to compare candidates
MAX_EPOCHS = 15            # longest final run
PATIENCE = 3               # stop after this many epochs without a better validation accuracy

# The search space. Each line is one candidate; the first one is the baseline's settings.
CANDIDATES = {
    "fashion": [
        {"optimizer": "sgd",  "lr": 1e-3, "momentum": 0.0, "batch_size": 64,  "hidden": 512},
        {"optimizer": "sgd",  "lr": 1e-2, "momentum": 0.0, "batch_size": 64,  "hidden": 512},
        {"optimizer": "sgd",  "lr": 1e-1, "momentum": 0.0, "batch_size": 64,  "hidden": 512},
        {"optimizer": "sgd",  "lr": 1e-2, "momentum": 0.9, "batch_size": 64,  "hidden": 512},
        {"optimizer": "adam", "lr": 3e-4, "momentum": 0.0, "batch_size": 64,  "hidden": 512},
        {"optimizer": "adam", "lr": 1e-3, "momentum": 0.0, "batch_size": 64,  "hidden": 512},
        {"optimizer": "adam", "lr": 1e-3, "momentum": 0.0, "batch_size": 128, "hidden": 512},
        {"optimizer": "adam", "lr": 1e-3, "momentum": 0.0, "batch_size": 64,  "hidden": 1024},
    ],
    "cifar10": [
        {"optimizer": "sgd",  "lr": 1e-3, "momentum": 0.9, "batch_size": 4,   "width": 1, "augment": False},
        {"optimizer": "sgd",  "lr": 1e-2, "momentum": 0.9, "batch_size": 32,  "width": 1, "augment": False},
        {"optimizer": "adam", "lr": 1e-3, "momentum": 0.0, "batch_size": 64,  "width": 1, "augment": False},
        {"optimizer": "adam", "lr": 1e-3, "momentum": 0.0, "batch_size": 64,  "width": 2, "augment": False},
        {"optimizer": "adam", "lr": 1e-3, "momentum": 0.0, "batch_size": 64,  "width": 2, "augment": True},
        {"optimizer": "adam", "lr": 2e-3, "momentum": 0.0, "batch_size": 128, "width": 2, "augment": True},
    ],
}


def to_config(dataset, cand):
    """Candidate line -> full training settings (the same format as train.BASELINE)."""
    arch = {"hidden": cand["hidden"]} if dataset == "fashion" else {"width": cand["width"]}
    return {"optimizer": cand["optimizer"], "lr": cand["lr"], "momentum": cand["momentum"],
            "batch_size": cand["batch_size"], "augment": cand.get("augment", False), "arch": arch}


def split_data(dataset, augment):
    """Same split every time: the last N training images become the validation set."""
    train_aug, test = load_datasets(dataset, root=HERE / "data", augment=augment)
    train_plain, _ = load_datasets(dataset, root=HERE / "data", augment=False)
    n = len(train_plain) - VALIDATION_SIZE[dataset]
    train = Subset(train_aug, range(n))
    val = Subset(train_plain, range(n, len(train_plain)))   # no augmentation when measuring
    return train, val, test


def run(dataset, cfg, epochs, patience=None):
    """Train with cfg; return (best model, history, best validation accuracy, seconds)."""
    torch.manual_seed(0)
    train, val, _ = split_data(dataset, cfg["augment"])
    train_loader = DataLoader(train, batch_size=cfg["batch_size"], shuffle=True)
    val_loader = DataLoader(val, batch_size=256)
    model = build_model(dataset, cfg["arch"])
    loss_fn = nn.CrossEntropyLoss()
    optimizer = make_optimizer(model, cfg)

    best_acc, best_state, best_epoch, history = -1.0, None, 0, []
    started = time.time()
    for epoch in range(1, epochs + 1):
        print(f"  epoch {epoch}/{epochs}")
        train_one_epoch(train_loader, model, loss_fn, optimizer)
        acc, _ = evaluate(val_loader, model, loss_fn)
        history.append({"epoch": epoch, "val_accuracy": round(acc, 4)})
        print(f"  validation accuracy {100 * acc:.1f}%")
        if acc > best_acc:
            best_acc, best_state, best_epoch = acc, copy.deepcopy(model.state_dict()), epoch
        elif patience and epoch - best_epoch >= patience:
            print(f"  early stopping: no improvement for {patience} epochs")
            break
    model.load_state_dict(best_state)
    return model, history, best_acc, best_epoch, time.time() - started


def describe(cfg):
    arch = ", ".join(f"{k} {v}" for k, v in cfg["arch"].items())
    mom = f", momentum {cfg['momentum']}" if cfg["optimizer"] == "sgd" and cfg["momentum"] else ""
    aug = ", augmentation" if cfg["augment"] else ""
    return f"{cfg['optimizer'].upper()} lr {cfg['lr']}{mom}, batch {cfg['batch_size']}, {arch}{aug}"


def main():
    dataset = sys.argv[1] if len(sys.argv) > 1 else "fashion"
    if dataset not in CANDIDATES:
        sys.exit("usage: python hpo.py fashion|cifar10")

    # ---- 1-2. search
    results = []
    for i, cand in enumerate(CANDIDATES[dataset], 1):
        cfg = to_config(dataset, cand)
        print(f"\n[{i}/{len(CANDIDATES[dataset])}] {describe(cfg)}")
        _, _, acc, _, secs = run(dataset, cfg, SEARCH_EPOCHS)
        results.append({"settings": describe(cfg), "config": cfg,
                        "val_accuracy": round(acc, 4), "seconds": round(secs)})
    best = max(results, key=lambda r: r["val_accuracy"])
    print(f"\nBest candidate: {best['settings']} ({100 * best['val_accuracy']:.1f}% validation)")

    # ---- 3. longer training with early stopping
    print(f"\nFinal training (up to {MAX_EPOCHS} epochs, early stopping)")
    cfg = dict(best["config"])
    model, history, val_acc, best_epoch, secs = run(dataset, cfg, MAX_EPOCHS, PATIENCE)
    cfg["epochs"] = best_epoch

    # ---- 4. one test-set measurement, save for Cog
    _, _, test = split_data(dataset, False)
    test_acc, test_loss = evaluate(DataLoader(test, batch_size=256), model, nn.CrossEntropyLoss())
    save_model(model, dataset, "optimized", cfg, history, test_acc, test_loss, secs)

    # ---- report files
    baseline_info = json.loads((HERE / "cog" / f"{dataset}-baseline" / "model_info.json").read_text()) \
        if (HERE / "cog" / f"{dataset}-baseline" / "model_info.json").exists() else None
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    (out / f"{dataset}_hpo.json").write_text(json.dumps(
        {"search": results, "best": best["settings"], "final_epochs": best_epoch,
         "final_val_accuracy": round(val_acc, 4), "final_test_accuracy": round(test_acc, 4)}, indent=2))
    lines = [f"# Hyperparameter search: {dataset}", "",
             f"Search: {SEARCH_EPOCHS} epochs per candidate, scored on {VALIDATION_SIZE[dataset]} validation images.", "",
             "| # | Settings | Validation accuracy | Time (s) |", "|---|---|---|---|"]
    lines += [f"| {i} | {r['settings']} | {100 * r['val_accuracy']:.1f}% | {r['seconds']} |"
              for i, r in enumerate(results, 1)]
    lines += ["", f"Best: **{best['settings']}**, trained {best_epoch} epochs (early stopping).", "",
              "| Model | Test accuracy |", "|---|---|"]
    if baseline_info:
        lines.append(f"| Baseline (tutorial settings) | {100 * baseline_info['test_accuracy']:.1f}% |")
    lines.append(f"| Optimized | {100 * test_acc:.1f}% |")
    (out / f"{dataset}_hpo.md").write_text("\n".join(lines) + "\n")
    print(f"Results written to {out / f'{dataset}_hpo.md'}")


if __name__ == "__main__":
    main()
