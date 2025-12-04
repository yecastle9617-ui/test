from playwright.sync_api import sync_playwright
import time
import os

# =======================
# 설정값
# =======================
BLOG_ID = "dmalab"

TITLE_TEXT = "자동 입력된 제목 테스트입니다"

TAG_LIST = [
    "자동화",
]

IMAGE_LIST = [
    "test.jpg"
]


def post_blog(title: str = None, tags: list = None, images: list = None):
    """
    네이버 블로그에 글을 발행하는 함수
    
    Args:
        title: 블로그 제목 (기본값: TITLE_TEXT)
        tags: 태그 리스트 (기본값: TAG_LIST)
        images: 이미지 파일 리스트 (기본값: IMAGE_LIST)
    """
    title = title or TITLE_TEXT
    tags = tags or TAG_LIST
    images = images or IMAGE_LIST
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="naver_state.json")
        page = context.new_page()

        # 1) 상위 글쓰기 페이지 로드
        page.goto(f"https://blog.naver.com/{BLOG_ID}?Redirect=Write")
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)

        # 2) iframe src 추출
        iframe_el = page.locator("iframe#mainFrame")
        iframe_src = iframe_el.get_attribute("src")

        editor_url = "https://blog.naver.com" + iframe_src
        print("에디터 iframe URL:", editor_url)

        # 3) iframe 페이지로 직접 이동 (여기가 진짜 작업 공간)
        page.goto(editor_url)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        print("✔ iframe 내부 페이지 직접 접속 완료")

        # ===============================================================
        # 제목 입력
        # ===============================================================
        title_box = page.locator("div.se-title-text")
        title_box.click()
        page.keyboard.type(title, delay=20)
        print("제목 입력 완료")

        # ===============================================================
        # 여러 이미지 업로드
        # ===============================================================
        try:
            with page.expect_file_chooser() as fc_info:
                page.locator("button.se-image-toolbar-button").click()

            chooser = fc_info.value
            abs_files = [os.path.abspath(file) for file in images]
            chooser.set_files(abs_files)

            print(f"{len(images)}개의 이미지 업로드 완료")
        except Exception as e:
            print("이미지 업로드 실패:", e)

        time.sleep(1)

        # ===============================================================
        # 발행 모달 열기
        # ===============================================================
        publish_btn = page.locator("button.publish_btn__m9KHH")
        publish_btn.click()
        print("발행 모달 열림")

        time.sleep(1)

        # ===============================================================
        # 태그 입력
        # ===============================================================
        for tag in tags:
            tag_input = page.locator("input#tag-input")
            tag_input.click()
            tag_input.fill(tag)
            page.keyboard.press("Enter")
            time.sleep(0.2)

        print("태그 입력 완료")

        # ===============================================================
        # 최종 발행
        # ===============================================================
        final_btn = page.locator("button.confirm_btn__WEaBq[data-testid='seOnePublishBtn']")
        final_btn.click()
        print("🎉 블로그 발행 완료!")

        input("브라우저 종료하려면 엔터 → ")


# 직접 실행할 때만 블로그 포스팅 수행
if __name__ == "__main__":
    post_blog()
