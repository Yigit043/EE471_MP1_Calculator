# Base image: slim Python on Debian 12 "bookworm" (package names below are for bookworm)
FROM python:3.12-slim-bookworm

# Libraries the Azure Speech SDK needs on Linux: OpenSSL, ALSA (audio), CA certificates
RUN apt-get update \
    && apt-get install -y --no-install-recommends libssl3 libasound2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Logs appear immediately, no .pyc files in the image
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first: this layer is cached and only rebuilt when requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy the application code
COPY . .

# The Azure key is NOT copied into the image; it comes from the .env file at runtime (docker-compose.yml)
EXPOSE 5000

# Production web server: listens on all interfaces so the port can be published to the host.
# Several threads, because a speech request can wait on Azure for a while.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", "--timeout", "180", "app:app"]
