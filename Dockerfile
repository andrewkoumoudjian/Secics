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
ENV GOOGLE_CLOUD_PROJECT=sec-insights-project

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "-m", "backend.api.app"]