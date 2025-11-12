"""
네이버 검색 결과 크롤링 모듈
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional
import re
import time
import random
from urllib.parse import urlparse, urljoin, parse_qs


class NaverCrawler:
    """네이버 검색 결과를 크롤링하는 클래스"""
    
    def __init__(self):
        """크롤러 초기화"""
        self.base_url = "https://search.naver.com/search.naver"
        # 세션 사용 (쿠키 유지, 연결 재사용)
        self.session = requests.Session()
        # 실제 브라우저처럼 보이도록 헤더 설정 (차단 방지)
        self._update_headers()
        
    def _update_headers(self):
        """헤더 업데이트 (User-Agent 로테이션)"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        self.headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Referer': 'https://www.naver.com/',
        }
        self.session.headers.update(self.headers)
    
    def _is_blocked_html(self, html_text: str) -> bool:
        """
        네이버 차단 페이지 여부를 판별합니다.
        단순히 '차단'이라는 단어만으로 오탐하지 않도록 대표적인 패턴을 확인합니다.
        """
        lowered = html_text.lower()
        # 대표적인 차단 문구/패턴
        block_patterns = [
            '해당 블로그는 운영정책 위반으로 접근이 제한되었습니다',
            'access to this blog has been blocked',
            'captcha-invitation',
            'blog.naver.com/section/notice',
            '본 인증을 완료해 주세요',
            '보안 인증을 위해'
        ]
        # iframe 차단 페이지: window.location.replace 등 리다이렉트
        redirect_patterns = [
            'location.replace("/blocked"',
            'location.href = "/blocked"',
            'window.location.replace("/blocked"',
            'securityNotice'
        ]
        
        for pattern in block_patterns:
            if pattern.lower() in lowered:
                return True
        
        for pattern in redirect_patterns:
            if pattern.lower() in lowered:
                return True
        
        return False
    
    def _fetch_blog_page(self, url: str) -> Optional[dict]:
        """
        블로그 본문을 포함한 HTML과 파싱 결과를 반환합니다.
        필요 시 iframe(mainFrame)과 모바일 페이지까지 추적합니다.
        """
        try:
            original_url = url
            current_url = url
            
            # 네이버 리다이렉트 URL 처리
            if 'naver.com/search.naver' in current_url or 'search.naver.com' in current_url:
                time.sleep(random.uniform(1, 2))
                response = self.session.get(current_url, timeout=15, allow_redirects=True)
                current_url = response.url
            
            # 요청 전 지연 (차단 방지)
            time.sleep(random.uniform(1, 3))
            
            # Referer 업데이트 (통합검색에서 이동한 것으로 설정)
            self.session.headers.update({'Referer': 'https://search.naver.com/'})
            
            response = self.session.get(current_url, timeout=15)
            
            if response.status_code != 200:
                print(f"[ERROR] 블로그 페이지 접속 실패: HTTP {response.status_code}")
                return None
            
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            html_text = response.text
            soup = BeautifulSoup(html_text, 'lxml')
            final_url = response.url
            source = 'main'
            
            # 차단 여부 확인
            if self._is_blocked_html(html_text):
                print("[WARN] 블로그 첫 페이지에서 차단 패턴이 감지되었지만, iframe/모바일 페이지를 추가로 확인합니다.")
            
            # iframe(mainFrame) 추적
            iframe = soup.find('iframe', id=lambda x: x and 'mainframe' in str(x).lower())
            if iframe and iframe.get('src'):
                iframe_src = iframe.get('src')
                if iframe_src.startswith('//'):
                    iframe_url = 'https:' + iframe_src.lstrip('/')
                elif iframe_src.startswith('http'):
                    iframe_url = iframe_src
                else:
                    iframe_url = urljoin('https://blog.naver.com/', iframe_src.lstrip('/'))
                
                print(f"[DEBUG] mainFrame iframe 발견, src: {iframe_src}")
                print(f"[DEBUG] iframe 요청 URL: {iframe_url}")
                
                time.sleep(random.uniform(1, 2))
                
                # Referer를 원본 블로그 URL로 설정
                referer_url = final_url if final_url else original_url
                self.session.headers.update({'Referer': referer_url})
                
                iframe_response = self.session.get(iframe_url, timeout=15)
                
                if iframe_response.status_code == 200:
                    iframe_response.raise_for_status()
                    iframe_response.encoding = 'utf-8'
                    html_text = iframe_response.text
                    soup = BeautifulSoup(html_text, 'lxml')
                    final_url = iframe_response.url
                    source = 'iframe'
                    print(f"[DEBUG] iframe 응답 수신 완료 (길이: {len(html_text)} 문자)")
                    
                    if self._is_blocked_html(html_text):
                        print("[WARN] iframe 응답에서 차단 패턴이 감지되었습니다. 모바일 페이지를 확인합니다.")
                else:
                    print(f"[ERROR] iframe 요청 실패: HTTP {iframe_response.status_code}")
            
            # 필요 시 모바일 페이지로 재시도
            html_lower = html_text.lower()
            if ('post-view' not in html_lower) and ('se-main-container' not in html_lower):
                blog_id = None
                log_no = None
                
                # 경로에서 추출
                parsed_path = urlparse(final_url).path.strip('/').split('/')
                if len(parsed_path) >= 2:
                    blog_id = parsed_path[0]
                    log_no = parsed_path[-1]
                
                # 쿼리에서 추출 (PostView.naver?blogId=...&logNo=...)
                parsed_query = parse_qs(urlparse(final_url).query)
                if 'blogId' in parsed_query:
                    blog_id = parsed_query['blogId'][0]
                if 'logNo' in parsed_query:
                    log_no = parsed_query['logNo'][0]
                
                if blog_id and log_no:
                    mobile_url = f"https://m.blog.naver.com/{blog_id}/{log_no}"
                    print(f"[DEBUG] 모바일 페이지로 재시도: {mobile_url}")
                    
                    time.sleep(random.uniform(1, 2))
                    self.session.headers.update({'Referer': f'https://blog.naver.com/{blog_id}'})
                    mobile_response = self.session.get(mobile_url, timeout=15)
                    
                    if mobile_response.status_code == 200:
                        mobile_response.raise_for_status()
                        mobile_response.encoding = 'utf-8'
                        html_text = mobile_response.text
                        soup = BeautifulSoup(html_text, 'lxml')
                        final_url = mobile_response.url
                        source = 'mobile'
                        print(f"[DEBUG] 모바일 페이지 응답 수신 완료 (길이: {len(html_text)} 문자)")
                        
                        if self._is_blocked_html(html_text):
                            print("[ERROR] 모바일 페이지에서도 차단 패턴이 감지되었습니다.")
                            return None
                    else:
                        print(f"[ERROR] 모바일 페이지 요청 실패: HTTP {mobile_response.status_code}")
                else:
                    print("[DEBUG] 모바일 페이지 재시도를 위한 blogId/logNo를 추출할 수 없습니다.")
            
            return {
                'html': html_text,
                'soup': soup,
                'final_url': final_url,
                'source': source
            }
        
        except Exception as e:
            print(f"[ERROR] 블로그 페이지 수집 실패 ({url}): {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_top_1_blog_info(self, keyword: str) -> dict:
        """
        네이버 통합검색에서 첫 번째 블로그 글의 제목과 URL을 반환합니다
        
        Args:
            keyword: 검색할 키워드
            
        Returns:
            {'title': str, 'url': str} 형태의 딕셔너리
        """
        try:
            # 네이버 통합검색 URL 생성
            params = {
                'query': keyword,
                'where': 'nexearch',
                'sm': 'top_hty',
                'fbm': '0',
                'ie': 'utf8'
            }
            
            # 요청 전 지연 (차단 방지)
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(
                self.base_url, 
                params=params, 
                timeout=15
            )
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            # HTML 소스에서 blog.naver.com이 포함된 부분 찾기
            html_text = response.text
            
            if 'blog.naver.com' not in html_text.lower():
                print("[ERROR] HTML 소스에 blog.naver.com이 없습니다.")
                return {'title': None, 'url': None}
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'lxml')
            all_links = soup.find_all('a', href=True)
            
            # 첫 번째 블로그 글 URL 찾기
            for link in all_links:
                href = link.get('href', '')
                
                # blog.naver.com 링크 찾기
                is_blog_link = 'blog.naver.com' in href.lower()
                
                if not is_blog_link:
                    continue
                
                # URL 정리
                if href.startswith('/'):
                    href = 'https://blog.naver.com' + href
                elif not href.startswith('http'):
                    continue
                
                # PostView나 하위 경로가 있는 실제 글 링크인지 확인
                from urllib.parse import urlparse
                parsed = urlparse(href)
                path_parts = parsed.path.strip('/').split('/')
                
                # 실제 글 링크인지 확인
                is_post_link = False
                if len(path_parts) > 1:  # 하위 경로가 있음
                    is_post_link = True
                elif 'postview' in href.lower() or 'post' in href.lower():
                    is_post_link = True
                
                if not is_post_link:
                    continue
                
                # 블로그 글 제목 추출
                blog_title = None
                
                # 방법 1: api_txt_lines 클래스를 가진 요소 찾기
                title_elem = link.find(['a', 'span', 'strong', 'b'], class_=lambda x: x and 'api_txt_lines' in str(x))
                if title_elem:
                    blog_title = title_elem.get_text(strip=True)
                
                # 방법 2: 부모 요소에서 찾기
                if not blog_title or len(blog_title) < 2:
                    parent = link.find_parent(['div', 'li', 'dt', 'dd'])
                    if parent:
                        title_elem = parent.find(['a', 'span', 'strong', 'b'], class_=lambda x: x and 'api_txt_lines' in str(x))
                        if title_elem:
                            blog_title = title_elem.get_text(strip=True)
                
                # 방법 3: 링크 텍스트에서 날짜 제거
                if not blog_title or len(blog_title) < 2:
                    link_text = link.get_text(strip=True)
                    date_pattern = r'\d{4}[.\-]\d{1,2}[.\-]\d{1,2}'
                    cleaned_text = re.sub(date_pattern, '', link_text).strip()
                    if cleaned_text and len(cleaned_text) > 2:
                        blog_title = cleaned_text
                
                # 방법 4: data-title, title 속성
                if not blog_title or len(blog_title) < 2:
                    for attr in ['data-title', 'title', 'aria-label']:
                        title_attr = link.get(attr)
                        if title_attr and len(str(title_attr).strip()) > 2:
                            blog_title = str(title_attr).strip()
                            break
                
                if blog_title and len(blog_title) > 2:
                    if len(blog_title) > 150:
                        blog_title = blog_title[:150]
                    return {
                        'title': blog_title,
                        'url': href
                    }
            
            print("[ERROR] 블로그 글을 찾을 수 없습니다.")
            return {'title': None, 'url': None}
            
        except Exception as e:
            print(f"오류 발생: {e}")
            return {'title': None, 'url': None}
    
    def count_se_main_container(self, url: str) -> int:
        """
        블로그 URL에 접속하여 se-main-container 클래스를 가진 요소의 개수를 반환합니다
        
        Args:
            url: 블로그 글 URL
            
        Returns:
            se-main-container 클래스를 가진 요소의 개수
        """
        try:
            page = self._fetch_blog_page(url)
            if not page:
                return 0
            
            soup = page['soup']
            html_text = page['html']
            source = page['source']
            print(f"[DEBUG] se-main-container 분석 소스: {source}")
            
            # se-main-container 클래스를 가진 모든 요소 찾기
            containers = soup.find_all(class_=lambda x: x and 'se-main-container' in str(x))
            
            count = len(containers)
            print(f"[INFO] se-main-container 클래스를 가진 요소 개수: {count}개")
            
            if count == 0 and 'se-main-container' in html_text.lower():
                print("[DEBUG] HTML 텍스트에는 'se-main-container' 문자열이 존재하지만 파싱 결과에서 찾지 못했습니다.")
            
            
            return count
            
        except Exception as e:
            print(f"[ERROR] se-main-container 개수 확인 실패 ({url}): {e}")
            return 0
    
    def count_post_view_div(self, url: str) -> int:
        """
        블로그 URL에서 글 ID를 추출하여 post-view{글ID} 형태의 div 개수를 확인합니다
        
        Args:
            url: 블로그 글 URL (예: https://blog.naver.com/username/223284686667)
            
        Returns:
            post-view{글ID} 형태의 div 요소 개수
        """
        try:
            # URL에서 글 ID 추출
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            # 글 ID는 보통 마지막 경로 부분 (예: /username/223284686667에서 223284686667)
            post_id = None
            if len(path_parts) >= 2:
                post_id = path_parts[-1]  # 마지막 부분이 글 ID
            
            if not post_id:
                print("[ERROR] URL에서 글 ID를 추출할 수 없습니다.")
                return 0
            
            print(f"[INFO] 추출한 글 ID: {post_id}")
            
            page = self._fetch_blog_page(url)
            if not page:
                return 0
            
            html_text = page['html']
            soup = page['soup']
            source = page['source']
            final_url = page['final_url']
            
            print(f"[DEBUG] post-view 분석 소스: {source}")
            print(f"[DEBUG] 최종 요청 URL: {final_url}")
            
            # 디버깅: HTML 응답에서 post-view 관련 텍스트 확인
            target_id_lower = f"post-view{post_id}".lower()
            
            # HTML 길이와 구조 확인
            print(f"[DEBUG] HTML 응답 크기: {len(html_text)} 문자")
            print(f"[DEBUG] HTML에 'post-view' 텍스트 포함 여부: {'post-view' in html_text.lower()}")
            print(f"[DEBUG] HTML에 'post-view{post_id}' 텍스트 포함 여부: {target_id_lower in html_text.lower()}")
            
            # HTML에 모든 id 속성 찾기 (디버깅용)
            import re
            all_id_pattern = re.compile(r'id\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
            all_ids_in_html = all_id_pattern.findall(html_text)
            post_view_ids_in_html = [id_val for id_val in all_ids_in_html if 'post-view' in id_val.lower()]
            
            print(f"[DEBUG] HTML에서 발견된 모든 id 개수: {len(all_ids_in_html)}개")
            if post_view_ids_in_html:
                print(f"[DEBUG] HTML에서 발견된 post-view 관련 id들: {post_view_ids_in_html[:10]}")
            else:
                print(f"[DEBUG] HTML에서 post-view 관련 id를 찾을 수 없습니다.")
                # post-view가 포함된 모든 텍스트 찾기
                post_view_lines = [line.strip() for line in html_text.split('\n') if 'post-view' in line.lower()]
                if post_view_lines:
                    print(f"[DEBUG] 'post-view'가 포함된 라인들 (최대 5개):")
                    for line in post_view_lines[:5]:
                        if len(line) > 300:
                            print(f"  ...{line[:150]}...{line[-150:]}")
                        else:
                            print(f"  {line}")
            
            if target_id_lower in html_text.lower():
                print(f"[DEBUG] HTML 응답에 '{target_id_lower}' 텍스트가 존재합니다.")
                # 해당 ID가 포함된 라인 찾기
                lines_with_id = [line.strip() for line in html_text.split('\n') if target_id_lower in line.lower() and 'post-view' in line.lower()]
                if lines_with_id:
                    print(f"[DEBUG] 해당 ID가 포함된 라인 예시 (최대 3개):")
                    for line in lines_with_id[:3]:
                        # 너무 긴 라인은 앞뒤 200자만 출력
                        if len(line) > 400:
                            print(f"  ...{line[:200]}...{line[-200:]}")
                        else:
                            print(f"  {line}")
            else:
                print(f"[DEBUG] HTML 응답에 '{target_id_lower}' 텍스트가 없습니다.")
            
            # BeautifulSoup이 파싱한 모든 id 확인
            all_parsed_ids = [elem.get('id') for elem in soup.find_all(id=True) if elem.get('id')]
            print(f"[DEBUG] BeautifulSoup이 파싱한 모든 id 개수: {len(all_parsed_ids)}개")
            parsed_post_view_ids = [id_val for id_val in all_parsed_ids if 'post-view' in str(id_val).lower()]
            if parsed_post_view_ids:
                print(f"[DEBUG] BeautifulSoup이 파싱한 post-view 관련 id들: {parsed_post_view_ids[:10]}")
            
            # 방법 1: 정확한 ID로 찾기
            target_id = f"post-view{post_id}"
            divs = soup.find_all('div', id=target_id)
            
            # 방법 2: 대소문자 무시하고 찾기
            if len(divs) == 0:
                divs = soup.find_all('div', id=lambda x: x and str(x).lower() == target_id.lower())
            
            # 방법 3: post-view로 시작하고 글 ID가 포함된 모든 div 찾기
            if len(divs) == 0:
                divs = soup.find_all('div', id=lambda x: x and 'post-view' in str(x).lower() and post_id in str(x))
            
            # 방법 4: 모든 태그에서 찾기 (div가 아닐 수도 있음)
            if len(divs) == 0:
                divs = soup.find_all(id=target_id)
            
            # 방법 5: 정규식으로 HTML에서 직접 찾기
            if len(divs) == 0:
                # HTML 텍스트에서 직접 찾기
                pattern = re.compile(rf'<[^>]+id\s*=\s*["\']post-view{re.escape(post_id)}["\'][^>]*>', re.IGNORECASE)
                matches = pattern.findall(html_text)
                if matches:
                    print(f"[DEBUG] 정규식으로 HTML에서 직접 찾은 결과: {len(matches)}개")
                    print(f"[DEBUG] 예시: {matches[0][:200]}")
            
            count = len(divs)
            print(f"[INFO] div id='{target_id}' 요소 개수: {count}개")
            
            # 디버깅: 찾은 요소들의 정보 출력
            if count > 0:
                for idx, div in enumerate(divs, 1):
                    found_id = div.get('id')
                    classes = div.get('class', [])
                    print(f"[DEBUG] {idx}번째 요소 - ID: {found_id}, 클래스: {classes}")
            else:
                # 디버깅: post-view로 시작하는 모든 id 확인
                all_post_view_ids = soup.find_all('div', id=lambda x: x and 'post-view' in str(x).lower())
                if all_post_view_ids:
                    found_ids = [div.get('id') for div in all_post_view_ids]
                    print(f"[DEBUG] post-view로 시작하는 다른 ID들 발견: {found_ids}")
                    print(f"[DEBUG] 찾고 있는 ID: {target_id}")
                
                # 디버깅: 글 ID가 포함된 모든 div id 확인
                all_divs_with_id = soup.find_all('div', id=lambda x: x and post_id in str(x))
                if all_divs_with_id:
                    found_ids_with_post_id = [div.get('id') for div in all_divs_with_id]
                    print(f"[DEBUG] 글 ID '{post_id}'가 포함된 모든 div ID: {found_ids_with_post_id}")
            
            return count
            
        except Exception as e:
            print(f"[ERROR] post-view div 개수 확인 실패 ({url}): {e}")
            import traceback
            traceback.print_exc()
            return 0
