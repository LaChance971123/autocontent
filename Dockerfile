FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose port for Render / Uvicorn
EXPOSE 8000

# Make start.sh executable
RUN chmod +x start.sh

# Default command
CMD ["./start.sh"]
