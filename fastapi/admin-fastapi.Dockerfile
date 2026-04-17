# 1. 베이스 이미지 설정 (가볍고 안정적인 파이썬 알파인/슬림 버전)
FROM python:3.14-slim

# 2. 작업 디렉토리 설정 (컨테이너 내부 경로)
WORKDIR /app

# 3. requirements.txt 복사 및 설치
# 현재 위치(app/..)에서 컨테이너의 현재 작업디렉토리(.)로 복사
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. app 폴더 내부의 모든 소스 코드를 컨테이너의 /app으로 복사
COPY app/ .

# 5. FastAPI 실행
# WORKDIR이 /app이고 소스가 그 안에 바로 있으므로 main:app으로 실행하면 됩니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]