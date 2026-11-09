"""Save a few test-set images as PNG files, to try the website and Postman with.

    python export_samples.py fashion      -> test-images/fashion/0_T-shirt-top_0.png ...
    python export_samples.py cifar10
The images come from the test set, so neither model saw them during training.
They are enlarged (without smoothing) only so they are easier to see on screen.
"""
import sys
from pathlib import Path

from PIL import Image
from torchvision import datasets

from models import CLASSES

HERE = Path(__file__).parent
PER_CLASS = 2
SCALE = {"fashion": 8, "cifar10": 4}

dataset = sys.argv[1] if len(sys.argv) > 1 else "fashion"
cls = datasets.FashionMNIST if dataset == "fashion" else datasets.CIFAR10
test = cls(root=HERE / "data", train=False, download=True)          # PIL images, no transform
out = HERE / "test-images" / dataset
out.mkdir(parents=True, exist_ok=True)

saved = {i: 0 for i in range(10)}
for img, label in test:
    if saved[label] < PER_CLASS:
        name = CLASSES[dataset][label].replace("/", "-").replace(" ", "-")
        big = img.resize((img.width * SCALE[dataset], img.height * SCALE[dataset]), Image.NEAREST)
        big.save(out / f"{label}_{name}_{saved[label]}.png")
        saved[label] += 1
    if all(n == PER_CLASS for n in saved.values()):
        break
print(f"{sum(saved.values())} images written to {out}")
