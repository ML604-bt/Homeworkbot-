# Use a minimal Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies for OCR and audio/video
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot code
COPY . .

# Expose the port that aiohttp will listen on
EXPOSE 5000

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Run your bot using aiohttp's built-in web server
CMD ["python", "main.py"]
