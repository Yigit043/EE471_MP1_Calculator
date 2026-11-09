# Week 7 – Train, optimize and containerize image classifiers

Two image classifiers trained with PyTorch, each in two versions:

| Dataset | Baseline (tutorial settings) | Optimized (after hyperparameter search) |
|---|---|---|
| Fashion-MNIST (10 kinds of garments, 28x28 grayscale) | quickstart network, SGD lr 0.001, batch 64, 5 epochs | best settings from `hpo.py` |
| CIFAR-10 (10 object classes, 32x32 colour) | tutorial CNN, SGD + momentum, lr 0.001, batch 4, 2 epochs | best settings from `hpo.py` |

Each model runs in its own Cog container. A small Flask website sends the uploaded image to both
containers at the same time and shows the two answers side by side.

## Folder structure

```
Week-7/
├── models.py            # datasets, transforms, networks, image preparation (shared)
├── train.py             # trains the baseline model          -> cog/<dataset>-baseline/
├── hpo.py               # hyperparameter search + final model -> cog/<dataset>-optimized/, results/
├── export_samples.py    # saves test images as PNG            -> test-images/<dataset>/
├── make_request.py      # image -> request.json for Postman
├── cog/
│   ├── fashion-baseline/    cog.yaml, run.py, requirements.txt, models.py, model.pth, model_info.json
│   ├── fashion-optimized/
│   ├── cifar10-baseline/
│   └── cifar10-optimized/
├── results/             # hyperparameter search tables (for the report)
├── web/                 # comparison website (Flask + HTML/CSS/JS, Dockerfile)
└── docker-compose.yml   # models + websites
```

## Setup

Requirements: Python 3.13, Docker Desktop (WSL 2), Cog (inside WSL/Ubuntu).

```
pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu
```

### 1. Train (Windows terminal, in `Week-7`)

```
python train.py fashion          # baseline
python hpo.py fashion            # search + optimized model
python export_samples.py fashion # test images
python train.py cifar10
python hpo.py cifar10
python export_samples.py cifar10
```
The datasets are downloaded into `data/` the first time (not committed).

### 2. Build the Cog images (Ubuntu / WSL)

```
cd /mnt/c/Users/<user>/EE471/EE471_MP1_Calculator/Week-7/cog/fashion-baseline && cog build -t fashion-baseline
cd ../fashion-optimized && cog build -t fashion-optimized
cd ../cifar10-baseline && cog build -t cifar10-baseline
cd ../cifar10-optimized && cog build -t cifar10-optimized
```
Quick test: `cog run fashion-optimized -i image=@../../test-images/fashion/9_Ankle-boot_0.png`

### 3. Run the websites (Windows terminal, in `Week-7`)

```
docker compose up --build fashion-web     # http://localhost:5012
docker compose up --build cifar10-web     # http://localhost:5022
```

| Service | Port | Container name |
|---|---|---|
| Fashion baseline Cog API | 5010 | week7-fashion-baseline-1 |
| Fashion optimized Cog API | 5011 | week7-fashion-optimized-1 |
| Garment website | 5012 | |
| CIFAR-10 baseline Cog API | 5020 | week7-cifar10-baseline-1 |
| CIFAR-10 optimized Cog API | 5021 | week7-cifar10-optimized-1 |
| CIFAR-10 website | 5022 | |

### 4. Live prediction logs (inside a container)

```
docker exec -it week7-fashion-optimized-1 tail -f /tmp/predictions.log
```

### 5. API verification with Postman

```
python make_request.py test-images/fashion/9_Ankle-boot_0.png      # writes request.json
```
Postman: `POST http://localhost:5011/predictions`, header `Content-Type: application/json`,
Body → binary → `request.json`. The answer contains `predicted_class`, `confidence` and `top3`.
