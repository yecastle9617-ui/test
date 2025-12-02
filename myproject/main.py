"""
메인 모듈
"""

from naver_crawler import NaverCrawler
from morpheme_analyzer import MorphemeAnalyzer
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from datetime import datetime
# from keyword_extractor import KeywordExtractor


def get_output_directory():
    """
    실행 시간 기준으로 출력 디렉토리 경로를 생성합니다.
    프로젝트 상위 디렉토리에 naver_crawler 디렉토리를 생성합니다.
    
    Returns:
        상위 디렉토리/naver_crawler/yyyymmdd_N 형식의 디렉토리 경로
    """
    # 현재 프로젝트 디렉토리의 상위 디렉토리 경로
    current_dir = os.path.dirname(os.path.abspath(__file__))  # myproject 디렉토리
    project_dir = os.path.dirname(current_dir)  # test 디렉토리
    parent_dir = os.path.dirname(project_dir)  # new_project 디렉토리 (상위)
    
    base_dir = os.path.join(parent_dir, "naver_crawler")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    # 오늘 날짜 형식: yyyymmdd
    today = datetime.now().strftime("%Y%m%d")
    
    # 같은 날짜에 실행된 디렉토리 찾기
    dir_pattern = f"{today}_"
    existing_dirs = [d for d in os.listdir(base_dir) if d.startswith(dir_pattern) and os.path.isdir(os.path.join(base_dir, d))]
    
    # 가장 큰 번호 찾기
    max_num = 0
    for dir_name in existing_dirs:
        try:
            num = int(dir_name.split('_')[-1])
            max_num = max(max_num, num)
        except ValueError:
            continue
    
    # 다음 번호 생성
    next_num = max_num + 1
    output_dir = os.path.join(base_dir, f"{today}_{next_num}")
    
    # 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # TOP1, TOP2, TOP3 디렉토리 생성
    for rank in [1, 2, 3]:
        top_dir = os.path.join(output_dir, f"TOP{rank}")
        os.makedirs(top_dir, exist_ok=True)
    
    return output_dir


def process_single_blog(crawler, blog_info, rank, base_output_dir):
    """
    단일 블로그를 처리하는 함수 (병렬 처리용)
    
    Args:
        crawler: NaverCrawler 인스턴스
        blog_info: {'title': str, 'url': str} 형태의 딕셔너리
        rank: 순위 (1, 2, 3)
        
    Returns:
        처리 결과 딕셔너리
    """
    prefix = f"TOP{rank}"
    result = {
        'rank': rank,
        'title': blog_info['title'],
        'url': blog_info['url'],
        'success': False,
        'txt_path': None,
        'excel_path': None,
        'body_text': None,
        'error': None
    }
    
    try:
        print(f"\n[{prefix}] 블로그 처리 시작: {blog_info['title']}")
        
        # TOP별 디렉토리 경로 생성
        top_dir = os.path.join(base_output_dir, prefix)
        
        # 본문 텍스트 추출
        body_text = crawler.extract_blog_body_text(blog_info['url'])
        
        if not body_text:
            result['error'] = "본문 텍스트를 추출할 수 없습니다."
            print(f"[{prefix}] ❌ {result['error']}")
            return result
        
        result['body_text'] = body_text
        print(f"[{prefix}] ✅ 본문 텍스트 추출 완료 (길이: {len(body_text)}자)")
        
        # 본문을 txt 파일로 저장 (TOP 디렉토리 내에 저장)
        txt_path = crawler.save_blog_to_txt(
            blog_info['url'], 
            title=blog_info['title'],
            output_dir=top_dir
        )
        
        if txt_path:
            result['txt_path'] = txt_path
            print(f"[{prefix}] ✅ 본문이 저장되었습니다: {txt_path}")
        else:
            print(f"[{prefix}] ⚠️  본문 저장에 실패했습니다 (계속 진행합니다).")
        
        # 형태소 분석 및 키워드 빈도 분석
        try:
            analyzer = MorphemeAnalyzer(use_konlpy=True)
            
            # 키워드 통계 출력 (상위 20개)
            analyzer.print_keyword_statistics(body_text, top_n=20, min_length=2, min_count=2)
            
            # 엑셀 파일로 저장 (TOP 디렉토리 내에 저장)
            if txt_path:
                base_name = os.path.splitext(os.path.basename(txt_path))[0]
                excel_path = os.path.join(top_dir, f"{base_name}_keyword_analysis.xlsx")
            else:
                # txt 파일이 없어도 엑셀 파일은 저장 시도
                excel_filename = f"blog_{int(os.path.getmtime(top_dir) if os.path.exists(top_dir) else 0)}_keyword_analysis.xlsx"
                excel_path = os.path.join(top_dir, excel_filename)
            
            excel_path = analyzer.export_to_excel(
                body_text, 
                output_path=excel_path,
                top_n=20,
                min_length=2,
                min_count=2
            )
            
            if excel_path:
                result['excel_path'] = excel_path
                print(f"[{prefix}] ✅ 키워드 분석 결과가 엑셀 파일로 저장되었습니다: {excel_path}")
            else:
                print(f"[{prefix}] ⚠️  엑셀 파일 저장에 실패했습니다.")
            
        except Exception as e:
            print(f"[{prefix}] ❌ 형태소 분석 중 오류 발생: {e}")
            result['error'] = f"형태소 분석 오류: {e}"
        
        result['success'] = True
        print(f"[{prefix}] ✅ 처리 완료")
        
    except Exception as e:
        result['error'] = str(e)
        print(f"[{prefix}] ❌ 처리 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    return result


def main():
    """메인 함수 - 단계별 실행"""
    # 검색 키워드 설정
    search_keyword = "아임웹 홈페이지 제작"
    
    print("=" * 60)
    print("네이버 블로그 크롤링 및 키워드 추출 (TOP3 병렬 처리)")
    print("=" * 60)
    
    # ===== 1단계: 탑3 블로그 글 찾기 =====
    print(f"\n[1단계] '{search_keyword}' 키워드로 네이버 통합검색 중...")
    crawler = NaverCrawler()
    blog_list = crawler.get_top_n_blog_info(search_keyword, n=3)
    
    if not blog_list or len(blog_list) == 0:
        print("\n❌ 블로그 글을 찾을 수 없습니다.")
        return
    
    print(f"\n✅ {len(blog_list)}개의 블로그 글 발견!")
    for i, blog_info in enumerate(blog_list, 1):
        print(f"   TOP{i}: {blog_info['title']}")
        print(f"        URL: {blog_info['url']}")
    
    # ===== 2단계: 출력 디렉토리 생성 =====
    output_dir = get_output_directory()
    print(f"\n[2단계] 출력 디렉토리 생성: {output_dir}")
    
    # ===== 3단계: 병렬 처리로 본문 추출 및 저장 =====
    print(f"\n[3단계] TOP3 블로그 병렬 처리 중...")
    results = []
    
    # 각 블로그마다 별도의 크롤러 인스턴스 생성 (세션 충돌 방지)
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 각 블로그에 대해 별도의 크롤러 인스턴스 생성
        futures = []
        for i, blog_info in enumerate(blog_list, 1):
            # 각 스레드마다 새로운 크롤러 인스턴스 생성
            crawler_instance = NaverCrawler()
            future = executor.submit(process_single_blog, crawler_instance, blog_info, i, output_dir)
            futures.append((i, future))
        
        # 완료된 작업부터 결과 수집
        for rank, future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"[TOP{rank}] ❌ 처리 중 예외 발생: {e}")
                results.append({
                    'rank': rank,
                    'title': blog_list[rank-1]['title'] if rank <= len(blog_list) else "알 수 없음",
                    'url': blog_list[rank-1]['url'] if rank <= len(blog_list) else "",
                    'success': False,
                    'error': str(e)
                })
    
    # 결과 정렬 (rank 순서대로)
    results.sort(key=lambda x: x['rank'])
    
    # ===== 최종 결과 요약 =====
    print("\n" + "=" * 60)
    print("[실행 완료 요약]")
    print("=" * 60)
    print(f"검색 키워드: {search_keyword}")
    print(f"발견된 블로그: {len(blog_list)}개")
    print(f"출력 디렉토리: {output_dir}")
    print("\n처리 결과:")
    
    for result in results:
        rank = result['rank']
        print(f"\n[TOP{rank}] {result['title']}")
        if result['success']:
            print(f"  ✅ 성공")
            if result['body_text']:
                print(f"  본문 텍스트 길이: {len(result['body_text'])}자")
            if result['txt_path']:
                print(f"  저장된 txt 파일: {result['txt_path']}")
            if result['excel_path']:
                print(f"  저장된 엑셀 파일: {result['excel_path']}")
        else:
            print(f"  ❌ 실패")
            if result.get('error'):
                print(f"  오류: {result['error']}")
    
    print("\n" + "=" * 60)
    print(f"모든 파일이 다음 디렉토리에 저장되었습니다:")
    print(f"  {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()

