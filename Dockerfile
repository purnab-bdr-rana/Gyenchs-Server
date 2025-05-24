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

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your project files
COPY . .

# Set environment variables for Flask
ENV FLASK_APP="app:create_app()"
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=3000
ENV FLASK_ENV=development 

# Expose the port your Flask app uses
EXPOSE 3000

# Run the Flask app directly (no Gunicorn)
CMD ["flask", "run"]