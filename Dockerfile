FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary __init__.py files if they don't exist
RUN mkdir -p backend/api && \
    touch backend/__init__.py && \
    touch backend/api/__init__.py

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run application with proper startup command
CMD exec uvicorn backend.api.app:app --host 0.0.0.0 --port $PORT