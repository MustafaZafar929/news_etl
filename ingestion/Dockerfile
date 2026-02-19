FROM python:3.10-slim
WORKDIR /opt/dagster/app

# Install git (needed for some AI model downloads)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-f", "injest.py"]