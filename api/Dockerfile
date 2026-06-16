FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy from repo root to preserve package structure
COPY pyproject.toml .
COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# Copy the entire repo to preserve api/ package structure
COPY . .

# Install as package so 'from api.workers...' works
RUN pip install --no-cache-dir -e .

RUN mkdir -p /app/logs /app/screenshots

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]