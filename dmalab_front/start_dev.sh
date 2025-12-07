#!/bin/bash
echo "===================================="
echo "DMaLab 프론트엔드 개발 서버 시작"
echo "파일 변경 시 자동으로 새로고침됩니다"
echo "===================================="
echo ""
echo "서버 실행 중: http://localhost:3000"
echo "종료하려면 Ctrl+C를 누르세요"
echo ""

cd "$(dirname "$0")"

# Python HTTP 서버 사용 (자동 새로고침은 브라우저 확장 프로그램 사용)
if command -v python3 &> /dev/null; then
    echo "Python HTTP 서버로 실행 중..."
    python3 -m http.server 3000
elif command -v python &> /dev/null; then
    echo "Python HTTP 서버로 실행 중..."
    python -m http.server 3000
elif command -v node &> /dev/null; then
    echo "Node.js http-server로 실행 중..."
    npx --yes http-server -p 3000 -c-1
else
    echo "Python 또는 Node.js가 필요합니다."
    echo "브라우저에서 index.html을 직접 열어주세요."
    exit 1
fi

