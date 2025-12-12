"""
FastAPI 서버 애플리케이션
네이버 블로그 크롤링 및 키워드 분석 API
"""

import sys
from pathlib import Path
import os
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from urllib.parse import quote, unquote, urlparse
import hashlib
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에서)
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent  # DMaLab 디렉토리
load_dotenv(project_root / ".env")

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import requests
import zipfile
import base64
import mimetypes
import json
import uuid
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum

from crawler.naver_crawler import NaverCrawler
from analyzer.morpheme_analyzer import MorphemeAnalyzer
from blog.gpt_generator import (
    generate_blog_content,
    save_blog_json,
    get_create_naver_directory,
    generate_blog_ideas,
)

# 로거 설정
logger = logging.getLogger("dmalab.api")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# FastAPI 앱 생성
app = FastAPI(
    title="네이버 블로그 크롤링 API",
    description="네이버 블로그 검색, 크롤링 및 키워드 분석 API",
    version="1.0.0"
)

# 이미지 저장 기본 디렉토리 설정 (naver_crawler 하위)
current_dir = Path(__file__).parent
project_dir = current_dir.parent
NAVER_CRAWLER_DIR = project_dir / "naver_crawler"
NAVER_CRAWLER_DIR.mkdir(parents=True, exist_ok=True)

# data 디렉토리 설정
DATA_DIR = project_dir / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# blog/create_naver 디렉토리 설정 (GPT 자동 생성용)

# ===== 사용량 제한 시스템 =====
# Admin IP 목록 (환경 변수에서 읽기, 쉼표로 구분)
ADMIN_IPS = os.getenv("ADMIN_IPS", "").split(",")
ADMIN_IPS = [ip.strip() for ip in ADMIN_IPS if ip.strip()]

# 일일 사용량 제한 (기본 3회)
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "3"))

# 상위 블로그 분석 일일 제한 (기본 5회)
REFERENCE_ANALYSIS_LIMIT = int(os.getenv("REFERENCE_ANALYSIS_LIMIT", "5"))

# 블로그 아이디어 생성 일일 제한 (기본 3회)
BLOG_IDEAS_LIMIT = int(os.getenv("BLOG_IDEAS_LIMIT", "3"))

# 사용량 추적 JSON 파일 경로
USAGE_DATA_FILE = DATA_DIR / "usage_data.json"

# ===== 사용량 데이터 JSON 파일 관리 =====
def load_usage_data() -> Dict[str, Any]:
    """JSON 파일에서 사용량 데이터를 로드합니다."""
    if not USAGE_DATA_FILE.exists():
        return {
            "blog_generation": {},
            "reference_analysis": {},
            "blog_ideas": {},
            "first_seen": {}  # IP별 첫 접속 시간
        }
    
    try:
        with open(USAGE_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # datetime 문자열을 datetime 객체로 변환
        for tracker_name in ["blog_generation", "reference_analysis", "blog_ideas"]:
            if tracker_name in data:
                for ip, usage_info in data[tracker_name].items():
                    if "reset_time" in usage_info and isinstance(usage_info["reset_time"], str):
                        usage_info["reset_time"] = datetime.fromisoformat(usage_info["reset_time"])
        
        return data
    except Exception as e:
        logger.exception(f"[USAGE_DATA] JSON 파일 로드 오류: {e}")
        return {
            "blog_generation": {},
            "reference_analysis": {},
            "blog_ideas": {},
            "first_seen": {}
        }

def save_usage_data(data: Dict[str, Any]):
    """사용량 데이터를 JSON 파일에 저장합니다."""
    try:
        # 기존 JSON 파일에서 first_seen 데이터 보존
        existing_data = load_usage_data()
        existing_first_seen = existing_data.get("first_seen", {})
        
        # 전달받은 data에 first_seen이 있으면 병합 (기존 데이터 우선)
        if "first_seen" in data:
            existing_first_seen.update(data["first_seen"])
        
        # datetime 객체를 문자열로 변환
        save_data = {
            "blog_generation": {},
            "reference_analysis": {},
            "blog_ideas": {},
            "first_seen": existing_first_seen
        }
        
        # 각 트래커의 데이터를 복사 (datetime을 문자열로 변환)
        for tracker_name in ["blog_generation", "reference_analysis", "blog_ideas"]:
            if tracker_name in data:
                for user_id, usage_info in data[tracker_name].items():
                    reset_time = usage_info.get("reset_time")
                    if isinstance(reset_time, datetime):
                        reset_time = reset_time.isoformat()
                    save_data[tracker_name][user_id] = {
                        "count": usage_info.get("count", 0),
                        "reset_time": reset_time
                    }
        
        # JSON 파일에 저장
        with open(USAGE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"[USAGE_DATA] 사용량 데이터 저장 완료")
    except Exception as e:
        logger.exception(f"[USAGE_DATA] JSON 파일 저장 오류: {e}")

def record_first_seen(ip: str):
    """IP의 첫 접속 시간을 기록합니다."""
    data = load_usage_data()
    if "first_seen" not in data:
        data["first_seen"] = {}
    
    if ip not in data["first_seen"]:
        data["first_seen"][ip] = datetime.now().isoformat()
        # JSON 파일에 저장
        try:
            with open(USAGE_DATA_FILE, 'r', encoding='utf-8') as f:
                full_data = json.load(f)
            full_data["first_seen"] = data["first_seen"]
            with open(USAGE_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[USAGE_DATA] 첫 접속 시간 기록 오류: {e}")

# ===== 비동기 작업 큐 시스템 =====
class TaskStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"  # 대기 중
    RUNNING = "running"   # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"    # 실패

# 작업 상태 추적 (메모리 기반)
# 구조: {task_id: {"status": TaskStatus, "progress": int, "result": Any, "error": str, "created_at": datetime, "ip": str}}
task_status_tracker: Dict[str, Dict[str, Any]] = {}

# 작업 큐 (IP별로 최대 동시 실행 작업 수 제한)
# 구조: {ip: [task_id1, task_id2, ...]}
task_queues: Dict[str, List[str]] = defaultdict(list)

# IP별 최대 동시 실행 작업 수 (기본 1개)
MAX_CONCURRENT_TASKS_PER_IP = int(os.getenv("MAX_CONCURRENT_TASKS_PER_IP", "1"))

def create_task_id() -> str:
    """고유한 작업 ID를 생성합니다."""
    return str(uuid.uuid4())

def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """작업 상태를 조회합니다."""
    return task_status_tracker.get(task_id)

def update_task_status(task_id: str, status: TaskStatus, progress: int = 0, result: Any = None, error: str = None):
    """작업 상태를 업데이트합니다."""
    if task_id not in task_status_tracker:
        return
    
    task_status_tracker[task_id].update({
        "status": status.value,
        "progress": progress,
        "result": result,
        "error": error,
        "updated_at": datetime.now().isoformat()
    })

def can_start_task(ip: str) -> bool:
    """해당 IP가 새로운 작업을 시작할 수 있는지 확인합니다."""
    running_tasks = [
        task_id for task_id, task_info in task_status_tracker.items()
        if task_info.get("ip") == ip and task_info.get("status") == TaskStatus.RUNNING.value
    ]
    return len(running_tasks) < MAX_CONCURRENT_TASKS_PER_IP

async def run_task_async(task_id: str, task_func, *args, **kwargs):
    """작업을 비동기로 실행합니다."""
    try:
        update_task_status(task_id, TaskStatus.RUNNING, progress=10)
        
        # 동기 함수를 비동기로 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, task_func, *args, **kwargs)
        
        update_task_status(task_id, TaskStatus.COMPLETED, progress=100, result=result)
        logger.info(f"[TASK] 작업 완료: task_id={task_id}")
        
    except Exception as e:
        logger.exception(f"[TASK] 작업 실패: task_id={task_id}, error={e}")
        update_task_status(task_id, TaskStatus.FAILED, progress=0, error=str(e))
    finally:
        # 작업 큐에서 제거
        task_info = task_status_tracker.get(task_id)
        if task_info:
            ip = task_info.get("ip")
            if ip and task_id in task_queues[ip]:
                task_queues[ip].remove(task_id)

# 작업 상태 조회 API 모델
class TaskStatusResponse(BaseModel):
    """작업 상태 응답 모델"""
    task_id: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, http_request: Request):
    """
    작업 상태를 조회합니다.
    """
    try:
        task_info = get_task_status(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        # IP 확인 (본인의 작업만 조회 가능, Admin은 모든 작업 조회 가능)
        client_ip = get_client_ip(http_request)
        task_ip = task_info.get("ip")
        if not is_admin_ip(client_ip) and task_ip != client_ip:
            raise HTTPException(status_code=403, detail="다른 사용자의 작업은 조회할 수 없습니다.")
        
        return TaskStatusResponse(
            task_id=task_id,
            status=task_info.get("status", "unknown"),
            progress=task_info.get("progress", 0),
            result=task_info.get("result"),
            error=task_info.get("error"),
            created_at=task_info.get("created_at", ""),
            updated_at=task_info.get("updated_at")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[TASK] 작업 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"작업 상태 조회 중 오류 발생: {str(e)}")

def get_client_ip(request: Request) -> str:
    """클라이언트 IP 주소를 가져옵니다."""
    # X-Forwarded-For 헤더 확인 (프록시/로드밸런서 뒤에 있을 경우)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 첫 번째 IP가 실제 클라이언트 IP
        return forwarded_for.split(",")[0].strip()
    
    # X-Real-IP 헤더 확인
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # 직접 연결인 경우
    if request.client:
        return request.client.host
    
    return "unknown"

def get_user_identifier(request: Request) -> str:
    """
    IP 주소와 브라우저 고유 ID를 조합하여 사용자 식별자를 생성합니다.
    같은 IP에서도 다른 브라우저/기기로 구분할 수 있습니다.
    """
    ip = get_client_ip(request)
    client_id = request.headers.get("X-Client-ID", "").strip()
    
    # Client-ID가 있으면 IP와 조합하여 사용
    if client_id:
        # IP와 Client-ID를 조합 (해시로 변환하여 안전하게 저장)
        combined = f"{ip}:{client_id}"
        # MD5 해시로 변환 (너무 길지 않게)
        identifier = hashlib.md5(combined.encode()).hexdigest()
        return identifier
    else:
        # Client-ID가 없으면 IP만 사용 (하위 호환성)
        return ip

def is_admin_ip(ip: str) -> bool:
    """IP가 admin IP 목록에 있는지 확인합니다."""
    if not ADMIN_IPS:
        return False
    return ip in ADMIN_IPS

def check_usage_limit(request: Request, limit: int = DAILY_LIMIT) -> tuple[bool, str]:
    """
    사용량 제한을 확인합니다.
    
    Returns:
        (is_allowed, message): 허용 여부와 메시지
    """
    ip = get_client_ip(request)
    user_id = get_user_identifier(request)
    
    # Admin IP는 무제한 사용 가능
    if is_admin_ip(ip):
        logger.info(f"[USAGE] Admin IP {ip} - 무제한 사용 허용")
        return True, "admin"
    
    # 첫 접속 시간 기록 (IP 기준으로 기록)
    record_first_seen(ip)
    
    # JSON 파일에서 사용량 데이터 로드
    data = load_usage_data()
    if "blog_generation" not in data:
        data["blog_generation"] = {}
    
    now = datetime.now()
    
    # 사용자 사용량 정보 가져오기
    if user_id not in data["blog_generation"]:
        data["blog_generation"][user_id] = {
            "count": 0,
            "reset_time": (now + timedelta(days=1)).isoformat()
        }
    
    usage_info = data["blog_generation"][user_id]
    reset_time_str = usage_info.get("reset_time")
    reset_time = datetime.fromisoformat(reset_time_str) if isinstance(reset_time_str, str) else reset_time_str
    count = usage_info.get("count", 0)
    
    # 리셋 시간이 지났으면 카운트 초기화
    if now > reset_time:
        count = 0
        reset_time = now + timedelta(days=1)
        logger.info(f"[USAGE] User {user_id} (IP: {ip}) - 일일 사용량 리셋")
    
    # 사용량 확인
    if count >= limit:
        remaining_time = reset_time - now
        hours = int(remaining_time.total_seconds() / 3600)
        minutes = int((remaining_time.total_seconds() % 3600) / 60)
        message = f"일일 사용량 제한({limit}회)에 도달했습니다. 다음 리셋까지 약 {hours}시간 {minutes}분 남았습니다."
        logger.warning(f"[USAGE] User {user_id} (IP: {ip}) - 사용량 제한 도달 ({count}/{limit})")
        # 현재 상태 저장 (리셋된 경우)
        data["blog_generation"][user_id] = {
            "count": count,
            "reset_time": reset_time.isoformat()
        }
        save_usage_data(data)
        return False, message
    
    # 사용량 증가
    count += 1
    remaining = limit - count
    logger.info(f"[USAGE] User {user_id} (IP: {ip}) - 사용량: {count}/{limit} (남은 횟수: {remaining})")
    
    # JSON 파일에 저장
    data["blog_generation"][user_id] = {
        "count": count,
        "reset_time": reset_time.isoformat()
    }
    save_usage_data(data)
    return True, f"사용량: {count}/{limit} (남은 횟수: {remaining})"

def get_usage_info(request: Request) -> Dict[str, Any]:
    """
    현재 사용자의 사용량 정보를 반환합니다.
    
    Returns:
        사용량 정보 딕셔너리
    """
    ip = get_client_ip(request)
    user_id = get_user_identifier(request)
    is_admin = is_admin_ip(ip)
    now = datetime.now()
    
    # JSON 파일에서 사용량 데이터 로드
    data = load_usage_data()
    
    # 블로그 생성 사용량
    if "blog_generation" not in data:
        data["blog_generation"] = {}
    if user_id not in data["blog_generation"]:
        data["blog_generation"][user_id] = {
            "count": 0,
            "reset_time": (now + timedelta(days=1)).isoformat()
        }
    usage_info = data["blog_generation"][user_id]
    reset_time_str = usage_info.get("reset_time")
    reset_time = datetime.fromisoformat(reset_time_str) if isinstance(reset_time_str, str) else reset_time_str
    count = usage_info.get("count", 0)
    if now > reset_time:
        count = 0
        reset_time = now + timedelta(days=1)
    remaining_time = reset_time - now
    
    # 상위 블로그 분석 사용량
    if "reference_analysis" not in data:
        data["reference_analysis"] = {}
    if user_id not in data["reference_analysis"]:
        data["reference_analysis"][user_id] = {
            "count": 0,
            "reset_time": (now + timedelta(days=1)).isoformat()
        }
    ref_usage_info = data["reference_analysis"][user_id]
    ref_reset_time_str = ref_usage_info.get("reset_time")
    ref_reset_time = datetime.fromisoformat(ref_reset_time_str) if isinstance(ref_reset_time_str, str) else ref_reset_time_str
    ref_count = ref_usage_info.get("count", 0)
    if now > ref_reset_time:
        ref_count = 0
        ref_reset_time = now + timedelta(days=1)
    ref_remaining_time = ref_reset_time - now
    
    # 블로그 아이디어 생성 사용량
    if "blog_ideas" not in data:
        data["blog_ideas"] = {}
    if user_id not in data["blog_ideas"]:
        data["blog_ideas"][user_id] = {
            "count": 0,
            "reset_time": (now + timedelta(days=1)).isoformat()
        }
    ideas_usage_info = data["blog_ideas"][user_id]
    ideas_reset_time_str = ideas_usage_info.get("reset_time")
    ideas_reset_time = datetime.fromisoformat(ideas_reset_time_str) if isinstance(ideas_reset_time_str, str) else ideas_reset_time_str
    ideas_count = ideas_usage_info.get("count", 0)
    if now > ideas_reset_time:
        ideas_count = 0
        ideas_reset_time = now + timedelta(days=1)
    ideas_remaining_time = ideas_reset_time - now
    
    return {
        "is_admin": is_admin,
        "blog_generation": {
            "used": count,
            "limit": DAILY_LIMIT if not is_admin else -1,  # -1은 무제한
            "remaining": DAILY_LIMIT - count if not is_admin else -1,
            "reset_in_hours": int(remaining_time.total_seconds() / 3600) if not is_admin else 0,
            "reset_in_minutes": int((remaining_time.total_seconds() % 3600) / 60) if not is_admin else 0
        },
        "reference_analysis": {
            "used": ref_count,
            "limit": REFERENCE_ANALYSIS_LIMIT if not is_admin else -1,
            "remaining": REFERENCE_ANALYSIS_LIMIT - ref_count if not is_admin else -1,
            "reset_in_hours": int(ref_remaining_time.total_seconds() / 3600) if not is_admin else 0,
            "reset_in_minutes": int((ref_remaining_time.total_seconds() % 3600) / 60) if not is_admin else 0
        },
        "blog_ideas": {
            "used": ideas_count,
            "limit": BLOG_IDEAS_LIMIT if not is_admin else -1,
            "remaining": BLOG_IDEAS_LIMIT - ideas_count if not is_admin else -1,
            "reset_in_hours": int(ideas_remaining_time.total_seconds() / 3600) if not is_admin else 0,
            "reset_in_minutes": int((ideas_remaining_time.total_seconds() % 3600) / 60) if not is_admin else 0
        }
    }

def check_reference_analysis_limit(request: Request, limit: int = REFERENCE_ANALYSIS_LIMIT) -> tuple[bool, str]:
    """
    상위 블로그 분석 사용량 제한을 확인합니다.
    
    Returns:
        (is_allowed, message): 허용 여부와 메시지
    """
    ip = get_client_ip(request)
    user_id = get_user_identifier(request)
    
    # Admin IP는 무제한 사용 가능
    if is_admin_ip(ip):
        logger.info(f"[REFERENCE] Admin IP {ip} - 무제한 사용 허용")
        return True, "admin"
    
    # 첫 접속 시간 기록 (IP 기준으로 기록)
    record_first_seen(ip)
    
    # JSON 파일에서 사용량 데이터 로드
    data = load_usage_data()
    if "reference_analysis" not in data:
        data["reference_analysis"] = {}
    
    now = datetime.now()
    
    # 사용자 사용량 정보 가져오기
    if user_id not in data["reference_analysis"]:
        data["reference_analysis"][user_id] = {
            "count": 0,
            "reset_time": (now + timedelta(days=1)).isoformat()
        }
    
    usage_info = data["reference_analysis"][user_id]
    reset_time_str = usage_info.get("reset_time")
    reset_time = datetime.fromisoformat(reset_time_str) if isinstance(reset_time_str, str) else reset_time_str
    count = usage_info.get("count", 0)
    
    # 리셋 시간이 지났으면 카운트 초기화
    if now > reset_time:
        count = 0
        reset_time = now + timedelta(days=1)
        logger.info(f"[REFERENCE] User {user_id} (IP: {ip}) - 일일 사용량 리셋")
    
    # 사용량 확인
    if count >= limit:
        remaining_time = reset_time - now
        hours = int(remaining_time.total_seconds() / 3600)
        minutes = int((remaining_time.total_seconds() % 3600) / 60)
        message = f"상위 블로그 분석 일일 사용량 제한({limit}회)에 도달했습니다. 다음 리셋까지 약 {hours}시간 {minutes}분 남았습니다."
        logger.warning(f"[REFERENCE] User {user_id} (IP: {ip}) - 사용량 제한 도달 ({count}/{limit})")
        # 현재 상태 저장 (리셋된 경우)
        data["reference_analysis"][user_id] = {
            "count": count,
            "reset_time": reset_time.isoformat()
        }
        save_usage_data(data)
        return False, message
    
    # 사용량 증가
    count += 1
    remaining = limit - count
    logger.info(f"[REFERENCE] User {user_id} (IP: {ip}) - 상위 블로그 분석 사용량: {count}/{limit} (남은 횟수: {remaining})")
    
    # JSON 파일에 저장
    data["reference_analysis"][user_id] = {
        "count": count,
        "reset_time": reset_time.isoformat()
    }
    save_usage_data(data)
    return True, f"상위 블로그 분석 사용량: {count}/{limit} (남은 횟수: {remaining})"


def check_blog_ideas_limit(request: Request, limit: int = BLOG_IDEAS_LIMIT) -> tuple[bool, str]:
    """
    블로그 아이디어 생성 사용량 제한을 확인합니다.
    
    Returns:
        (is_allowed, message): 허용 여부와 메시지
    """
    ip = get_client_ip(request)
    user_id = get_user_identifier(request)
    
    # Admin IP는 무제한 사용 가능
    if is_admin_ip(ip):
        logger.info(f"[BLOG_IDEAS] Admin IP {ip} - 무제한 사용 허용")
        return True, "admin"
    
    # 첫 접속 시간 기록 (IP 기준으로 기록)
    record_first_seen(ip)
    
    # JSON 파일에서 사용량 데이터 로드
    data = load_usage_data()
    if "blog_ideas" not in data:
        data["blog_ideas"] = {}
    
    now = datetime.now()
    
    # 사용자 사용량 정보 가져오기
    if user_id not in data["blog_ideas"]:
        data["blog_ideas"][user_id] = {
            "count": 0,
            "reset_time": (now + timedelta(days=1)).isoformat()
        }
    
    usage_info = data["blog_ideas"][user_id]
    reset_time_str = usage_info.get("reset_time")
    reset_time = datetime.fromisoformat(reset_time_str) if isinstance(reset_time_str, str) else reset_time_str
    count = usage_info.get("count", 0)
    
    # 리셋 시간이 지났으면 카운트 초기화
    if now > reset_time:
        count = 0
        reset_time = now + timedelta(days=1)
        logger.info(f"[BLOG_IDEAS] User {user_id} (IP: {ip}) - 일일 사용량 리셋")
    
    # 사용량 확인
    if count >= limit:
        remaining_time = reset_time - now
        hours = int(remaining_time.total_seconds() / 3600)
        minutes = int((remaining_time.total_seconds() % 3600) / 60)
        message = f"블로그 아이디어 생성 일일 사용량 제한({limit}회)에 도달했습니다. 다음 리셋까지 약 {hours}시간 {minutes}분 남았습니다."
        logger.warning(f"[BLOG_IDEAS] User {user_id} (IP: {ip}) - 사용량 제한 도달 ({count}/{limit})")
        # 현재 상태 저장 (리셋된 경우)
        data["blog_ideas"][user_id] = {
            "count": count,
            "reset_time": reset_time.isoformat()
        }
        save_usage_data(data)
        return False, message
    
    # 사용량 증가
    count += 1
    remaining = limit - count
    logger.info(f"[BLOG_IDEAS] User {user_id} (IP: {ip}) - 블로그 아이디어 생성 사용량: {count}/{limit} (남은 횟수: {remaining})")
    
    # JSON 파일에 저장
    data["blog_ideas"][user_id] = {
        "count": count,
        "reset_time": reset_time.isoformat()
    }
    save_usage_data(data)
    return True, f"블로그 아이디어 생성 사용량: {count}/{limit} (남은 횟수: {remaining})"

# blog/create_naver 디렉토리 설정 (GPT 자동 생성용)
CREATE_NAVER_DIR = DATA_DIR / "blog" / "create_naver"
CREATE_NAVER_DIR.mkdir(parents=True, exist_ok=True)

# blog/export_blog 디렉토리 설정 (에디터 역포맷/내보내기용)
EXPORT_BLOG_DIR = DATA_DIR / "blog" / "export_blog"
EXPORT_BLOG_DIR.mkdir(parents=True, exist_ok=True)

# blog/create_blog_prompt 디렉토리 설정 (블로그 아이디어 TXT/ZIP 저장용)
CREATE_BLOG_PROMPT_DIR = DATA_DIR / "blog" / "create_blog_prompt"
CREATE_BLOG_PROMPT_DIR.mkdir(parents=True, exist_ok=True)

# 임시 저장 디렉토리 설정 (IP 기반)
DRAFT_DIR = DATA_DIR / "blog" / "drafts"
DRAFT_DIR.mkdir(parents=True, exist_ok=True)

# blog/image_downloads 디렉토리 설정 (이미지 ZIP 다운로드용)
IMAGE_DOWNLOADS_DIR = DATA_DIR / "blog" / "image_downloads"
IMAGE_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# 정적 파일 서빙 (naver_crawler 디렉토리 전체)
app.mount("/static/naver_crawler", StaticFiles(directory=str(NAVER_CRAWLER_DIR)), name="static_naver_crawler")

# 정적 파일 서빙 (blog/create_naver 디렉토리 전체)
app.mount("/static/blog/create_naver", StaticFiles(directory=str(CREATE_NAVER_DIR)), name="static_create_naver")

# 정적 파일 서빙 (blog/export_blog 디렉토리 전체)
app.mount("/static/blog/export_blog", StaticFiles(directory=str(EXPORT_BLOG_DIR)), name="static_export_blog")

# 정적 파일 서빙 (blog/image_downloads 디렉토리 전체)
app.mount("/static/blog/image_downloads", StaticFiles(directory=str(IMAGE_DOWNLOADS_DIR)), name="static_image_downloads")

# 정적 파일 서빙 (blog/create_blog_prompt 디렉토리 전체)
app.mount(
    "/static/blog/create_blog_prompt",
    StaticFiles(directory=str(CREATE_BLOG_PROMPT_DIR)),
    name="static_create_blog_prompt",
)

# CORS 설정 (필요시 수정)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Pydantic 모델 정의 =====

class BlogInfo(BaseModel):
    """블로그 정보 모델"""
    title: str
    url: str


class SearchRequest(BaseModel):
    """검색 요청 모델"""
    keyword: str = Field(..., description="검색 키워드")
    n: int = Field(default=3, ge=1, le=10, description="가져올 블로그 개수 (1-10)")


class SearchResponse(BaseModel):
    """검색 응답 모델"""
    keyword: str
    count: int
    blogs: List[BlogInfo]


class CrawlRequest(BaseModel):
    """크롤링 요청 모델 (단일)"""
    url: str = Field(..., description="블로그 URL")
    title: Optional[str] = Field(None, description="블로그 제목 (선택사항)")


class CrawlBulkRequest(BaseModel):
    """크롤링 요청 모델 (리스트)"""
    urls: List[str] = Field(..., description="크롤링할 블로그 URL 리스트")
    titles: Optional[List[Optional[str]]] = Field(None, description="블로그 제목 리스트 (선택사항, urls와 같은 길이)")


class CrawlResponse(BaseModel):
    """크롤링 응답 모델"""
    success: bool
    title: Optional[str] = None
    url: str
    body_text: Optional[str] = None
    body_length: Optional[int] = None
    image_urls: Optional[List[str]] = None
    link_urls: Optional[List[str]] = None
    txt_path: Optional[str] = None
    error: Optional[str] = None


class CrawlBulkResponse(BaseModel):
    """크롤링 응답 모델 (리스트)"""
    total_count: int
    success_count: int
    results: List[CrawlResponse]


class AnalyzeRequest(BaseModel):
    """키워드 분석 요청 모델"""
    text: str = Field(..., description="분석할 텍스트")
    top_n: int = Field(default=20, ge=1, le=100, description="상위 N개 키워드")
    min_length: int = Field(default=2, ge=1, description="최소 키워드 길이")
    min_count: int = Field(default=2, ge=1, description="최소 출현 횟수")


class KeywordStat(BaseModel):
    """키워드 통계 모델"""
    keyword: str
    count: int
    rank: int


class AnalyzeResponse(BaseModel):
    """키워드 분석 응답 모델"""
    success: bool
    total_keywords: int
    keywords: List[KeywordStat]
    excel_path: Optional[str] = None
    error: Optional[str] = None


class ProcessRequest(BaseModel):
    """전체 처리 요청 모델 (검색 + 크롤링 + 분석)"""
    keyword: str = Field(..., description="검색 키워드")
    n: int = Field(default=3, ge=1, le=10, description="처리할 블로그 개수")
    analyze: bool = Field(default=True, description="키워드 분석 수행 여부")
    top_n: int = Field(default=20, ge=1, le=100, description="상위 N개 키워드")
    min_length: int = Field(default=2, ge=1, description="최소 키워드 길이")
    min_count: int = Field(default=2, ge=1, description="최소 출현 횟수")


class ProcessResult(BaseModel):
    """단일 블로그 처리 결과"""
    rank: int
    title: str
    url: str
    success: bool
    body_text: Optional[str] = None
    body_length: Optional[int] = None
    image_urls: Optional[List[str]] = None
    link_urls: Optional[List[str]] = None
    txt_path: Optional[str] = None
    excel_path: Optional[str] = None
    keywords: Optional[List[KeywordStat]] = None
    error: Optional[str] = None


class ProcessResponse(BaseModel):
    """전체 처리 응답 모델"""
    keyword: str
    output_dir: str
    total_count: int
    success_count: int
    results: List[ProcessResult]


class GenerateBlogRequest(BaseModel):
    """GPT 블로그 생성 요청 모델"""
    keywords: str = Field(..., description="블로그 글의 주요 키워드")
    category: str = Field(default="일반", description="카테고리")
    blog_level: str = Field(default="mid", description="블로그 레벨 (new, mid, high)")
    ban_words: Optional[List[str]] = Field(default=None, description="금칙어 목록")
    analysis_json: Optional[Dict[str, Any]] = Field(default=None, description="상위 글 분석 JSON")
    use_auto_reference: bool = Field(
        default=False,
        description="키워드 기반 상위 블로그 자동 수집·분석 사용 여부"
    )
    reference_count: int = Field(
        default=3,
        ge=1,
        le=10,
        description="자동 수집할 상위 블로그 개수 (1~10)"
    )
    manual_reference_urls: Optional[List[str]] = Field(
        default=None,
        description="사용자가 직접 추가한 참고 블로그 URL 목록"
    )
    external_links: Optional[List[str]] = Field(
        default=None,
        description="본문에 자연스럽게 삽입할 외부 링크 목록 (new 레벨에서는 무시됨)"
    )
    generate_images: bool = Field(
        default=True,
        description="이미지 마커에 대해 자동으로 이미지 생성할지 여부"
    )
    image_style: str = Field(
        default="photo",
        description="이미지 스타일: 'photo' (실사/사진 스타일) 또는 'illustration' (애니메이션/일러스트 스타일)"
    )
    model: str = Field(default="gpt-4o", description="사용할 GPT 모델")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="생성 온도")
    save_json: bool = Field(default=True, description="JSON 파일로 저장 여부")


class GenerateBlogResponse(BaseModel):
    """GPT 블로그 생성 응답 모델"""
    success: bool
    blog_content: Optional[Dict[str, Any]] = None
    json_path: Optional[str] = None
    error: Optional[str] = None
    image_retry_count: Optional[int] = None


class ExportImageItem(BaseModel):
    """에디터에서 추출된 이미지 정보"""
    index: int
    src: str
    style: Optional[str] = None
    # 썸네일 여부 (프론트에서 선택한 경우 true)
    is_thumbnail: Optional[bool] = None
    caption: Optional[str] = None


class ExportBlogRequest(BaseModel):
    """에디터 내용을 기반으로 네이버 발행용 파일을 생성하는 요청 모델"""
    blog_content: Dict[str, Any]
    images: List[ExportImageItem]


class ExportBlogResponse(BaseModel):
    success: bool
    zip_path: Optional[str] = None
    error: Optional[str] = None


class DownloadImagesRequest(BaseModel):
    """이미지 다운로드 요청 모델"""
    image_paths: List[str] = Field(..., description="다운로드할 이미지 경로 리스트 (상대 경로)")


class DownloadImagesResponse(BaseModel):
    """이미지 다운로드 응답 모델"""
    success: bool
    zip_path: Optional[str] = None
    error: Optional[str] = None


class GenerateBlogIdeasRequest(BaseModel):
    """블로그 제목/프롬프트 아이디어 생성 요청 모델"""
    keyword: str = Field(..., description="대표 키워드")
    topic: str = Field(..., description="글의 주제/카테고리")
    blog_profile: str = Field(..., description="현재 내 블로그의 특징(톤, 타깃, 운영 스타일 등)")
    extra_prompt: Optional[str] = Field(default=None, description="추가로 강조하고 싶은 프롬프트 내용 (선택)")
    count: int = Field(default=3, ge=1, le=10, description="생성할 아이디어 개수 (1~10)")
    model: str = Field(default="gpt-4o-mini", description="사용할 GPT 모델")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="생성 온도")
    save_files: bool = Field(default=True, description="각 아이디어를 개별 텍스트 파일로 저장할지 여부")
    auto_topic: bool = Field(default=False, description="주제/방향을 GPT에게 자동 추천받을지 여부")


class BlogIdeaItem(BaseModel):
    """단일 블로그 제목/프롬프트 아이디어"""
    index: int
    title: str
    prompt: str
    file_path: Optional[str] = None


class GenerateBlogIdeasResponse(BaseModel):
    """블로그 제목/프롬프트 아이디어 생성 응답 모델"""
    success: bool
    ideas: List[BlogIdeaItem] = []
    zip_path: Optional[str] = None
    error: Optional[str] = None


# ===== 유틸리티 함수 =====

def get_output_directory(count: int = 10):
    """
    실행 시간 기준으로 출력 디렉토리 경로를 생성합니다.
    
    Args:
        count: 생성할 TOP 디렉토리 개수 (기본값: 10)
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)
    
    base_dir = os.path.join(project_dir, "naver_crawler")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y%m%d")
    dir_pattern = f"{today}_"
    existing_dirs = [d for d in os.listdir(base_dir) if d.startswith(dir_pattern) and os.path.isdir(os.path.join(base_dir, d))]
    
    max_num = 0
    for dir_name in existing_dirs:
        try:
            num = int(dir_name.split('_')[-1])
            max_num = max(max_num, num)
        except ValueError:
            continue
    
    next_num = max_num + 1
    output_dir = os.path.join(base_dir, f"{today}_{next_num}")
    os.makedirs(output_dir, exist_ok=True)
    
    # 요청한 개수만큼만 TOP 디렉토리 생성
    for rank in range(1, count + 1):
        top_dir = os.path.join(output_dir, f"TOP{rank}")
        os.makedirs(top_dir, exist_ok=True)
    
    return output_dir


def slugify_filename(text: str, max_length: int = 50) -> str:
    """
    파일명에 사용할 수 있도록 텍스트를 슬러그 형태로 변환합니다.
    - 공백은 언더스코어로 변환
    - 위험 문자는 제거
    - 너무 길면 max_length 이내로 자름
    """
    if not text:
        return ""
    # 공백 → _
    text = text.strip().replace(" ", "_")
    # 위험 문자 제거
    forbidden = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for ch in forbidden:
        text = text.replace(ch, '')
    # 길이 제한
    if len(text) > max_length:
        text = text[:max_length]
    return text


def get_export_blog_directory() -> Path:
    """
    blog/export_blog 디렉토리 내에 날짜별 번호 디렉토리를 생성합니다.
    형식: blog/export_blog/yyyymmdd_1, yyyymmdd_2, ...
    """
    base_dir = EXPORT_BLOG_DIR
    base_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    dir_pattern = f"{today}_"
    existing_dirs = [
        d for d in base_dir.iterdir()
        if d.is_dir() and d.name.startswith(dir_pattern)
    ]

    max_num = 0
    for dir_path in existing_dirs:
        try:
            num = int(dir_path.name.split('_')[-1])
            max_num = max(max_num, num)
        except (ValueError, IndexError):
            continue

    next_num = max_num + 1
    output_dir = base_dir / f"{today}_{next_num}"
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def get_create_blog_prompt_directory() -> Path:
    """
    blog/create_blog_prompt 디렉토리 내에 날짜별 번호 디렉토리를 생성합니다.
    형식: blog/create_blog_prompt/yyyymmdd_1, yyyymmdd_2, ...
    """
    base_dir = CREATE_BLOG_PROMPT_DIR
    base_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    dir_pattern = f"{today}_"
    existing_dirs = [
        d for d in base_dir.iterdir()
        if d.is_dir() and d.name.startswith(dir_pattern)
    ]

    max_num = 0
    for dir_path in existing_dirs:
        try:
            num = int(dir_path.name.split('_')[-1])
            max_num = max(max_num, num)
        except (ValueError, IndexError):
            continue

    next_num = max_num + 1
    output_dir = base_dir / f"{today}_{next_num}"
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def build_reference_analysis(
    keyword: str,
    use_auto_reference: bool,
    reference_count: int,
    manual_urls: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    키워드와 참고용 블로그 URL들을 기반으로 상위 블로그 본문을 수집·분석하여
    GPT 프롬프트에 전달할 analysis_json을 생성합니다.
    """
    from analyzer.morpheme_analyzer import MorphemeAnalyzer

    try:
        reference_urls: List[str] = []

        # 1) 키워드 기반 상위 블로그 자동 수집
        if use_auto_reference:
            crawler = NaverCrawler()
            logger.info(f"[GENERATE][REF] auto reference enabled, keyword={keyword!r}, n={reference_count}")
            auto_list = crawler.get_top_n_blog_info(keyword, n=reference_count)
            for item in auto_list or []:
                url = item.get("url")
                if url and url not in reference_urls:
                    reference_urls.append(url)

        # 2) 사용자가 직접 추가한 참고 블로그 URL 병합
        if manual_urls:
            for url in manual_urls:
                u = (url or "").strip()
                if u and u not in reference_urls:
                    reference_urls.append(u)

        if not reference_urls:
            logger.info("[GENERATE][REF] no reference urls provided/collected")
            return None

        # 3) 각 URL에서 본문 텍스트 수집
        crawler = NaverCrawler()
        body_texts: List[str] = []
        used_urls: List[str] = []

        for url in reference_urls:
            try:
                result = crawler.extract_blog_body_with_media(url)
                body_text = result.get("body_text") if result else None
                if not body_text:
                    logger.warning(f"[GENERATE][REF] no body_text for reference url={url!r}")
                    continue
                text = str(body_text).strip()
                if not text:
                    continue
                body_texts.append(text)
                used_urls.append(url)
            except Exception as e:
                logger.warning(f"[GENERATE][REF] error extracting body for url={url!r}: {e}")
                continue

        if not body_texts:
            logger.warning("[GENERATE][REF] no usable body_text from any reference urls")
            return {
                "reference_urls": reference_urls,
                "used_reference_urls": [],
                "combined_body_length": 0,
                "top_keywords": []
            }

        combined_text = "\n\n".join(body_texts)

        # 4) 키워드 분석
        analyzer = MorphemeAnalyzer(use_konlpy=True)
        keyword_stats = analyzer.get_keyword_ranking(
            combined_text,
            top_n=10,
            min_length=2,
            min_count=2
        )

        top_keywords = [
            {
                "keyword": k,
                "count": v.get("count", 0),
                "rank": v.get("rank", 0)
            }
            for k, v in keyword_stats.items()
        ]

        analysis = {
            "reference_urls": reference_urls,
            "used_reference_urls": used_urls,
            "combined_body_length": len(combined_text),
            "top_keywords": top_keywords
        }

        logger.info(
            f"[GENERATE][REF] analysis built: refs={len(reference_urls)}, "
            f"used={len(used_urls)}, top_keywords={len(top_keywords)}"
        )
        return analysis

    except Exception as e:
        logger.exception(f"[GENERATE][REF] analysis error for keyword={keyword!r}: {e}")
        return None


def process_single_blog(
    crawler: NaverCrawler,
    blog_info: Dict[str, str],
    rank: int,
    base_output_dir: str,
    analyze: bool = True,
    top_n: int = 20,
    min_length: int = 2,
    min_count: int = 2
) -> ProcessResult:
    """단일 블로그를 처리하는 함수"""
    result = ProcessResult(
        rank=rank,
        title=blog_info['title'],
        url=blog_info['url'],
        success=False
    )
    
    try:
        top_dir = os.path.join(base_output_dir, f"TOP{rank}")
        
        # 본문 텍스트 및 미디어 URL 추출
        media_result = crawler.extract_blog_body_with_media(blog_info['url'])
        
        if not media_result or not media_result.get('body_text'):
            result.error = "본문 텍스트를 추출할 수 없습니다."
            return result
        
        body_text = media_result['body_text']
        result.body_text = body_text
        result.body_length = len(body_text)
        
        # 이미지 URL을 다운로드하여 저장하고 경로 변환 (마커 순서와 일치)
        original_image_urls = media_result.get('image_urls', [])
        saved_image_paths = []
        for idx, img_url in enumerate(original_image_urls, 1):
            # 블로그 URL을 Referer로 전달하여 원본 이미지 다운로드
            # NaverCrawler의 세션을 사용하여 쿠키와 헤더 유지
            saved_path = download_and_save_image(
                img_url, 
                top_dir, 
                image_index=idx, 
                referer_url=blog_info['url'],
                session=crawler.session
            )
            if saved_path:
                # 저장된 경로는 상대 경로로 반환 (프론트엔드에서 API_BASE_URL 추가)
                saved_image_paths.append(saved_path)
            else:
                # 저장 실패 시 프록시 URL 사용
                saved_image_paths.append(f"/api/image-proxy?url={quote(img_url)}&output_dir={quote(top_dir)}&referer={quote(blog_info['url'])}")
        
        result.image_urls = saved_image_paths
        result.link_urls = media_result.get('link_urls', [])
        
        # 본문을 txt 파일로 저장
        txt_path = crawler.save_blog_to_txt(
            blog_info['url'],
            title=blog_info['title'],
            output_dir=top_dir
        )
        result.txt_path = txt_path
        
        # 키워드 분석
        if analyze:
            try:
                analyzer = MorphemeAnalyzer(use_konlpy=True)
                
                # 키워드 통계 가져오기
                keyword_stats = analyzer.get_keyword_ranking(
                    body_text,
                    top_n=top_n,
                    min_length=min_length,
                    min_count=min_count
                )
                
                # 키워드 리스트 생성
                keywords = [
                    KeywordStat(keyword=k, count=v['count'], rank=v['rank'])
                    for k, v in keyword_stats.items()
                ]
                result.keywords = keywords
                
                # 엑셀 파일로 저장
                if txt_path:
                    base_name = os.path.splitext(os.path.basename(txt_path))[0]
                    excel_path = os.path.join(top_dir, f"{base_name}_keyword_analysis.xlsx")
                else:
                    excel_filename = f"blog_{int(datetime.now().timestamp())}_keyword_analysis.xlsx"
                    excel_path = os.path.join(top_dir, excel_filename)
                
                excel_path = analyzer.export_to_excel(
                    body_text,
                    output_path=excel_path,
                    top_n=top_n,
                    min_length=min_length,
                    min_count=min_count
                )
                result.excel_path = excel_path
                
            except Exception as e:
                result.error = f"형태소 분석 오류: {str(e)}"
        
        result.success = True
        
    except Exception as e:
        result.error = str(e)
    
    return result


# ===== API 엔드포인트 =====

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "네이버 블로그 크롤링 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


@app.get("/api/usage")
async def get_usage(http_request: Request):
    """
    현재 IP의 사용량 정보를 반환합니다.
    """
    try:
        usage_info = get_usage_info(http_request)
        return usage_info
    except Exception as e:
        logger.exception(f"[USAGE] 사용량 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"사용량 조회 중 오류 발생: {str(e)}")


# ===== 임시 저장 API (IP 기반) =====
class SaveDraftRequest(BaseModel):
    """임시 저장 요청 모델"""
    title: Optional[Dict[str, Any]] = Field(None, description="제목 (Quill Delta 형식)")
    body: Optional[Dict[str, Any]] = Field(None, description="본문 (Quill Delta 형식)")
    tags: Optional[Dict[str, Any]] = Field(None, description="태그 (Quill Delta 형식)")
    image_meta: Optional[Dict[str, Any]] = Field(None, description="이미지 메타데이터")


class SaveDraftResponse(BaseModel):
    """임시 저장 응답 모델"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class GetDraftResponse(BaseModel):
    """임시 저장 불러오기 응답 모델"""
    success: bool
    title: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None
    image_meta: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def get_draft_file_path(user_id: str) -> Path:
    """사용자별 임시 저장 파일 경로를 반환합니다."""
    # 사용자 ID를 파일명으로 사용 (특수문자 제거)
    safe_id = user_id.replace(".", "_").replace(":", "_").replace("/", "_")
    return DRAFT_DIR / f"draft_{safe_id}.json"


@app.post("/api/save-draft", response_model=SaveDraftResponse)
async def save_draft(request: SaveDraftRequest, http_request: Request):
    """
    에디터 내용을 사용자별로 임시 저장합니다.
    """
    try:
        user_id = get_user_identifier(http_request)
        client_ip = get_client_ip(http_request)
        draft_path = get_draft_file_path(user_id)
        
        draft_data = {
            "ip": client_ip,
            "user_id": user_id,
            "saved_at": datetime.now().isoformat(),
            "title": request.title,
            "body": request.body,
            "tags": request.tags,
            "image_meta": request.image_meta
        }
        
        # JSON 파일로 저장
        with open(draft_path, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[DRAFT] 임시 저장 완료: User={user_id}, IP={client_ip}")
        return SaveDraftResponse(success=True, message="임시 저장 완료")
        
    except Exception as e:
        logger.exception(f"[DRAFT] 임시 저장 오류: {e}")
        return SaveDraftResponse(
            success=False,
            error=f"임시 저장 중 오류 발생: {str(e)}"
        )


@app.get("/api/get-draft", response_model=GetDraftResponse)
async def get_draft(http_request: Request):
    """
    현재 사용자의 임시 저장된 내용을 불러옵니다.
    """
    try:
        user_id = get_user_identifier(http_request)
        draft_path = get_draft_file_path(user_id)
        
        if not draft_path.exists():
            return GetDraftResponse(success=True)  # 저장된 내용 없음
        
        # JSON 파일 읽기
        with open(draft_path, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        logger.info(f"[DRAFT] 임시 저장 불러오기 완료: User={user_id}")
        return GetDraftResponse(
            success=True,
            title=draft_data.get("title"),
            body=draft_data.get("body"),
            tags=draft_data.get("tags"),
            image_meta=draft_data.get("image_meta")
        )
        
    except Exception as e:
        logger.exception(f"[DRAFT] 임시 저장 불러오기 오류: {e}")
        return GetDraftResponse(
            success=False,
            error=f"임시 저장 불러오기 중 오류 발생: {str(e)}"
        )


@app.delete("/api/delete-draft")
async def delete_draft(http_request: Request):
    """
    현재 사용자의 임시 저장된 내용을 삭제합니다.
    """
    try:
        user_id = get_user_identifier(http_request)
        draft_path = get_draft_file_path(user_id)
        
        if draft_path.exists():
            draft_path.unlink()
            logger.info(f"[DRAFT] 임시 저장 삭제 완료: User={user_id}")
        
        return {"success": True, "message": "임시 저장 삭제 완료"}
        
    except Exception as e:
        logger.exception(f"[DRAFT] 임시 저장 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=f"임시 저장 삭제 중 오류 발생: {str(e)}")


# ===== 관리자용 사용량 조회 API =====
class UsageStatsResponse(BaseModel):
    """전체 사용량 통계 응답 모델"""
    total_users: int
    users: List[Dict[str, Any]]


@app.get("/api/admin/usage-stats", response_model=UsageStatsResponse)
async def get_usage_stats(http_request: Request):
    """
    관리자용: 전체 접속자 수와 각 IP별 사용량을 조회합니다.
    Admin IP만 접근 가능합니다.
    """
    try:
        client_ip = get_client_ip(http_request)
        
        # Admin IP 확인
        if not is_admin_ip(client_ip):
            raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
        
        # JSON 파일에서 사용량 데이터 로드
        data = load_usage_data()
        first_seen_data = data.get("first_seen", {})
        
        # 모든 user_id 수집 (세 가지 트래커에서)
        all_user_ids = set()
        all_user_ids.update(data.get("blog_generation", {}).keys())
        all_user_ids.update(data.get("reference_analysis", {}).keys())
        all_user_ids.update(data.get("blog_ideas", {}).keys())
        
        # 각 user_id별 사용량 정보 수집
        users = []
        now = datetime.now()
        for user_id in all_user_ids:
            # 각 트래커에서 사용량 가져오기
            blog_gen_info = data.get("blog_generation", {}).get(user_id, {"count": 0, "reset_time": (now + timedelta(days=1)).isoformat()})
            ref_analysis_info = data.get("reference_analysis", {}).get(user_id, {"count": 0, "reset_time": (now + timedelta(days=1)).isoformat()})
            blog_ideas_info = data.get("blog_ideas", {}).get(user_id, {"count": 0, "reset_time": (now + timedelta(days=1)).isoformat()})
            
            # datetime 변환
            blog_reset_time_str = blog_gen_info.get("reset_time")
            blog_reset_time = datetime.fromisoformat(blog_reset_time_str) if isinstance(blog_reset_time_str, str) else blog_reset_time_str
            ref_reset_time_str = ref_analysis_info.get("reset_time")
            ref_reset_time = datetime.fromisoformat(ref_reset_time_str) if isinstance(ref_reset_time_str, str) else ref_reset_time_str
            ideas_reset_time_str = blog_ideas_info.get("reset_time")
            ideas_reset_time = datetime.fromisoformat(ideas_reset_time_str) if isinstance(ideas_reset_time_str, str) else ideas_reset_time_str
            
            # 리셋 시간 계산
            blog_reset = blog_reset_time - now if blog_reset_time > now else timedelta(0)
            ref_reset = ref_reset_time - now if ref_reset_time > now else timedelta(0)
            ideas_reset = ideas_reset_time - now if ideas_reset_time > now else timedelta(0)
            
            # user_id에서 IP 추출 (user_id는 IP와 client_id의 MD5 해시이므로, IP만으로는 추출 불가)
            # 대신 user_id를 그대로 사용하거나, first_seen에서 IP를 찾아야 함
            # 일단 user_id를 표시하고, first_seen에서 매칭되는 IP를 찾아보자
            matching_ip = None
            for ip, first_seen in first_seen_data.items():
                # user_id는 IP와 client_id의 조합이므로, 정확한 매칭은 어렵지만
                # 일단 user_id를 표시
                pass
            
            # IP는 user_id의 일부일 수 있지만, 정확한 추출은 어려우므로 user_id를 사용
            ip = user_id  # 임시로 user_id를 IP로 사용 (실제로는 user_id)
            
            user_info = {
                "ip": ip,  # 실제로는 user_id
                "is_admin": False,  # user_id만으로는 admin 여부 확인 불가, 필요시 별도 로직 추가
                "first_seen": None,  # user_id와 IP 매칭이 어려워서 None
                "blog_generation": {
                    "used": blog_gen_info.get("count", 0),
                    "limit": DAILY_LIMIT,
                    "reset_in_hours": int(blog_reset.total_seconds() / 3600) if blog_reset.total_seconds() > 0 else 0,
                    "reset_in_minutes": int((blog_reset.total_seconds() % 3600) / 60) if blog_reset.total_seconds() > 0 else 0
                },
                "reference_analysis": {
                    "used": ref_analysis_info.get("count", 0),
                    "limit": REFERENCE_ANALYSIS_LIMIT,
                    "reset_in_hours": int(ref_reset.total_seconds() / 3600) if ref_reset.total_seconds() > 0 else 0,
                    "reset_in_minutes": int((ref_reset.total_seconds() % 3600) / 60) if ref_reset.total_seconds() > 0 else 0
                },
                "blog_ideas": {
                    "used": blog_ideas_info.get("count", 0),
                    "limit": BLOG_IDEAS_LIMIT,
                    "reset_in_hours": int(ideas_reset.total_seconds() / 3600) if ideas_reset.total_seconds() > 0 else 0,
                    "reset_in_minutes": int((ideas_reset.total_seconds() % 3600) / 60) if ideas_reset.total_seconds() > 0 else 0
                }
            }
            users.append(user_info)
        
        # IP별로 정렬 (첫 접속 시간 기준, 최신순)
        users.sort(key=lambda x: x.get("first_seen") or "", reverse=True)
        
        return UsageStatsResponse(
            total_users=len(users),
            users=users
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[ADMIN] 사용량 통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"사용량 통계 조회 중 오류 발생: {str(e)}")


@app.post("/api/search", response_model=SearchResponse)
async def search_blogs(request: SearchRequest):
    """
    키워드로 네이버 블로그 검색
    
    - **keyword**: 검색할 키워드
    - **n**: 가져올 블로그 개수 (1-10)
    """
    try:
        logger.info(f"[SEARCH] keyword={request.keyword!r}, n={request.n}")
        crawler = NaverCrawler()
        blog_list = crawler.get_top_n_blog_info(request.keyword, n=request.n)
        
        if not blog_list or len(blog_list) == 0:
            raise HTTPException(status_code=404, detail="블로그 글을 찾을 수 없습니다.")
        
        blogs = [BlogInfo(title=blog['title'], url=blog['url']) for blog in blog_list]
        logger.info(f"[SEARCH] found {len(blogs)} blogs for keyword={request.keyword!r}")
        
        return SearchResponse(
            keyword=request.keyword,
            count=len(blogs),
            blogs=blogs
        )
    except Exception as e:
        logger.exception(f"[SEARCH] error for keyword={request.keyword!r}: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@app.post("/api/crawl", response_model=CrawlResponse)
async def crawl_blog(request: CrawlRequest):
    """
    블로그 본문 크롤링 (단일)
    
    - **url**: 크롤링할 블로그 URL
    - **title**: 블로그 제목 (선택사항)
    """
    try:
        logger.info(f"[CRAWL] single url={request.url!r}, title={request.title!r}")
        crawler = NaverCrawler()
        result = crawler.extract_blog_body_with_media(request.url)
        
        if not result or not result.get('body_text'):
            logger.warning(f"[CRAWL] no body_text extracted for url={request.url!r}")
            return CrawlResponse(
                success=False,
                url=request.url,
                error="본문 텍스트를 추출할 수 없습니다."
            )
        
        body_text = result['body_text']
        image_urls = result.get('image_urls', [])
        link_urls = result.get('link_urls', [])
        logger.info(
            f"[CRAWL] success url={request.url!r}, "
            f"body_length={len(body_text)}, images={len(image_urls)}, links={len(link_urls)}"
        )
        
        # txt 파일 저장 (선택사항)
        txt_path = None
        if request.title:
            txt_path = crawler.save_blog_to_txt(request.url, title=request.title)
        
        return CrawlResponse(
            success=True,
            title=request.title,
            url=request.url,
            body_text=body_text,
            body_length=len(body_text),
            image_urls=image_urls if image_urls else None,
            link_urls=link_urls if link_urls else None,
            txt_path=txt_path
        )
    except Exception as e:
        logger.exception(f"[CRAWL] error for url={request.url!r}: {e}")
        return CrawlResponse(
            success=False,
            url=request.url,
            error=str(e)
        )


@app.post("/api/crawl/bulk", response_model=CrawlBulkResponse)
async def crawl_blogs_bulk(request: CrawlBulkRequest):
    """
    블로그 본문 크롤링 (리스트)
    
    - **urls**: 크롤링할 블로그 URL 리스트
    - **titles**: 블로그 제목 리스트 (선택사항, urls와 같은 길이)
    """
    try:
        # titles 길이 검증
        if request.titles and len(request.titles) != len(request.urls):
            raise HTTPException(
                status_code=400,
                detail="titles 리스트의 길이가 urls 리스트의 길이와 일치하지 않습니다."
            )
        
        crawler = NaverCrawler()
        results = []
        success_count = 0
        
        for i, url in enumerate(request.urls):
            title = request.titles[i] if request.titles else None
            
            try:
                media_result = crawler.extract_blog_body_with_media(url)
                
                if not media_result or not media_result.get('body_text'):
                    results.append(CrawlResponse(
                        success=False,
                        url=url,
                        title=title,
                        error="본문 텍스트를 추출할 수 없습니다."
                    ))
                    continue
                
                body_text = media_result['body_text']
                image_urls = media_result.get('image_urls', [])
                link_urls = media_result.get('link_urls', [])
                
                # txt 파일 저장 (선택사항)
                txt_path = None
                if title:
                    txt_path = crawler.save_blog_to_txt(url, title=title)
                
                results.append(CrawlResponse(
                    success=True,
                    title=title,
                    url=url,
                    body_text=body_text,
                    body_length=len(body_text),
                    image_urls=image_urls if image_urls else None,
                    link_urls=link_urls if link_urls else None,
                    txt_path=txt_path
                ))
                success_count += 1
                
            except Exception as e:
                results.append(CrawlResponse(
                    success=False,
                    url=url,
                    title=title,
                    error=str(e)
                ))
        
        return CrawlBulkResponse(
            total_count=len(results),
            success_count=success_count,
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_keywords(request: AnalyzeRequest):
    """
    텍스트에서 키워드 분석
    
    - **text**: 분석할 텍스트
    - **top_n**: 상위 N개 키워드
    - **min_length**: 최소 키워드 길이
    - **min_count**: 최소 출현 횟수
    """
    try:
        logger.info(
            f"[ANALYZE] text_length={len(request.text)}, "
            f"top_n={request.top_n}, min_length={request.min_length}, min_count={request.min_count}"
        )
        analyzer = MorphemeAnalyzer(use_konlpy=True)
        
        # 키워드 통계 가져오기
        keyword_stats = analyzer.get_keyword_ranking(
            request.text,
            top_n=request.top_n,
            min_length=request.min_length,
            min_count=request.min_count
        )
        
        keywords = [
            KeywordStat(keyword=k, count=v['count'], rank=v['rank'])
            for k, v in keyword_stats.items()
        ]
        
        response = AnalyzeResponse(
            success=True,
            total_keywords=len(keywords),
            keywords=keywords
        )
        logger.info(f"[ANALYZE] success total_keywords={len(keywords)}")
        return response
    except Exception as e:
        logger.exception(f"[ANALYZE] error: {e}")
        return AnalyzeResponse(
            success=False,
            total_keywords=0,
            keywords=[],
            error=str(e)
        )


@app.post("/api/process", response_model=ProcessResponse)
async def process_blogs(request: ProcessRequest, http_request: Request):
    """
    전체 처리 (검색 + 크롤링 + 분석)
    
    - **keyword**: 검색 키워드
    - **n**: 처리할 블로그 개수
    - **analyze**: 키워드 분석 수행 여부
    - **top_n**: 상위 N개 키워드
    - **min_length**: 최소 키워드 길이
    - **min_count**: 최소 출현 횟수
    """
    try:
        # 사용량 제한 확인 (상위 블로그 분석)
        is_allowed, message = check_reference_analysis_limit(http_request)
        if not is_allowed:
            return ProcessResponse(
                success=False,
                total_count=0,
                success_count=0,
                results=[],
                error=message
            )
        logger.info(
            f"[PROCESS] keyword={request.keyword!r}, n={request.n}, "
            f"analyze={request.analyze}, top_n={request.top_n}, "
            f"min_length={request.min_length}, min_count={request.min_count}"
        )
        # 1. 블로그 검색 (비동기 처리)
        loop = asyncio.get_event_loop()
        crawler = NaverCrawler()
        blog_list = await loop.run_in_executor(
            None,
            crawler.get_top_n_blog_info,
            request.keyword,
            request.n
        )
        
        if not blog_list or len(blog_list) == 0:
            raise HTTPException(status_code=404, detail="블로그 글을 찾을 수 없습니다.")
        
        logger.info(f"[PROCESS] search found {len(blog_list)} blogs")
        # 2. 출력 디렉토리 생성 (요청한 개수만큼만) - 동기 처리 (순서 보장 필요)
        output_dir = get_output_directory(count=request.n)
        
        # 3. 병렬 처리 (비동기로 실행하여 다른 요청을 블로킹하지 않음)
        results = []
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=min(request.n, 3)) as executor:
            # 각 블로그 처리를 비동기로 실행
            async def process_single_blog_async(blog_info, rank):
                crawler_instance = NaverCrawler()
                return await loop.run_in_executor(
                    executor,
                    process_single_blog,
                    crawler_instance,
                    blog_info,
                    rank,
                    output_dir,
                    request.analyze,
                    request.top_n,
                    request.min_length,
                    request.min_count
                )
            
            # 모든 블로그를 동시에 처리
            tasks = [
                process_single_blog_async(blog_info, i)
                for i, blog_info in enumerate(blog_list, 1)
            ]
            
            # 결과 수집
            processed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for rank, result in enumerate(processed_results, 1):
                if isinstance(result, Exception):
                    logger.exception(f"[PROCESS] error processing rank={rank}: {result}")
                    results.append(ProcessResult(
                        rank=rank,
                        title=blog_list[rank-1]['title'] if rank <= len(blog_list) else "알 수 없음",
                        url=blog_list[rank-1]['url'] if rank <= len(blog_list) else "",
                        success=False,
                        error=str(result)
                    ))
                else:
                    results.append(result)
        
        # 결과 정렬 (동기 처리 - 순서 보장 필요)
        results.sort(key=lambda x: x.rank)
        
        success_count = sum(1 for r in results if r.success)
        logger.info(
            f"[PROCESS] done keyword={request.keyword!r}, "
            f"total={len(results)}, success={success_count}"
        )
        
        return ProcessResponse(
            keyword=request.keyword,
            output_dir=output_dir,
            total_count=len(results),
            success_count=success_count,
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[PROCESS] fatal error: {e}")
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


def download_and_save_image(image_url: str, output_dir: Optional[str] = None, image_index: Optional[int] = None, referer_url: Optional[str] = None, session: Optional[requests.Session] = None) -> str:
    """
    이미지를 다운로드하여 서버에 저장하고, 저장된 파일 경로를 반환합니다.
    
    Args:
        image_url: 다운로드할 이미지 URL
        output_dir: 저장할 디렉토리 경로 (예: naver_crawler/20251205_1/TOP1)
                    None이면 기본 위치에 저장
        image_index: 이미지 인덱스 (마커 순서와 일치, 예: 1, 2, 3...)
                    None이면 MD5 해시 사용
        referer_url: Referer 헤더로 사용할 블로그 URL (원본 이미지 다운로드를 위해 필요)
        session: requests.Session 객체 (쿠키와 헤더 유지를 위해 사용)
        
    Returns:
        저장된 이미지 파일의 상대 경로 (예: /static/naver_crawler/.../이미지삽입1.jpg)
    """
    try:
        # URL에서 파일 확장자 추출
        parsed_url = urlparse(image_url)
        path = parsed_url.path
        ext = os.path.splitext(path)[1] or '.jpg'
        
        # 파일명 생성: image_index가 있으면 마커 순서와 일치하게, 없으면 MD5 해시 사용
        if image_index is not None:
            filename = f"이미지삽입{image_index}{ext}"
        else:
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            filename = f"{url_hash}{ext}"
        
        # 저장 디렉토리 결정
        if output_dir:
            # output_dir이 제공되면 해당 TOP 디렉토리 하위에 images 폴더 생성
            images_dir = Path(output_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            filepath = images_dir / filename
            # 정적 파일 경로는 naver_crawler 기준 상대 경로
            relative_path = filepath.relative_to(NAVER_CRAWLER_DIR)
            static_path = f"/static/naver_crawler/{relative_path.as_posix()}"
        else:
            # 기본 위치 (naver_crawler/images)
            images_dir = NAVER_CRAWLER_DIR / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            filepath = images_dir / filename
            static_path = f"/static/naver_crawler/images/{filename}"
        
        # 이미 파일이 존재하면 저장된 경로 반환
        if filepath.exists():
            return static_path
        
        # 수집된 URL을 그대로 사용 (w966이 있으면 고화질, 없으면 저화질)
        # 크롤러에서 이미 올바른 URL을 수집했으므로 변환하지 않음
        original_image_url = image_url
        
        # 이미지 다운로드 (Referer 헤더 포함 - 실제 블로그 URL 사용)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': referer_url if referer_url else 'https://blog.naver.com/',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'identity',  # 압축 해제를 위해 identity 사용
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
            'Cache-Control': 'no-cache'
        }
        
        # 세션이 제공되면 사용 (쿠키와 헤더 유지)
        if session:
            # 세션의 기본 헤더를 복사하고 추가 헤더 업데이트
            session_headers = dict(session.headers)
            session_headers.update(headers)
            response = session.get(original_image_url, headers=session_headers, timeout=10, stream=True)
        else:
            response = requests.get(original_image_url, headers=headers, timeout=10, stream=True)
        
        response.raise_for_status()
        
        # 이미지 데이터 저장
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return static_path
        
    except Exception as e:
        print(f"[ERROR] 이미지 다운로드 실패 ({image_url}): {e}")
        # 다운로드 실패 시 원본 URL 반환 (프록시 방식으로 폴백)
        return None


@app.get("/api/image-proxy")
async def proxy_image(url: str, output_dir: Optional[str] = None, image_index: Optional[int] = None, referer: Optional[str] = None):
    """
    이미지를 다운로드하여 서버에 저장한 후 제공합니다.
    네이버 포스트파일 서버의 Referer 제한을 우회하기 위해 사용합니다.
    
    - **url**: 다운로드할 이미지 URL (URL 인코딩 필요)
    - **output_dir**: 저장할 디렉토리 경로 (선택사항, 예: naver_crawler/20251205_1/TOP1)
    - **image_index**: 이미지 인덱스 (선택사항, 마커 순서와 일치, 예: 1, 2, 3...)
    - **referer**: Referer 헤더로 사용할 블로그 URL (선택사항, 원본 이미지 다운로드를 위해 필요)
    """
    try:
        # URL 디코딩
        image_url = unquote(url)
        
        # URL 유효성 검사
        if not image_url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="유효하지 않은 URL입니다.")
        
        # 네이버 포스트파일 서버만 허용 (보안)
        allowed_domains = ['postfiles.pstatic.net', 'blogpf.pstatic.net', 'blogfiles.pstatic.net']
        if not any(domain in image_url for domain in allowed_domains):
            raise HTTPException(status_code=403, detail="허용되지 않은 도메인입니다.")
        
        # output_dir이 제공되면 절대 경로로 변환
        if output_dir:
            if not os.path.isabs(output_dir):
                # 상대 경로면 naver_crawler 기준으로 변환
                output_dir = str(NAVER_CRAWLER_DIR / output_dir.replace('naver_crawler/', ''))
        
        # 이미지 다운로드 및 저장 (image_index 및 referer 전달)
        referer_url = unquote(referer) if referer else None
        saved_path = download_and_save_image(image_url, output_dir, image_index=image_index, referer_url=referer_url)
        
        if saved_path:
            # 저장된 파일 경로 파싱
            # /static/naver_crawler/20251205_1/TOP1/images/xxx.jpg 형식
            relative_path = saved_path.replace('/static/naver_crawler/', '')
            filepath = NAVER_CRAWLER_DIR / relative_path
            
            if filepath.exists():
                return FileResponse(
                    path=str(filepath),
                    headers={
                        'Cache-Control': 'public, max-age=86400',  # 24시간 캐시
                        'Access-Control-Allow-Origin': '*'
                    }
                )
        
        # 저장 실패 시 스트리밍 방식으로 폴백
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': referer_url if referer_url else 'https://blog.naver.com/',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site'
        }
        
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        
        return Response(
            content=response.content,
            media_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=3600',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"이미지를 가져올 수 없습니다: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 프록시 중 오류 발생: {str(e)}")


@app.get("/api/default-ban-words")
async def get_default_ban_words():
    """
    기본 금칙어 목록을 반환합니다.
    """
    from blog.gpt_generator import load_default_ban_words
    return {"default_ban_words": load_default_ban_words()}


@app.post("/api/generate-blog", response_model=GenerateBlogResponse)
async def generate_blog(request: GenerateBlogRequest, http_request: Request):
    """
    GPT API를 사용하여 블로그 글을 생성합니다.
    
    - **keywords**: 블로그 글의 주요 키워드
    - **category**: 카테고리 (기본값: "일반")
    - **blog_level**: 블로그 레벨 ("new", "mid", "high", 기본값: "mid")
    - **ban_words**: 추가 금칙어 목록 (선택사항, 기본 금칙어와 병합됨)
    - **analysis_json**: 상위 글 분석 JSON (선택사항)
    - **external_links**: 본문에 자연스럽게 삽입할 외부 링크 목록 (선택사항, new 레벨에서는 무시)
    - **model**: 사용할 GPT 모델 (기본값: "gpt-4o")
    - **temperature**: 생성 온도 (기본값: 0.7)
    - **save_json**: JSON 파일로 저장 여부 (기본값: True)
    """
    try:
        # 사용량 제한 확인
        is_allowed, message = check_usage_limit(http_request)
        if not is_allowed:
            return GenerateBlogResponse(
                success=False,
                error=message
            )
        
        # 1) 상위 블로그 자동 수집/사용자 지정 참고 URL 기반 analysis_json 구성
        # AI 블로그 생성 탭에서는 상위 블로그 분석을 별도로 카운트하지 않고
        # 블로그 생성 버튼 클릭 1회 = 1회로 계산
        analysis_json = request.analysis_json
        if analysis_json is None and (request.use_auto_reference or (request.manual_reference_urls or [])):
            logger.info(
                f"[GENERATE] building reference analysis: "
                f"keyword={request.keywords!r}, "
                f"use_auto_reference={request.use_auto_reference}, "
                f"reference_count={request.reference_count}, "
                f"manual_refs={len(request.manual_reference_urls or [])}"
            )
            # 비동기로 실행
            loop = asyncio.get_event_loop()
            analysis_json = await loop.run_in_executor(
                None,
                build_reference_analysis,
                request.keywords,
                request.use_auto_reference,
                request.reference_count,
                request.manual_reference_urls or []
            )

        logger.info(
            f"[GENERATE] keywords={request.keywords!r}, "
            f"category={request.category!r}, level={request.blog_level!r}, "
            f"ban_words_count={len(request.ban_words or [])}, "
            f"has_analysis={analysis_json is not None}, "
            f"use_auto_reference={request.use_auto_reference}, "
            f"reference_count={request.reference_count}, "
            f"manual_refs={len(request.manual_reference_urls or [])}, "
            f"external_links_count={len(request.external_links or []) if request.blog_level != 'new' else 0}"
        )

        # 2) 블로그 글 생성 (기본 금칙어는 generate_blog_content 내부에서 자동 병합됨)
        # 비동기로 실행하여 여러 요청을 동시에 처리 가능
        loop = asyncio.get_event_loop()
        blog_content = await loop.run_in_executor(
            None,
            generate_blog_content,
            request.keywords,
            request.category,
            request.blog_level,
            request.ban_words or [],
            analysis_json,
            request.model,
            request.temperature,
            None,  # max_tokens
            None if request.blog_level == "new" else (request.external_links or None)  # external_links
        )
        
        # 3) 이미지 플레이스홀더 추출 및 이미지 생성 (generate_images가 True인 경우만)
        from blog.image_generator import generate_image, build_image_prompt
        from blog.gpt_generator import extract_image_placeholders, get_create_naver_directory
        
        image_placeholders = extract_image_placeholders(blog_content)
        output_dir = None
        
        if image_placeholders:
            if request.generate_images:
                logger.info(f"[GENERATE] 이미지 플레이스홀더 발견: {len(image_placeholders)}개, 이미지 생성 활성화")
            else:
                logger.info(f"[GENERATE] 이미지 플레이스홀더 발견: {len(image_placeholders)}개, 이미지 생성 비활성화 (체크박스 해제)")
        
        if image_placeholders and request.generate_images:
            
            # 출력 디렉토리 준비 (JSON 저장 위치와 동일)
            if request.save_json:
                output_dir = get_create_naver_directory()
            else:
                # JSON 저장하지 않아도 이미지만 저장할 수 있도록 임시 디렉토리 생성
                output_dir = get_create_naver_directory()
            
            # 각 이미지 플레이스홀더에 대해 이미지 생성 (병렬 처리)
            generated_images = []
            image_retry_count = 0
            
            # 이미지 생성을 병렬로 처리하는 함수
            def generate_single_image(img_placeholder):
                nonlocal image_retry_count
                attempts = 0
                image_path = None
                while attempts < 3 and image_path is None:
                    attempts += 1
                    try:
                        image_prompt = build_image_prompt(
                            img_placeholder["image_prompt"],
                            image_style=request.image_style
                        )
                        image_path = generate_image(
                            image_prompt=image_prompt,
                            output_dir=output_dir,
                            image_index=img_placeholder["index"]
                        )
                        
                        if image_path:
                            # 상대 경로로 변환 (프론트엔드에서 접근 가능하도록)
                            relative_to_base = image_path.relative_to(CREATE_NAVER_DIR)
                            relative_path = str(relative_to_base).replace('\\', '/')
                            result = {
                                "index": img_placeholder["index"],
                                "placeholder": img_placeholder["placeholder"],
                                "image_path": relative_path,
                                "full_path": str(image_path)
                            }
                            logger.info(f"[GENERATE] 이미지 생성 완료: {relative_path}")
                            return result
                        else:
                            logger.warning(
                                f"[GENERATE] 이미지 생성 실패: index={img_placeholder['index']}, "
                                f"attempt={attempts}"
                            )
                            if attempts < 3:
                                image_retry_count += 1
                    except Exception as e:
                        logger.error(
                            f"[GENERATE] 이미지 생성 오류: index={img_placeholder['index']}, "
                            f"attempt={attempts}, error={str(e)}"
                        )
                        if attempts < 3:
                            image_retry_count += 1
                return None
            
            # ThreadPoolExecutor를 사용하여 병렬 처리 (최대 3개 동시 실행)
            # 비동기로 실행하여 다른 요청을 블로킹하지 않음
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 모든 이미지 생성을 비동기로 실행
                futures = [
                    loop.run_in_executor(executor, generate_single_image, img_placeholder)
                    for img_placeholder in image_placeholders
                ]
                
                # 결과 수집 (인덱스 순서대로 정렬)
                results = await asyncio.gather(*futures, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"[GENERATE] 이미지 생성 중 예외 발생: {result}")
                    elif result:
                        generated_images.append(result)
            
            # 인덱스 순서대로 정렬
            generated_images.sort(key=lambda x: x["index"])
            
            # 생성된 이미지 정보를 blog_content에 추가
            if generated_images:
                blog_content["generated_images"] = generated_images
                logger.info(f"[GENERATE] 생성된 이미지 정보 추가: {len(generated_images)}개")
        
        # 분석된 키워드 정보(analysis_json)를 blog_content에 추가
        if analysis_json:
            blog_content["analysis"] = analysis_json
            logger.info(f"[GENERATE] 분석 정보 추가: top_keywords={len(analysis_json.get('top_keywords', []))}개")
        
        # 외부 링크 정보를 blog_content에 추가 (프론트엔드에서 에디터 하단에 배치하기 위해)
        if request.external_links and request.blog_level != "new":
            blog_content["external_links"] = request.external_links
            logger.info(f"[GENERATE] 외부 링크 정보 추가: {len(request.external_links)}개")
        
        # JSON 파일로 저장
        json_path = None
        if request.save_json:
            # blog/create_naver/yyyymmdd_N 형식으로 자동 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"blog_generated_{timestamp}.json"
            json_path = save_blog_json(blog_content, output_dir=output_dir, filename=filename)
            logger.info(f"[GENERATE] json saved: {json_path}")
        
        return GenerateBlogResponse(
            success=True,
            blog_content=blog_content,
            json_path=json_path,
            image_retry_count=image_retry_count if image_placeholders and request.generate_images else 0
        )
        
    except ValueError as e:
        return GenerateBlogResponse(
            success=False,
            error=f"입력값 오류: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"[GENERATE] error: {e}")
        return GenerateBlogResponse(
            success=False,
            error=f"블로그 생성 중 오류 발생: {str(e)}"
        )


@app.post("/api/export-blog", response_model=ExportBlogResponse)
async def export_blog(request: ExportBlogRequest):
    """
    에디터에서 작성한 내용을 기반으로 네이버 발행용 JSON + 이미지 패키지를 생성하고
    ZIP 파일 경로를 반환합니다.
    """
    try:
        blog_content = request.blog_content
        images = request.images or []

        # blog/export_blog/yyyymmdd_N 디렉토리 생성 (에디터 내보내기 전용)
        output_dir = get_export_blog_directory()
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # 이미지 저장 및 generated_images 구성
        generated_images = []
        for img in images:
            src = img.src or ""
            if not src:
                continue

            # 파일명 생성
            caption_slug = slugify_filename(img.caption or "")
            base_name = f"img{img.index}"
            if caption_slug:
                base_name = f"{base_name}_{caption_slug}"

            # 확장자 결정
            ext = "jpg"
            mime = None

            # data URL (base64)
            if src.startswith("data:"):
                # data:image/png;base64,xxxx
                try:
                    header, b64data = src.split(",", 1)
                    if header.startswith("data:") and ";base64" in header:
                        mime = header[5:header.index(";base64")]
                        guessed_ext = mimetypes.guess_extension(mime) or ""
                        if guessed_ext:
                            ext = guessed_ext.lstrip(".")
                        image_bytes = base64.b64decode(b64data)
                        filename = f"{base_name}.{ext}"
                        file_path = images_dir / filename
                        with open(file_path, "wb") as f:
                            f.write(image_bytes)
                    else:
                        continue
                except Exception as e:
                    logger.error(f"[EXPORT] data URL 이미지 처리 실패: index={img.index}, error={str(e)}")
                    continue

            # /static/blog/create_naver/... 형식 (기존 생성 이미지 복사)
            elif src.startswith("/static/blog/create_naver/") or urlparse(src).path.startswith("/static/blog/create_naver/"):
                # 절대 URL인 경우 path 부분만 사용
                path = urlparse(src).path
                if path.startswith("/static/blog/create_naver/"):
                    relative = path[len("/static/blog/create_naver/"):]
                else:
                    relative = src[len("/static/blog/create_naver/"):]
                src_path = CREATE_NAVER_DIR / Path(unquote(relative))
                if not src_path.exists():
                    logger.warning(f"[EXPORT] 원본 이미지 파일을 찾을 수 없음: {src_path}")
                    continue
                # 확장자
                ext = src_path.suffix.lstrip(".") or "jpg"
                filename = f"{base_name}.{ext}"
                file_path = images_dir / filename
                try:
                    with open(src_path, "rb") as rf, open(file_path, "wb") as wf:
                        wf.write(rf.read())
                except Exception as e:
                    logger.error(f"[EXPORT] 이미지 복사 실패: src={src_path}, error={str(e)}")
                    continue

            # http/https URL
            elif src.startswith("http://") or src.startswith("https://"):
                try:
                    resp = requests.get(src, timeout=10)
                    if resp.status_code != 200:
                        logger.warning(f"[EXPORT] 이미지 다운로드 실패: url={src}, status={resp.status_code}")
                        continue
                    mime = resp.headers.get("Content-Type", "")
                    guessed_ext = mimetypes.guess_extension(mime) or ""
                    if guessed_ext:
                        ext = guessed_ext.lstrip(".")
                    else:
                        # URL에서 확장자 추정
                        url_path = urlparse(src).path
                        url_ext = os.path.splitext(url_path)[1].lstrip(".")
                        if url_ext:
                            ext = url_ext
                    filename = f"{base_name}.{ext}"
                    file_path = images_dir / filename
                    with open(file_path, "wb") as f:
                        f.write(resp.content)
                except Exception as e:
                    logger.error(f"[EXPORT] 이미지 다운로드 실패: url={src}, error={str(e)}")
                    continue

            else:
                # 알 수 없는 형식은 스킵
                logger.warning(f"[EXPORT] 지원하지 않는 이미지 src 형식: {src}")
                continue

            # EXPORT_BLOG_DIR 기준 상대 경로 계산
            try:
                relative_to_base = file_path.relative_to(EXPORT_BLOG_DIR)
            except ValueError:
                # 만약 output_dir가 EXPORT_BLOG_DIR 하위가 아닌 경우 대비
                relative_to_base = file_path
            relative_path = str(relative_to_base).replace("\\", "/")

            generated_images.append({
                "index": img.index,
                "placeholder": img.caption or "",
                "image_path": relative_path,
                "full_path": str(file_path),
                # 에디터에서 설정한 메타데이터를 그대로 보존
                "style": img.style,
                "is_thumbnail": img.is_thumbnail,
            })

        if generated_images:
            blog_content["generated_images"] = generated_images

        # JSON 파일 저장 (export 용 이름)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"blog_export_{timestamp}.json"
        json_path = save_blog_json(blog_content, output_dir=str(output_dir), filename=json_filename)
        logger.info(f"[EXPORT] export json saved: {json_path}")

        # ZIP 파일 생성 (output_dir 전체를 압축)
        zip_filename = f"{output_dir.name}.zip"
        zip_path = output_dir.parent / zip_filename
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    full_path = Path(root) / file
                    # ZIP 안에서는 output_dir 기준 상대 경로로 저장
                    arcname = str(full_path.relative_to(output_dir)).replace("\\", "/")
                    zf.write(full_path, arcname)

        # 클라이언트에 제공할 정적 ZIP 경로 (/static/blog/export_blog/...)
        try:
            relative_zip = zip_path.relative_to(EXPORT_BLOG_DIR)
            zip_relative_path = str(relative_zip).replace("\\", "/")
            zip_url_path = f"/static/blog/export_blog/{zip_relative_path}"
        except ValueError:
            # fallback: 절대 경로 그대로 전달 (프론트에서 직접 사용할 경우)
            zip_url_path = str(zip_path)

        return ExportBlogResponse(
            success=True,
            zip_path=zip_url_path
        )
    except Exception as e:
        logger.error(f"[EXPORT] export-blog 처리 중 오류: {str(e)}")
        return ExportBlogResponse(
            success=False,
            error=f"export-blog 처리 중 오류: {str(e)}"
        )


@app.post("/api/download-images", response_model=DownloadImagesResponse)
async def download_images(request: DownloadImagesRequest):
    """
    생성된 이미지들을 ZIP 파일로 압축하여 다운로드 경로를 반환합니다.
    
    - **image_paths**: 다운로드할 이미지 경로 리스트 (예: ["images/이미지삽입1.jpg", ...])
    """
    try:
        if not request.image_paths:
            return DownloadImagesResponse(
                success=False,
                error="이미지 경로가 제공되지 않았습니다."
            )
        
        # ZIP 파일 생성 디렉토리
        temp_zip_dir = IMAGE_DOWNLOADS_DIR
        
        # ZIP 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"blog_images_{timestamp}.zip"
        zip_path = temp_zip_dir / zip_filename
        
        # ZIP 파일 생성
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, image_path in enumerate(request.image_paths, 1):
                try:
                    # 경로 정규화 (상대 경로 처리)
                    full_path = None
                    
                    if image_path.startswith("/static/blog/create_naver/"):
                        # /static/blog/create_naver/... 형식
                        relative_path = image_path[len("/static/blog/create_naver/"):]
                        full_path = CREATE_NAVER_DIR / Path(unquote(relative_path))
                    elif image_path.startswith("/static/"):
                        # 다른 /static/... 경로
                        relative_path = image_path[len("/static/"):]
                        full_path = project_dir / "static" / Path(unquote(relative_path))
                    elif not os.path.isabs(image_path):
                        # 상대 경로 (create_naver 기준)
                        # images/이미지삽입1.jpg 같은 경우 직접 처리
                        if image_path.startswith("images/"):
                            full_path = CREATE_NAVER_DIR / Path(unquote(image_path))
                        else:
                            # 파일명만 있는 경우 images 폴더 추가
                            full_path = CREATE_NAVER_DIR / "images" / Path(unquote(image_path))
                    else:
                        # 절대 경로
                        full_path = Path(image_path)
                    
                    # 파일 존재 확인 및 디버깅
                    if not full_path:
                        logger.warning(f"[DOWNLOAD_IMAGES] 경로 생성 실패: {image_path}")
                        continue
                    
                    if not full_path.exists():
                        logger.warning(f"[DOWNLOAD_IMAGES] 이미지 파일을 찾을 수 없음: {full_path}, 원본 경로: {image_path}")
                        # images 폴더 안에서 찾기 시도
                        if "images" not in str(full_path):
                            alt_path = CREATE_NAVER_DIR / "images" / full_path.name
                            if alt_path.exists():
                                full_path = alt_path
                                logger.info(f"[DOWNLOAD_IMAGES] 대체 경로에서 찾음: {full_path}")
                            else:
                                continue
                        else:
                            continue
                    
                    # ZIP 내부 파일명 (원본 파일명 유지)
                    arcname = full_path.name
                    zf.write(full_path, arcname)
                    logger.debug(f"[DOWNLOAD_IMAGES] 이미지 추가: {full_path.name}")
                    
                except Exception as e:
                    logger.warning(f"[DOWNLOAD_IMAGES] 이미지 추가 실패: {image_path}, 오류: {e}")
                    continue
        
        # 정적 파일 경로 구성
        try:
            relative_zip = zip_path.relative_to(temp_zip_dir)
            zip_relative_path = str(relative_zip).replace("\\", "/")
            zip_url_path = f"/static/blog/image_downloads/{zip_relative_path}"
            
        except ValueError:
            zip_url_path = str(zip_path)
        
        logger.info(f"[DOWNLOAD_IMAGES] ZIP 파일 생성 완료: {zip_path}, 이미지 수: {len(request.image_paths)}")
        
        return DownloadImagesResponse(
            success=True,
            zip_path=zip_url_path
        )
        
    except Exception as e:
        logger.exception(f"[DOWNLOAD_IMAGES] 오류: {e}")
        return DownloadImagesResponse(
            success=False,
            error=f"이미지 다운로드 중 오류 발생: {str(e)}"
        )


@app.post("/api/generate-blog-ideas", response_model=GenerateBlogIdeasResponse)
async def generate_blog_ideas_api(request: GenerateBlogIdeasRequest, http_request: Request):
    """
    GPT API를 사용하여 블로그 제목과 작성 프롬프트 아이디어를 여러 개 생성합니다.

    - **keyword**: 대표 키워드
    - **topic**: 글의 주제/카테고리 느낌
    - **blog_profile**: 현재 내 블로그의 특징(톤, 타깃, 운영 스타일 등)
    - **extra_prompt**: 추가로 강조하고 싶은 조건/설명 (선택)
    - **count**: 생성할 아이디어 개수 (1~10)
    """
    try:
        # 사용량 제한 확인 (블로그 아이디어 생성용 별도 트래커)
        is_allowed, message = check_blog_ideas_limit(http_request)
        if not is_allowed:
            return GenerateBlogIdeasResponse(
                success=False,
                error=message,
                ideas=[]
            )
        
        keyword = request.keyword.strip()
        topic = request.topic.strip()
        blog_profile = request.blog_profile.strip()

        if not keyword:
            raise ValueError("대표 키워드를 입력해 주세요.")
        # auto_topic이 False인 경우에만 주제 필수
        if not topic and not request.auto_topic:
            raise ValueError("주제를 입력해 주세요.")
        if not blog_profile:
            raise ValueError("내 블로그의 특징을 입력해 주세요.")

        # 안전하게 개수 보정
        count = max(1, min(10, request.count))

        logger.info(
            f"[IDEAS] keyword={keyword!r}, topic={topic!r}, "
            f"count={count}, model={request.model!r}, temperature={request.temperature}, "
            f"auto_topic={request.auto_topic}"
        )

        # 1) GPT로 아이디어 생성 (비동기 처리)
        loop = asyncio.get_event_loop()
        ideas_data = await loop.run_in_executor(
            None,
            generate_blog_ideas,
            keyword,
            topic,
            blog_profile,
            request.extra_prompt,
            count,
            request.model,
            request.temperature,
            request.auto_topic
        )

        if not ideas_data:
            return GenerateBlogIdeasResponse(
                success=False,
                ideas=[],
                error="생성된 아이디어가 없습니다. 입력값을 조금 더 구체적으로 조정해 보세요.",
            )

        idea_items: List[BlogIdeaItem] = []
        zip_url_path: Optional[str] = None

        # 2) 파일 저장 및 ZIP 생성 (save_files=True인 경우)
        if request.save_files:
            # 블로그 아이디어 전용 디렉토리 (blog/create_blog_prompt/yyyymmdd_N)
            output_dir = get_create_blog_prompt_directory()

            for idx, idea in enumerate(ideas_data, start=1):
                title = idea.get("title", "").strip()
                prompt_text = idea.get("prompt", "").strip()

                # 파일명: 인덱스 + 슬러그화된 제목 일부
                base_name = f"idea_{idx:02d}"
                safe_title = slugify_filename(title, max_length=40) or f"{idx:02d}"
                filename = f"{base_name}_{safe_title}.txt"

                file_path = output_dir / filename
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"제목: {title}\n\n")
                    f.write("작성 프롬프트:\n")
                    f.write(prompt_text)
                    f.write("\n")

                # 정적 서빙용 상대 경로 (/static/blog/create_blog_prompt/...)
                try:
                    relative_to_base = file_path.relative_to(CREATE_BLOG_PROMPT_DIR)
                    relative_path = str(relative_to_base).replace("\\\\", "/")
                    static_path = f"/static/blog/create_blog_prompt/{relative_path}"
                except ValueError:
                    static_path = str(file_path)

                idea_items.append(
                    BlogIdeaItem(
                        index=idx,
                        title=title,
                        prompt=prompt_text,
                        file_path=static_path,
                    )
                )

            # 디렉토리 전체를 ZIP으로 압축
            zip_filename = f"{output_dir.name}.zip"
            zip_path = output_dir.parent / zip_filename
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        full_path = Path(root) / file
                        arcname = str(full_path.relative_to(output_dir)).replace("\\\\", "/")
                        zf.write(full_path, arcname)

            # 정적 ZIP 경로 구성 (/static/blog/create_blog_prompt/...)
            try:
                relative_zip = zip_path.relative_to(CREATE_BLOG_PROMPT_DIR)
                zip_relative_path = str(relative_zip).replace("\\\\", "/")
                zip_url_path = f"/static/blog/create_blog_prompt/{zip_relative_path}"
            except ValueError:
                zip_url_path = str(zip_path)

        else:
            # 파일 저장 없이 메모리 내 결과만 반환
            for idx, idea in enumerate(ideas_data, start=1):
                idea_items.append(
                    BlogIdeaItem(
                        index=idx,
                        title=idea.get("title", "").strip(),
                        prompt=idea.get("prompt", "").strip(),
                        file_path=None,
                    )
                )

        return GenerateBlogIdeasResponse(
            success=True,
            ideas=idea_items,
            zip_path=zip_url_path,
        )

    except ValueError as e:
        return GenerateBlogIdeasResponse(
            success=False,
            ideas=[],
            error=f"입력값 오류: {str(e)}",
        )
    except Exception as e:
        logger.exception(f"[IDEAS] error: {e}")
        return GenerateBlogIdeasResponse(
            success=False,
            ideas=[],
            error=f"아이디어 생성 중 오류 발생: {str(e)}",
        )


@app.get("/api/blog-json/{filename:path}")
async def get_blog_json(filename: str):
    """
    저장된 블로그 JSON 파일을 조회합니다.
    
    - **filename**: JSON 파일명 (예: blog_generated_20251205_123456.json)
    """
    try:
        current_dir = Path(__file__).parent
        project_dir = current_dir.parent
        
        # 검색할 디렉토리 목록 (data/blog/create_naver 우선, naver_crawler는 하위 호환성)
        search_dirs = [
            DATA_DIR / "blog" / "create_naver",
            project_dir / "naver_crawler"
        ]
        
        # 파일 찾기 (하위 디렉토리에서 검색)
        json_file = None
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for root, dirs, files in os.walk(search_dir):
                if filename in files:
                    json_file = Path(root) / filename
                    break
            if json_file:
                break
        
        if not json_file or not json_file.exists():
            raise HTTPException(status_code=404, detail=f"JSON 파일을 찾을 수 없습니다: {filename}")
        
        # JSON 파일 읽기
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            blog_data = json.load(f)
        
        return blog_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON 파일 조회 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    # 개발 모드: --reload 옵션으로 코드 변경 시 자동 재시작
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

