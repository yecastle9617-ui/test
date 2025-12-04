from playwright.sync_api import sync_playwright
import time
import random
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def human_type(page, element, text, min_delay=50, max_delay=150):
    """인간처럼 타이핑하는 함수 (랜덤 딜레이)"""
    element.click()
    time.sleep(random.uniform(0.1, 0.3))
    for char in text:
        element.type(char, delay=random.randint(min_delay, max_delay))
        time.sleep(random.uniform(0.01, 0.05))

def add_stealth_scripts(page):
    """봇 탐지 우회를 위한 JavaScript 주입"""
    page.add_init_script("""
        // webdriver 속성 제거
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Chrome 객체 추가
        window.chrome = {
            runtime: {}
        };
        
        // Permissions API 모킹
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Plugins 배열 추가
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Languages 설정
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ko-KR', 'ko', 'en-US', 'en']
        });
        
        // Platform 설정
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });
        
        // Hardware concurrency 설정
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
        
        // Device memory 설정
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
    """)

def login_naver():
    """
    네이버 로그인을 수행하는 함수
    직접 실행할 때만 호출됩니다.
    """
    # =======================
    # 네이버 로그인 정보 (환경 변수에서 가져오기)
    # =======================
    NAVER_ID = os.getenv("NAVER_ID")
    NAVER_PW = os.getenv("NAVER_PW")
    
    # 환경 변수 확인
    if not NAVER_ID or not NAVER_PW:
        raise ValueError("❌ 환경 변수가 설정되지 않았습니다. .env 파일에 NAVER_ID와 NAVER_PW를 설정해주세요.")
    
    try:
        with sync_playwright() as p:
            # 브라우저 실행 (실제 브라우저처럼 보이도록 설정)
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',  # 자동화 감지 비활성화
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                ]
            )
            
            # 실제 브라우저처럼 보이도록 컨텍스트 설정
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='ko-KR',
                timezone_id='Asia/Seoul',
                permissions=['geolocation', 'notifications'],
                extra_http_headers={
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                    'DNT': '1',
                }
            )

            page = context.new_page()
            
            # 봇 탐지 우회 스크립트 주입
            add_stealth_scripts(page)
            
            # 페이지 이동
            page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")
            time.sleep(random.uniform(1.5, 2.5))  # 랜덤 대기

            # 마우스를 자연스럽게 움직임
            page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            time.sleep(random.uniform(0.2, 0.5))

            # ID 입력 (인간처럼 타이핑)
            id_input = page.locator("input#id")
            id_input.click()
            time.sleep(random.uniform(0.2, 0.4))
            human_type(page, id_input, NAVER_ID, min_delay=80, max_delay=200)
            print("✔ ID 입력 완료")
            time.sleep(random.uniform(0.5, 1.0))

            # PW 입력 (인간처럼 타이핑)
            pw_input = page.locator("input#pw")
            pw_input.click()
            time.sleep(random.uniform(0.2, 0.4))
            human_type(page, pw_input, NAVER_PW, min_delay=80, max_delay=200)
            print("✔ 비밀번호 입력 완료")
            time.sleep(random.uniform(0.5, 1.0))

            # 엔터 키로 로그인 실행
            page.keyboard.press("Enter")
            print("✔ 엔터 키로 로그인 실행 완료")

            # 로그인 완료 대기 (리다이렉트 또는 페이지 변경 대기)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except:
                pass
            time.sleep(random.uniform(2, 3))

            # 로그인 성공 여부 확인 (자동 로그인 실패 시 수동 입력 대기)
            current_url = page.url
            if "nid.naver.com" in current_url:
                print("⚠ 자동 로그인 실패 또는 추가 인증 필요")
                print("👉 수동으로 로그인 완료 후 엔터를 입력하세요.")
                input()
            else:
                print("✔ 자동 로그인 성공")

            # 로그인 완료 후 쿠키 상태 저장
            context.storage_state(path="naver_state.json")
            print("✔ 로그인 세션 저장 완료 (naver_state.json)")
            
            browser.close()
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        raise


# 직접 실행할 때만 로그인 수행
if __name__ == "__main__":
    login_naver()
