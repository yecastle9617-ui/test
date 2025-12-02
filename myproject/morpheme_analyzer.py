"""
형태소 분석을 통한 키워드 빈도 및 순위 분석 모듈
블로그 글에서 키워드가 몇 개씩 나오는지 개수와 순위를 분석합니다.
"""

from typing import List, Dict, Tuple, Optional
import re
import os
from collections import Counter

# rich import 시도 (예쁜 출력용)
RICH_AVAILABLE = False
try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# pandas import 시도 (엑셀 저장용)
PANDAS_AVAILABLE = False
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("[WARN] pandas가 설치되지 않았습니다. 엑셀 저장 기능을 사용할 수 없습니다.")
    print("[INFO] pip install pandas openpyxl 로 설치하세요.")

# Java 경로 자동 찾기 (JAVA_HOME이 설정되지 않은 경우)
def _find_java_home():
    """Java 설치 경로를 자동으로 찾습니다"""
    import os
    import subprocess
    
    # JAVA_HOME이 이미 설정되어 있으면 사용
    if os.environ.get('JAVA_HOME'):
        return os.environ.get('JAVA_HOME')
    
    # Windows에서 일반적인 Java 설치 경로 확인
    possible_paths = [
        r'D:\jdk21.0.6+7',  # 사용자 지정 경로
        r'C:\Program Files\Eclipse Adoptium\jdk-21',
        r'C:\Program Files\Eclipse Adoptium\jdk-17',
        r'C:\Program Files\Java\jdk-21',
        r'C:\Program Files\Java\jdk-17',
        r'C:\Program Files\OpenJDK\openjdk-21',
        r'C:\Program Files\OpenJDK\openjdk-17',
    ]
    
    # java.exe를 찾아서 상위 디렉토리 확인
    try:
        result = subprocess.run(['where', 'java'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            java_path = result.stdout.strip().split('\n')[0]
            # java.exe의 상위 디렉토리들 확인
            java_dir = os.path.dirname(java_path)  # bin 디렉토리
            java_home = os.path.dirname(java_dir)  # JDK 루트
            if os.path.exists(java_home):
                return java_home
    except:
        pass
    
    # 가능한 경로들 확인
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

# konlpy import 전에 JAVA_HOME 설정 시도
import os
if not os.environ.get('JAVA_HOME'):
    java_home = _find_java_home()
    if java_home:
        os.environ['JAVA_HOME'] = java_home
        print(f"[INFO] JAVA_HOME을 자동으로 설정했습니다: {java_home}")

# konlpy import 시도
KONLPY_AVAILABLE = False
Okt = None
Kkma = None
Komoran = None

try:
    from konlpy.tag import Okt, Kkma, Komoran
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    print("[WARN] konlpy가 설치되지 않았습니다. 기본 키워드 분석 방법을 사용합니다.")
    print("[INFO] pip install konlpy 로 설치하거나, 간단한 분석 방법을 사용합니다.")
except Exception as e:
    error_msg = str(e).lower()
    if any(keyword in error_msg for keyword in ['vpn', 'network', 'connection', 'timeout', 'java', 'jvm', 'jpype']):
        print(f"[WARN] konlpy import 중 네트워크/Java 에러 발생: {e}")
        print("[INFO] Java 기반 분석기는 Java 설치 및 JAVA_HOME 환경 변수 설정이 필요합니다.")
        print("[INFO] 간단한 키워드 분석 방법을 사용합니다.")
    else:
        print(f"[WARN] konlpy import 실패: {e}")
        print("[INFO] 간단한 키워드 분석 방법을 사용합니다.")
    KONLPY_AVAILABLE = False


class MorphemeAnalyzer:
    """형태소 분석을 통해 키워드 빈도와 순위를 분석하는 클래스"""
    
    def __init__(self, use_konlpy: bool = True):
        """
        형태소 분석기 초기화
        
        Args:
            use_konlpy: konlpy 라이브러리 사용 여부 (기본값: True)
        """
        self.use_konlpy = use_konlpy and KONLPY_AVAILABLE
        self.analyzer = None
        
        if self.use_konlpy:
            analyzer_initialized = False
            
            # Okt 시도 (konlpy는 Java 기반이므로 Java 설치 필요)
            if not analyzer_initialized:
                try:
                    self.analyzer = Okt()
                    print("[INFO] Okt 형태소 분석기를 사용합니다. (Java 기반)")
                    analyzer_initialized = True
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ['vpn', 'network', 'connection', 'timeout', 'java', 'jvm']):
                        print(f"[WARN] Okt 초기화 중 Java/JVM 에러 발생: {e}")
                        print("[INFO] Java가 설치되지 않았거나 JAVA_HOME 환경 변수가 설정되지 않았습니다.")
                        print("[INFO] Java 설치 후 간단한 키워드 분석 방법을 사용합니다.")
                        self.use_konlpy = False
                        analyzer_initialized = False
                    else:
                        print(f"[WARN] Okt 초기화 실패: {e}")
            
            # Kkma 시도 (Okt 실패 시, Java 필요)
            if not analyzer_initialized and Kkma is not None:
                try:
                    self.analyzer = Kkma()
                    print("[INFO] Kkma 형태소 분석기를 사용합니다. (Java 기반)")
                    analyzer_initialized = True
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ['vpn', 'network', 'connection', 'timeout', 'java', 'jvm', 'jpype']):
                        print(f"[WARN] Kkma 초기화 중 Java/JVM 에러 발생: {e}")
                        print("[INFO] Java 기반 분석기는 Java 설치가 필요합니다. Okt(순수 Python) 또는 간단한 방법을 사용합니다.")
                        self.use_konlpy = False
                        analyzer_initialized = False
                    else:
                        print(f"[WARN] Kkma 초기화 실패: {e}")
            
            # Komoran 시도 (Kkma 실패 시, Java 필요)
            if not analyzer_initialized and Komoran is not None:
                try:
                    self.analyzer = Komoran()
                    print("[INFO] Komoran 형태소 분석기를 사용합니다. (Java 기반)")
                    analyzer_initialized = True
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ['vpn', 'network', 'connection', 'timeout', 'java', 'jvm', 'jpype']):
                        print(f"[WARN] Komoran 초기화 중 Java/JVM 에러 발생: {e}")
                        print("[INFO] Java 기반 분석기는 Java 설치가 필요합니다. Okt(순수 Python) 또는 간단한 방법을 사용합니다.")
                        self.use_konlpy = False
                    else:
                        print(f"[WARN] 모든 형태소 분석기 초기화 실패: {e}")
                        print("[INFO] 간단한 키워드 분석 방법을 사용합니다.")
                        self.use_konlpy = False
        
        # 불용어 리스트 (한국어) - 기본 조사와 의미 없는 단어만 포함
        # 조사가 붙은 형태는 정규식 패턴으로 자동 처리하므로 여기서는 기본 조사만 포함
        self.stopwords = {
            # 기본 조사 (단독으로 사용되는 경우)
            '이', '가', '을', '를', '에', '의', '와', '과', '은', '는',
            '도', '로', '으로', '에서', '에게', '께', '한테', '처럼',
            '만', '까지', '부터', '보다', '같이', '하고',
            '만큼', '대로', '마저', '조차',
            
            # 대명사/지시어
            '그', '이것', '저것', '그것', '이런', '저런', '그런',
            '이', '저', '그', '어떤', '무엇', '누구', '어디',
            
            # 일반 명사 (의미 없는 단어)
            '것', '수', '때', '등', '및', '또', '또한', '그리고',
            '경우', '때문', '위해', '통해', '대해', '관련',
            
            # 접속어/부사
            '하지만', '그러나', '따라서', '그래서', '그런데',
            '그래도', '그리고', '또한', '그래서', '따라서',
            '그런데', '그러면', '그렇다면', '그러므로',
            
            # 동사 어간/어미 (기본 형태만)
            '있', '없', '되', '하',
            '있다', '없다', '된다', '하다', '이다', '아니다',
            
            # 기타 불필요한 단어
            '등', '및', '또', '또한', '그리고', '그러나',
            '때문', '위해', '통해', '대해', '관련', '경우',
            '수', '때', '것',
        }
        
        # 어미 패턴 (정규식으로 필터링할 패턴) - 범용적으로 적용
        self.ending_patterns = [
            # 종결 어미
            r'습니다$', r'합니다$', r'됩니다$', r'입니다$', r'합니다$',
            # 연결 어미
            r'해야$', r'해야$', r'해야$',
            r'할$', r'한$', r'하는$', r'되는$', r'있는$', r'없는$',
            r'해$', r'되$', r'있$', r'없$',
            # 동사/형용사 어미 패턴
            r'[하되있없]다$',  # ~하다, ~되다, ~있다, ~없다
            r'[하되있없]는$',  # ~하는, ~되는, ~있는, ~없는
            r'[하되있없]한$',  # ~한
            r'[하되있없]할$',  # ~할
            r'[하되있없]해$',  # ~해
        ]
        
        # 조사 패턴 (정규식으로 필터링할 패턴) - 범용적으로 적용
        # 모든 조사가 단어 끝에 붙는 패턴을 감지
        self.josa_patterns = [
            # 주격 조사
            r'이$', r'가$', r'은$', r'는$',
            # 목적격 조사
            r'을$', r'를$',
            # 부사격 조사
            r'에$', r'에서$', r'에게$', r'께$', r'한테$',
            # 관형격 조사
            r'의$',
            # 보조사
            r'도$', r'만$', r'까지$', r'부터$', r'보다$', r'처럼$', r'같이$',
            # 부사격 조사 (추가)
            r'로$', r'으로$', r'하고$',
        ]
    
    def analyze_keywords(self, text: str, min_length: int = 2, min_count: int = 1) -> List[Tuple[str, int, int]]:
        """
        텍스트에서 키워드를 추출하고 빈도와 순위를 계산합니다.
        
        Args:
            text: 분석할 텍스트
            min_length: 키워드 최소 길이 (기본값: 2)
            min_count: 최소 출현 횟수 (기본값: 1, 이 횟수 이상인 키워드만 반환)
            
        Returns:
            (키워드, 빈도, 순위) 튜플 리스트 (빈도순 정렬)
        """
        if not text or len(text.strip()) == 0:
            return []
        
        try:
            if self.use_konlpy and self.analyzer:
                keywords = self._extract_keywords_with_konlpy(text, min_length)
            else:
                keywords = self._extract_keywords_simple(text, min_length)
            
            # 빈도 계산
            keyword_counter = Counter(keywords)
            
            # 최소 출현 횟수 필터링
            filtered_keywords = {
                word: count for word, count in keyword_counter.items()
                if count >= min_count
            }
            
            # 빈도순 정렬 및 순위 부여
            sorted_keywords = sorted(
                filtered_keywords.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # 순위와 함께 반환
            result = []
            for rank, (keyword, count) in enumerate(sorted_keywords, start=1):
                result.append((keyword, count, rank))
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 키워드 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_keyword_ranking(self, text: str, top_n: Optional[int] = None, min_length: int = 2, min_count: int = 1) -> Dict[str, Dict[str, int]]:
        """
        키워드 빈도와 순위를 딕셔너리 형태로 반환합니다.
        
        Args:
            text: 분석할 텍스트
            top_n: 상위 N개만 반환 (None이면 전체 반환)
            min_length: 키워드 최소 길이 (기본값: 2)
            min_count: 최소 출현 횟수 (기본값: 1)
            
        Returns:
            {키워드: {'count': 빈도, 'rank': 순위}} 형태의 딕셔너리
        """
        results = self.analyze_keywords(text, min_length=min_length, min_count=min_count)
        
        if top_n:
            results = results[:top_n]
        
        return {
            keyword: {'count': count, 'rank': rank}
            for keyword, count, rank in results
        }
    
    def print_keyword_statistics(self, text: str, top_n: Optional[int] = None, min_length: int = 2, min_count: int = 1):
        """
        키워드 통계를 출력합니다.
        
        Args:
            text: 분석할 텍스트
            top_n: 상위 N개만 출력 (None이면 전체 출력)
            min_length: 키워드 최소 길이 (기본값: 2)
            min_count: 최소 출현 횟수 (기본값: 1)
        """
        results = self.analyze_keywords(text, min_length=min_length, min_count=min_count)
        
        if not results:
            print("[INFO] 분석된 키워드가 없습니다.")
            return
        
        if top_n:
            results = results[:top_n]
        
        # rich 라이브러리가 있으면 예쁘게 출력
        if RICH_AVAILABLE:
            console = Console()
            
            # 테이블 생성
            table = Table(
                title="키워드 빈도 및 순위 분석 결과",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta",
                title_style="bold cyan"
            )
            
            # 컬럼 추가
            table.add_column("순위", justify="center", style="cyan", no_wrap=True)
            table.add_column("키워드", justify="left", style="green", min_width=20)
            table.add_column("빈도", justify="right", style="yellow", no_wrap=True)
            
            # 데이터 추가
            for keyword, count, rank in results:
                # 상위 3개는 강조
                if rank <= 3:
                    table.add_row(
                        f"[bold]{rank}[/bold]",
                        f"[bold]{keyword}[/bold]",
                        f"[bold]{count}회[/bold]"
                    )
                else:
                    table.add_row(str(rank), keyword, f"{count}회")
            
            # 테이블 출력
            console.print()
            console.print(table)
            console.print(f"[dim]총 {len(results)}개의 키워드가 분석되었습니다.[/dim]")
            console.print()
        else:
            # rich가 없으면 기본 출력
            print("\n" + "=" * 60)
            print("키워드 빈도 및 순위 분석 결과")
            print("=" * 60)
            print(f"{'순위':<6} {'키워드':<20} {'빈도':<10}")
            print("-" * 60)
            
            for keyword, count, rank in results:
                print(f"{rank:<6} {keyword:<20} {count:<10}회")
            
            print("=" * 60)
            print(f"총 {len(results)}개의 키워드가 분석되었습니다.")
            print("=" * 60 + "\n")
    
    def _extract_keywords_with_konlpy(self, text: str, min_length: int, max_text_length: int = 10000) -> List[str]:
        """
        konlpy를 사용한 키워드 추출
        """
        try:
            # 텍스트 전처리
            cleaned_text = self._preprocess_text(text)
            
            # 텍스트가 너무 길면 자동으로 잘라서 처리
            if len(cleaned_text) > max_text_length:
                print(f"[INFO] 텍스트가 너무 깁니다 ({len(cleaned_text)}자). 처음 {max_text_length}자만 분석합니다.")
                cleaned_text = cleaned_text[:max_text_length]
            
            keywords = []
            
            # Okt 사용 시
            if isinstance(self.analyzer, Okt):
                try:
                    if len(cleaned_text) > 2000:
                        # 긴 텍스트는 문장 단위로 나눠서 처리
                        sentences = re.split(r'[.!?。！？\n]+', cleaned_text)
                        for sentence in sentences:
                            if len(sentence.strip()) > 0:
                                try:
                                    pos_tags = self.analyzer.pos(sentence.strip(), stem=True)
                                    sentence_keywords = []
                                    for word, pos in pos_tags:
                                        # 명사와 영문만
                                        if pos not in ['Noun', 'Alpha']:
                                            continue
                                        # 조사가 붙은 경우 제거 시도
                                        if self._has_josa(word):
                                            word = self._remove_josa(word)
                                        # 최소 길이 체크
                                        if len(word) < min_length:
                                            continue
                                        # 불용어 체크
                                        if word in self.stopwords:
                                            continue
                                        # 어미 패턴 체크
                                        if self._is_ending_word(word):
                                            continue
                                        sentence_keywords.append(word)
                                    keywords.extend(sentence_keywords)
                                except Exception:
                                    continue
                    else:
                        pos_tags = self.analyzer.pos(cleaned_text, stem=True)
                        keywords = []
                        for word, pos in pos_tags:
                            # 명사와 영문만
                            if pos not in ['Noun', 'Alpha']:
                                continue
                            # 조사가 붙은 경우 제거 시도
                            if self._has_josa(word):
                                word = self._remove_josa(word)
                            # 최소 길이 체크
                            if len(word) < min_length:
                                continue
                            # 불용어 체크
                            if word in self.stopwords:
                                continue
                            # 어미 패턴 체크
                            if self._is_ending_word(word):
                                continue
                            keywords.append(word)
                except Exception as e:
                    print(f"[WARN] Okt 형태소 분석 중 오류: {e}")
                    return self._extract_keywords_simple(text, min_length)
            
            # Kkma 사용 시
            elif isinstance(self.analyzer, Kkma):
                try:
                    if len(cleaned_text) > 2000:
                        sentences = re.split(r'[.!?。！？\n]+', cleaned_text)
                        for sentence in sentences:
                            if len(sentence.strip()) > 0:
                                try:
                                    pos_tags = self.analyzer.pos(sentence.strip())
                                    sentence_keywords = []
                                    for word, pos in pos_tags:
                                        # 명사만
                                        if not pos.startswith('N'):
                                            continue
                                        # 조사, 어미, 동사, 형용사 제외
                                        if pos.startswith('J') or pos.startswith('E') or pos.startswith('V') or pos.startswith('VA'):
                                            continue
                                        # 조사가 붙은 경우 제거 시도
                                        if self._has_josa(word):
                                            word = self._remove_josa(word)
                                        # 최소 길이 체크
                                        if len(word) < min_length:
                                            continue
                                        # 불용어 체크
                                        if word in self.stopwords:
                                            continue
                                        # 어미 패턴 체크
                                        if self._is_ending_word(word):
                                            continue
                                        sentence_keywords.append(word)
                                    keywords.extend(sentence_keywords)
                                except Exception:
                                    continue
                    else:
                        pos_tags = self.analyzer.pos(cleaned_text)
                        keywords = []
                        for word, pos in pos_tags:
                            # 명사만
                            if not pos.startswith('N'):
                                continue
                            # 조사, 어미, 동사, 형용사 제외
                            if pos.startswith('J') or pos.startswith('E') or pos.startswith('V') or pos.startswith('VA'):
                                continue
                            # 조사가 붙은 경우 제거 시도
                            if self._has_josa(word):
                                word = self._remove_josa(word)
                            # 최소 길이 체크
                            if len(word) < min_length:
                                continue
                            # 불용어 체크
                            if word in self.stopwords:
                                continue
                            # 어미 패턴 체크
                            if self._is_ending_word(word):
                                continue
                            keywords.append(word)
                except Exception as e:
                    print(f"[WARN] Kkma 형태소 분석 중 오류: {e}")
                    return self._extract_keywords_simple(text, min_length)
            
            # Komoran 사용 시
            elif isinstance(self.analyzer, Komoran):
                try:
                    if len(cleaned_text) > 2000:
                        sentences = re.split(r'[.!?。！？\n]+', cleaned_text)
                        for sentence in sentences:
                            if len(sentence.strip()) > 0:
                                try:
                                    pos_tags = self.analyzer.pos(sentence.strip())
                                    sentence_keywords = []
                                    for word, pos in pos_tags:
                                        # 명사만
                                        if not pos.startswith('N'):
                                            continue
                                        # 조사, 어미, 동사, 형용사 제외
                                        if pos.startswith('J') or pos.startswith('E') or pos.startswith('V') or pos.startswith('VA'):
                                            continue
                                        # 조사가 붙은 경우 제거 시도
                                        if self._has_josa(word):
                                            word = self._remove_josa(word)
                                        # 최소 길이 체크
                                        if len(word) < min_length:
                                            continue
                                        # 불용어 체크
                                        if word in self.stopwords:
                                            continue
                                        # 어미 패턴 체크
                                        if self._is_ending_word(word):
                                            continue
                                        sentence_keywords.append(word)
                                    keywords.extend(sentence_keywords)
                                except Exception:
                                    continue
                    else:
                        pos_tags = self.analyzer.pos(cleaned_text)
                        keywords = []
                        for word, pos in pos_tags:
                            # 명사만
                            if not pos.startswith('N'):
                                continue
                            # 조사, 어미, 동사, 형용사 제외
                            if pos.startswith('J') or pos.startswith('E') or pos.startswith('V') or pos.startswith('VA'):
                                continue
                            # 조사가 붙은 경우 제거 시도
                            if self._has_josa(word):
                                word = self._remove_josa(word)
                            # 최소 길이 체크
                            if len(word) < min_length:
                                continue
                            # 불용어 체크
                            if word in self.stopwords:
                                continue
                            # 어미 패턴 체크
                            if self._is_ending_word(word):
                                continue
                            keywords.append(word)
                except Exception as e:
                    print(f"[WARN] Komoran 형태소 분석 중 오류: {e}")
                    return self._extract_keywords_simple(text, min_length)
            
            return keywords
            
        except Exception as e:
            print(f"[ERROR] konlpy 키워드 추출 실패: {e}")
            return self._extract_keywords_simple(text, min_length)
    
    def _is_ending_word(self, word: str) -> bool:
        """
        어미 패턴이 포함된 단어인지 확인합니다.
        
        Args:
            word: 확인할 단어
            
        Returns:
            어미 패턴이 포함되어 있으면 True
        """
        for pattern in self.ending_patterns:
            if re.search(pattern, word):
                return True
        return False
    
    def _has_josa(self, word: str) -> bool:
        """
        조사가 붙은 단어인지 확인합니다.
        
        Args:
            word: 확인할 단어
            
        Returns:
            조사가 붙어있으면 True
        """
        for pattern in self.josa_patterns:
            if re.search(pattern, word):
                return True
        return False
    
    def _remove_josa(self, word: str) -> str:
        """
        단어에서 조사를 제거합니다. (범용적 처리)
        
        Args:
            word: 조사를 제거할 단어
            
        Returns:
            조사가 제거된 단어 (조사가 제거된 후 빈 문자열이면 원본 반환)
        """
        original_word = word
        for pattern in self.josa_patterns:
            word = re.sub(pattern, '', word)
        word = word.strip()
        # 조사 제거 후 단어가 너무 짧아지면 원본 반환 (예: "이" -> "")
        if len(word) < 1:
            return original_word
        return word
    
    def _extract_keywords_simple(self, text: str, min_length: int) -> List[str]:
        """
        konlpy 없이 간단한 키워드 추출
        """
        try:
            # 텍스트 전처리
            cleaned_text = self._preprocess_text(text)
            
            # 단어 분리 (공백, 구두점 기준)
            words = re.findall(r'[\w가-힣]+', cleaned_text)
            
            # 필터링: 최소 길이, 불용어 제외, 어미 패턴 제외, 조사 제거
            filtered_words = []
            for word in words:
                # 조사가 붙은 경우 제거 시도
                if self._has_josa(word):
                    word = self._remove_josa(word)
                # 최소 길이 체크
                if len(word) < min_length:
                    continue
                # 불용어 체크
                if word in self.stopwords:
                    continue
                # 숫자 제외
                if word.isdigit():
                    continue
                # 어미 패턴 제외
                if self._is_ending_word(word):
                    continue
                filtered_words.append(word)
            
            return filtered_words
            
        except Exception as e:
            print(f"[ERROR] 간단한 키워드 추출 실패: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # URL 제거
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 이메일 제거
        text = re.sub(r'\S+@\S+', '', text)
        
        # 마커 패턴 제거 ([이미지 삽입1], [링크 삽입2], [이모티콘 삽입3] 등)
        # 숫자가 포함된 패턴과 숫자가 없는 패턴 모두 처리
        text = re.sub(r'\[(이미지|링크|이모티콘)\s*삽입\s*\d+\]', '', text)
        text = re.sub(r'\[(이미지|링크|이모티콘)\s*삽입\]', '', text)
        
        # 특수 문자 제거 (일부 제외)
        text = re.sub(r'[^\w가-힣\s]', ' ', text)
        
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def analyze_from_file(self, file_path: str, min_length: int = 2, min_count: int = 1) -> List[Tuple[str, int, int]]:
        """
        파일에서 텍스트를 읽어 키워드를 분석합니다.
        
        Args:
            file_path: 분석할 파일 경로
            min_length: 키워드 최소 길이 (기본값: 2)
            min_count: 최소 출현 횟수 (기본값: 1)
            
        Returns:
            (키워드, 빈도, 순위) 튜플 리스트
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return self.analyze_keywords(text, min_length=min_length, min_count=min_count)
            
        except FileNotFoundError:
            print(f"[ERROR] 파일을 찾을 수 없습니다: {file_path}")
            return []
        except Exception as e:
            print(f"[ERROR] 파일 읽기 실패: {e}")
            return []
    
    def export_to_excel(self, text: str, output_path: str = None, top_n: Optional[int] = None, 
                       min_length: int = 2, min_count: int = 1) -> Optional[str]:
        """
        키워드 분석 결과를 엑셀 파일로 저장합니다.
        
        Args:
            text: 분석할 텍스트
            output_path: 저장할 엑셀 파일 경로 (None이면 자동 생성)
            top_n: 상위 N개만 저장 (None이면 전체 저장)
            min_length: 키워드 최소 길이 (기본값: 2)
            min_count: 최소 출현 횟수 (기본값: 1)
            
        Returns:
            저장된 파일 경로 (실패하면 None)
        """
        if not PANDAS_AVAILABLE:
            print("[ERROR] pandas가 설치되지 않았습니다. 엑셀 저장 기능을 사용할 수 없습니다.")
            print("[INFO] pip install pandas openpyxl 로 설치하세요.")
            return None
        
        try:
            # 키워드 분석
            results = self.analyze_keywords(text, min_length=min_length, min_count=min_count)
            
            if not results:
                print("[WARN] 분석된 키워드가 없습니다. 엑셀 파일을 생성할 수 없습니다.")
                return None
            
            if top_n:
                results = results[:top_n]
            
            # 데이터프레임 생성
            data = {
                '순위': [rank for _, _, rank in results],
                '키워드': [keyword for keyword, _, _ in results],
                '빈도': [count for _, count, _ in results]
            }
            df = pd.DataFrame(data)
            
            # 출력 경로 생성
            if not output_path:
                import time
                timestamp = int(time.time())
                output_path = f"keyword_analysis_{timestamp}.xlsx"
            
            # 디렉토리가 없으면 생성
            output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 엑셀 파일로 저장
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='키워드 분석', index=False)
                
                # 열 너비 자동 조정
                worksheet = writer.sheets['키워드 분석']
                worksheet.column_dimensions['A'].width = 10  # 순위
                worksheet.column_dimensions['B'].width = 30  # 키워드
                worksheet.column_dimensions['C'].width = 15  # 빈도
            
            print(f"[INFO] 키워드 분석 결과가 엑셀 파일로 저장되었습니다: {output_path}")
            print(f"[INFO] 총 {len(results)}개의 키워드가 저장되었습니다.")
            return output_path
            
        except ImportError:
            print("[ERROR] openpyxl이 설치되지 않았습니다.")
            print("[INFO] pip install openpyxl 로 설치하세요.")
            return None
        except Exception as e:
            print(f"[ERROR] 엑셀 파일 저장 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def export_from_file_to_excel(self, input_file_path: str, output_path: str = None,
                                  top_n: Optional[int] = None, min_length: int = 2, min_count: int = 1) -> Optional[str]:
        """
        파일에서 텍스트를 읽어 분석한 후 엑셀 파일로 저장합니다.
        
        Args:
            input_file_path: 분석할 텍스트 파일 경로
            output_path: 저장할 엑셀 파일 경로 (None이면 자동 생성)
            top_n: 상위 N개만 저장 (None이면 전체 저장)
            min_length: 키워드 최소 길이 (기본값: 2)
            min_count: 최소 출현 횟수 (기본값: 1)
            
        Returns:
            저장된 파일 경로 (실패하면 None)
        """
        try:
            with open(input_file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # 출력 경로가 지정되지 않았으면 입력 파일명 기반으로 생성
            if not output_path:
                base_name = os.path.splitext(os.path.basename(input_file_path))[0]
                output_path = f"{base_name}_keyword_analysis.xlsx"
            
            return self.export_to_excel(text, output_path=output_path, top_n=top_n, 
                                       min_length=min_length, min_count=min_count)
            
        except FileNotFoundError:
            print(f"[ERROR] 파일을 찾을 수 없습니다: {input_file_path}")
            return None
        except Exception as e:
            print(f"[ERROR] 파일 읽기 실패: {e}")
            return None


def analyze_keywords_from_text(text: str, top_n: Optional[int] = None, min_length: int = 2, min_count: int = 1, use_konlpy: bool = True) -> List[Tuple[str, int, int]]:
    """
    간편 함수: 텍스트에서 키워드 빈도와 순위 분석
    
    Args:
        text: 분석할 텍스트
        top_n: 상위 N개만 반환 (None이면 전체 반환)
        min_length: 키워드 최소 길이 (기본값: 2)
        min_count: 최소 출현 횟수 (기본값: 1)
        use_konlpy: konlpy 사용 여부 (기본값: True)
        
    Returns:
        (키워드, 빈도, 순위) 튜플 리스트
    """
    analyzer = MorphemeAnalyzer(use_konlpy=use_konlpy)
    results = analyzer.analyze_keywords(text, min_length=min_length, min_count=min_count)
    
    if top_n:
        results = results[:top_n]
    
    return results


def export_keywords_to_excel(text: str, output_path: str = None, top_n: Optional[int] = None,
                             min_length: int = 2, min_count: int = 1, use_konlpy: bool = True) -> Optional[str]:
    """
    간편 함수: 텍스트에서 키워드를 분석하여 엑셀 파일로 저장
    
    Args:
        text: 분석할 텍스트
        output_path: 저장할 엑셀 파일 경로 (None이면 자동 생성)
        top_n: 상위 N개만 저장 (None이면 전체 저장)
        min_length: 키워드 최소 길이 (기본값: 2)
        min_count: 최소 출현 횟수 (기본값: 1)
        use_konlpy: konlpy 사용 여부 (기본값: True)
        
    Returns:
        저장된 파일 경로 (실패하면 None)
    """
    analyzer = MorphemeAnalyzer(use_konlpy=use_konlpy)
    return analyzer.export_to_excel(text, output_path=output_path, top_n=top_n,
                                   min_length=min_length, min_count=min_count)


if __name__ == "__main__":
    # 테스트 코드
    sample_text = """
    홈페이지제작은 현대 비즈니스에서 매우 중요한 요소입니다. 
    웹사이트 제작을 통해 기업은 온라인에서 고객과 소통할 수 있습니다.
    홈페이지 개발 시에는 사용자 경험과 SEO 최적화를 고려해야 합니다.
    웹사이트 제작 전문가들은 최신 기술을 활용하여 효과적인 홈페이지를 만들 수 있습니다.
    홈페이지제작 과정에서는 디자인, 개발, 최적화 등 다양한 요소가 필요합니다.
    홈페이지제작은 지속적인 관리와 업데이트가 필요합니다.
    웹사이트 제작 시 반응형 디자인을 고려해야 합니다.
    """
    
    print("=" * 60)
    print("형태소 분석 모듈 테스트")
    print("=" * 60)
    
    analyzer = MorphemeAnalyzer(use_konlpy=True)
    
    # 키워드 분석 및 통계 출력
    analyzer.print_keyword_statistics(sample_text, top_n=10, min_length=2, min_count=1)
    
    # 딕셔너리 형태로 결과 가져오기
    ranking = analyzer.get_keyword_ranking(sample_text, top_n=10, min_length=2, min_count=1)
    print("\n[딕셔너리 형태 결과]")
    for keyword, info in ranking.items():
        print(f"  {keyword}: {info['count']}회 (순위: {info['rank']})")
    
    # 튜플 리스트 형태로 결과 가져오기
    results = analyzer.analyze_keywords(sample_text, min_length=2, min_count=1)
    print(f"\n[튜플 리스트 형태 결과] (상위 5개)")
    for keyword, count, rank in results[:5]:
        print(f"  순위 {rank}: {keyword} ({count}회)")
    
    # 엑셀 파일로 저장
    print("\n[엑셀 파일 저장 테스트]")
    excel_path = analyzer.export_to_excel(sample_text, output_path="test_keyword_analysis.xlsx", 
                                         top_n=20, min_length=2, min_count=1)
    if excel_path:
        print(f"✅ 엑셀 파일이 저장되었습니다: {excel_path}")

