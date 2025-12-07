"""
GPT API를 사용하여 블로그 글을 생성하는 모듈
프롬프트 템플릿을 사용하여 OpenAI GPT API를 호출합니다.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 (지연 초기화)
_client = None


def get_openai_client() -> OpenAI:
    """
    OpenAI 클라이언트를 반환합니다 (지연 초기화).
    
    Returns:
        OpenAI 클라이언트 인스턴스
    """
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        _client = OpenAI(api_key=api_key)
    return _client


def load_prompt_template() -> Dict[str, Any]:
    """
    프롬프트 템플릿 JSON 파일을 로드합니다.
    
    Returns:
        프롬프트 템플릿 딕셔너리
    """
    current_dir = Path(__file__).parent
    project_dir = current_dir.parent
    template_path = project_dir / "config" / "prompt_template.json"
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_default_ban_words() -> List[str]:
    """
    기본 금칙어 목록을 로드합니다.
    
    Returns:
        기본 금칙어 리스트
    """
    current_dir = Path(__file__).parent
    project_dir = current_dir.parent
    ban_words_path = project_dir / "config" / "default_ban_words.json"
    
    try:
        with open(ban_words_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("default_ban_words", [])
    except FileNotFoundError:
        # 파일이 없으면 빈 리스트 반환
        return []
    except json.JSONDecodeError:
        # JSON 파싱 오류 시 빈 리스트 반환
        return []


def build_system_prompt(
    template: Dict[str, Any],
    blog_level: str = "mid"
) -> str:
    """
    시스템 프롬프트를 구성합니다.
    
    Args:
        template: 프롬프트 템플릿 딕셔너리
        blog_level: 블로그 지수 ("new", "mid", "high")
    
    Returns:
        시스템 프롬프트 문자열
    """
    system_parts = []
    
    # 공통 규칙
    system_parts.extend(template.get("system_common", []))
    
    # 레벨별 규칙
    if blog_level == "new":
        system_parts.extend(template.get("system_level_new", []))
    elif blog_level == "high":
        system_parts.extend(template.get("system_level_high", []))
    else:  # mid (기본값)
        system_parts.extend(template.get("system_level_mid", []))
    
    return "\n".join(system_parts)


def build_user_prompt(
    template: Dict[str, Any],
    keywords: str,
    category: str,
    blog_level: str,
    ban_words: List[str],
    analysis_json: Optional[Dict[str, Any]] = None,
    external_links: Optional[List[str]] = None
) -> str:
    """
    사용자 프롬프트를 구성합니다.
    
    Args:
        template: 프롬프트 템플릿 딕셔너리
        keywords: 키워드
        category: 카테고리
        blog_level: 블로그 레벨
        ban_words: 금칙어 목록
        analysis_json: 상위 글 분석 JSON (선택사항)
    
    Returns:
        사용자 프롬프트 문자열
    """
    user_template = template.get("user_prompt_template", [])
    user_prompt = "\n".join(user_template)
    
    # 레벨별 글자 수 요구사항 동적 생성
    char_count_requirement = ""
    if blog_level == "new":
        char_count_requirement = "- **new 레벨: 최소 2000자, 목표 2200~2400자** (JSON 구조 제외 순수 텍스트만 계산)\n  - introduction.content + body의 모든 subtitle.content와 blocks.content + conclusion.content의 합계"
    elif blog_level == "mid":
        char_count_requirement = "- **mid 레벨: 최소 2500자, 목표 2700~2900자** (JSON 구조 제외 순수 텍스트만 계산)\n  - introduction.content + body의 모든 subtitle.content와 blocks.content + conclusion.content의 합계"
    elif blog_level == "high":
        char_count_requirement = "- **high 레벨: 최소 3000자, 목표 3200~3400자** (JSON 구조 제외 순수 텍스트만 계산)\n  - introduction.content + body의 모든 subtitle.content와 blocks.content + conclusion.content + FAQ의 모든 q.content와 a.content의 합계"
    
    # 변수 치환
    user_prompt = user_prompt.replace("{{keywords}}", keywords)
    user_prompt = user_prompt.replace("{{category}}", category)
    user_prompt = user_prompt.replace("{{blog_level}}", blog_level)
    user_prompt = user_prompt.replace("{{ban_words}}", ", ".join(ban_words) if ban_words else "없음")
    # {{char_count_requirement}} 플레이스홀더가 있으면 치환, 없으면 그대로 둠
    if "{{char_count_requirement}}" in user_prompt:
        user_prompt = user_prompt.replace("{{char_count_requirement}}", char_count_requirement)
    
    # analysis_json 처리
    if analysis_json:
        analysis_str = json.dumps(analysis_json, ensure_ascii=False, indent=2)
    else:
        analysis_str = "{}"
    user_prompt = user_prompt.replace("{{analysis_json}}", analysis_str)
    
    # 외부 링크 처리
    if external_links:
        external_links_str = "\n".join(external_links)
    else:
        external_links_str = "없음"
    user_prompt = user_prompt.replace("{{external_links}}", external_links_str)
    
    return user_prompt


def get_max_tokens_for_level(blog_level: str) -> int:
    """
    블로그 레벨에 따른 최대 토큰 수를 반환합니다.
    
    Args:
        blog_level: 블로그 레벨 ("new", "mid", "high")
    
    Returns:
        최대 토큰 수
    """
    # 한글 1자 ≈ 1.5~2 토큰, JSON 구조 고려하여 여유 있게 설정
    # JSON 구조, 스타일 정보, 마크업 등을 고려하여 충분한 토큰 할당
    level_tokens = {
        "new": 6000,      # 2000~2500자 → 약 4000~5000 토큰 + JSON 구조 여유분
        "mid": 7000,      # 2500~3000자 → 약 5000~6000 토큰 + JSON 구조 여유분
        "high": 9000      # 3000~3500자 이상 → 약 6000~7000 토큰 + JSON 구조 여유분
    }
    return level_tokens.get(blog_level, 7000)  # 기본값: mid


def generate_blog_content(
    keywords: str,
    category: str = "일반",
    blog_level: str = "mid",
    ban_words: Optional[List[str]] = None,
    analysis_json: Optional[Dict[str, Any]] = None,
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    external_links: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    GPT API를 호출하여 블로그 글을 생성합니다.
    
    Args:
        keywords: 블로그 글의 주요 키워드
        category: 카테고리 (기본값: "일반")
        blog_level: 블로그 레벨 ("new", "mid", "high", 기본값: "mid")
        ban_words: 금칙어 목록 (기본값: None)
        analysis_json: 상위 글 분석 JSON (기본값: None)
        model: 사용할 GPT 모델 (기본값: "gpt-4o")
        temperature: 생성 온도 (기본값: 0.7)
        max_tokens: 최대 출력 토큰 수 (기본값: None, blog_level에 따라 자동 설정)
        external_links: 본문에 자연스럽게 삽입할 외부 링크 목록 (new 레벨에서는 사용하지 않음)
    
    Returns:
        생성된 블로그 글 JSON 딕셔너리
    """
    # 기본 금칙어 로드
    default_ban_words = load_default_ban_words()
    
    # 사용자 입력 금칙어와 기본 금칙어 병합 (중복 제거)
    if ban_words is None:
        ban_words = []
    
    # 기본 금칙어와 사용자 금칙어를 합치고 중복 제거
    all_ban_words = list(set(default_ban_words + ban_words))
    
    # 프롬프트 템플릿 로드
    template = load_prompt_template()
    
    # 시스템 프롬프트 구성
    system_prompt = build_system_prompt(template, blog_level)
    
    # 사용자 프롬프트 구성
    user_prompt = build_user_prompt(
        template=template,
        keywords=keywords,
        category=category,
        blog_level=blog_level,
        ban_words=all_ban_words,
        analysis_json=analysis_json,
        external_links=external_links
    )
    
    # 최대 토큰 수 설정
    if max_tokens is None:
        max_tokens = get_max_tokens_for_level(blog_level)
    
    # GPT API 호출
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,  # 최대 출력 토큰 수 설정
            response_format={"type": "json_object"}  # JSON 형식으로 응답 받기
        )
        
        # 응답에서 JSON 추출
        content = response.choices[0].message.content
        
        # JSON 파싱
        blog_content = json.loads(content)
        
        return blog_content
        
    except json.JSONDecodeError as e:
        raise ValueError(f"GPT 응답을 JSON으로 파싱할 수 없습니다: {str(e)}")
    except Exception as e:
        raise Exception(f"GPT API 호출 중 오류 발생: {str(e)}")


def get_create_naver_directory() -> Path:
    """
    blog/create_naver 디렉토리 내에 날짜별 번호 디렉토리를 생성합니다.
    형식: blog/create_naver/yyyymmdd_1, yyyymmdd_2, ...
    
    Returns:
        생성된 디렉토리 경로
    """
    current_dir = Path(__file__).parent
    project_dir = current_dir.parent
    base_dir = project_dir / "blog" / "create_naver"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # 오늘 날짜 형식: yyyymmdd
    today = datetime.now().strftime("%Y%m%d")
    
    # 같은 날짜에 생성된 디렉토리 찾기
    dir_pattern = f"{today}_"
    existing_dirs = [
        d for d in base_dir.iterdir()
        if d.is_dir() and d.name.startswith(dir_pattern)
    ]
    
    # 가장 큰 번호 찾기
    max_num = 0
    for dir_path in existing_dirs:
        try:
            num = int(dir_path.name.split('_')[-1])
            max_num = max(max_num, num)
        except (ValueError, IndexError):
            continue
    
    # 다음 번호 생성
    next_num = max_num + 1
    output_dir = base_dir / f"{today}_{next_num}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir


def extract_image_placeholders(blog_content: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    블로그 콘텐츠에서 이미지 플레이스홀더를 추출합니다.
    
    Args:
        blog_content: 블로그 콘텐츠 딕셔너리
    
    Returns:
        이미지 플레이스홀더 리스트 (각 항목은 {placeholder, image_prompt, index})
    """
    image_placeholders = []
    index = 1
    
    # body 섹션에서 이미지 플레이스홀더 찾기
    if "body" in blog_content and isinstance(blog_content["body"], list):
        for section in blog_content["body"]:
            if "blocks" in section and isinstance(section["blocks"], list):
                for block in section["blocks"]:
                    if block.get("type") == "image_placeholder":
                        placeholder = block.get("placeholder", "")
                        image_prompt = block.get("image_prompt", "")
                        
                        if image_prompt:  # image_prompt가 있는 경우만 추가
                            image_placeholders.append({
                                "placeholder": placeholder,
                                "image_prompt": image_prompt,
                                "index": index
                            })
                            index += 1
    
    return image_placeholders


def save_blog_json(
    blog_content: Dict[str, Any],
    output_dir: Optional[str] = None,
    filename: Optional[str] = None
) -> str:
    """
    생성된 블로그 글을 JSON 파일로 저장합니다.
    
    Args:
        blog_content: 생성된 블로그 글 딕셔너리
        output_dir: 저장할 디렉토리 경로 (기본값: None, blog/create_naver/yyyymmdd_N 자동 생성)
        filename: 저장할 파일명 (기본값: None, 타임스탬프 기반)
    
    Returns:
        저장된 파일의 경로
    """
    if output_dir is None:
        output_dir = get_create_naver_directory()
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"blog_generated_{timestamp}.json"
    
    filepath = output_dir / filename
    
    # JSON 파일로 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(blog_content, f, ensure_ascii=False, indent=2)
    
    return str(filepath)


if __name__ == "__main__":
    # 테스트 코드
    try:
        result = generate_blog_content(
            keywords="아임웹 홈페이지 제작",
            category="웹사이트 제작",
            blog_level="mid",
            ban_words=["스팸", "광고"]
        )
        
        print("생성된 블로그 글:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # JSON 파일로 저장
        saved_path = save_blog_json(result)
        print(f"\n저장 완료: {saved_path}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

