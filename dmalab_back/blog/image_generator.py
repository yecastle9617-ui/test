"""
Gemini API를 사용하여 이미지를 생성하는 모듈
"""

import os
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from PIL import Image
import logging

# .env 파일 로드 (프로젝트 루트에서)
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent  # DMaLab 디렉토리
load_dotenv(project_root / ".env")

logger = logging.getLogger(__name__)

# Gemini 클라이언트 (지연 초기화)
_client = None

# 이미지 프롬프트 가이드 (지연 로드)
_image_prompt_guide = None


def get_gemini_client() -> genai.Client:
    """
    Gemini 클라이언트를 반환합니다 (지연 초기화).
    
    Returns:
        Gemini 클라이언트 인스턴스
    """
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        _client = genai.Client(api_key=api_key)
    return _client


def load_image_prompt_guide() -> Dict[str, Any]:
    """
    이미지 프롬프트 가이드 JSON 파일을 로드합니다.
    
    Returns:
        이미지 프롬프트 가이드 딕셔너리
    """
    global _image_prompt_guide
    if _image_prompt_guide is None:
        current_dir = Path(__file__).parent
        project_dir = current_dir.parent
        guide_path = project_dir / "config" / "image_prompt_guide.json"
        
        try:
            with open(guide_path, 'r', encoding='utf-8') as f:
                _image_prompt_guide = json.load(f)
        except FileNotFoundError:
            logger.warning(f"[IMAGE] 이미지 프롬프트 가이드 파일을 찾을 수 없습니다: {guide_path}")
            _image_prompt_guide = {"default_style_guide": {}}
        except json.JSONDecodeError as e:
            logger.error(f"[IMAGE] 이미지 프롬프트 가이드 JSON 파싱 오류: {e}")
            _image_prompt_guide = {"default_style_guide": {}}
    
    return _image_prompt_guide


def build_image_prompt(
    image_description: str,
    image_style: str = "photo",
    style_guide: Optional[Dict[str, Any]] = None
) -> str:
    """
    이미지 생성 프롬프트를 구성합니다.
    
    Args:
        image_description: GPT가 생성한 완전한 이미지 프롬프트 (주제, 상세 묘사, 스타일, 제한 포함)
        image_style: 이미지 스타일 ('photo' 또는 'illustration')
        style_guide: 스타일 가이드 (선택사항, 현재는 사용하지 않음 - GPT 프롬프트를 우선시)
    
    Returns:
        구성된 이미지 생성 프롬프트 (GPT 프롬프트 + 선택한 스타일로 강제)
    """
    # GPT가 생성한 프롬프트를 그대로 사용 (이미 완전한 프롬프트 형식)
    cleaned_prompt = image_description
    
    # 선택한 스타일에 따라 처리
    if image_style == "illustration":
        # 애니메이션/일러스트 스타일인 경우
        # 사진 관련 키워드 제거
        photo_keywords_to_remove = [
            "사진", "photorealistic", "professional photography", "DSLR",
            "실사", "현실적", "realistic photo"
        ]
        
        for keyword in photo_keywords_to_remove:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            cleaned_prompt = pattern.sub("", cleaned_prompt)
        
        # 스타일 섹션을 애니메이션/일러스트 스타일로 강제
        if "스타일:" in cleaned_prompt or "style:" in cleaned_prompt.lower():
            style_pattern = re.compile(
                r'(스타일:|style:).*?(?=\n제한:|제한:|restrictions:|$)', 
                re.IGNORECASE | re.DOTALL
            )
            replacement = r'\1\n- 화풍: 부드럽고 깔끔한 애니메이션/일러스트 스타일 (smooth animation, clean illustration style)\n- 스타일: 픽사나 디즈니 애니메이션처럼 부드럽고 친근한 느낌\n- 조명: 부드러운 조명, 따뜻한 분위기\n- 색감: 밝고 생동감 있는 색감\n- 분위기: 밝고 친근하며 포근한 느낌'
            cleaned_prompt = style_pattern.sub(replacement, cleaned_prompt)
        
        # 마지막에 스타일 일관성 강조 문구 추가
        final_prompt = cleaned_prompt
        if not final_prompt.endswith(".") and not final_prompt.endswith("!"):
            final_prompt += "\n"
        
        final_prompt += "\n[중요] 반드시 부드럽고 깔끔한 애니메이션/일러스트 스타일로 생성하세요. 픽사나 디즈니 애니메이션처럼 부드럽고 친근한 느낌의 이미지로 생성해야 합니다. 사진 스타일은 절대 사용하지 마세요."
        
    else:
        # 사진 스타일인 경우 (기본값)
        # 애니메이션/일러스트 관련 키워드 제거
        style_keywords_to_remove = [
            "애니메이션", "일러스트", "만화", "픽사", "디즈니", "카툰",
            "animation", "illustration", "cartoon", "pixar", "disney",
            "3D render", "3D 렌더링", "일러스트레이션"
        ]
        
        for keyword in style_keywords_to_remove:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            cleaned_prompt = pattern.sub("", cleaned_prompt)
        
        # 연속된 공백 정리
        cleaned_prompt = re.sub(r'\s+', ' ', cleaned_prompt).strip()
        
        # 스타일 섹션을 사진 스타일로 강제
        if "스타일:" in cleaned_prompt or "style:" in cleaned_prompt.lower():
            style_pattern = re.compile(
                r'(스타일:|style:).*?(?=\n제한:|제한:|restrictions:|$)', 
                re.IGNORECASE | re.DOTALL
            )
            replacement = r'\1\n- 화풍: 고품질 사진 스타일 (photorealistic, professional photography)\n- 사진 스타일: DSLR 카메라로 촬영한 것처럼 현실적이고 선명한 이미지\n- 조명: 자연스러운 조명 또는 전문적인 스튜디오 조명\n- 색감: 자연스럽고 현실적인 색감\n- 분위기: 밝고 전문적인 느낌'
            cleaned_prompt = style_pattern.sub(replacement, cleaned_prompt)
        
        # 마지막에 스타일 일관성 강조 문구 추가
        final_prompt = cleaned_prompt
        if not final_prompt.endswith(".") and not final_prompt.endswith("!"):
            final_prompt += "\n"
        
        final_prompt += "\n[중요] 반드시 실제 사진처럼 보이는 현실적인 이미지로 생성하세요. 일러스트, 애니메이션, 만화, 3D 렌더링 스타일은 절대 사용하지 마세요. 모든 이미지는 고품질 사진 스타일(photorealistic, professional photography)로만 생성해야 합니다."
    
    return final_prompt


def generate_image(
    image_prompt: str,
    output_dir: Path,
    image_index: int = 1
) -> Optional[Path]:
    """
    Gemini API를 사용하여 이미지를 생성하고 저장합니다.
    
    Args:
        image_prompt: 이미지 생성 프롬프트
        output_dir: 이미지를 저장할 디렉토리 (images 폴더가 자동 생성됨)
        image_index: 이미지 인덱스 (파일명에 사용)
    
    Returns:
        생성된 이미지 파일 경로 (실패 시 None)
    """
    try:
        client = get_gemini_client()
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-image")
        
        logger.info(f"[IMAGE] 이미지 생성 시작: index={image_index}, prompt_length={len(image_prompt)}, model={model_name}")
        logger.debug(f"[IMAGE] 프롬프트: {image_prompt[:200]}...")  # 프롬프트 일부만 로깅
        
        # 이미지 생성 요청
        response = client.models.generate_content(
            model=model_name,
            contents=[image_prompt],
        )
        
        # 응답 디버깅
        logger.debug(f"[IMAGE] 응답 타입: {type(response)}")
        logger.debug(f"[IMAGE] 응답 parts 개수: {len(response.parts) if hasattr(response, 'parts') else 'N/A'}")
        
        # 응답에서 이미지 추출
        image_saved = False
        image_path = None
        
        if not hasattr(response, 'parts') or not response.parts:
            logger.warning(f"[IMAGE] 응답에 parts가 없습니다. response: {response}")
            # 응답 전체를 확인
            if hasattr(response, 'text'):
                logger.warning(f"[IMAGE] 응답 텍스트: {response.text}")
            return None
        
        for i, part in enumerate(response.parts):
            logger.debug(f"[IMAGE] Part {i}: type={type(part)}, has_inline_data={hasattr(part, 'inline_data') and part.inline_data is not None}, has_text={hasattr(part, 'text') and part.text is not None}")
            
            # 텍스트 응답이 있으면 로깅 (디버깅용)
            if hasattr(part, 'text') and part.text is not None:
                logger.info(f"[IMAGE] 텍스트 응답 수신: {part.text[:500]}...")
            
            # 이미지 데이터 확인 (우선순위: inline_data)
            if hasattr(part, 'inline_data') and part.inline_data is not None:
                logger.info(f"[IMAGE] 이미지 데이터 수신 완료: index={image_index}")
                try:
                    image = part.as_image()
                    
                    # images 디렉토리 생성
                    images_dir = output_dir / "images"
                    images_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 파일명 생성
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"image_{image_index}_{timestamp}.png"
                    image_path = images_dir / filename
                    
                    # 이미지 저장
                    image.save(str(image_path))
                    logger.info(f"[IMAGE] 이미지 저장 완료: {image_path}")
                    image_saved = True
                    break
                except Exception as img_error:
                    logger.error(f"[IMAGE] 이미지 처리 오류: {str(img_error)}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        if not image_saved:
            logger.warning(f"[IMAGE] 이미지 생성 실패: index={image_index} - 응답에 이미지 데이터가 없습니다.")
            logger.warning(f"[IMAGE] 응답 전체 정보: {response}")
            return None
        
        return image_path
        
    except Exception as e:
        logger.error(f"[IMAGE] 이미지 생성 오류: index={image_index}, error={str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

