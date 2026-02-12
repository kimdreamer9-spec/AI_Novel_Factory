import os
import json
import sys
import random
import re
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 환경 및 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

try:
    from model_selector import find_best_model
    MODEL_NAME = find_best_model()
except ImportError:
    MODEL_NAME = 'gemini-1.5-pro-latest'

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# 2. 데이터 경로
RUBRIC_FILE = PROJECT_ROOT / "00_기준정보_보물창고" / "standard-rubric.json"
TREND_REPORT = PROJECT_ROOT / "02_분석실_Analysis" / "00_통합_트렌드_리포트.json"
TIP_DIR = PROJECT_ROOT / "00_기준정보_보물창고" / "05_팁_보물창고"

# 3. Few-Shot Examples (Style Guide)
FEW_SHOT_EXAMPLES = """
[Example: Hunter/Regression]
Logline: "멸망한 세상의 보상 담당관이 회귀했다. 이제 모든 꿀 보상은 내 것이다."
Characters: [Main] 강진우(보상 전문가), [Sub] 박지훈(정보통), [Sub] 최서윤(라이벌), [Sub] 황회장(빌런), [Sub] 시스템 관리자(조력자)
"""

def gather_materials(mode):
    rubric = RUBRIC_FILE.read_text(encoding='utf-8') if RUBRIC_FILE.exists() else ""
    trend = TREND_REPORT.read_text(encoding='utf-8') if TREND_REPORT.exists() else ""
    tips_data = ""
    try:
        if TIP_DIR.exists():
            tips = list(TIP_DIR.rglob("*.md")) + list(TIP_DIR.rglob("*.txt"))
            if tips:
                selected = random.sample(tips, min(len(tips), 5))
                for f in selected:
                    tips_data += f"\n[Tip: {f.name}]\n{f.read_text(encoding='utf-8')[:800]}\n"
    except: pass
    return rubric, trend, tips_data

def create_plan(round_num, feedback, mode=1, user_input=""):
    rubric, trend, tips = gather_materials(mode)
    
    task_desc = "Create a Commercial Hit Novel."
    if mode == 2: task_desc = "Develop User Idea."
    elif mode == 3: task_desc = "Fix Failed Story."

    prompt = f"""
    # Role
    You are **Korea's Top Web Novel CP**. strict and data-driven.

    # RAG Context
    - [Trend]: {trend[:1500]}
    - [Rubric]: {rubric[:1000]}
    - [Tips]: {tips}

    # Input
    - Request: "{user_input}"
    - Feedback: "{feedback}" (Fix these issues!)

    # Requirements
    1. **Format**: JSON ONLY.
    2. **Characters**: Create **EXACTLY 5 Characters** (1 Main + 4 Key Subs). 
       - Must have distinct roles (Protagonist, Antagonist, Helper, Rival, etc.).
    3. **World**: Include specific 'World/System Settings' (Rules of the world).
    4. **Language**: Korean.

    # Output JSON Structure
    {{
        "title": "Title",
        "genre": "Genre",
        "keywords": ["#Tag1", "#Tag2"],
        "logline": "1 sentence hook",
        "planning_intent": "Planning Intent & Commercial Strategy",
        "world_view": "Specific World Setting & System Rules (e.g., Reward System, Regression Rule)",
        "characters": [
            {{ "name": "Name", "role": "Main Protagonist", "mbti": "Type", "desc": "Desire, Ability, Flaw" }},
            {{ "name": "Name", "role": "Main Antagonist", "desc": "..." }},
            {{ "name": "Name", "role": "Sub Character", "desc": "..." }},
            {{ "name": "Name", "role": "Sub Character", "desc": "..." }},
            {{ "name": "Name", "role": "Sub Character", "desc": "..." }}
        ],
        "synopsis": "Full Story (Intro -> Development -> Crisis -> Climax)",
        "episode_plots": [
            {{ "ep": 1, "title": "...", "summary": "..." }},
            {{ "ep": 2, "title": "...", "summary": "..." }},
            {{ "ep": 3, "title": "...", "summary": "..." }},
            {{ "ep": 4, "title": "...", "summary": "..." }},
            {{ "ep": 5, "title": "...", "summary": "..." }}
        ],
        "sales_points": ["Point 1", "Point 2", "Point 3"]
    }}
    """
    
    try:
        res = model.generate_content(prompt)
        text = res.text.strip()
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text: text = text.replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"title": "Error", "logline": str(e), "is_corrupted": True}