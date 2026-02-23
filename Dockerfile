FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.cloud.txt .
RUN pip install --no-cache-dir -r requirements.cloud.txt

# Copy application code
COPY src/ src/
COPY bot/ bot/

# Cloud Run uses PORT env var
ENV PORT=8080

EXPOSE 8080

CMD ["python", "-m", "bot.main"]
