"""
Gemini API를 사용하여 이미지를 생성하는 모듈
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from PIL import Image
import logging

# .env 파일 로드
load_dotenv()

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
    style_guide: Optional[Dict[str, Any]] = None
) -> str:
    """
    이미지 생성 프롬프트를 구성합니다.
    
    Args:
        image_description: 이미지에 대한 설명 (GPT가 제공한 마커의 설명 부분)
        style_guide: 스타일 가이드 (선택사항, 제공되지 않으면 기본 가이드 사용)
    
    Returns:
        구성된 이미지 생성 프롬프트
    """
    prompt_parts = []
    
    # 주제
    prompt_parts.append(f"주제:\n{image_description}")
    
    # 스타일 가이드가 있으면 사용, 없으면 기본 가이드 로드
    if style_guide:
        if "detail" in style_guide:
            detail_list = style_guide["detail"] if isinstance(style_guide["detail"], list) else [style_guide["detail"]]
            prompt_parts.append("\n상세 묘사:")
            prompt_parts.extend(detail_list)
        if "style" in style_guide:
            style_list = style_guide["style"] if isinstance(style_guide["style"], list) else [style_guide["style"]]
            prompt_parts.append("\n스타일:")
            prompt_parts.extend(style_list)
        if "restrictions" in style_guide:
            restrictions_list = style_guide["restrictions"] if isinstance(style_guide["restrictions"], list) else [style_guide["restrictions"]]
            prompt_parts.append("\n제한:")
            prompt_parts.extend(restrictions_list)
    else:
        # 기본 스타일 가이드 로드
        guide = load_image_prompt_guide()
        default_guide = guide.get("default_style_guide", {})
        
        if "detail" in default_guide:
            prompt_parts.append("\n상세 묘사:")
            prompt_parts.extend(default_guide["detail"])
        
        if "style" in default_guide:
            prompt_parts.append("\n스타일:")
            prompt_parts.extend(default_guide["style"])
        
        if "restrictions" in default_guide:
            prompt_parts.append("\n제한:")
            prompt_parts.extend(default_guide["restrictions"])
    
    return "\n".join(prompt_parts)


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
        
        logger.info(f"[IMAGE] 이미지 생성 시작: index={image_index}, prompt_length={len(image_prompt)}")
        
        # 이미지 생성 요청
        response = client.models.generate_content(
            model=model_name,
            contents=[image_prompt],
        )
        
        # 응답에서 이미지 추출
        image_saved = False
        image_path = None
        
        for part in response.parts:
            if part.inline_data is not None:
                logger.info(f"[IMAGE] 이미지 데이터 수신 완료: index={image_index}")
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
        
        if not image_saved:
            logger.warning(f"[IMAGE] 이미지 생성 실패: index={image_index} - 응답에 이미지 데이터가 없습니다.")
            return None
        
        return image_path
        
    except Exception as e:
        logger.error(f"[IMAGE] 이미지 생성 오류: index={image_index}, error={str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

