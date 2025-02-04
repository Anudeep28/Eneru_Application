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
    wkhtmltopdf \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3.11 -m pip install --no-cache-dir virtualenv && \
    python3.11 -m virtualenv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/media /app/static

# Collect static files
RUN python manage.py collectstatic --noinput

# Create wrapper script for wkhtmltopdf with xvfb
RUN echo '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf $*' > /usr/local/bin/wkhtmltopdf.sh \
    && chmod +x /usr/local/bin/wkhtmltopdf.sh

# Set the wkhtmltopdf wrapper as the default wkhtmltopdf
ENV WKHTMLTOPDF_CMD=/usr/local/bin/wkhtmltopdf.sh

# Expose port
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "chitfund.wsgi:application"]
