#!/usr/bin/env python3
# naver_blog_to_pdf.py
# 사용법:
#   pip install playwright requests bs4
#   playwright install
#   python naver_blog_to_pdf.py

import os
import time
import hashlib
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import requests
from bs4 import BeautifulSoup

# ===== 설정 =====
TARGET_URL = "https://blog.naver.com/blogpython/223537381396"
OUTPUT_DIR = "output"
PDF_FILENAME = None  # None이면 자동 파일명 생성
VIEWPORT = {"width": 1200, "height": 1600}
WAIT_AFTER_LOAD = 1.0
SCROLL_PAUSES = [0.3, 0.3, 0.5]
ELEMENT_SELECTOR_CANDIDATES = [
    "div.se-main-container",
    "div#postViewArea",
    "div.blog2_content",
    "div.postView",
]

# ===== 유틸 함수 =====
def ensure_outdir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def make_safe_fname_from_url(url):
    parsed = urlparse(url)
    base = (parsed.netloc + parsed.path + (parsed.fragment or "") + (parsed.query or ""))
    h = hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]
    netloc = parsed.netloc.replace(":", "_")
    return f"{netloc}_{h}"

def fetch_og_meta(url):
    """OG 메타(title, description) 수집"""
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        og_title = soup.find("meta", property="og:title")
        og_desc  = soup.find("meta", property="og:description")
        return {
            "og_title": og_title["content"] if og_title and og_title.has_attr("content") else "",
            "og_desc":  og_desc["content"] if og_desc and og_desc.has_attr("content") else ""
        }
    except Exception:
        return {"og_title": "", "og_desc": ""}

def find_body_selector(page):
    for sel in ELEMENT_SELECTOR_CANDIDATES:
        try:
            if page.query_selector(sel):
                return sel
        except Exception:
            continue
    return None

# ===== 메인 캡처 함수 =====
def capture_blog_as_pdf(url, outdir, pdf_name=None):
    ensure_outdir(outdir)
    base = make_safe_fname_from_url(url)
    if not pdf_name:
        pdf_name = f"{base}.pdf"
    pdf_path = os.path.join(outdir, pdf_name)

    meta = fetch_og_meta(url)
    print(f"[INFO] 제목: {meta.get('og_title')}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport=VIEWPORT)
        page = context.new_page()

        print(f"[INFO] 페이지 열기: {url}")
        try:
            page.goto(url, timeout=40000, wait_until="load")
        except PWTimeout:
            print("[WARN] 로드 시간 초과, 그래도 계속 진행합니다.")

        time.sleep(WAIT_AFTER_LOAD)

        # 스크롤해서 lazy-load된 이미지 불러오기
        for pause in SCROLL_PAUSES:
            page.mouse.wheel(0, 2000)
            time.sleep(pause)

        # 본문 셀렉터 확인
        selector = find_body_selector(page)
        if selector:
            print(f"[INFO] 본문 셀렉터 탐지됨: {selector}")
            try:
                page.wait_for_selector(selector, timeout=5000)
            except PWTimeout:
                print("[WARN] 셀렉터 대기 실패, 전체 페이지 저장으로 진행")

        # PDF 생성
        print("[INFO] PDF 생성 중...")
        page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            display_header_footer=False,
            margin={"top": "0.5cm", "bottom": "0.5cm"}
        )

        print(f"[DONE] PDF 저장 완료: {pdf_path}")
        browser.close()

    # 메타정보 파일 저장
    meta_file = os.path.join(outdir, base + "_meta.txt")
    with open(meta_file, "w", encoding="utf-8") as m:
        m.write(f"source_url: {url}\n")
        m.write(f"captured_at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        m.write(f"og_title: {meta.get('og_title')}\n")
        m.write(f"og_desc: {meta.get('og_desc')}\n")
        m.write(f"pdf_path: {pdf_path}\n")

if __name__ == "__main__":
    capture_blog_as_pdf(TARGET_URL, OUTPUT_DIR, PDF_FILENAME)
