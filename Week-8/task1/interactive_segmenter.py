"""Interactive Segmenter: click a point -> the object under it is cut out (MagicTouch)."""
import cv2
import mediapipe as mp
import numpy as np

from common import image, label, load_bgr, model, save

V = mp.tasks.vision
path = image("pose-2.jpg")
click = (0.5, 0.45)                                   # normalized x, y: the man's sweater
options = V.InteractiveSegmenterOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("interactive_segmenter")))
mp_image = mp.Image.create_from_file(path)            # keep a reference while the task uses it
x, y = click
scribble = [V.InteractiveSegmenterStrokePoint(x + dx, y + dy)   # a short scribble around the click
            for dx, dy in [(-0.02, 0), (0, -0.02), (0.02, 0), (0, 0.02), (0, 0)]]
with V.InteractiveSegmenter.create_from_options(options) as segmenter:
    segmenter.set_image(mp_image)
    stroke = V.InteractiveSegmenterStroke(
        brush_mode=V.InteractiveSegmenterBrushMode.POSITIVE, points=scribble, is_completed=True)
    mask = np.array(segmenter.segment([stroke]).numpy_view())   # 0..1 per pixel (copied)

mask = np.squeeze(mask) > 0.5
img = load_bgr(path)
print(f"Selected object covers {mask.mean() * 100:.1f}% of the image")
out = img.copy()
out[~mask] = (out[~mask] * 0.25).astype(np.uint8)      # darken everything that was not selected
h, w = img.shape[:2]
cv2.circle(out, (int(click[0] * w), int(click[1] * h)), 6, (0, 0, 255), -1)
label(out, "red dot = click", scale=0.55)
save(out, "interactive_segmenter.png")
