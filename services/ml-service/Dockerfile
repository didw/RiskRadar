FROM python:3.11-slim

WORKDIR /app

# Install Java for KoNLPy
RUN apt-get update && apt-get install -y openjdk-17-jre-headless && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8002

CMD ["python", "main.py"]