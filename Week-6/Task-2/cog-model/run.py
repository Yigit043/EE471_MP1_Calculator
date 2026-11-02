"""Cat-kind classifier for Cog (Week 6 - Task 2).

Uses the pre-trained ResNet50 from Cog's getting-started guide (ImageNet, 1000 classes) and
keeps only the cat classes, so the answer is the kind of cat in the photo.
Every prediction is also written to a log file inside the container:
    docker exec -it <container> tail -f /tmp/predictions.log
"""
import logging
import os
import time

os.environ["TORCH_HOME"] = "/opt/torch"   # weights were downloaded here during `cog build`

import torch
from cog import BaseRunner, Input, Path
from PIL import Image
from torchvision import models

WEIGHTS = models.ResNet50_Weights.IMAGENET1K_V1

# ImageNet class index -> readable name. 281-285 are house cats, 286-293 are wild cats.
CAT_KINDS = {
    281: "Tabby cat",
    282: "Tiger cat",
    283: "Persian cat",
    284: "Siamese cat",
    285: "Egyptian cat",
    286: "Cougar",
    287: "Lynx",
    288: "Leopard",
    289: "Snow leopard",
    290: "Jaguar",
    291: "Lion",
    292: "Tiger",
    293: "Cheetah",
}
CAT_THRESHOLD = 0.30        # below this total cat probability we say "this is probably not a cat"
LOG_FILE = "/tmp/predictions.log"


def make_logger():
    """Log to the container's stdout and to a file we can follow with `docker exec`."""
    logger = logging.getLogger("cat-classifier")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s  %(message)s", "%Y-%m-%d %H:%M:%S")
        for handler in (logging.StreamHandler(), logging.FileHandler(LOG_FILE)):
            handler.setFormatter(fmt)
            logger.addHandler(handler)
    return logger


class Runner(BaseRunner):
    def setup(self):
        """Runs once when the container starts: load the model into memory."""
        self.log = make_logger()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet50(weights=WEIGHTS).to(self.device)
        self.model.eval()
        self.transform = WEIGHTS.transforms()
        self.categories = WEIGHTS.meta["categories"]
        self.count = 0
        self.log.info("Model loaded (ResNet50, device=%s). Waiting for cat photos...", self.device)

    def run(self, image: Path = Input(description="Photo of a cat")) -> dict:
        """Runs for every request: classify the image and return the cat kind."""
        started = time.time()
        img = Image.open(image).convert("RGB")
        with torch.no_grad():
            batch = self.transform(img).unsqueeze(0).to(self.device)
            probs = self.model(batch)[0].softmax(0)

        cat_total = float(sum(probs[i] for i in CAT_KINDS))
        ranked = sorted(CAT_KINDS, key=lambda i: float(probs[i]), reverse=True)[:3]
        top_index = int(probs.argmax())
        is_cat = cat_total >= CAT_THRESHOLD or top_index in CAT_KINDS

        result = {
            "is_cat": is_cat,
            "cat_kind": CAT_KINDS[ranked[0]] if is_cat else None,
            # probability of each kind *among the cat classes* (they add up to about 1)
            "top3": [
                {"kind": CAT_KINDS[i], "probability": round(float(probs[i]) / cat_total, 4)}
                for i in ranked
            ] if cat_total > 0 else [],
            "cat_probability": round(cat_total, 4),
            "model_top_label": self.categories[top_index],
        }

        self.count += 1
        if is_cat:
            answer = f"{result['cat_kind']} ({100 * result['top3'][0]['probability']:.0f}% among cat kinds)"
        else:
            answer = f"NOT A CAT (model sees: {result['model_top_label']})"
        self.log.info("#%d  %dx%d image -> %s, cat probability %.0f%%, %.2f s",
                      self.count, img.width, img.height, answer, 100 * cat_total,
                      time.time() - started)
        return result
