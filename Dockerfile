FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    APP_HOME=/app

WORKDIR $APP_HOME

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY agents/ ./agents/
COPY tools/ ./tools/
COPY knowledge/ ./knowledge/
COPY ui/ ./ui/

# Expose default Cloud Run port
EXPOSE 8080

# Start FastAPI UI Server & Multi-Agent Orchestrator
CMD ["python", "-m", "ui.server"]
