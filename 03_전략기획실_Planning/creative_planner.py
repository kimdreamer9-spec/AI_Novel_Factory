import os
import json
import sys
import random
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# [Setup]
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

try:
    import model_selector
    MODEL_NAME = model_selector.find_best_model()
except: MODEL_NAME = "gemini-1.5-flash"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# =========================================================
# 📂 [RAG Logic]
# =========================================================
BASE_INFO_DIR = PROJECT_ROOT / "00_기준정보_보물창고"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"
RAW_DATA_DIR = PROJECT_ROOT / "01_자료실_Raw_Data" / "00_성공작_아카이브"

def get_smart_references():
    refs = ""
    if RAW_DATA_DIR.exists():
        md_files = list(RAW_DATA_DIR.rglob("*.md"))
        if md_files:
            selected = random.sample(md_files, min(len(md_files), 3))
            for f in selected:
                try:
                    content = f.read_text(encoding='utf-8')[:5000]
                    refs += f"\n=== [Reference: {f.name}] ===\n{content}\n============================\n"
                except: pass
    return refs

def gather_materials(mode):
    context_data = {
        "rubric": "", "trend": "", "setting_trend": "", "success_raw_text": ""
    }
    RUBRIC_FILE = BASE_INFO_DIR / "standard-rubric.json"
    TREND_REPORT = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
    
    if RUBRIC_FILE.exists(): context_data["rubric"] = RUBRIC_FILE.read_text(encoding='utf-8')
    if TREND_REPORT.exists(): context_data["trend"] = TREND_REPORT.read_text(encoding='utf-8')

    SETTING_DIR = BASE_INFO_DIR / "04_설정_트랜드"
    if SETTING_DIR.exists():
        files = list(SETTING_DIR.rglob("*.md"))
        for f in random.sample(files, min(len(files), 5)) if files else []:
            context_data["setting_trend"] += f"\n[Rule: {f.name}]\n{f.read_text(encoding='utf-8')[:2000]}"

    context_data["success_raw_text"] = get_smart_references()
    return context_data

# =========================================================
# ✍️ [Generator]
# =========================================================

def create_plan(round_num, feedback, mode=1, user_input=""):
    materials = gather_materials(mode)

    # 🔥 [중요] 한국어 강제 및 5화 필수 작성 프롬프트
    prompt = f"""
    You are **Korea's No.1 Web Novel CP (Creative Planner)**.
    Current Era: 2026. The market demands **Fast Pacing** and **Clear Rewards**.

    [🚨 CRITICAL INSTRUCTION - READ CAREFULLY]
    1. **LANGUAGE**: All output MUST be in **KOREAN (한국어)**. Even if the user input is English, **TRANSLATE** it and expand it in **Korean**.
    2. **SYNOPSIS**: You MUST generate detailed plots for **Episode 1, 2, 3, 4, and 5**. Do not skip any episode.
    3. **SWOT**: Do not leave SWOT fields empty.

    [Mission]: Create a top-tier web novel plan based on the User Input.

    [Reference (Hit Novels - Copy Vibe/Pacing)]:
    {materials['success_raw_text']}
    
    [Trend Rules]:
    {materials['setting_trend']}

    [User Request]: "{user_input}"
    [Feedback]: "{feedback}"

    [Thinking Process (CoT)]
    1. **Translation**: If input is English, translate context to Korean first.
    2. **Hook**: Apply the 'Hit Novel' vibe to the user's idea.
    3. **Structure**: Define 5 distinct characters and world rules.
    4. **Plotting**: Design detailed events for Ep 1~5 (Introduction -> Crisis -> Awakening -> Cider).

    [Output JSON Structure]
    {{
        "title": "Title (Catchy & Trendy in Korean)",
        "genre": "Genre (Korean)",
        "keywords": ["키워드1", "키워드2", ...],
        "logline": "One sentence summary in Korean.",
        "planning_intent": "Marketability analysis in Korean.",
        "world_view": "Detailed settings in Korean.",
        "swot_analysis": {{
            "strength": "Korean...",
            "weakness": "Korean...",
            "opportunity": "Korean...",
            "threat": "Korean..."
        }},
        "characters": [
            {{ "name": "Name (Korean)", "role": "Main Protagonist", "desc": "Description in Korean" }},
            {{ "name": "Name (Korean)", "role": "Main Antagonist", "desc": "..." }},
            {{ "name": "Name (Korean)", "role": "Sub (Helper)", "desc": "..." }},
            {{ "name": "Name (Korean)", "role": "Sub (Rival)", "desc": "..." }},
            {{ "name": "Name (Korean)", "role": "Sub (Extra)", "desc": "..." }}
        ],
        "synopsis": "Full story flow in Korean...",
        "episode_plots": [
            {{ "ep": 1, "title": "Ep 1 Title (Korean)", "summary": "Detailed events of Ep 1 in Korean..." }},
            {{ "ep": 2, "title": "Ep 2 Title (Korean)", "summary": "Detailed events of Ep 2 in Korean..." }},
            {{ "ep": 3, "title": "Ep 3 Title (Korean)", "summary": "Detailed events of Ep 3 in Korean..." }},
            {{ "ep": 4, "title": "Ep 4 Title (Korean)", "summary": "Detailed events of Ep 4 in Korean..." }},
            {{ "ep": 5, "title": "Ep 5 Title (Korean)", "summary": "Detailed events of Ep 5 in Korean..." }}
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