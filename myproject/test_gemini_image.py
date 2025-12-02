"""
Gemini 2.5 Flash 이미지 생성 테스트
"""

from google import genai
from google.genai import types
from PIL import Image
import os
from datetime import datetime
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()


def test_image_generation():
    """Gemini API를 사용한 이미지 생성 테스트"""
    
    # .env 파일에서 API 키와 모델 가져오기
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-image")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
    
    # 클라이언트 초기화
    client = genai.Client(api_key=api_key)
    
    # 기본 프롬프트
    prompt = "A beautiful sunset over a calm ocean with vibrant colors"
    
    print("=" * 60)
    print("Gemini 2.5 Flash 이미지 생성 테스트")
    print("=" * 60)
    print(f"모델: {model_name}")
    print(f"프롬프트: {prompt}\n")
    
    try:
        # 이미지 생성 요청
        print("이미지 생성 중...")
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt],
        )
        
        # 응답 처리
        image_saved = False
        for part in response.parts:
            if part.text is not None:
                print(f"\n텍스트 응답: {part.text}")
            elif part.inline_data is not None:
                print("\n✅ 이미지 데이터를 받았습니다!")
                image = part.as_image()
                
                # 이미지 저장 (프로젝트 상위 디렉토리에 생성)
                current_dir = os.path.dirname(os.path.abspath(__file__))  # myproject 디렉토리
                project_dir = os.path.dirname(current_dir)  # test 디렉토리
                parent_dir = os.path.dirname(project_dir)  # new_project 디렉토리 (상위)
                output_dir = os.path.join(parent_dir, "generated_images")
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = os.path.join(output_dir, f"generated_image_{timestamp}.png")
                
                image.save(image_path)
                print(f"✅ 이미지가 저장되었습니다: {image_path}")
                image_saved = True
        
        if not image_saved:
            print("\n⚠️  이미지가 생성되지 않았습니다.")
            print("응답에 이미지 데이터가 포함되어 있지 않습니다.")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_image_generation()

