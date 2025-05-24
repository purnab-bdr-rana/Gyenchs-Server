# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app source code
COPY . .

# Expose the port that the app runs on
EXPOSE 3000

# Set the environment variable to tell Flask it's in production
ENV FLASK_ENV=production

# Command to run the app
CMD ["gunicorn", "-b", "0.0.0.0:3000", "app:create_app()", "--worker-class", "gevent", "--workers", "4"]
