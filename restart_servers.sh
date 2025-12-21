#!/bin/bash

# 출력 버퍼링 비활성화 (즉시 출력)
exec > >(tee -a /tmp/restart_servers.log)
exec 2>&1

echo "=========================================="
echo "Docker 서버 재시작 스크립트 시작"
echo "=========================================="
echo ""

# 프로젝트 루트로 이동
cd /home/DMaLab || exit 1

# Docker 및 Docker Compose 설치 확인
if ! command -v docker &> /dev/null; then
    echo "  ✗ Docker가 설치되어 있지 않습니다."
    echo "  ℹ Docker 설치: https://docs.docker.com/get-docker/"
    exit 1
fi

# Docker Compose 플러그인 확인 (최신 Docker는 docker compose 사용)
if ! docker compose version &> /dev/null; then
    echo "  ✗ Docker Compose가 설치되어 있지 않습니다."
    echo "  ℹ Docker Compose 설치: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "[1/4] 기존 컨테이너 종료 중..."
docker compose down && echo "  ✓ 기존 컨테이너 종료됨" || echo "  ℹ 실행 중인 컨테이너 없음"
sleep 2

echo ""
echo "[2/4] Docker 이미지 빌드 중..."
docker compose build && echo "  ✓ 이미지 빌드 완료" || {
    echo "  ✗ 이미지 빌드 실패"
    exit 1
}

echo ""
echo "[3/4] 서버 시작 중..."
docker compose up -d && echo "  ✓ 서버 시작됨" || {
    echo "  ✗ 서버 시작 실패"
    exit 1
}

echo ""
echo "[4/4] 서버 상태 확인 중..."
sleep 3
echo ""
echo "실행 중인 컨테이너:"
docker compose ps

echo ""
echo "서버 로그 (최근 10줄):"
docker compose logs --tail=10

echo ""
echo "=========================================="
echo "서버 재시작 완료!"
echo "=========================================="
echo ""
echo "접속 주소:"
echo "  - 백엔드 API: http://localhost:8000"
echo "  - API 문서: http://localhost:8000/docs"
echo "  - 프론트엔드: http://localhost:3000"
echo ""
echo "유용한 명령어:"
echo "  - 로그 확인: docker compose logs -f"
echo "  - 서버 중지: docker compose down"
echo "  - 서버 재시작: docker compose restart"
echo "=========================================="
