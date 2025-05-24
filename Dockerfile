FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your project files
COPY . .

# Expose the port your Flask app uses
EXPOSE 3000

# Run the Flask app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "app:create_app()"]