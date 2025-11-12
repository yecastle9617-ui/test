"""
메인 모듈
"""

from myproject.naver_crawler import NaverCrawler


def main():
    """메인 함수"""
    crawler = NaverCrawler()
    
    # 예시: "벽제납골당" 검색
    keyword = "벽제납골당"
    
    print(f"'{keyword}' 키워드로 네이버 통합검색 중...")
    print("=" * 60)
    
    # 1. 탑1 블로그 글의 제목과 URL 찾기
    blog_info = crawler.get_top_1_blog_info(keyword)
    
    if blog_info['title'] and blog_info['url']:
        print(f"\n[탑1 블로그 글]")
        print(f"제목: {blog_info['title']}")
        print(f"URL: {blog_info['url']}")
        print("=" * 60)
        
        # 2. 해당 URL에서 se-main-container 개수 찾기
        print(f"\n[se-main-container 개수 확인 중...]")
        count = crawler.count_se_main_container(blog_info['url'])
        print(f"se-main-container 클래스를 가진 요소 개수: {count}개")
        
        # 3. post-view{글ID} div 개수 찾기
        print(f"\n[post-view div 개수 확인 중...]")
        post_view_count = crawler.count_post_view_div(blog_info['url'])
        print(f"post-view div 요소 개수: {post_view_count}개")
    else:
        print("\n❌ 블로그 글을 찾을 수 없습니다.")


if __name__ == "__main__":
    main()

