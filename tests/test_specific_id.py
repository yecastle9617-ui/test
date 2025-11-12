"""
특정 ID 요소에서 본문 추출 테스트
"""

from myproject.naver_crawler import NaverCrawler
import requests
from bs4 import BeautifulSoup


def test_specific_id_extraction():
    """특정 ID(SE-c616417b-b825-4aa5-887a-c2798755af4f) 아래 본문 추출 테스트"""
    
    crawler = NaverCrawler()
    
    # 테스트용: 실제 블로그 URL 하나 가져오기
    keyword = "벽제납골당"
    print(f"'{keyword}' 키워드로 블로그 검색 중...")
    
    blogs = crawler.get_top_5_blogs(keyword)
    
    if not blogs:
        print("❌ 블로그를 찾을 수 없습니다.")
        return
    
    # 첫 번째 블로그 URL 사용
    test_url = blogs[0]['url']
    print(f"\n테스트 URL: {test_url}")
    print("=" * 60)
    
    # 블로그 페이지 접속
    response = requests.get(test_url, headers=crawler.headers, timeout=10)
    response.raise_for_status()
    response.encoding = 'utf-8'
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    # 특정 ID 요소 찾기
    target_id = "SE-b0cbad23-b7e0-4653-82c2-55a7d1d46f27"
    target_element = soup.find(id=target_id)
    
    if not target_element:
        print(f"❌ ID '{target_id}'를 가진 요소를 찾을 수 없습니다.")
        print("\n[DEBUG] 페이지에 있는 ID 목록 (일부):")
        # 모든 ID 찾기
        all_ids = [elem.get('id') for elem in soup.find_all(id=True) if elem.get('id')]
        for idx, elem_id in enumerate(all_ids[:20]):  # 처음 20개만
            print(f"  - {elem_id}")
        return
    
    print(f"✅ ID '{target_id}' 요소 찾음!")
    print(f"태그: {target_element.name}")
    print(f"클래스: {target_element.get('class', [])}")
    
    # 해당 요소 아래의 모든 텍스트 추출
    print("\n[본문 추출 테스트]")
    print("-" * 60)
    
    # 방법 1: 해당 요소부터 시작해서 모든 하위 요소의 텍스트 추출
    content_container = BeautifulSoup(str(target_element), 'lxml')
    
    # 제목 요소 제거
    for title_elem in content_container.find_all(class_=lambda x: x and 'documentTitle' in str(x)):
        title_elem.decompose()
    
    # 스크립트, 스타일 제거
    for script in content_container(["script", "style", "noscript", "img"]):
        script.decompose()
    
    # 이미지 처리
    for img in content_container.find_all('img'):
        img.replace_with(' [사진] ')
    
    # 텍스트 추출
    text_content = content_container.get_text(separator='\n', strip=True)
    
    # 연속된 공백 제거
    import re
    text_content = re.sub(r'\n{3,}', '\n\n', text_content)
    
    print(f"추출된 텍스트 길이: {len(text_content)}자")
    print(f"\n[본문 내용 (처음 500자)]:")
    print(text_content[:500])
    if len(text_content) > 500:
        print("...")
    
    # 방법 2: 부모 요소 찾기 (se-main-container가 부모일 수도 있음)
    parent = target_element.find_parent(class_=lambda x: x and 'se-main-container' in str(x))
    if parent:
        print(f"\n✅ 부모 요소 'se-main-container' 발견!")
        parent_text = parent.get_text(separator='\n', strip=True)
        print(f"부모 요소 텍스트 길이: {len(parent_text)}자")
    
    # 방법 3: 해당 ID 아래의 모든 요소 구조 확인
    print(f"\n[요소 구조 확인]")
    print(f"직접 하위 요소 개수: {len(target_element.find_all(recursive=False))}")
    print(f"모든 하위 요소 개수: {len(target_element.find_all())}")
    
    # 주요 하위 요소들 확인
    print("\n[주요 하위 요소]:")
    for child in target_element.find_all(['div', 'p', 'span'], limit=10):
        classes = child.get('class', [])
        text = child.get_text(strip=True)[:50]
        if text:
            print(f"  - {child.name} (class: {classes}): {text}...")


if __name__ == "__main__":
    test_specific_id_extraction()

