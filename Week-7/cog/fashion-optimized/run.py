"""Cog runner for a model trained in Week 7 (the same file is used in every cog/ folder).

The folder holds the trained weights (model.pth), the training settings and test accuracy
(model_info.json) and models.py, so the network is built exactly as it was trained.
Every prediction is also written to a log file inside the container:
    docker exec -it <container> tail -f /tmp/predictions.log
"""
import json
import logging
import time

import torch
from cog import BaseRunner, Input, Path
from PIL import Image

from models import build_model, predict

LOG_FILE = "/tmp/predictions.log"


def make_logger(name):
    """Log to the container's output and to a file we can follow with `docker exec`."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s  %(message)s", "%Y-%m-%d %H:%M:%S")
        for handler in (logging.StreamHandler(), logging.FileHandler(LOG_FILE)):
            handler.setFormatter(fmt)
            logger.addHandler(handler)
    return logger


class Runner(BaseRunner):
    def setup(self):
        """Runs once when the container starts: build the network and load the trained weights."""
        self.info = json.loads(open("model_info.json").read())
        self.dataset = self.info["dataset"]
        self.name = f"{self.dataset}-{self.info['variant']}"
        self.log = make_logger(self.name)
        self.model = build_model(self.dataset, self.info["settings"]["arch"])
        self.model.load_state_dict(torch.load("model.pth", map_location="cpu", weights_only=True))
        self.model.eval()
        self.count = 0
        self.log.info("%s loaded (test accuracy %.1f%%). Waiting for images...",
                      self.name, 100 * self.info["test_accuracy"])

    def run(self, image: Path = Input(description="Image to classify")) -> dict:
        """Runs for every request: classify the image and return the predicted class."""
        started = time.time()
        img = Image.open(image)
        top3 = predict(self.model, self.dataset, img)
        self.count += 1
        self.log.info("#%d  %s  %dx%d image -> %s (%.0f%%), %.3f s", self.count, self.name,
                      img.width, img.height, top3[0]["label"], 100 * top3[0]["probability"],
                      time.time() - started)
        return {
            "predicted_class": top3[0]["label"],
            "confidence": top3[0]["probability"],
            "top3": top3,
            "model": self.name,
            "test_accuracy": self.info["test_accuracy"],
            "settings": self.info["settings"],
        }
