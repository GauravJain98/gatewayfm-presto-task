FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY load_generator.py .

# Set environment variables
ENV GETH_URL=http://geth-devnet-service:8545
ENV TARGET_TPS=10
ENV CONCURRENCY=10
ENV METRICS_PORT=8080
ENV TEST_DURATION=3600

# Expose metrics port
EXPOSE 8080

# Run the application
CMD ["python", "load_generator.py"]