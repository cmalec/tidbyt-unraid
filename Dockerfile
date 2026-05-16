FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Environment variables with defaults
ENV PYTHONUNBUFFERED=1
ENV UNRAID_URL=""
ENV UNRAID_API_KEY=""
ENV TIDBYT_DEVICE_ID=""
ENV TIDBYT_API_KEY=""
ENV UPDATE_INTERVAL=60
ENV TZ=America/Los_Angeles

# Run the scheduler
CMD ["python", "-m", "app.main"]
