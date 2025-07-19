FROM python:3.11-slim

WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Docker 환경 변수 설정
ENV DOCKER_ENV=true
ENV PYTHONPATH=/app

EXPOSE 8003

# 올바른 진입점 설정
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]