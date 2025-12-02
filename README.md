# 네이버 블로그 크롤러

네이버 통합검색에서 블로그 글을 검색하고, 본문 텍스트를 추출하여 저장하는 파이썬 프로젝트입니다.

## 주요 기능

- **네이버 통합검색 크롤링**: 키워드로 네이버 통합검색을 수행하여 탑1 블로그 글을 찾습니다.
- **블로그 본문 추출**: 블로그 글의 본문 텍스트를 추출합니다.
  - iframe(mainFrame) 자동 추적
  - 모바일 페이지 자동 재시도
  - 차단 페이지 감지 및 처리
- **미디어 마커 삽입**: 이미지, 링크, 이모티콘 위치에 마커를 삽입합니다.
  - `[이미지 삽입]`: 이미지가 있는 위치
  - `[링크 삽입]`: 외부 링크가 있는 위치
  - `[이모티콘 삽입]`: 이모티콘이 있는 위치
- **텍스트 파일 저장**: 추출한 본문을 txt 파일로 저장합니다.

## 설치 방법

```bash
pip install -r requirements.txt
```

## 사용 방법

### 기본 실행

```bash
python -m myproject.main
```

기본적으로 `main.py`에서 설정된 키워드("아임웹 홈페이지 제작")로 검색을 수행합니다.

### 코드에서 사용하기

```python
from myproject.naver_crawler import NaverCrawler

crawler = NaverCrawler()

# 1. 키워드로 검색하여 탑1 블로그 정보 가져오기
blog_info = crawler.get_top_1_blog_info("검색 키워드")
print(f"제목: {blog_info['title']}")
print(f"URL: {blog_info['url']}")

# 2. 블로그 본문 텍스트 추출
body_text = crawler.extract_blog_body_text(blog_info['url'])
print(f"본문 길이: {len(body_text)}자")

# 3. 본문을 txt 파일로 저장
txt_path = crawler.save_blog_to_txt(
    blog_info['url'], 
    title=blog_info['title']
)
print(f"저장된 파일: {txt_path}")
```

## 프로젝트 구조

```
.
├── myproject/              # 메인 소스 코드
│   ├── __init__.py
│   ├── main.py            # 메인 실행 파일
│   ├── naver_crawler.py   # 네이버 크롤링 모듈
│   └── keyword_extractor.py  # 키워드 추출 모듈 (현재 미사용)
├── requirements.txt        # 의존성 패키지
├── setup.py               # 패키지 설정
└── README.md              # 프로젝트 설명
```

## 개발 환경 설정

1. 가상 환경 생성:
```bash
python -m venv venv
```

2. 가상 환경 활성화:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

## 주요 클래스 및 메서드

### NaverCrawler

네이버 블로그 크롤링을 담당하는 메인 클래스입니다.

#### 주요 메서드

- `get_top_1_blog_info(keyword: str) -> dict`
  - 키워드로 네이버 통합검색을 수행하여 첫 번째 블로그 글의 제목과 URL을 반환합니다.
  - 반환값: `{'title': str, 'url': str}`

- `extract_blog_body_text(url: str) -> Optional[str]`
  - 블로그 글의 본문 텍스트를 추출합니다.
  - 이미지/링크/이모티콘 위치에 마커를 삽입합니다.
  - iframe과 모바일 페이지를 자동으로 처리합니다.

- `save_blog_to_txt(url: str, output_path: str = None, title: str = None) -> Optional[str]`
  - 블로그 본문을 txt 파일로 저장합니다.
  - 파일명은 자동 생성되거나 지정할 수 있습니다.

## 동작 방식

1. **검색 단계**: 네이버 통합검색에서 키워드로 검색하여 블로그 링크를 찾습니다.
2. **페이지 접근**: 블로그 URL에 접속하여 HTML을 가져옵니다.
3. **iframe 처리**: 필요 시 mainFrame iframe을 추적하여 실제 본문을 가져옵니다.
4. **모바일 페이지 재시도**: 본문을 찾지 못한 경우 모바일 페이지로 재시도합니다.
5. **본문 추출**: `se-main-container` 또는 `post-view` 클래스를 가진 요소에서 본문을 추출합니다.
6. **마커 삽입**: 이미지, 링크, 이모티콘 위치에 적절한 마커를 삽입합니다.
7. **파일 저장**: 추출한 본문을 txt 파일로 저장합니다.

## 주의사항

- 네이버의 검색 결과 페이지 구조는 변경될 수 있으므로, 크롤링 코드가 작동하지 않을 수 있습니다.
- 과도한 요청을 보내지 않도록 주의하세요. 코드에는 요청 간 지연 시간이 포함되어 있습니다.
- 네이버의 로봇 배제 표준(robots.txt)을 준수하세요.
- 차단 페이지가 감지되면 자동으로 모바일 페이지로 재시도하지만, 완전한 차단을 피할 수는 없습니다.
