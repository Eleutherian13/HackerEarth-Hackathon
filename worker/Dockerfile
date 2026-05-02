# Multi-stage build for Celery worker
FROM python:3.11-slim as builder

# Install system dependencies for OCR and PDF processing
RUN apt-get update && apt-get install -y \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libtesseract-dev \
    poppler-utils \
    libpoppler-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash worker

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/worker/.local
ENV PATH=/home/worker/.local/bin:$PATH

# Copy application code from backend source tree
COPY ./backend /app

# Change ownership to non-root user
RUN chown -R worker:worker /app

# Switch to non-root user
USER worker

# Entrypoint script
COPY ./worker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
