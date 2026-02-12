import os
import json
import time
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# =========================================================
# ⚖️ [총괄 PD] Strategy Judge (Web API Ver)
# 위치: 03_전략기획실_Planning/strategy_judge.py
# =========================================================

# 환경 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# 모델 로드 (전역 변수)
pd_model = None

def init_engine():
    """엔진 시동 (app.py가 호출)"""
    global pd_model
    try:
        pd_model = genai.GenerativeModel("gemini-1.5-pro-latest")
        return True, "PD Engine Online (Gemini 1.5 Pro)"
    except Exception as e:
        return False, f"Engine Fail: {str(e)}"

def process_planning(mode, user_input):
    """
    [핵심] app.py에서 호출하는 함수
    mode: 1(오리지널), 2(유저기획), 3(심폐소생)
    """
    logs = []
    def log(msg): logs.append(msg)

    log(f"🧠 [PD] 기획 엔진 가동... 모드: {mode}")

    # 1. 프롬프트 구성
    role = "You are the Chief Producer of a Web Novel Studio."
    task = ""
    if mode == 1: task = f"Create a block-buster web novel plan. Input keyword: {user_input}"
    elif mode == 2: task = f"Develop this user idea into a hit novel: {user_input}"
    elif mode == 3: task = f"Fix this failed story logic: {user_input}"

    prompt = f"""
    {role}
    Task: {task}
    Output Format: JSON only.
    Keys required: "title", "genre", "logline", "selling_points"(list), "character_brief"
    Language: Korean
    """

    # 2. Gemini 호출
    try:
        if not pd_model: init_engine()
        response = pd_model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(text)
        
        log("✅ 기획안 생성 완료.")
        return result_json, "\n".join(logs)

    except Exception as e:
        log(f"❌ 에러 발생: {e}")
        # 실패 시 비상용 더미 데이터 리턴 (앱이 안 죽게)
        dummy = {
            "title": "생성 실패 (API 에러)",
            "logline": f"에러 내용: {str(e)}",
            "selling_points": ["API 키 확인 필요", "네트워크 확인 필요"]
        }
        return dummy, "\n".join(logs)