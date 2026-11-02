# Week 6 – Docker and Cog

```
Week-6/
├── Task-1/                      Docker: the two Week 5 apps in containers
│   ├── docker-compose.yml       runs both containers
│   ├── speech-website/          Week-5-Task-1 + Dockerfile + .dockerignore
│   └── voice-calculator/        Week-5-Task-2 + Dockerfile + .dockerignore
└── Task-2/                      Cog: cat-kind classifier
    ├── docker-compose.yml       runs the model container + the website container
    ├── cog-model/               cog.yaml, run.py, requirements.txt (pre-trained ResNet50)
    ├── web/                     Flask website + Dockerfile
    └── make_request.py          builds a JSON request body from an image (for Postman)
```

## Requirements

- **Docker Desktop** (Windows: with the WSL 2 backend).
- **Cog** (Task 2 only). Cog runs on Linux/macOS; on Windows install it inside WSL (Ubuntu):
  ```bash
  sudo curl -o /usr/local/bin/cog -L "https://github.com/replicate/cog/releases/latest/download/cog_$(uname -s)_$(uname -m)"
  sudo chmod +x /usr/local/bin/cog
  ```
  and turn on *Docker Desktop → Settings → Resources → WSL integration → Ubuntu*.
- A `.env` file in the **repository root** (never committed – it is in `.gitignore`):
  ```
  SPEECH_KEY=<your Azure Speech key>
  SPEECH_REGION=<your Azure region, e.g. germanywestcentral>
  ```

## Task 1 – Containerized speech website and voice calculator

```bash
cd Week-6/Task-1
docker compose up --build
```

| App | URL |
|---|---|
| Speech website (TTS, STT, diarization, translation, pronunciation) | http://localhost:5000 |
| Voice-activated calculator | http://localhost:5001 |

Stop with `Ctrl+C`, or `docker compose down`.
The Azure key is passed at run time with `env_file` – it is **not** copied into the images.

## Task 2 – Cat-kind classifier with Cog

**1. Build the model image with Cog** (in WSL/Ubuntu):
```bash
cd /mnt/c/<path-to-repo>/Week-6/Task-2/cog-model
cog build -t cat-classifier
```
Optional quick test without the website:
```bash
cog run cat-classifier -i image=@/path/to/cat.jpg
```

**2. Start the model and the website** (PowerShell or WSL):
```bash
cd Week-6/Task-2
docker compose up --build
```

| Service | URL |
|---|---|
| Website | http://localhost:5003 |
| Cog model HTTP API | http://localhost:5002/predictions |

**3. Live prediction logs from inside the container:**
```bash
docker ps                                                # find the cat-model container
docker exec -it week6-task2-cat-model-1 tail -f /tmp/predictions.log
```
(`docker compose logs -f cat-model` shows the same lines from outside.)

**4. API verification with Postman:**
```bash
python make_request.py path/to/cat.jpg                   # writes request.json
```
Postman: `POST http://localhost:5002/predictions` → Body → **binary** → select `request.json`
→ Headers: `Content-Type: application/json` → Send. The response's `output` contains `cat_kind`.

Alternatively, with an image on the web:
```json
{"input": {"image": "https://example.com/cat.jpg"}}
```

## How the model works

`run.py` loads the pre-trained ResNet50 from Cog's getting-started guide (ImageNet, 1000 classes)
once in `setup()`. `run()` classifies the photo and keeps only the 13 cat classes
(tabby, tiger cat, Persian, Siamese, Egyptian cat, cougar, lynx, leopard, snow leopard, jaguar,
lion, tiger, cheetah). If the cat classes together are below 30 % and the top label is not a cat,
the answer is "not a cat". The weights are downloaded during `cog build` and stored in the image,
so the container starts without internet.
