"""Train the baseline model, following the PyTorch tutorials step by step.

    python train.py fashion      # quickstart: SGD, lr 0.001, batch 64, 5 epochs
    python train.py cifar10      # "Training a classifier": SGD + momentum, lr 0.001, batch 4, 2 epochs

The weights and a model_info.json (settings + test accuracy) are written into
cog/<dataset>-baseline/, together with a copy of models.py, ready for `cog build`.
hpo.py reuses the functions in this file.
"""
import json
import shutil
import sys
import time
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader

from models import build_model, load_datasets

HERE = Path(__file__).parent

BASELINE = {
    "fashion": {"optimizer": "sgd", "lr": 1e-3, "momentum": 0.0, "batch_size": 64,
                "epochs": 5, "augment": False, "arch": {"hidden": 512}},
    "cifar10": {"optimizer": "sgd", "lr": 1e-3, "momentum": 0.9, "batch_size": 4,
                "epochs": 2, "augment": False, "arch": {"width": 1}},
}


def make_optimizer(model, cfg):
    if cfg["optimizer"] == "adam":
        return torch.optim.Adam(model.parameters(), lr=cfg["lr"])
    return torch.optim.SGD(model.parameters(), lr=cfg["lr"], momentum=cfg["momentum"])


def train_one_epoch(dataloader, model, loss_fn, optimizer):
    """One pass over the training data: predict, measure the loss, backpropagate, update."""
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        loss = loss_fn(model(X), y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        if batch % 300 == 0:
            print(f"    loss {loss.item():.4f}  [{batch * len(X):>6d}/{len(dataloader.dataset)}]")


def evaluate(dataloader, model, loss_fn):
    """Accuracy and average loss on data the model did not train on."""
    model.eval()
    loss, correct = 0.0, 0
    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X)
            loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).sum().item()
    return correct / len(dataloader.dataset), loss / len(dataloader)


def save_model(model, dataset, variant, cfg, history, test_acc, test_loss, seconds):
    """Write weights + model_info.json + models.py into the Cog folder."""
    out = HERE / "cog" / f"{dataset}-{variant}"
    out.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out / "model.pth")
    info = {
        "dataset": dataset,
        "variant": variant,
        "settings": cfg,
        "test_accuracy": round(test_acc, 4),
        "test_loss": round(test_loss, 4),
        "history": history,
        "training_seconds": round(seconds),
    }
    (out / "model_info.json").write_text(json.dumps(info, indent=2))
    shutil.copy(HERE / "models.py", out / "models.py")
    print(f"\nSaved {out / 'model.pth'}  (test accuracy {100 * test_acc:.1f}%)")


def main():
    dataset = sys.argv[1] if len(sys.argv) > 1 else "fashion"
    if dataset not in BASELINE:
        sys.exit("usage: python train.py fashion|cifar10")
    cfg = BASELINE[dataset]
    torch.manual_seed(0)

    training_data, test_data = load_datasets(dataset, root=HERE / "data")
    train_loader = DataLoader(training_data, batch_size=cfg["batch_size"], shuffle=True)
    test_loader = DataLoader(test_data, batch_size=256)

    model = build_model(dataset, cfg["arch"])
    print(model)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = make_optimizer(model, cfg)

    history, started = [], time.time()
    for epoch in range(1, cfg["epochs"] + 1):
        print(f"\nEpoch {epoch}/{cfg['epochs']}")
        train_one_epoch(train_loader, model, loss_fn, optimizer)
        acc, loss = evaluate(test_loader, model, loss_fn)
        history.append({"epoch": epoch, "test_accuracy": round(acc, 4)})
        print(f"  test accuracy {100 * acc:.1f}%, test loss {loss:.4f}")

    save_model(model, dataset, "baseline", cfg, history, acc, loss, time.time() - started)


if __name__ == "__main__":
    main()
