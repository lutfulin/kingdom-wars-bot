FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY models.py .
COPY strategy.py .
COPY server.py .

# Expose port
EXPOSE 8000

# Run with 2 workers for high throughput
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
