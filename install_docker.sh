#!/bin/bash

# Docker 설치 스크립트 (Ubuntu 22.04)
# 카페24 리눅스 서버용

set -e

echo "=========================================="
echo "Docker 설치 스크립트 시작"
echo "=========================================="
echo ""

# root 권한 확인
if [ "$EUID" -ne 0 ]; then 
    echo "  ✗ 이 스크립트는 root 권한이 필요합니다."
    echo "  ℹ sudo ./install_docker.sh 또는 root로 실행하세요."
    exit 1
fi

echo "[1/5] 기존 Docker 제거 중..."
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

echo ""
echo "[2/5] 필수 패키지 설치 중..."
apt-get update
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

echo ""
echo "[3/5] Docker 공식 GPG 키 추가 중..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo ""
echo "[4/5] Docker 저장소 추가 중..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

echo ""
echo "[5/5] Docker 설치 중..."
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo ""
echo "=========================================="
echo "Docker 설치 완료!"
echo "=========================================="
echo ""

# Docker 서비스 시작 및 자동 시작 설정
echo "Docker 서비스 시작 중..."
systemctl start docker
systemctl enable docker

# Docker Compose 확인
echo ""
echo "설치 확인:"
docker --version
docker compose version

echo ""
echo "Docker 서비스 상태:"
systemctl status docker --no-pager -l | head -n 5

echo ""
echo "=========================================="
echo "설치 완료!"
echo "=========================================="
echo ""
echo "다음 명령어로 테스트하세요:"
echo "  docker run hello-world"
echo ""

