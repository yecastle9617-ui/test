#!/bin/bash
echo "===================================="
echo "DMaLab 백엔드 개발 서버 시작"
echo "코드 변경 시 자동으로 재시작됩니다"
echo "===================================="
echo ""

cd "$(dirname "$0")"
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

