FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install CPU-only PyTorch first to avoid pulling the large CUDA variant
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Model weights are downloaded from GitHub on first startup and cached in
# the named Docker volume mounted at /models/megadetector.
ENV MEGADETECTOR_MODEL_DIR=/models/megadetector
ENV SPECIESNET_URL=http://detector-speciesnet:8101

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8102"]
