FROM python:3.11.10-alpine

# Install security updates, build dependencies, and create non-root user
RUN apk update && \
    apk upgrade && \
    apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        libffi-dev \
        openssl-dev \
    && addgroup -S appuser && adduser -S appuser -G appuser

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    apk del .build-deps

# Copy application with proper ownership
COPY --chown=appuser:appuser load_generator.py .

# Set proper permissions
RUN chmod 755 /app && \
    chmod 644 /app/load_generator.py

# Switch to non-root user
USER appuser

# Expose metrics port
EXPOSE 8080

# Run the application
CMD ["python", "load_generator.py"]