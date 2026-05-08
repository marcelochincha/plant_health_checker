FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY services/classifier/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Shared CV libraries from the repo root — inference imports `pipeline`,
# `features`, `processing`, `dataset`, `classifiers` directly.
COPY pipeline.py features.py processing.py dataset.py classifiers.py /app/
COPY services/classifier/app /app/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
