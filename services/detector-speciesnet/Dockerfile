FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# git is required for the HuggingFace pip install
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Install CPU-only PyTorch first to avoid pulling the CUDA variant (~2 GB saved)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Model weights are downloaded from HuggingFace on first startup and cached here.
ENV HF_HOME=/app/.cache/huggingface
ENV SPECIESNET_MODEL=Addax-Data-Science/SPECIESNET-v4-0-1-A-v1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8101"]
