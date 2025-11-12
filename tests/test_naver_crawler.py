"""
네이버 크롤러 테스트
"""

import pytest
from myproject.naver_crawler import NaverCrawler


def test_naver_crawler_initialization():
    """크롤러 초기화 테스트"""
    crawler = NaverCrawler()
    assert crawler is not None
    assert crawler.base_url == "https://search.naver.com/search.naver"


def test_search_blog_title():
    """블로그 검색 테스트"""
    crawler = NaverCrawler()
    result = crawler.search_blog_title("벽제납골당")
    
    # 결과가 None이거나 문자열이어야 함
    assert result is None or isinstance(result, str)


def test_get_first_blog_info():
    """블로그 정보 가져오기 테스트"""
    crawler = NaverCrawler()
    result = crawler.get_first_blog_info("벽제납골당")
    
    # 결과는 딕셔너리여야 함
    assert isinstance(result, dict)
    assert 'site_name' in result
    assert 'url' in result


if __name__ == "__main__":
    pytest.main([__file__])

