FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-hin tesseract-ocr-eng poppler-utils libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY global-automation/govdoc-ocr /app/global-automation/govdoc-ocr
COPY global-automation/govdoc_ocr /app/global-automation/govdoc_ocr
COPY worker/worker.py /app/worker.py
ENV PYTHONPATH=/app/global-automation:/app/global-automation/govdoc-ocr
CMD ["python", "/app/worker.py"]
