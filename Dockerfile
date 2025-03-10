# Use Python 3.9 as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_CLOUD_PROJECT=halogen-rampart-452816-r2

# Expose port
EXPOSE 8080

# Run application - fixed command to properly start the server
CMD exec python -m uvicorn backend.api.app:app --host 0.0.0.0 --port ${PORT}
