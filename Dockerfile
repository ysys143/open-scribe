# Multi-stage Dockerfile for testing open-scribe installation

# Stage 1: Build environment with dependencies
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    make \
    build-essential \
    python3.11 \
    python3.11-venv \
    python3-pip \
    ffmpeg \
    zsh \
    bash \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Copy project repository
WORKDIR /app
COPY . .

# Test installation
RUN make install

# Verify installation
RUN ~/.local/bin/scribe --help

# Stage 2: Runtime environment (simpler approach - just test in builder)
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV OPEN_SCRIBE_HOME=/root/.local/share/open-scribe
ENV PATH="/root/.local/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    ffmpeg \
    zsh \
    bash \
    curl \
    ca-certificates \
    git \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Copy installed open-scribe from builder
COPY --from=builder /root/.local /root/.local

# Verify installation
RUN ~/.local/bin/scribe --help

# Set working directory
WORKDIR /root

# Default command
CMD ["/bin/bash"]
