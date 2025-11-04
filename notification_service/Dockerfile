FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Make the start script executable
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]