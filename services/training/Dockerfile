FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY services/training/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Shared CV libraries from the repo root.
COPY pipeline.py features.py processing.py dataset.py classifiers.py /app/
COPY services/training /app/training
WORKDIR /app/training

CMD ["python", "train.py", "--help"]
