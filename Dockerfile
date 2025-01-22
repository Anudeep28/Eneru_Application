# Use NVIDIA CUDA base image
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=chitfund.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    python3-pip \
    postgresql-client \
    libpq-dev \
    ffmpeg \
    tesseract-ocr \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libsndfile1 \
    libasound2-dev \
    portaudio19-dev \
    python3-all-dev \
    ninja-build \
    meson \
    gfortran \
    libopenblas-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3.11 -m pip install --no-cache-dir virtualenv && \
    python3.11 -m virtualenv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Collect static files
RUN python manage.py collectstatic --noinput

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "chitfund.wsgi:application"]
