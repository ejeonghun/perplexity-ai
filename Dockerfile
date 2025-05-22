# Python 3.11 이미지를 기반으로 함
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 환경 변수 설정 (Python 버퍼링 비활성화)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 필요한 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# browser_cookie3 패키지 (쿠키 추출에 필요) 설치
RUN pip install --no-cache-dir browser_cookie3

# 애플리케이션 코드 복사
COPY . .

# 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]