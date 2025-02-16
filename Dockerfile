FROM python:3.9-slim

# Set environment variable to avoid cache issues
ENV PIP_NO_CACHE_DIR=1

# Install required system dependencies
RUN apt update && apt install --no-install-recommends -y \
    bash curl git wget sudo unzip ffmpeg \
    libjpeg-dev libwebp-dev libffi-dev libssl-dev libopus0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /bot

# Copy the bot files
COPY . /bot

# Upgrade pip and install dependencies
RUN pip3 install --upgrade pip setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

# Start the bot
CMD ["python3", "-m", "shivu"]
