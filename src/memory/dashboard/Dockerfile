# Dockerfile for Memory Knowledge Graph Dashboard
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 8050

# Set environment variables
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "src/memory/dashboard/enhanced_dashboard.py"]
