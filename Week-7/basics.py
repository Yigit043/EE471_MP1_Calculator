"""PyTorch basics in four short steps (for the pre-demo video).

    python basics.py
Uses the Fashion-MNIST data that train.py already downloaded into data/.
"""
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

print("=== 1. Tensors ===")
x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])          # from a Python list
print(x, "\nshape:", x.shape, " dtype:", x.dtype)
print("x * 10 =\n", x * 10)                          # element-wise math
print("x @ x =\n", x @ x)                            # matrix multiplication
print("random 2x3:\n", torch.rand(2, 3))

print("\n=== 2. Datasets & DataLoaders ===")
training_data = datasets.FashionMNIST(root="data", train=True, download=True,
                                      transform=transforms.ToTensor())
print("training images:", len(training_data))
image, label = training_data[0]                      # one sample = (image, label)
print("one image:", tuple(image.shape), " label:", label, training_data.classes[label])
loader = DataLoader(training_data, batch_size=64, shuffle=True)
images, labels = next(iter(loader))                  # one batch of 64
print("one batch:", tuple(images.shape), tuple(labels.shape))

print("\n=== 3. Transforms ===")
raw, _ = datasets.FashionMNIST(root="data", train=True, download=True)[0]
print("before: PIL image", raw.size, "pixel values 0..255, e.g.", raw.getpixel((14, 14)))
t = transforms.ToTensor()(raw)
print("after ToTensor: tensor", tuple(t.shape), f"values {t.min():.1f}..{t.max():.1f}")
flipped = transforms.RandomHorizontalFlip(p=1.0)(raw)
print("RandomHorizontalFlip: same size", flipped.size, "- used to get more varied training images")

print("\n=== 4. Building a neural network ===")
model = nn.Sequential(
    nn.Flatten(),               # 1x28x28 image -> 784 numbers
    nn.Linear(28 * 28, 512),    # fully connected layer
    nn.ReLU(),                  # non-linearity
    nn.Linear(512, 512),
    nn.ReLU(),
    nn.Linear(512, 10),         # one score (logit) per class
)
print(model)
logits = model(images[:1])                           # the untrained network on one image
probs = logits.softmax(dim=1)
print("10 class probabilities:", [round(p, 2) for p in probs[0].tolist()])
print("prediction before training:", training_data.classes[probs.argmax().item()],
      "| true label:", training_data.classes[labels[0].item()])
print("parameters:", sum(p.numel() for p in model.parameters()))
