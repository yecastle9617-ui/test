@echo off
echo ====================================
echo DMaLab 프론트엔드 개발 서버 시작
echo 파일 변경 시 자동으로 새로고침됩니다
echo ====================================
echo.
echo 서버 실행 중: http://localhost:3000
echo 종료하려면 Ctrl+C를 누르세요
echo.

cd /d %~dp0

REM Python이 설치되어 있으면 Python HTTP 서버 사용
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Python HTTP 서버로 실행 중...
    python -m http.server 3000
) else (
    REM Node.js가 설치되어 있으면 http-server 사용
    where node >nul 2>&1
    if %errorlevel% == 0 (
        echo Node.js http-server로 실행 중...
        npx --yes http-server -p 3000 -c-1
    ) else (
        echo Python 또는 Node.js가 필요합니다.
        echo 브라우저에서 index.html을 직접 열어주세요.
        pause
        exit /b 1
    )
)

pause

