"""
네이버 검색 결과 크롤링 모듈
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional
import re
import time
import random
import os
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
    
    def get_top_n_blog_info(self, keyword: str, n: int = 3) -> list:
        """
        네이버 통합검색에서 상위 N개 블로그 글의 제목과 URL을 반환합니다
        
        Args:
            keyword: 검색할 키워드
            n: 가져올 블로그 글 개수 (기본값: 3)
            
        Returns:
            [{'title': str, 'url': str}, ...] 형태의 리스트
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
                return []
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'lxml')
            all_links = soup.find_all('a', href=True)
            
            blog_list = []
            seen_urls = set()  # 중복 URL 방지
            
            # 상위 N개 블로그 글 URL 찾기
            for link in all_links:
                if len(blog_list) >= n:
                    break
                    
                href = link.get('href', '')
                
                # blog.naver.com 링크 찾기
                is_blog_link = 'blog.naver.com' in href.lower()
                
                if not is_blog_link:
                    continue
                
                # 광고 링크 필터링 (광고는 특정 클래스나 구조를 가짐)
                parent = link.find_parent(['div', 'li', 'article', 'section'])
                if parent:
                    # 광고 관련 클래스나 속성 확인
                    parent_classes = parent.get('class', [])
                    parent_id = parent.get('id', '')
                    parent_str = str(parent_classes) + ' ' + str(parent_id)
                    
                    # 광고 관련 키워드 확인 (네이버 광고 표시 패턴)
                    ad_keywords = ['ad', 'advertisement', 'sponsored', 'promotion', '광고', 'ad_area', 'ad_bx', 'ad_wrap']
                    is_ad = any(keyword.lower() in parent_str.lower() for keyword in ad_keywords)
                    
                    if is_ad:
                        continue  # 광고는 건너뛰기
                
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
                
                # 중복 URL 체크
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                
                # 블로그 글 제목 추출
                blog_title = None
                
                # 방법 1: sds-comps-text-type-headline1 클래스를 가진 span에서 제목 찾기 (우선순위 1)
                parent = link.find_parent(['div', 'li', 'dt', 'dd', 'article', 'section'])
                if parent:
                    # headline1 클래스를 가진 span 찾기 (제목용)
                    headline_span = parent.find('span', class_=lambda x: x and 'sds-comps-text-type-headline1' in str(x))
                    if headline_span:
                        # 전체 텍스트 가져오기 (mark 태그 포함, 띄어쓰기 보존)
                        blog_title = headline_span.get_text(separator=' ', strip=True)
                        blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                
                # 방법 2: sds-comps-text-type-headline1이 없으면 다른 sds-comps-text에서 찾기 (body2 제외)
                if not blog_title or len(blog_title) < 2:
                    if parent:
                        sds_spans = parent.find_all('span', class_=lambda x: x and 'sds-comps-text' in str(x))
                        for sds_span in sds_spans:
                            class_str = str(sds_span.get('class', []))
                            if 'sds-comps-text-type-body2' in class_str:
                                continue
                            span_text = sds_span.get_text(separator=' ', strip=True)
                            span_text = re.sub(r'\s+', ' ', span_text).strip()
                            if span_text and 'blog.naver.com' not in span_text and '›' not in span_text and len(span_text) > 2:
                                blog_title = span_text
                                break
                
                # 방법 3: se-fs- se-ff-nanummaruburi 클래스를 가진 span에서 찾기
                if not blog_title or len(blog_title) < 2:
                    if parent:
                        se_span = parent.find('span', class_=lambda x: x and 'se-fs-' in str(x) and 'se-ff-nanummaruburi' in str(x))
                        if se_span:
                            blog_title = se_span.get_text(separator=' ', strip=True)
                            blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                
                # 방법 4: api_txt_lines 클래스를 가진 요소 찾기
                if not blog_title or len(blog_title) < 2:
                    title_elem = link.find(['a', 'span', 'strong', 'b'], class_=lambda x: x and 'api_txt_lines' in str(x))
                    if title_elem:
                        blog_title = title_elem.get_text(separator=' ', strip=True)
                        blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                
                # 방법 5: 부모 요소에서 api_txt_lines 찾기
                if not blog_title or len(blog_title) < 2:
                    if not parent:
                        parent = link.find_parent(['div', 'li', 'dt', 'dd'])
                    if parent:
                        title_elem = parent.find(['a', 'span', 'strong', 'b'], class_=lambda x: x and 'api_txt_lines' in str(x))
                        if title_elem:
                            blog_title = title_elem.get_text(separator=' ', strip=True)
                            blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                
                # 방법 6: 링크 텍스트에서 날짜 제거
                if not blog_title or len(blog_title) < 2:
                    link_text = link.get_text(strip=True)
                    if 'blog.naver.com' not in link_text and '›' not in link_text:
                        date_pattern = r'\d{4}[.\-]\d{1,2}[.\-]\d{1,2}'
                        cleaned_text = re.sub(date_pattern, '', link_text).strip()
                        if cleaned_text and len(cleaned_text) > 2:
                            blog_title = cleaned_text
                
                # 방법 7: data-title, title 속성
                if not blog_title or len(blog_title) < 2:
                    for attr in ['data-title', 'title', 'aria-label']:
                        title_attr = link.get(attr)
                        if title_attr and len(str(title_attr).strip()) > 2:
                            blog_title = str(title_attr).strip()
                            break
                
                # 방법 8: 블로그 페이지에서 직접 제목 추출 시도
                if not blog_title or len(blog_title) < 2:
                    try:
                        page = self._fetch_blog_page(href)
                        if page:
                            page_soup = page['soup']
                            se_span = page_soup.find('span', class_=lambda x: x and 'se-fs-' in str(x) and 'se-ff-nanummaruburi' in str(x))
                            if se_span:
                                blog_title = se_span.get_text(separator=' ', strip=True)
                                blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                            
                            if not blog_title or len(blog_title) < 2:
                                sds_span = page_soup.find('span', class_=lambda x: x and 'sds-comps-text-type-headline1' in str(x))
                                if sds_span:
                                    blog_title = sds_span.get_text(separator=' ', strip=True)
                                    blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                                else:
                                    sds_span = page_soup.find('span', class_=lambda x: x and 'sds-comps-text' in str(x))
                                    if sds_span:
                                        mark_elem = sds_span.find('mark')
                                        if mark_elem:
                                            blog_title = sds_span.get_text(separator=' ', strip=True)
                                            blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                    except Exception as e:
                        print(f"[DEBUG] 블로그 페이지에서 제목 추출 시도 중 오류: {e}")
                
                if blog_title and len(blog_title) > 2:
                    if len(blog_title) > 150:
                        blog_title = blog_title[:150]
                    blog_list.append({
                        'title': blog_title,
                        'url': href
                    })
            
            return blog_list
            
        except Exception as e:
            print(f"오류 발생: {e}")
            return []
    
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
                
                # 방법 1: sds-comps-text-type-headline1 클래스를 가진 span에서 제목 찾기 (우선순위 1)
                parent = link.find_parent(['div', 'li', 'dt', 'dd', 'article', 'section'])
                if parent:
                    # headline1 클래스를 가진 span 찾기 (제목용)
                    headline_span = parent.find('span', class_=lambda x: x and 'sds-comps-text-type-headline1' in str(x))
                    if headline_span:
                        # 전체 텍스트 가져오기 (mark 태그 포함, 띄어쓰기 보존)
                        # separator=' '를 사용하여 태그 사이 공백 보존
                        blog_title = headline_span.get_text(separator=' ', strip=True)
                        # 연속된 공백 정리
                        blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                
                # 방법 2: sds-comps-text-type-headline1이 없으면 다른 sds-comps-text에서 찾기 (body2 제외)
                if not blog_title or len(blog_title) < 2:
                    if parent:
                        # body2는 프로필 정보이므로 제외하고, headline1이나 다른 타입 찾기
                        sds_spans = parent.find_all('span', class_=lambda x: x and 'sds-comps-text' in str(x))
                        for sds_span in sds_spans:
                            class_str = str(sds_span.get('class', []))
                            # body2는 제외 (프로필 정보)
                            if 'sds-comps-text-type-body2' in class_str:
                                continue
                            # headline1이나 다른 타입에서 찾기 (mark 태그 포함 전체 텍스트)
                            # separator=' '를 사용하여 태그 사이 공백 보존
                            span_text = sds_span.get_text(separator=' ', strip=True)
                            # 연속된 공백 정리
                            span_text = re.sub(r'\s+', ' ', span_text).strip()
                            # blog.naver.com이나 프로필 정보가 포함된 경우 제외
                            if span_text and 'blog.naver.com' not in span_text and '›' not in span_text and len(span_text) > 2:
                                blog_title = span_text
                                break
                
                # 방법 3: se-fs- se-ff-nanummaruburi 클래스를 가진 span에서 찾기
                if not blog_title or len(blog_title) < 2:
                    if parent:
                        se_span = parent.find('span', class_=lambda x: x and 'se-fs-' in str(x) and 'se-ff-nanummaruburi' in str(x))
                        if se_span:
                            blog_title = se_span.get_text(separator=' ', strip=True)
                            blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                
                # 방법 4: api_txt_lines 클래스를 가진 요소 찾기
                if not blog_title or len(blog_title) < 2:
                    title_elem = link.find(['a', 'span', 'strong', 'b'], class_=lambda x: x and 'api_txt_lines' in str(x))
                    if title_elem:
                        blog_title = title_elem.get_text(separator=' ', strip=True)
                        blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                
                # 방법 5: 부모 요소에서 api_txt_lines 찾기
                if not blog_title or len(blog_title) < 2:
                    if not parent:
                        parent = link.find_parent(['div', 'li', 'dt', 'dd'])
                    if parent:
                        title_elem = parent.find(['a', 'span', 'strong', 'b'], class_=lambda x: x and 'api_txt_lines' in str(x))
                        if title_elem:
                            blog_title = title_elem.get_text(separator=' ', strip=True)
                            blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                
                # 방법 6: 링크 텍스트에서 날짜 제거 (body2 같은 프로필 정보 제외)
                if not blog_title or len(blog_title) < 2:
                    link_text = link.get_text(strip=True)
                    # blog.naver.com이나 프로필 정보 패턴 제거
                    if 'blog.naver.com' in link_text or '›' in link_text:
                        # 프로필 정보가 포함된 경우 건너뛰기
                        pass
                    else:
                        date_pattern = r'\d{4}[.\-]\d{1,2}[.\-]\d{1,2}'
                        cleaned_text = re.sub(date_pattern, '', link_text).strip()
                        if cleaned_text and len(cleaned_text) > 2:
                            blog_title = cleaned_text
                
                # 방법 7: data-title, title 속성
                if not blog_title or len(blog_title) < 2:
                    for attr in ['data-title', 'title', 'aria-label']:
                        title_attr = link.get(attr)
                        if title_attr and len(str(title_attr).strip()) > 2:
                            blog_title = str(title_attr).strip()
                            break
                
                # 방법 8: 블로그 페이지에서 직접 제목 추출 시도
                if not blog_title or len(blog_title) < 2:
                    try:
                        page = self._fetch_blog_page(href)
                        if page:
                            page_soup = page['soup']
                            # se-fs- se-ff-nanummaruburi 클래스를 가진 span 찾기
                            se_span = page_soup.find('span', class_=lambda x: x and 'se-fs-' in str(x) and 'se-ff-nanummaruburi' in str(x))
                            if se_span:
                                blog_title = se_span.get_text(separator=' ', strip=True)
                                blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                            
                            # sds-comps-text 클래스를 가진 span에서 전체 텍스트 추출 (mark 태그 포함)
                            if not blog_title or len(blog_title) < 2:
                                sds_span = page_soup.find('span', class_=lambda x: x and 'sds-comps-text-type-headline1' in str(x))
                                if sds_span:
                                    # 전체 텍스트 추출 (mark 태그 포함, 띄어쓰기 보존)
                                    blog_title = sds_span.get_text(separator=' ', strip=True)
                                    blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                                else:
                                    # sds-comps-text 클래스를 가진 span 하위의 mark 태그만 찾기 (fallback)
                                    sds_span = page_soup.find('span', class_=lambda x: x and 'sds-comps-text' in str(x))
                                    if sds_span:
                                        mark_elem = sds_span.find('mark')
                                        if mark_elem:
                                            # mark 태그만이 아니라 전체 span의 텍스트를 가져오기
                                            blog_title = sds_span.get_text(separator=' ', strip=True)
                                            blog_title = re.sub(r'\s+', ' ', blog_title).strip()
                    except Exception as e:
                        print(f"[DEBUG] 블로그 페이지에서 제목 추출 시도 중 오류: {e}")
                
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
    
    def _extract_text_with_media_markers(self, element) -> str:
        """
        요소에서 텍스트를 추출하면서 이미지와 링크 태그 위치에 마커를 삽입합니다.
        se-module-image 내의 링크는 [링크 삽입]을 넣지 않고 [이미지 삽입]만 넣습니다.
        se-module-oglink 내의 링크는 [링크 삽입]을 넣습니다.
        se-module-sticker 내의 이미지는 [이모티콘 삽입]을 넣습니다.
        각 마커는 인덱스 번호가 붙습니다 (예: [이미지 삽입1], [링크 삽입2]).
        
        Args:
            element: BeautifulSoup 요소
            
        Returns:
            이미지/링크 마커가 포함된 텍스트
        """
        if element is None:
            return ''
        
        try:
            # 원본 HTML 문자열 가져오기
            element_html = str(element)
            
            # BeautifulSoup으로 파싱하여 모듈별로 처리
            soup = BeautifulSoup(element_html, 'lxml')
            
            # 마커 인덱스 카운터 초기화
            image_counter = 0
            link_counter = 0
            emoji_counter = 0
            
            # se-module-sticker 모듈 처리: 이미지를 [이모티콘 삽입]으로, 링크는 마커 없이 제거
            sticker_modules = soup.find_all('div', class_=lambda x: x and 'se-module-sticker' in str(x))
            for sticker_module in sticker_modules:
                # 이미지 태그를 [이모티콘 삽입N]으로 교체
                for img in sticker_module.find_all('img'):
                    emoji_counter += 1
                    img.replace_with(f'[이모티콘 삽입{emoji_counter}]')
                # 링크 태그는 제거 (링크 삽입 마커 없이)
                for link in sticker_module.find_all('a'):
                    # 링크 내부의 텍스트가 있으면 유지, 없으면 제거
                    link_text = link.get_text(strip=True)
                    if link_text:
                        link.replace_with(link_text)
                    else:
                        link.decompose()
            
            # se-module-image 모듈 처리: 이미지만 [이미지 삽입]으로, 링크는 마커 없이 제거
            image_modules = soup.find_all('div', class_=lambda x: x and 'se-module-image' in str(x))
            for img_module in image_modules:
                # 이미지 태그를 [이미지 삽입N]으로 교체
                for img in img_module.find_all('img'):
                    image_counter += 1
                    img.replace_with(f'[이미지 삽입{image_counter}]')
                # 링크 태그는 제거 (링크 삽입 마커 없이)
                for link in img_module.find_all('a'):
                    # 링크 내부의 텍스트가 있으면 유지, 없으면 제거
                    link_text = link.get_text(strip=True)
                    if link_text:
                        link.replace_with(link_text)
                    else:
                        link.decompose()
            
            # se-module-oglink 모듈 처리: 전체 모듈을 [링크 삽입N] 하나로 교체 (텍스트는 제외)
            oglink_modules = soup.find_all('div', class_=lambda x: x and 'se-module-oglink' in str(x))
            for oglink_module in oglink_modules:
                # 전체 oglink 모듈을 [링크 삽입N] 하나로 교체 (내부 텍스트는 모두 제거)
                link_counter += 1
                oglink_module.replace_with(f'[링크 삽입{link_counter}]')
            
            # 나머지 이미지 태그 처리 (se-module-image, se-module-sticker가 아닌 곳의 이미지)
            for img in soup.find_all('img'):
                # 이미 처리된 이미지는 건너뛰기
                parent_sticker_module = img.find_parent('div', class_=lambda x: x and 'se-module-sticker' in str(x))
                parent_img_module = img.find_parent('div', class_=lambda x: x and 'se-module-image' in str(x))
                parent_oglink_module = img.find_parent('div', class_=lambda x: x and 'se-module-oglink' in str(x))
                
                if not parent_sticker_module and not parent_img_module and not parent_oglink_module:
                    image_counter += 1
                    img.replace_with(f'[이미지 삽입{image_counter}]')
            
            # 나머지 링크 태그 처리 (se-module-image, se-module-oglink, se-module-sticker가 아닌 곳의 링크)
            for link in soup.find_all('a'):
                # 이미 처리된 링크는 건너뛰기
                parent_sticker_module = link.find_parent('div', class_=lambda x: x and 'se-module-sticker' in str(x))
                parent_img_module = link.find_parent('div', class_=lambda x: x and 'se-module-image' in str(x))
                parent_oglink_module = link.find_parent('div', class_=lambda x: x and 'se-module-oglink' in str(x))
                
                if not parent_sticker_module and not parent_img_module and not parent_oglink_module:
                    link_text = link.get_text(strip=True)
                    link_counter += 1
                    if link_text:
                        link.replace_with(f"{link_text}\n[링크 삽입{link_counter}]")
                    else:
                        link.replace_with(f'[링크 삽입{link_counter}]')
            
            # 최종 텍스트 추출
            if soup.body:
                result_text = soup.body.get_text(separator='\n', strip=True)
            elif soup.contents:
                result_text = soup.contents[0].get_text(separator='\n', strip=True) if len(soup.contents) > 0 else soup.get_text(separator='\n', strip=True)
            else:
                result_text = soup.get_text(separator='\n', strip=True)
            
            # 결과가 비어있으면 원본 요소에서 직접 추출
            if not result_text or len(result_text.strip()) == 0:
                result_text = element.get_text(separator='\n', strip=True)
            
            return result_text
            
        except Exception as e:
            # 오류 발생 시 원본 텍스트 반환
            print(f"[WARN] _extract_text_with_media_markers 오류: {e}")
            try:
                return element.get_text(separator='\n', strip=True)
            except:
                return ''
    
    def extract_blog_body_text(self, url: str) -> Optional[str]:
        """
        블로그 글의 본문 텍스트를 추출합니다.
        이미지 태그가 있으면 [이미지 삽입], 링크 태그가 있으면 [링크 삽입]을 삽입합니다.
        
        Args:
            url: 블로그 글 URL
            
        Returns:
            추출된 본문 텍스트 (없으면 None)
        """
        try:
            page = self._fetch_blog_page(url)
            if not page:
                print("[ERROR] 블로그 페이지를 가져올 수 없습니다.")
                return None
            
            soup = page['soup']
            html_text = page['html']  # 원본 HTML 텍스트도 가져오기
            body_text_parts = []
            
            # 방법 1: se-main-container 클래스를 가진 요소에서 텍스트 추출
            containers = soup.find_all(class_=lambda x: x and 'se-main-container' in str(x))
            if containers:
                print(f"[수집] 방법 1: se-main-container 클래스 요소 발견 ({len(containers)}개)")
                for idx, container in enumerate(containers, 1):
                    # 요소 정보 수집
                    tag_name = container.name
                    element_id = container.get('id', '없음')
                    element_classes = container.get('class', [])
                    class_str = ' '.join(element_classes) if element_classes else '없음'
                    
                    # 전체 컨테이너를 한 번에 처리하여 이미지와 링크를 놓치지 않도록 함
                    text = self._extract_text_with_media_markers(container)
                    if text and len(text.strip()) > 0:
                        print(f"[수집] ✓ 방법 1 성공 - 요소#{idx}: <{tag_name}> 태그, ID='{element_id}', 클래스='{class_str}', 텍스트 길이={len(text)}자")
                        body_text_parts.append(text)
                        # 첫 번째 성공한 요소만 사용 (중복 방지)
                        break
            
            # 방법 2: post-view{글ID} div에서 텍스트 추출
            if not body_text_parts:
                post_view_divs = soup.find_all('div', id=lambda x: x and 'post-view' in str(x).lower())
                if post_view_divs:
                    print(f"[수집] 방법 2: post-view div 요소 발견 ({len(post_view_divs)}개)")
                    for idx, div in enumerate(post_view_divs, 1):
                        element_id = div.get('id', '없음')
                        element_classes = div.get('class', [])
                        class_str = ' '.join(element_classes) if element_classes else '없음'
                        
                        text = self._extract_text_with_media_markers(div)
                        if text and len(text.strip()) > 0:
                            print(f"[수집] ✓ 방법 2 성공 - 요소#{idx}: <div> 태그, ID='{element_id}', 클래스='{class_str}', 텍스트 길이={len(text)}자")
                            body_text_parts.append(text)
                            # 첫 번째 성공한 요소만 사용 (중복 방지)
                            break
            
            # 방법 3: 본문 영역으로 보이는 div 찾기 (class나 id 패턴) - fallback
            if not body_text_parts:
                body_selectors = [
                    ('id에 post 포함', {'id': lambda x: x and 'post' in str(x).lower()}),
                    ('class에 post 포함', {'class': lambda x: x and 'post' in str(x).lower()}),
                    ('class에 content 포함', {'class': lambda x: x and 'content' in str(x).lower()}),
                    ('class에 article 포함', {'class': lambda x: x and 'article' in str(x).lower()}),
                ]
                
                for selector_name, selector in body_selectors:
                    elements = soup.find_all('div', **selector)
                    if elements:
                        print(f"[수집] 방법 3: {selector_name} 요소 발견 ({len(elements)}개)")
                        for idx, elem in enumerate(elements, 1):
                            element_id = elem.get('id', '없음')
                            element_classes = elem.get('class', [])
                            class_str = ' '.join(element_classes) if element_classes else '없음'
                            
                            text = self._extract_text_with_media_markers(elem)
                            if text and len(text.strip()) > 20:  # 최소 길이 체크
                                print(f"[수집] ✓ 방법 3 성공 - {selector_name}, 요소#{idx}: <div> 태그, ID='{element_id}', 클래스='{class_str}', 텍스트 길이={len(text)}자")
                                body_text_parts.append(text)
                                break
                        if body_text_parts:
                            break
            
            # 방법 4: 전체 body에서 스크립트, 스타일, nav 등 제거하고 본문 추출
            if not body_text_parts:
                print(f"[수집] 방법 4: body 태그에서 본문 추출 시도")
                # 스크립트, 스타일, 메타 태그 등 제거
                for script in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    script.decompose()
                
                body = soup.find('body')
                if body:
                    body_id = body.get('id', '없음')
                    body_classes = body.get('class', [])
                    class_str = ' '.join(body_classes) if body_classes else '없음'
                    
                    text = self._extract_text_with_media_markers(body)
                    # 너무 짧은 라인 제거
                    lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 5]
                    if lines:
                        final_text = '\n'.join(lines)
                        print(f"[수집] ✓ 방법 4 성공 - <body> 태그, ID='{body_id}', 클래스='{class_str}', 텍스트 길이={len(final_text)}자")
                        body_text_parts.append(final_text)
                    else:
                        print(f"[수집] ✗ 방법 4 실패 - <body> 태그에서 유효한 텍스트 없음")
                else:
                    print(f"[수집] ✗ 방법 4 실패 - body 태그를 찾을 수 없음")
            
            if body_text_parts:
                print(f"[수집] 최종: {len(body_text_parts)}개의 본문 파트 수집 완료, 중복 제거 및 정리 중...")
                # 중복 제거: 줄 단위로 중복 제거
                all_lines = []
                seen_lines = set()
                
                # 마커 패턴 정의 (인덱스 포함)
                marker_pattern = re.compile(r'^\[(이미지 삽입|링크 삽입|이모티콘 삽입)\d+\]$')
                
                for part in body_text_parts:
                    lines = part.split('\n')
                    for line in lines:
                        line_stripped = line.strip()
                        if line_stripped:
                            # [이미지 삽입N], [링크 삽입N], [이모티콘 삽입N] 마커는 중복 제거에서 제외
                            if marker_pattern.match(line_stripped):
                                all_lines.append(line_stripped)
                            else:
                                # 정규화하여 비교 (공백 정리, 소문자 변환)
                                normalized = re.sub(r'\s+', ' ', line_stripped.lower())
                                if normalized and normalized not in seen_lines:
                                    all_lines.append(line)
                                    seen_lines.add(normalized)
                        elif all_lines and all_lines[-1].strip():  # 빈 줄은 연속되지 않도록
                            all_lines.append('')
                
                # 최종 텍스트 생성
                final_text = '\n'.join(all_lines)
                # 연속된 빈 줄 정리 (3개 이상 -> 2개로)
                final_text = re.sub(r'\n{3,}', '\n\n', final_text)
                final_length = len(final_text.strip())
                print(f"[수집] ✓ 최종 본문 텍스트 생성 완료: {final_length}자")
                return final_text.strip()
            else:
                print("[수집] ✗ 모든 방법 실패: 본문 텍스트를 찾을 수 없습니다.")
                return None
                
        except Exception as e:
            print(f"[ERROR] 본문 텍스트 추출 실패 ({url}): {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_blog_to_txt(self, url: str, output_path: str = None, title: str = None, prefix: str = None, output_dir: str = None) -> Optional[str]:
        """
        블로그 글의 본문 텍스트를 txt 파일로 저장합니다.
        
        Args:
            url: 블로그 글 URL
            output_path: 저장할 파일 경로 (None이면 자동 생성)
            title: 파일 제목에 포함할 제목 (선택사항)
            prefix: 파일명 접두사 (사용 안 함, 하위 호환성 유지)
            output_dir: 저장할 디렉토리 경로 (None이면 현재 디렉토리)
            
        Returns:
            저장된 파일 경로 (실패하면 None)
        """
        try:
            # 본문 텍스트 추출
            body_text = self.extract_blog_body_text(url)
            if not body_text:
                print("[ERROR] 본문 텍스트를 추출할 수 없습니다.")
                return None
            
            # 출력 경로 생성
            if not output_path:
                # URL에서 파일명 생성
                parsed = urlparse(url)
                path_parts = [p for p in parsed.path.strip('/').split('/') if p]
                
                if path_parts:
                    base_filename = f"blog_{path_parts[-1]}.txt"
                else:
                    # 쿼리 파라미터에서 추출
                    query_params = parse_qs(parsed.query)
                    if 'logNo' in query_params:
                        base_filename = f"blog_{query_params['logNo'][0]}.txt"
                    else:
                        base_filename = f"blog_{int(time.time())}.txt"
                
                # output_dir이 지정된 경우 해당 디렉토리에 저장
                if output_dir:
                    output_path = os.path.join(output_dir, base_filename)
                else:
                    # 접두사 추가 (하위 호환성)
                    if prefix:
                        output_path = f"{prefix}_{base_filename}"
                    else:
                        output_path = base_filename
            
            # 디렉토리가 없으면 생성
            final_output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
            if final_output_dir and not os.path.exists(final_output_dir):
                os.makedirs(final_output_dir, exist_ok=True)
            
            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                # 제목이 제공되면 헤더에 포함
                if title:
                    f.write(f"제목: {title}\n")
                    f.write(f"URL: {url}\n")
                    f.write("=" * 80 + "\n\n")
                
                f.write(body_text)
            
            print(f"[INFO] 본문 텍스트가 저장되었습니다: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[ERROR] txt 파일 저장 실패 ({url}): {e}")
            import traceback
            traceback.print_exc()
            return None

