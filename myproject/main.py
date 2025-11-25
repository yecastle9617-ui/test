"""
메인 모듈
"""

from naver_crawler import NaverCrawler
# from keyword_extractor import KeywordExtractor


def main():
    """메인 함수 - 단계별 실행"""
    # 검색 키워드 설정
    search_keyword = "아임웹 홈페이지 제작"
    
    print("=" * 60)
    print("네이버 블로그 크롤링 및 키워드 추출")
    print("=" * 60)
    
    # ===== 1단계: 탑1 블로그 글 찾기 =====
    print(f"\n[1단계] '{search_keyword}' 키워드로 네이버 통합검색 중...")
    crawler = NaverCrawler()
    blog_info = crawler.get_top_1_blog_info(search_keyword)
    
    if not blog_info['title'] or not blog_info['url']:
        print("\n❌ 블로그 글을 찾을 수 없습니다.")
        return
    
    print(f"\n✅ 탑1 블로그 글 발견!")
    print(f"   제목: {blog_info['title']}")
    print(f"   URL: {blog_info['url']}")
    
    # ===== 2단계: 본문 텍스트 추출 =====
    print(f"\n[2단계] 본문 텍스트 추출 중...")
    body_text = crawler.extract_blog_body_text(blog_info['url'])
    
    if not body_text:
        print("❌ 본문 텍스트를 추출할 수 없습니다.")
        return
    
    print(f"✅ 본문 텍스트 추출 완료 (길이: {len(body_text)}자)")
    
    # ===== 3단계: 본문을 txt 파일로 저장 =====
    print(f"\n[3단계] 본문 텍스트를 txt 파일로 저장 중...")
    txt_path = crawler.save_blog_to_txt(blog_info['url'], title=blog_info['title'])
    
    if txt_path:
        print(f"✅ 본문이 저장되었습니다: {txt_path}")
    else:
        print("⚠️  본문 저장에 실패했습니다 (계속 진행합니다).")
    
    # ===== 4단계: 키워드 추출 =====
    # print(f"\n[4단계] 자주 나오는 키워드 3개 추출 중...")
    # try:
    #     extractor = KeywordExtractor(use_konlpy=True)
    #     keywords = extractor.extract_keywords(body_text, top_n=3)
    #     
    #     if keywords:
    #         print(f"\n✅ 추출된 키워드 (상위 3개):")
    #         for i, keyword in enumerate(keywords, 1):
    #             print(f"   {i}. {keyword}")
    #         
    #         # 키워드와 빈도 함께 표시
    #         keywords_with_weights = extractor.extract_with_weights(body_text, top_n=3)
    #         if keywords_with_weights:
    #             print(f"\n[키워드 빈도 정보]")
    #             for i, (keyword, count) in enumerate(keywords_with_weights, 1):
    #                 print(f"   {i}. {keyword} (빈도: {count}회)")
    #     else:
    #         print("❌ 키워드를 추출할 수 없습니다.")
    #         
    # except Exception as e:
    #     print(f"❌ 키워드 추출 중 오류 발생: {e}")
    #     import traceback
    #     traceback.print_exc()
    
    # ===== 최종 결과 요약 =====
    print("\n" + "=" * 60)
    print("[실행 완료 요약]")
    print("=" * 60)
    print(f"검색 키워드: {search_keyword}")
    print(f"발견된 블로그: {blog_info['title']}")
    print(f"본문 텍스트 길이: {len(body_text)}자")
    if txt_path:
        print(f"저장된 파일: {txt_path}")
    # if 'keywords' in locals() and keywords:
    #     print(f"추출된 키워드: {', '.join(keywords)}")
    print("=" * 60)


if __name__ == "__main__":
    main()

