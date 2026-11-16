"""Image Segmenter: label every pixel (DeepLab-V3: background, person, cat, dog, ...)."""
import mediapipe as mp
import numpy as np

from common import image, label, load_bgr, model, save

V = mp.tasks.vision
path = image("pose-1.jpg")
options = V.ImageSegmenterOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("image_segmenter")),
    output_category_mask=True, output_confidence_masks=False)
with V.ImageSegmenter.create_from_options(options) as segmenter:
    result = segmenter.segment(mp.Image.create_from_file(path))
    labels = segmenter.labels

mask = np.squeeze(result.category_mask.numpy_view())   # one class number per pixel (H x W)
img = load_bgr(path)
for cls in np.unique(mask):
    share = (mask == cls).mean() * 100
    print(f"{labels[cls]:12s} {share:5.1f}% of the pixels")
overlay = img.copy()
overlay[mask > 0] = (0.5 * overlay[mask > 0] + [0, 0, 127]).astype(np.uint8)   # tint non-background red
label(overlay, "red = person", scale=0.6)
save(overlay, "image_segmenter.png")
