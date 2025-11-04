FROM python:3.10-slim

# Install system dependencies for PostGIS/GeoAlchemy2
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libproj-dev \
    libgeos-dev \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]