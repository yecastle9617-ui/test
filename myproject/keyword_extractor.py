"""
자연어 처리를 통한 키워드 추출 모듈
"""

from typing import List
import re
from collections import Counter

# konlpy import 시도
# 참고: konlpy의 분석기 종류
# - Okt: 순수 Python 구현, Java 불필요 (권장)
# - Kkma, Komoran: Java 기반, JPype와 JVM 필요
KONLPY_AVAILABLE = False
Okt = None
Kkma = None
Komoran = None

try:
    from konlpy.tag import Okt, Kkma, Komoran
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    print("[WARN] konlpy가 설치되지 않았습니다. 기본 키워드 추출 방법을 사용합니다.")
    print("[INFO] pip install konlpy 로 설치하거나, 간단한 추출 방법을 사용합니다.")
except Exception as e:
    # VPN, 네트워크, Java 등 다른 에러도 처리
    error_msg = str(e).lower()
    if any(keyword in error_msg for keyword in ['vpn', 'network', 'connection', 'timeout', 'java', 'jvm', 'jpype']):
        print(f"[WARN] konlpy import 중 네트워크/Java 에러 발생: {e}")
        print("[INFO] Java 기반 분석기(Kkma, Komoran)는 Java 설치가 필요합니다.")
        print("[INFO] Okt(순수 Python) 또는 간단한 키워드 추출 방법을 사용합니다.")
    else:
        print(f"[WARN] konlpy import 실패: {e}")
        print("[INFO] 간단한 키워드 추출 방법을 사용합니다.")
    KONLPY_AVAILABLE = False


class KeywordExtractor:
    """자연어 처리를 통해 텍스트에서 키워드를 추출하는 클래스"""
    
    def __init__(self, use_konlpy: bool = True):
        """
        키워드 추출기 초기화
        
        Args:
            use_konlpy: konlpy 라이브러리 사용 여부 (기본값: True)
        """
        self.use_konlpy = use_konlpy and KONLPY_AVAILABLE
        self.analyzer = None
        
        if self.use_konlpy:
            # konlpy 초기화를 시도하되, 네트워크/Java 관련 에러는 무시
            analyzer_initialized = False
            
            # Okt 시도 (순수 Python 구현, Java 불필요 - 가장 안전)
            if not analyzer_initialized:
                try:
                    self.analyzer = Okt()
                    print("[INFO] Okt 형태소 분석기를 사용합니다. (순수 Python, Java 불필요)")
                    analyzer_initialized = True
                except Exception as e:
                    error_msg = str(e).lower()
                    # VPN/네트워크 관련 에러는 무시하고 간단한 방법 사용
                    if any(keyword in error_msg for keyword in ['vpn', 'network', 'connection', 'timeout', 'java', 'jvm']):
                        print(f"[WARN] Okt 초기화 중 네트워크/Java 에러 발생: {e}")
                        print("[INFO] VPN/네트워크 문제로 간단한 키워드 추출 방법을 사용합니다.")
                        self.use_konlpy = False
                        analyzer_initialized = False
                    else:
                        print(f"[WARN] Okt 초기화 실패: {e}")
            
            # Java 기반 분석기들은 Java 설치/설정 문제로 인해 실패할 수 있으므로
            # Okt가 실패한 경우에만 시도 (선택적)
            # 주의: Kkma와 Komoran은 Java/JVM이 필요합니다
            
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
                        print("[INFO] 간단한 키워드 추출 방법을 사용합니다.")
                        self.use_konlpy = False
        
        # 불용어 리스트 (한국어)
        self.stopwords = {
            '이', '가', '을', '를', '에', '의', '와', '과', '은', '는',
            '도', '로', '으로', '에서', '에게', '께', '한테', '처럼',
            '만', '까지', '부터', '보다', '같이', '하고', '또한',
            '그', '이것', '저것', '그것', '이런', '저런', '그런',
            '것', '수', '때', '등', '및', '또', '또한', '그리고',
            '하지만', '그러나', '따라서', '그래서', '그런데',
            '그래도', '그리고', '또한', '그래서', '따라서',
            '있', '없', '되', '하', '되', '되', '되', '되'
        }
    
    def extract_keywords(self, text: str, top_n: int = 3, min_length: int = 2) -> List[str]:
        """
        텍스트에서 자주 나오는 키워드를 추출합니다.
        
        Args:
            text: 분석할 텍스트
            top_n: 추출할 키워드 개수 (기본값: 3)
            min_length: 키워드 최소 길이 (기본값: 2)
            
        Returns:
            추출된 키워드 리스트 (빈도순 정렬)
        """
        if not text or len(text.strip()) == 0:
            return []
        
        if self.use_konlpy and self.analyzer:
            return self._extract_with_konlpy(text, top_n, min_length)
        else:
            return self._extract_simple(text, top_n, min_length)
    
    def _extract_with_konlpy(self, text: str, top_n: int, min_length: int, max_text_length: int = 5000) -> List[str]:
        """
        konlpy를 사용한 키워드 추출
        긴 텍스트는 자동으로 잘라서 처리합니다.
        """
        try:
            # 텍스트 전처리
            cleaned_text = self._preprocess_text(text)
            
            # 텍스트가 너무 길면 자동으로 잘라서 처리 (konlpy는 긴 텍스트에서 매우 느림)
            if len(cleaned_text) > max_text_length:
                print(f"[INFO] 텍스트가 너무 깁니다 ({len(cleaned_text)}자). 처음 {max_text_length}자만 분석합니다.")
                cleaned_text = cleaned_text[:max_text_length]
            
            # 형태소 분석 및 명사 추출
            nouns = []
            
            # Okt 사용 시
            if isinstance(self.analyzer, Okt):
                try:
                    # 명사만 추출 (긴 텍스트는 청크로 나눠서 처리)
                    if len(cleaned_text) > 2000:
                        # 긴 텍스트는 문장 단위로 나눠서 처리
                        sentences = re.split(r'[.!?。！？\n]+', cleaned_text)
                        for sentence in sentences:
                            if len(sentence.strip()) > 0:
                                try:
                                    pos_tags = self.analyzer.pos(sentence.strip(), stem=True)
                                    sentence_nouns = [word for word, pos in pos_tags 
                                                    if pos in ['Noun', 'Alpha']
                                                    and len(word) >= min_length
                                                    and word not in self.stopwords]
                                    nouns.extend(sentence_nouns)
                                except Exception as e:
                                    # 개별 문장 처리 실패 시 무시하고 계속
                                    continue
                    else:
                        # 짧은 텍스트는 한 번에 처리
                        pos_tags = self.analyzer.pos(cleaned_text, stem=True)
                        nouns = [word for word, pos in pos_tags 
                                if pos in ['Noun', 'Alpha']  # 명사와 영문
                                and len(word) >= min_length
                                and word not in self.stopwords]
                except Exception as e:
                    print(f"[WARN] Okt 형태소 분석 중 오류: {e}")
                    # 폴백: 간단한 방법 사용
                    return self._extract_simple(text, top_n, min_length)
            # Kkma 사용 시
            elif isinstance(self.analyzer, Kkma):
                try:
                    if len(cleaned_text) > 2000:
                        sentences = re.split(r'[.!?。！？\n]+', cleaned_text)
                        for sentence in sentences:
                            if len(sentence.strip()) > 0:
                                try:
                                    pos_tags = self.analyzer.pos(sentence.strip())
                                    sentence_nouns = [word for word, pos in pos_tags 
                                                    if pos.startswith('N')
                                                    and len(word) >= min_length
                                                    and word not in self.stopwords]
                                    nouns.extend(sentence_nouns)
                                except:
                                    continue
                    else:
                        pos_tags = self.analyzer.pos(cleaned_text)
                        nouns = [word for word, pos in pos_tags 
                                if pos.startswith('N')  # 명사류
                                and len(word) >= min_length
                                and word not in self.stopwords]
                except Exception as e:
                    print(f"[WARN] Kkma 형태소 분석 중 오류: {e}")
                    return self._extract_simple(text, top_n, min_length)
            # Komoran 사용 시
            elif isinstance(self.analyzer, Komoran):
                try:
                    if len(cleaned_text) > 2000:
                        sentences = re.split(r'[.!?。！？\n]+', cleaned_text)
                        for sentence in sentences:
                            if len(sentence.strip()) > 0:
                                try:
                                    pos_tags = self.analyzer.pos(sentence.strip())
                                    sentence_nouns = [word for word, pos in pos_tags 
                                                    if pos.startswith('N')
                                                    and len(word) >= min_length
                                                    and word not in self.stopwords]
                                    nouns.extend(sentence_nouns)
                                except:
                                    continue
                    else:
                        pos_tags = self.analyzer.pos(cleaned_text)
                        nouns = [word for word, pos in pos_tags 
                                if pos.startswith('N')  # 명사류
                                and len(word) >= min_length
                                and word not in self.stopwords]
                except Exception as e:
                    print(f"[WARN] Komoran 형태소 분석 중 오류: {e}")
                    return self._extract_simple(text, top_n, min_length)
            
            # 빈도 계산
            noun_counter = Counter(nouns)
            
            # 상위 N개 추출
            top_keywords = [word for word, count in noun_counter.most_common(top_n)]
            
            return top_keywords
            
        except Exception as e:
            print(f"[ERROR] konlpy 키워드 추출 실패: {e}")
            import traceback
            traceback.print_exc()
            # 폴백: 간단한 방법 사용
            return self._extract_simple(text, top_n, min_length)
    
    def _extract_simple(self, text: str, top_n: int, min_length: int) -> List[str]:
        """konlpy 없이 간단한 키워드 추출"""
        try:
            # 텍스트 전처리
            cleaned_text = self._preprocess_text(text)
            
            # 단어 분리 (공백, 구두점 기준)
            words = re.findall(r'[\w가-힣]+', cleaned_text)
            
            # 필터링: 최소 길이, 불용어 제외
            filtered_words = [
                word for word in words
                if len(word) >= min_length
                and word not in self.stopwords
                and not word.isdigit()  # 숫자 제외
            ]
            
            # 빈도 계산
            word_counter = Counter(filtered_words)
            
            # 상위 N개 추출
            top_keywords = [word for word, count in word_counter.most_common(top_n)]
            
            return top_keywords
            
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
        
        # 특수 문자 제거 (일부 제외)
        text = re.sub(r'[^\w가-힣\s]', ' ', text)
        
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_phrases(self, text: str, top_n: int = 3, min_length: int = 2) -> List[str]:
        """
        텍스트에서 자주 나오는 구(phrase)를 추출합니다.
        2-4단어로 구성된 구를 추출합니다.
        
        Args:
            text: 분석할 텍스트
            top_n: 추출할 구 개수 (기본값: 3)
            min_length: 단어 최소 길이 (기본값: 2)
            
        Returns:
            추출된 구 리스트 (빈도순 정렬)
        """
        if not text or len(text.strip()) == 0:
            return []
        
        try:
            # 텍스트 전처리
            cleaned_text = self._preprocess_text(text)
            
            if self.use_konlpy and self.analyzer:
                # 형태소 분석
                if isinstance(self.analyzer, Okt):
                    pos_tags = self.analyzer.pos(cleaned_text, stem=True)
                    words = [word for word, pos in pos_tags 
                            if pos in ['Noun', 'Alpha']
                            and len(word) >= min_length
                            and word not in self.stopwords]
                else:
                    pos_tags = self.analyzer.pos(cleaned_text)
                    words = [word for word, pos in pos_tags 
                            if pos.startswith('N')
                            and len(word) >= min_length
                            and word not in self.stopwords]
            else:
                # 간단한 방법
                words = re.findall(r'[\w가-힣]+', cleaned_text)
                words = [w for w in words 
                        if len(w) >= min_length 
                        and w not in self.stopwords
                        and not w.isdigit()]
            
            # 구(phrase) 생성: 2-4단어 조합
            phrases = []
            for n in range(2, 5):  # 2, 3, 4단어
                for i in range(len(words) - n + 1):
                    phrase = ' '.join(words[i:i+n])
                    phrases.append(phrase)
            
            # 빈도 계산
            phrase_counter = Counter(phrases)
            
            # 상위 N개 추출
            top_phrases = [phrase for phrase, count in phrase_counter.most_common(top_n)]
            
            return top_phrases
            
        except Exception as e:
            print(f"[ERROR] 구(phrase) 추출 실패: {e}")
            return []
    
    def extract_with_weights(self, text: str, top_n: int = 3, min_length: int = 2) -> List[tuple]:
        """
        키워드와 빈도를 함께 반환합니다.
        
        Args:
            text: 분석할 텍스트
            top_n: 추출할 키워드 개수 (기본값: 3)
            min_length: 키워드 최소 길이 (기본값: 2)
            
        Returns:
            (키워드, 빈도) 튜플 리스트
        """
        if not text or len(text.strip()) == 0:
            return []
        
        try:
            if self.use_konlpy and self.analyzer:
                cleaned_text = self._preprocess_text(text)
                
                if isinstance(self.analyzer, Okt):
                    pos_tags = self.analyzer.pos(cleaned_text, stem=True)
                    nouns = [word for word, pos in pos_tags 
                            if pos in ['Noun', 'Alpha']
                            and len(word) >= min_length
                            and word not in self.stopwords]
                else:
                    pos_tags = self.analyzer.pos(cleaned_text)
                    nouns = [word for word, pos in pos_tags 
                            if pos.startswith('N')
                            and len(word) >= min_length
                            and word not in self.stopwords]
            else:
                cleaned_text = self._preprocess_text(text)
                words = re.findall(r'[\w가-힣]+', cleaned_text)
                nouns = [w for w in words 
                        if len(w) >= min_length 
                        and w not in self.stopwords
                        and not w.isdigit()]
            
            noun_counter = Counter(nouns)
            top_keywords = noun_counter.most_common(top_n)
            
            return top_keywords
            
        except Exception as e:
            print(f"[ERROR] 키워드 추출 (가중치 포함) 실패: {e}")
            return []


def extract_keywords_from_text(text: str, top_n: int = 3, use_konlpy: bool = True) -> List[str]:
    """
    간편 함수: 텍스트에서 키워드 추출
    
    Args:
        text: 분석할 텍스트
        top_n: 추출할 키워드 개수 (기본값: 3)
        use_konlpy: konlpy 사용 여부 (기본값: True)
        
    Returns:
        추출된 키워드 리스트
    """
    extractor = KeywordExtractor(use_konlpy=use_konlpy)
    return extractor.extract_keywords(text, top_n=top_n)


if __name__ == "__main__":
    # 테스트 코드
    sample_text = """
    홈페이지제작은 현대 비즈니스에서 매우 중요한 요소입니다. 
    웹사이트 제작을 통해 기업은 온라인에서 고객과 소통할 수 있습니다.
    홈페이지 개발 시에는 사용자 경험과 SEO 최적화를 고려해야 합니다.
    웹사이트 제작 전문가들은 최신 기술을 활용하여 효과적인 홈페이지를 만들 수 있습니다.
    홈페이지제작 과정에서는 디자인, 개발, 최적화 등 다양한 요소가 필요합니다.
    """
    
    print("=" * 60)
    print("키워드 추출 테스트")
    print("=" * 60)
    
    extractor = KeywordExtractor(use_konlpy=True)
    
    # 단어 키워드 추출
    keywords = extractor.extract_keywords(sample_text, top_n=3)
    print(f"\n[단어 키워드] (상위 3개)")
    for i, keyword in enumerate(keywords, 1):
        print(f"  {i}. {keyword}")
    
    # 구(phrase) 추출
    phrases = extractor.extract_phrases(sample_text, top_n=3)
    print(f"\n[구(phrase) 키워드] (상위 3개)")
    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase}")
    
    # 가중치 포함 추출
    keywords_with_weights = extractor.extract_with_weights(sample_text, top_n=3)
    print(f"\n[키워드 + 빈도] (상위 3개)")
    for i, (keyword, count) in enumerate(keywords_with_weights, 1):
        print(f"  {i}. {keyword} (빈도: {count})")
    
    print("\n" + "=" * 60)

