# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and .env file
COPY . .
COPY .env .

# Create necessary directories
RUN mkdir -p app/static/uploads app/static/profile_pics

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Initialize database
RUN python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    try:
        db.create_all()
        print('✅ Database initialized')
    except Exception as e:
        print(f'❌ Database init failed: {e}')
"

# Expose port
EXPOSE 5000

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "--log-level", "debug", "run:app"]