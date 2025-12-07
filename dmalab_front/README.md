# DMaLab Frontend

네이버 블로그 분석 및 GPT 블로그 생성을 위한 웹 프론트엔드입니다.

## 사용 방법

### 1. 백엔드 서버 실행

프론트엔드를 사용하기 전에 백엔드 서버가 실행 중이어야 합니다:

```bash
cd ../dmalab_back
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

백엔드 서버는 http://localhost:8000 에서 실행됩니다.

### 2. 프론트엔드 실행

**개발 모드 (자동 새로고침):**
```bash
cd dmalab_front
python -m http.server 3000
# 또는
start_dev.bat      # Windows
./start_dev.sh     # Linux/Mac
```

브라우저에서:
- **일반 모드**: `http://localhost:3000/index.html`
- **개발 모드**: `http://localhost:3000/dev.html` (3초마다 자동 새로고침)

## 주요 기능

### 네이버 상위 블로그 분석
- 키워드로 네이버 블로그 검색
- 상위 블로그 크롤링 및 본문 추출
- 키워드 분석 (형태소 분석 기반)

### GPT 블로그 생성
- 키워드 기반 블로그 글 자동 생성
- 상위 블로그 분석 결과를 참고하여 SEO 최적화
- 이미지 자동 생성 (Gemini API)
- 블로그 레벨 선택 (신규/중급/고지수)
- 카테고리 선택 (네이버 블로그 카테고리 구조)
- 금칙어 설정
- 외부 링크 삽입

## 기술 스택

- 순수 HTML/JavaScript (React 없음)
- FastAPI 백엔드 연동
- OpenAI GPT API
- Google Gemini API (이미지 생성)

## 파일 구조

```
dmalab_front/
├── index.html          # 메인 HTML 파일
├── app.js              # 메인 JavaScript 파일
├── style.css           # 스타일시트
├── dev.html            # 개발 모드 (자동 새로고침)
└── README.md           # 이 파일
```

## 주의사항

- 백엔드 서버가 실행 중이어야 프론트엔드가 정상 작동합니다
- CORS 설정은 백엔드에서 모든 origin을 허용하도록 설정되어 있습니다
- 브라우저 캐시 문제가 발생하면 강력 새로고침 (`Ctrl+Shift+R`)을 사용하세요
