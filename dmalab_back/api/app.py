"""
FastAPI 서버 애플리케이션
네이버 블로그 크롤링 및 키워드 분석 API
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import uvicorn

from crawler.naver_crawler import NaverCrawler
from analyzer.morpheme_analyzer import MorphemeAnalyzer

# FastAPI 앱 생성
app = FastAPI(
    title="네이버 블로그 크롤링 API",
    description="네이버 블로그 검색, 크롤링 및 키워드 분석 API",
    version="1.0.0"
)

# CORS 설정 (필요시 수정)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Pydantic 모델 정의 =====

class BlogInfo(BaseModel):
    """블로그 정보 모델"""
    title: str
    url: str


class SearchRequest(BaseModel):
    """검색 요청 모델"""
    keyword: str = Field(..., description="검색 키워드")
    n: int = Field(default=3, ge=1, le=10, description="가져올 블로그 개수 (1-10)")


class SearchResponse(BaseModel):
    """검색 응답 모델"""
    keyword: str
    count: int
    blogs: List[BlogInfo]


class CrawlRequest(BaseModel):
    """크롤링 요청 모델 (단일)"""
    url: str = Field(..., description="블로그 URL")
    title: Optional[str] = Field(None, description="블로그 제목 (선택사항)")


class CrawlBulkRequest(BaseModel):
    """크롤링 요청 모델 (리스트)"""
    urls: List[str] = Field(..., description="크롤링할 블로그 URL 리스트")
    titles: Optional[List[Optional[str]]] = Field(None, description="블로그 제목 리스트 (선택사항, urls와 같은 길이)")


class CrawlResponse(BaseModel):
    """크롤링 응답 모델"""
    success: bool
    title: Optional[str] = None
    url: str
    body_text: Optional[str] = None
    body_length: Optional[int] = None
    txt_path: Optional[str] = None
    error: Optional[str] = None


class CrawlBulkResponse(BaseModel):
    """크롤링 응답 모델 (리스트)"""
    total_count: int
    success_count: int
    results: List[CrawlResponse]


class AnalyzeRequest(BaseModel):
    """키워드 분석 요청 모델"""
    text: str = Field(..., description="분석할 텍스트")
    top_n: int = Field(default=20, ge=1, le=100, description="상위 N개 키워드")
    min_length: int = Field(default=2, ge=1, description="최소 키워드 길이")
    min_count: int = Field(default=2, ge=1, description="최소 출현 횟수")


class KeywordStat(BaseModel):
    """키워드 통계 모델"""
    keyword: str
    count: int
    rank: int


class AnalyzeResponse(BaseModel):
    """키워드 분석 응답 모델"""
    success: bool
    total_keywords: int
    keywords: List[KeywordStat]
    excel_path: Optional[str] = None
    error: Optional[str] = None


class ProcessRequest(BaseModel):
    """전체 처리 요청 모델 (검색 + 크롤링 + 분석)"""
    keyword: str = Field(..., description="검색 키워드")
    n: int = Field(default=3, ge=1, le=10, description="처리할 블로그 개수")
    analyze: bool = Field(default=True, description="키워드 분석 수행 여부")
    top_n: int = Field(default=20, ge=1, le=100, description="상위 N개 키워드")
    min_length: int = Field(default=2, ge=1, description="최소 키워드 길이")
    min_count: int = Field(default=2, ge=1, description="최소 출현 횟수")


class ProcessResult(BaseModel):
    """단일 블로그 처리 결과"""
    rank: int
    title: str
    url: str
    success: bool
    body_text: Optional[str] = None
    body_length: Optional[int] = None
    txt_path: Optional[str] = None
    excel_path: Optional[str] = None
    keywords: Optional[List[KeywordStat]] = None
    error: Optional[str] = None


class ProcessResponse(BaseModel):
    """전체 처리 응답 모델"""
    keyword: str
    output_dir: str
    total_count: int
    success_count: int
    results: List[ProcessResult]


# ===== 유틸리티 함수 =====

def get_output_directory():
    """
    실행 시간 기준으로 출력 디렉토리 경로를 생성합니다.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)
    
    base_dir = os.path.join(project_dir, "naver_crawler")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y%m%d")
    dir_pattern = f"{today}_"
    existing_dirs = [d for d in os.listdir(base_dir) if d.startswith(dir_pattern) and os.path.isdir(os.path.join(base_dir, d))]
    
    max_num = 0
    for dir_name in existing_dirs:
        try:
            num = int(dir_name.split('_')[-1])
            max_num = max(max_num, num)
        except ValueError:
            continue
    
    next_num = max_num + 1
    output_dir = os.path.join(base_dir, f"{today}_{next_num}")
    os.makedirs(output_dir, exist_ok=True)
    
    for rank in range(1, 11):  # 최대 10개까지 지원
        top_dir = os.path.join(output_dir, f"TOP{rank}")
        os.makedirs(top_dir, exist_ok=True)
    
    return output_dir


def process_single_blog(
    crawler: NaverCrawler,
    blog_info: Dict[str, str],
    rank: int,
    base_output_dir: str,
    analyze: bool = True,
    top_n: int = 20,
    min_length: int = 2,
    min_count: int = 2
) -> ProcessResult:
    """단일 블로그를 처리하는 함수"""
    result = ProcessResult(
        rank=rank,
        title=blog_info['title'],
        url=blog_info['url'],
        success=False
    )
    
    try:
        top_dir = os.path.join(base_output_dir, f"TOP{rank}")
        
        # 본문 텍스트 추출
        body_text = crawler.extract_blog_body_text(blog_info['url'])
        
        if not body_text:
            result.error = "본문 텍스트를 추출할 수 없습니다."
            return result
        
        result.body_text = body_text
        result.body_length = len(body_text)
        
        # 본문을 txt 파일로 저장
        txt_path = crawler.save_blog_to_txt(
            blog_info['url'],
            title=blog_info['title'],
            output_dir=top_dir
        )
        result.txt_path = txt_path
        
        # 키워드 분석
        if analyze:
            try:
                analyzer = MorphemeAnalyzer(use_konlpy=True)
                
                # 키워드 통계 가져오기
                keyword_stats = analyzer.get_keyword_ranking(
                    body_text,
                    top_n=top_n,
                    min_length=min_length,
                    min_count=min_count
                )
                
                # 키워드 리스트 생성
                keywords = [
                    KeywordStat(keyword=k, count=v['count'], rank=v['rank'])
                    for k, v in keyword_stats.items()
                ]
                result.keywords = keywords
                
                # 엑셀 파일로 저장
                if txt_path:
                    base_name = os.path.splitext(os.path.basename(txt_path))[0]
                    excel_path = os.path.join(top_dir, f"{base_name}_keyword_analysis.xlsx")
                else:
                    excel_filename = f"blog_{int(datetime.now().timestamp())}_keyword_analysis.xlsx"
                    excel_path = os.path.join(top_dir, excel_filename)
                
                excel_path = analyzer.export_to_excel(
                    body_text,
                    output_path=excel_path,
                    top_n=top_n,
                    min_length=min_length,
                    min_count=min_count
                )
                result.excel_path = excel_path
                
            except Exception as e:
                result.error = f"형태소 분석 오류: {str(e)}"
        
        result.success = True
        
    except Exception as e:
        result.error = str(e)
    
    return result


# ===== API 엔드포인트 =====

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "네이버 블로그 크롤링 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


@app.post("/api/search", response_model=SearchResponse)
async def search_blogs(request: SearchRequest):
    """
    키워드로 네이버 블로그 검색
    
    - **keyword**: 검색할 키워드
    - **n**: 가져올 블로그 개수 (1-10)
    """
    try:
        crawler = NaverCrawler()
        blog_list = crawler.get_top_n_blog_info(request.keyword, n=request.n)
        
        if not blog_list or len(blog_list) == 0:
            raise HTTPException(status_code=404, detail="블로그 글을 찾을 수 없습니다.")
        
        blogs = [BlogInfo(title=blog['title'], url=blog['url']) for blog in blog_list]
        
        return SearchResponse(
            keyword=request.keyword,
            count=len(blogs),
            blogs=blogs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@app.post("/api/crawl", response_model=CrawlResponse)
async def crawl_blog(request: CrawlRequest):
    """
    블로그 본문 크롤링 (단일)
    
    - **url**: 크롤링할 블로그 URL
    - **title**: 블로그 제목 (선택사항)
    """
    try:
        crawler = NaverCrawler()
        body_text = crawler.extract_blog_body_text(request.url)
        
        if not body_text:
            return CrawlResponse(
                success=False,
                url=request.url,
                error="본문 텍스트를 추출할 수 없습니다."
            )
        
        # txt 파일 저장 (선택사항)
        txt_path = None
        if request.title:
            txt_path = crawler.save_blog_to_txt(request.url, title=request.title)
        
        return CrawlResponse(
            success=True,
            title=request.title,
            url=request.url,
            body_text=body_text,
            body_length=len(body_text),
            txt_path=txt_path
        )
    except Exception as e:
        return CrawlResponse(
            success=False,
            url=request.url,
            error=str(e)
        )


@app.post("/api/crawl/bulk", response_model=CrawlBulkResponse)
async def crawl_blogs_bulk(request: CrawlBulkRequest):
    """
    블로그 본문 크롤링 (리스트)
    
    - **urls**: 크롤링할 블로그 URL 리스트
    - **titles**: 블로그 제목 리스트 (선택사항, urls와 같은 길이)
    """
    try:
        # titles 길이 검증
        if request.titles and len(request.titles) != len(request.urls):
            raise HTTPException(
                status_code=400,
                detail="titles 리스트의 길이가 urls 리스트의 길이와 일치하지 않습니다."
            )
        
        crawler = NaverCrawler()
        results = []
        success_count = 0
        
        for i, url in enumerate(request.urls):
            title = request.titles[i] if request.titles else None
            
            try:
                body_text = crawler.extract_blog_body_text(url)
                
                if not body_text:
                    results.append(CrawlResponse(
                        success=False,
                        url=url,
                        title=title,
                        error="본문 텍스트를 추출할 수 없습니다."
                    ))
                    continue
                
                # txt 파일 저장 (선택사항)
                txt_path = None
                if title:
                    txt_path = crawler.save_blog_to_txt(url, title=title)
                
                results.append(CrawlResponse(
                    success=True,
                    title=title,
                    url=url,
                    body_text=body_text,
                    body_length=len(body_text),
                    txt_path=txt_path
                ))
                success_count += 1
                
            except Exception as e:
                results.append(CrawlResponse(
                    success=False,
                    url=url,
                    title=title,
                    error=str(e)
                ))
        
        return CrawlBulkResponse(
            total_count=len(results),
            success_count=success_count,
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_keywords(request: AnalyzeRequest):
    """
    텍스트에서 키워드 분석
    
    - **text**: 분석할 텍스트
    - **top_n**: 상위 N개 키워드
    - **min_length**: 최소 키워드 길이
    - **min_count**: 최소 출현 횟수
    """
    try:
        analyzer = MorphemeAnalyzer(use_konlpy=True)
        
        # 키워드 통계 가져오기
        keyword_stats = analyzer.get_keyword_ranking(
            request.text,
            top_n=request.top_n,
            min_length=request.min_length,
            min_count=request.min_count
        )
        
        keywords = [
            KeywordStat(keyword=k, count=v['count'], rank=v['rank'])
            for k, v in keyword_stats.items()
        ]
        
        return AnalyzeResponse(
            success=True,
            total_keywords=len(keywords),
            keywords=keywords
        )
    except Exception as e:
        return AnalyzeResponse(
            success=False,
            total_keywords=0,
            keywords=[],
            error=str(e)
        )


@app.post("/api/process", response_model=ProcessResponse)
async def process_blogs(request: ProcessRequest):
    """
    전체 처리 (검색 + 크롤링 + 분석)
    
    - **keyword**: 검색 키워드
    - **n**: 처리할 블로그 개수
    - **analyze**: 키워드 분석 수행 여부
    - **top_n**: 상위 N개 키워드
    - **min_length**: 최소 키워드 길이
    - **min_count**: 최소 출현 횟수
    """
    try:
        # 1. 블로그 검색
        crawler = NaverCrawler()
        blog_list = crawler.get_top_n_blog_info(request.keyword, n=request.n)
        
        if not blog_list or len(blog_list) == 0:
            raise HTTPException(status_code=404, detail="블로그 글을 찾을 수 없습니다.")
        
        # 2. 출력 디렉토리 생성
        output_dir = get_output_directory()
        
        # 3. 병렬 처리
        results = []
        with ThreadPoolExecutor(max_workers=min(request.n, 3)) as executor:
            futures = []
            for i, blog_info in enumerate(blog_list, 1):
                crawler_instance = NaverCrawler()
                future = executor.submit(
                    process_single_blog,
                    crawler_instance,
                    blog_info,
                    i,
                    output_dir,
                    request.analyze,
                    request.top_n,
                    request.min_length,
                    request.min_count
                )
                futures.append((i, future))
            
            for rank, future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(ProcessResult(
                        rank=rank,
                        title=blog_list[rank-1]['title'] if rank <= len(blog_list) else "알 수 없음",
                        url=blog_list[rank-1]['url'] if rank <= len(blog_list) else "",
                        success=False,
                        error=str(e)
                    ))
        
        # 결과 정렬
        results.sort(key=lambda x: x.rank)
        
        success_count = sum(1 for r in results if r.success)
        
        return ProcessResponse(
            keyword=request.keyword,
            output_dir=output_dir,
            total_count=len(results),
            success_count=success_count,
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

