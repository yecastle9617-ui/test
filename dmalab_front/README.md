# DMaLab Frontend

네이버 블로그 크롤링 및 키워드 분석을 위한 웹 프론트엔드입니다.

## 사용 방법

**설치 불필요!** 순수 HTML/JavaScript로 작성되어 있어 바로 사용할 수 있습니다.

1. 백엔드 서버 실행:
```bash
cd ../dmalab_back
python api/app.py
```

2. `index.html` 파일을 브라우저에서 열기:
   - 파일 탐색기에서 `index.html`을 더블클릭
   - 또는 브라우저에서 `file:///경로/dmalab_front/index.html` 열기

3. 또는 간단한 HTTP 서버로 실행 (선택사항):
```bash
# Python 3
python -m http.server 3000

# Node.js (http-server 설치 필요)
npx http-server -p 3000
```

그 후 브라우저에서 http://localhost:3000 으로 접속하세요.

## 기능

- **검색**: 키워드로 네이버 블로그 검색
- **크롤링**: 단일 또는 리스트로 블로그 본문 크롤링
- **키워드 분석**: 텍스트에서 키워드 추출 및 분석
- **전체 처리**: 검색 + 크롤링 + 분석을 한 번에 처리

## 백엔드 서버

프론트엔드를 사용하기 전에 백엔드 서버가 실행 중이어야 합니다:

```bash
cd ../dmalab_back
python api/app.py
```

백엔드 서버는 http://localhost:8000 에서 실행됩니다.

## CORS 설정

브라우저에서 직접 파일을 열 때 CORS 오류가 발생할 수 있습니다. 이 경우:
1. 간단한 HTTP 서버를 사용하거나
2. 백엔드의 CORS 설정을 확인하세요 (이미 모든 origin을 허용하도록 설정되어 있습니다)
