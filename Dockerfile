FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.6.1

# Copy poetry configuration files
COPY pyproject.toml poetry.lock ./

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/

# Install AWS X-Ray daemon dependencies
RUN apt-get update && \
    apt-get install -y curl unzip && \
    curl -o /tmp/xray.zip https://s3.us-east-2.amazonaws.com/aws-xray-assets.us-east-2/xray-daemon/aws-xray-daemon-linux-3.x.zip && \
    unzip /tmp/xray.zip -d /usr/local/bin/ && \
    rm /tmp/xray.zip && \
    apt-get purge -y --auto-remove curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.fastapi_bootstrap.main:app", "--host", "0.0.0.0", "--port", "8000"]