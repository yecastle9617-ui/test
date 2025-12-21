# 프론트엔드 Dockerfile
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 프로젝트 파일 복사
COPY . .

# 포트 노출
EXPOSE 3000

# 서버 실행
CMD ["python3", "-m", "http.server", "3000"]

