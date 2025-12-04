# 프로젝트 구조 제안

## 추천 구조 (기능별 모듈화)

```
dmalab_back/
├── api/                    # API 레이어
│   ├── __init__.py
│   ├── main.py            # FastAPI 앱 진입점
│   ├── routes/            # API 라우트
│   │   ├── __init__.py
│   │   ├── search.py      # 검색 엔드포인트
│   │   ├── crawl.py       # 크롤링 엔드포인트
│   │   └── analyze.py     # 분석 엔드포인트
│   └── models/            # Pydantic 모델
│       ├── __init__.py
│       ├── request.py
│       └── response.py
│
├── services/              # 비즈니스 로직
│   ├── __init__.py
│   ├── crawler_service.py
│   └── analyzer_service.py
│
├── core/                  # 핵심 모듈
│   ├── __init__.py
│   ├── crawler/           # 크롤링 관련
│   │   ├── __init__.py
│   │   ├── naver_crawler.py
│   │   └── naver_login.py
│   ├── analyzer/          # 분석 관련
│   │   ├── __init__.py
│   │   └── morpheme_analyzer.py
│   └── blog/              # 블로그 관련
│       ├── __init__.py
│       └── blog_posting.py
│
├── config/                # 설정 파일
│   ├── __init__.py
│   ├── settings.py
│   └── prompt_template.json
│
├── utils/                 # 유틸리티
│   ├── __init__.py
│   └── file_utils.py
│
├── cli/                   # CLI 명령어
│   ├── __init__.py
│   └── main.py
│
├── tests/                 # 테스트 파일
│   ├── __init__.py
│   ├── test_crawler.py
│   └── test_analyzer.py
│
├── requirements.txt
├── setup.py
└── README.md
```

## 장점

1. **명확한 책임 분리**: 각 모듈이 명확한 역할을 가짐
2. **확장성**: 새로운 기능 추가가 쉬움
3. **테스트 용이**: 각 모듈을 독립적으로 테스트 가능
4. **유지보수성**: 코드 찾기와 수정이 쉬움
5. **표준 구조**: FastAPI 프로젝트의 일반적인 구조

## 대안 구조 (간단한 버전)

프로젝트가 작다면 더 간단하게:

```
dmalab_back/
├── api/
│   ├── __init__.py
│   └── app.py            # FastAPI 앱
│
├── crawler/               # 크롤링 모듈
│   ├── __init__.py
│   ├── naver_crawler.py
│   └── naver_login.py
│
├── analyzer/              # 분석 모듈
│   ├── __init__.py
│   └── morpheme_analyzer.py
│
├── blog/                  # 블로그 모듈
│   ├── __init__.py
│   └── blog_posting.py
│
├── config/
│   └── prompt_template.json
│
├── cli/
│   └── main.py
│
├── tests/
│   └── test_*.py
│
├── requirements.txt
└── README.md
```

