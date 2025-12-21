# Docker를 사용한 서버 실행 가이드

Docker를 사용하여 백엔드와 프론트엔드 서버를 실행하는 방법입니다.

## 사전 요구사항

- Docker 설치
- Docker Compose 설치

## 빠른 시작

### 1. 서버 시작

```bash
cd /home/DMaLab
docker-compose up -d
```

### 2. 서버 상태 확인

```bash
docker-compose ps
```

### 3. 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 백엔드만
docker-compose logs -f backend

# 프론트엔드만
docker-compose logs -f frontend
```

### 4. 서버 중지

```bash
docker-compose down
```

### 5. 서버 재시작

```bash
docker-compose restart
```

## 주요 명령어

### 컨테이너 관리

```bash
# 서버 시작 (백그라운드)
docker-compose up -d

# 서버 시작 (포그라운드, 로그 확인)
docker-compose up

# 서버 중지
docker-compose down

# 서버 중지 및 볼륨 삭제
docker-compose down -v

# 서버 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart backend
docker-compose restart frontend
```

### 로그 관리

```bash
# 실시간 로그 확인
docker-compose logs -f

# 최근 100줄 로그
docker-compose logs --tail=100

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 컨테이너 접속

```bash
# 백엔드 컨테이너 접속
docker-compose exec backend bash

# 프론트엔드 컨테이너 접속
docker-compose exec frontend bash
```

### 이미지 재빌드

```bash
# 모든 서비스 재빌드
docker-compose build

# 특정 서비스만 재빌드
docker-compose build backend
docker-compose build frontend

# 재빌드 후 재시작
docker-compose up -d --build
```

## 접속 주소

- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **프론트엔드**: http://localhost:3000

## 환경 변수 설정

`.env` 파일을 프로젝트 루트(`/home/DMaLab/.env`)에 생성하면 자동으로 로드됩니다.

```bash
# .env 파일 예시
API_KEY=your_api_key
DATABASE_URL=your_database_url
```

## 볼륨 마운트

현재 설정은 개발 모드로, 코드 변경 시 자동으로 반영됩니다:
- `./dmalab_back:/app` - 백엔드 코드
- `./dmalab_front:/app` - 프론트엔드 코드
- `./dmalab_back/data:/app/data` - 데이터 디렉토리
- `./dmalab_back/naver_crawler:/app/naver_crawler` - 크롤러 데이터

## 문제 해결

### 포트가 이미 사용 중인 경우

```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :8000
sudo lsof -i :3000

# 프로세스 종료
sudo kill -9 <PID>
```

### 컨테이너가 시작되지 않는 경우

```bash
# 로그 확인
docker-compose logs

# 컨테이너 상태 확인
docker-compose ps

# 이미지 재빌드
docker-compose build --no-cache
docker-compose up -d
```

### 컨테이너 완전히 제거 후 재시작

```bash
docker-compose down
docker-compose rm -f
docker-compose build --no-cache
docker-compose up -d
```

## 프로덕션 배포

프로덕션 환경에서는 `docker-compose.prod.yml`을 별도로 만들어 사용하는 것을 권장합니다:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./dmalab_back
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    # 볼륨 마운트 제거 (코드 변경 자동 반영 비활성화)
    restart: always
    # 리소스 제한 설정
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## Cursor 종료 후에도 서버 유지

Docker를 사용하면 Cursor를 종료해도 서버가 계속 실행됩니다. 시스템 재부팅 후에도 자동으로 시작하려면:

```bash
# 시스템 재부팅 시 자동 시작 설정
docker-compose up -d
```

또는 systemd 서비스로 등록:

```bash
# /etc/systemd/system/dmalab.service 파일 생성
sudo nano /etc/systemd/system/dmalab.service
```

```ini
[Unit]
Description=DMaLab Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/DMaLab
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 활성화
sudo systemctl enable dmalab.service
sudo systemctl start dmalab.service
```

