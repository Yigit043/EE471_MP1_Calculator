# Week 8 – MediaPipe

## Setup

```
pip install --only-binary=:all: mediapipe
```
Python 3.13, MediaPipe 1.2.3. The models are not part of the package; each script downloads
the model it needs the first time (into a `models/` folder, not committed).

## Task 2 – Which arm is up? (`task2-pose/`)

MediaPipe **Pose Landmarker** finds 33 body points. An arm is "up" when its wrist is higher
than the nose. `left` / `right` are the person's own arms (MediaPipe's convention).

```
cd task2-pose
python arm_up.py ../images/pose-1.jpg            # -> right
python arm_up.py ../images/pose-2.jpg            # -> right
python arm_up.py ../images/pose-3.jpg            # -> both
python arm_up.py ../images/pose-1.jpg --save     # also draws the points into pose-1_result.jpg
```

Cog (inside WSL / Ubuntu):
```
cog build -t arm-up
cog run arm-up -i image=@../images/pose-1.jpg
```

## Task 3 – Where is the face looking? (`task3-face/`)

MediaPipe **Face Landmarker** finds 478 face points. We measure where the nose tip lies
between the two edges of the face (0 = left edge, 0.5 = middle, 1 = right edge):
below 0.40 → `left`, above 0.60 → `right`, otherwise `straight`.
`left` / `right` are as seen in the picture.

```
cd task3-face
python face_direction.py ../images/face-1.png    # -> left
python face_direction.py ../images/face-2.png    # -> right
python face_direction.py ../images/face-3.png    # -> straight
```

Cog (inside WSL / Ubuntu):
```
cog build -t face-direction
cog run face-direction -i image=@../images/face-1.png
```

## Task 1 – MediaPipe solutions (`task1/`)

One short demo script per solution (added later).
