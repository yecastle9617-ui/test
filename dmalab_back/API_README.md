# FastAPI 서버 사용 가이드

네이버 블로그 크롤링 및 키워드 분석을 위한 FastAPI 서버입니다.

## 설치 방법

```bash
pip install -r requirements.txt
```

## 서버 실행

### 방법 1: Python으로 직접 실행

```bash
cd dmalab_back
python api/app.py
```

### 방법 2: uvicorn으로 실행

```bash
cd dmalab_back
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 다음 주소에서 접근할 수 있습니다:
- API 문서: http://localhost:8000/docs
- 대체 문서: http://localhost:8000/redoc
- API 루트: http://localhost:8000

## API 엔드포인트

### 1. 헬스 체크
```
GET /health
```

### 2. 블로그 검색
```
POST /api/search
```

**요청 본문:**
```json
{
  "keyword": "아임웹 홈페이지 제작",
  "n": 3
}
```

**응답:**
```json
{
  "keyword": "아임웹 홈페이지 제작",
  "count": 3,
  "blogs": [
    {
      "title": "블로그 제목",
      "url": "https://blog.naver.com/..."
    }
  ]
}
```

### 3. 블로그 크롤링
```
POST /api/crawl
```

**요청 본문:**
```json
{
  "url": "https://blog.naver.com/...",
  "title": "블로그 제목 (선택사항)"
}
```

**응답:**
```json
{
  "success": true,
  "title": "블로그 제목",
  "url": "https://blog.naver.com/...",
  "body_text": "본문 텍스트...",
  "body_length": 1234,
  "txt_path": "경로/to/file.txt"
}
```

### 4. 키워드 분석
```
POST /api/analyze
```

**요청 본문:**
```json
{
  "text": "분석할 텍스트...",
  "top_n": 20,
  "min_length": 2,
  "min_count": 2
}
```

**응답:**
```json
{
  "success": true,
  "total_keywords": 20,
  "keywords": [
    {
      "keyword": "키워드",
      "count": 10,
      "rank": 1
    }
  ]
}
```

### 5. 전체 처리 (검색 + 크롤링 + 분석)
```
POST /api/process
```

**요청 본문:**
```json
{
  "keyword": "아임웹 홈페이지 제작",
  "n": 3,
  "analyze": true,
  "top_n": 20,
  "min_length": 2,
  "min_count": 2
}
```

**응답:**
```json
{
  "keyword": "아임웹 홈페이지 제작",
  "output_dir": "경로/to/output",
  "total_count": 3,
  "success_count": 3,
  "results": [
    {
      "rank": 1,
      "title": "블로그 제목",
      "url": "https://blog.naver.com/...",
      "success": true,
      "body_text": "본문 텍스트...",
      "body_length": 1234,
      "txt_path": "경로/to/file.txt",
      "excel_path": "경로/to/file.xlsx",
      "keywords": [
        {
          "keyword": "키워드",
          "count": 10,
          "rank": 1
        }
      ]
    }
  ]
}
```

## 사용 예시

### Python requests 사용

```python
import requests

# 블로그 검색
response = requests.post(
    "http://localhost:8000/api/search",
    json={"keyword": "아임웹 홈페이지 제작", "n": 3}
)
data = response.json()
print(data)

# 전체 처리
response = requests.post(
    "http://localhost:8000/api/process",
    json={
        "keyword": "아임웹 홈페이지 제작",
        "n": 3,
        "analyze": True
    }
)
data = response.json()
print(data)
```

### cURL 사용

```bash
# 블로그 검색
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "아임웹 홈페이지 제작", "n": 3}'

# 전체 처리
curl -X POST "http://localhost:8000/api/process" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "아임웹 홈페이지 제작",
    "n": 3,
    "analyze": true
  }'
```

## 주의사항

- 네이버의 검색 결과 페이지 구조는 변경될 수 있으므로, 크롤링 코드가 작동하지 않을 수 있습니다.
- 과도한 요청을 보내지 않도록 주의하세요. 코드에는 요청 간 지연 시간이 포함되어 있습니다.
- 네이버의 로봇 배제 표준(robots.txt)을 준수하세요.

