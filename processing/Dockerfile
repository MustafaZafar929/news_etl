FROM python:3.10-slim

WORKDIR /opt/dagster/app

# 1. Install System Dependencies
# ADDED: libgomp1 (Required for scikit-learn/DBSCAN to work)
RUN apt-get update && apt-get install -y \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install CPU-only PyTorch (Keeps image small)
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 3. Install other requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# 4. Copy Code
COPY . .

CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-f", "process.py"]