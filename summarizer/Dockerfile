FROM python:3.10-slim

WORKDIR /opt/dagster/app

# 1. Install System Dependencies
# libgomp1 is good to have just in case we add ML libs later.
RUN apt-get update && apt-get install -y \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install requirements
COPY requirements.txt .
# Force rebuild for new dependencies
RUN pip install -r requirements.txt

# 3. Copy Code
COPY . .

# Run Dagster gRPC server
CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4002", "-f", "summarize.py"]
