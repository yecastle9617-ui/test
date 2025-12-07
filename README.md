# DMaLab

네이버 블로그 크롤링 및 키워드 분석을 위한 풀스택 프로젝트입니다.

## 프로젝트 구조

```
.
├── dmalab_back/           # 백엔드 (FastAPI 서버)
│   ├── api/               # API 레이어
│   │   └── app.py         # FastAPI 서버
│   ├── crawler/           # 크롤링 모듈
│   │   ├── naver_crawler.py
│   │   └── naver_login.py
│   ├── analyzer/          # 분석 모듈
│   │   └── morpheme_analyzer.py
│   ├── blog/              # 블로그 모듈
│   │   └── blog_posting.py
│   ├── cli/               # CLI 명령어
│   │   └── main.py
│   ├── config/            # 설정 파일
│   │   └── prompt_template.json
│   ├── tests/             # 테스트 파일
│   ├── requirements.txt   # 의존성 패키지
│   └── API_README.md      # API 사용 가이드
├── dmalab_front/          # 프론트엔드 (예정)
│   └── README.md
└── README.md              # 프로젝트 설명
```

## 빠른 시작

### 백엔드 서버 실행

**개발 모드 (자동 재시작):**
```bash
cd dmalab_back
pip install -r requirements.txt
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
# 또는
start_dev.bat      # Windows
./start_dev.sh     # Linux/Mac
```

**일반 실행:**
```bash
cd dmalab_back
python api/app.py
```

서버가 실행되면:
- API 문서: http://localhost:8000/docs
- API 루트: http://localhost:8000

### 프론트엔드 실행

```bash
cd dmalab_front
python -m http.server 3000
```

브라우저에서 `http://localhost:3000/index.html` 접속

자세한 내용은 각 디렉토리의 README.md를 참고하세요.

## 주요 기능

### 백엔드 (dmalab_back)

- **네이버 통합검색 크롤링**: 키워드로 네이버 통합검색을 수행하여 블로그 글을 찾습니다.
- **블로그 본문 추출**: 블로그 글의 본문 텍스트를 추출합니다.
  - iframe(mainFrame) 자동 추적
  - 모바일 페이지 자동 재시도
  - 차단 페이지 감지 및 처리
- **키워드 분석**: 형태소 분석을 통한 키워드 빈도 및 순위 분석
- **FastAPI 서버**: RESTful API 제공
- **미디어 마커 삽입**: 이미지, 링크, 이모티콘 위치에 마커를 삽입합니다.

### 프론트엔드 (dmalab_front)

- **네이버 상위 블로그 분석**: 키워드로 상위 블로그를 검색하고 분석
- **GPT 블로그 생성**: GPT API를 사용한 블로그 글 자동 생성
- **이미지 생성**: Gemini API를 사용한 이미지 자동 생성
- **순수 HTML/JavaScript**: React 없이 순수 HTML/JS로 구현

## API 엔드포인트

자세한 API 문서는 서버 실행 후 http://localhost:8000/docs 에서 확인할 수 있습니다.

주요 엔드포인트:
- `POST /api/search` - 블로그 검색
- `POST /api/crawl` - 블로그 크롤링
- `POST /api/analyze` - 키워드 분석
- `POST /api/process` - 전체 처리 (검색 + 크롤링 + 분석)

## 주의사항

- 네이버의 검색 결과 페이지 구조는 변경될 수 있으므로, 크롤링 코드가 작동하지 않을 수 있습니다.
- 과도한 요청을 보내지 않도록 주의하세요. 코드에는 요청 간 지연 시간이 포함되어 있습니다.
- 네이버의 로봇 배제 표준(robots.txt)을 준수하세요.
- 차단 페이지가 감지되면 자동으로 모바일 페이지로 재시도하지만, 완전한 차단을 피할 수는 없습니다.
