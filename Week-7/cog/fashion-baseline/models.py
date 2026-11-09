"""Datasets, networks and image preparation for Week 7 (Fashion-MNIST and CIFAR-10).

Used by train.py and hpo.py for training, and copied into every Cog folder, so the
container builds exactly the same network and prepares images exactly the same way.
"""
import torch
from PIL import Image, ImageOps
from torch import nn
from torchvision import datasets, transforms

CLASSES = {
    "fashion": ["T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
                "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"],
    "cifar10": ["airplane", "automobile", "bird", "cat", "deer",
                "dog", "frog", "horse", "ship", "truck"],
}


# ---------------------------------------------------------------- networks
class FashionNet(nn.Module):
    """The network from the PyTorch quickstart: 28x28 image -> 512 -> 512 -> 10 classes."""

    def __init__(self, hidden=512):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28 * 28, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 10),
        )

    def forward(self, x):
        return self.linear_relu_stack(self.flatten(x))


class CifarNet(nn.Module):
    """The small CNN from the PyTorch "Training a classifier" tutorial.

    width=1 is the tutorial network (6 and 16 filters); width=2 doubles every layer.
    """

    def __init__(self, width=1):
        super().__init__()
        c1, c2 = 6 * width, 16 * width
        self.features = nn.Sequential(
            nn.Conv2d(3, c1, 5), nn.ReLU(), nn.MaxPool2d(2, 2),   # 3x32x32 -> c1x14x14
            nn.Conv2d(c1, c2, 5), nn.ReLU(), nn.MaxPool2d(2, 2),  # -> c2x5x5
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(c2 * 5 * 5, 120 * width), nn.ReLU(),
            nn.Linear(120 * width, 84 * width), nn.ReLU(),
            nn.Linear(84 * width, 10),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


def build_model(dataset, arch):
    """arch is a small dict saved next to the weights, e.g. {"hidden": 512} or {"width": 2}."""
    if dataset == "fashion":
        return FashionNet(**arch)
    return CifarNet(**arch)


# ---------------------------------------------------------------- data
CIFAR_NORMALIZE = transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))


def make_transform(dataset, augment=False):
    """Transforms turn a PIL image into the tensor the network expects."""
    if dataset == "fashion":
        return transforms.ToTensor()                       # 1x28x28, values 0..1
    steps = []
    if augment:                                            # only for training images
        steps += [transforms.RandomCrop(32, padding=4), transforms.RandomHorizontalFlip()]
    steps += [transforms.ToTensor(), CIFAR_NORMALIZE]      # 3x32x32, values -1..1
    return transforms.Compose(steps)


def load_datasets(dataset, root="data", augment=False):
    """Download (first time only) and return (training set, test set)."""
    cls = datasets.FashionMNIST if dataset == "fashion" else datasets.CIFAR10
    train = cls(root=root, train=True, download=True, transform=make_transform(dataset, augment))
    test = cls(root=root, train=False, download=True, transform=make_transform(dataset))
    return train, test


# ---------------------------------------------------------------- real photos
def prepare_image(dataset, img):
    """Turn any uploaded photo into one input tensor shaped like the training images."""
    if dataset == "fashion":
        # Fashion-MNIST: light garment on a black background, 28x28 grayscale.
        gray = ImageOps.exif_transpose(img).convert("L")
        w, h = gray.size
        border = [gray.getpixel((x, y)) for x in (0, w - 1) for y in (0, h - 1)]
        if sum(border) / len(border) > 127:                # photo on a light background
            gray = ImageOps.invert(gray)
        gray = ImageOps.pad(gray, (28, 28), color=0)       # keep the shape, fill with black
        return make_transform("fashion")(gray).unsqueeze(0)
    rgb = ImageOps.exif_transpose(img).convert("RGB").resize((32, 32), Image.BILINEAR)
    return make_transform("cifar10")(rgb).unsqueeze(0)


def predict(model, dataset, img, top_k=3):
    """Return the top-k classes with their probabilities for one PIL image."""
    with torch.no_grad():
        probs = model(prepare_image(dataset, img))[0].softmax(0)
    best = probs.topk(top_k)
    return [{"label": CLASSES[dataset][i], "probability": round(float(p), 4)}
            for p, i in zip(best.values, best.indices)]
