FROM python:3.10-slim

# Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Disable GPU
ENV CUDA_VISIBLE_DEVICES=""

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your project files
COPY . .

# Expose the port your Flask app uses
EXPOSE 3000

# Run the Flask app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "app:create_app()"]