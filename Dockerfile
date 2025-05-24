FROM python:3.10-slim

# Install system dependencies required by OpenCV and rembg
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir --timeout 100 --retries 10 -r requirements.txt

# Copy all app files
COPY . .

# Expose the port the app runs on
EXPOSE 3000

# Use environment variables (set securely in hosting platform or .env in dev)
ENV PYTHONUNBUFFERED=1
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:3000 --workers=3"

# Start app with Gunicorn and Flask factory
CMD ["gunicorn", "app:create_app()"]
