# Production Dockerfile for Medicall FastAPI Backend
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Copy and prepare startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Run as non-privileged user
RUN useradd -m medicalluser && chown -R medicalluser:medicalluser /app /start.sh
USER medicalluser

EXPOSE 8000

CMD ["/start.sh"]
