import os
import json
import sys
import random
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# [Setup] 환경 설정 및 경로 안전장치
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# API 키 로드
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

# 모델 선택기 연결
try:
    import model_selector
    MODEL_NAME = model_selector.find_best_model()
except: MODEL_NAME = "gemini-1.5-flash"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# =========================================================
# 📂 [RAG Logic] Smart Sampling (사장님 로직 100% 보존)
# =========================================================
BASE_INFO_DIR = PROJECT_ROOT / "00_기준정보_보물창고"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"
RAW_DATA_DIR = PROJECT_ROOT / "01_자료실_Raw_Data" / "00_성공작_아카이브"

def get_smart_references():
    """
    [CTO Solution] 
    전체를 다 읽으면 AI가 체합니다. 
    성공작 중 '랜덤으로 3개'만 골라서 '도입부(초반)' 텍스트만 훔쳐옵니다.
    """
    refs = ""
    if RAW_DATA_DIR.exists():
        # 모든 마크다운 파일 탐색
        md_files = list(RAW_DATA_DIR.rglob("*.md"))
        
        if md_files:
            # 🔥 [핵심] 랜덤으로 3개만 뽑음 (과부하 방지 + 다양성 확보)
            selected = random.sample(md_files, min(len(md_files), 3))
            
            for f in selected:
                try:
                    # 파일 내용 읽기 (너무 길면 앞부분 5000자만 끊음 -> 도입부 훅이 중요하니까)
                    content = f.read_text(encoding='utf-8')[:5000]
                    refs += f"\n=== [Reference: {f.name}] ===\n{content}\n============================\n"
                except: pass
    
    if not refs:
        refs = "(참고할 원문 데이터가 없습니다. 분석 리포트로 대체합니다.)"
        
    return refs

def gather_materials(mode):
    context_data = {
        "rubric": "", "trend": "", "setting_trend": "", 
        "success_raw_text": ""
    }

    # 1. 루브릭 & 트렌드 (이건 기본 헌법이니 무조건 읽음)
    RUBRIC_FILE = BASE_INFO_DIR / "standard-rubric.json"
    TREND_REPORT = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
    
    if RUBRIC_FILE.exists(): context_data["rubric"] = RUBRIC_FILE.read_text(encoding='utf-8')
    if TREND_REPORT.exists(): context_data["trend"] = TREND_REPORT.read_text(encoding='utf-8')

    # 2. 설정 파일 (규칙)
    SETTING_DIR = BASE_INFO_DIR / "04_설정_트랜드"
    if SETTING_DIR.exists():
        files = list(SETTING_DIR.rglob("*.md"))
        # 설정 파일은 짧으니까 최대 5개까지 읽음
        for f in random.sample(files, min(len(files), 5)) if files else []:
            context_data["setting_trend"] += f"\n[Rule: {f.name}]\n{f.read_text(encoding='utf-8')[:2000]}"

    # 3. 🔥 [Smart Sampling] 원문 3개만 딥러닝
    context_data["success_raw_text"] = get_smart_references()

    return context_data

# =========================================================
# ✍️ [Generator: 2026 Creative Brain]
# =========================================================

def create_plan(round_num, feedback, mode=1, user_input=""):
    materials = gather_materials(mode)

    prompt = f"""
    You are **Korea's No.1 Web Novel CP (Creative Planner)**.
    Current Era: 2026. The market demands **Fast Pacing** and **Clear Rewards**.

    [Mission]: Create a top-tier web novel plan based on the User Input.

    [Secret Weapon: Actual Hit Novel Snippets]
    The following texts are **RAW** snippets from mega-hit novels.
    **Do NOT copy the plot.** **Copy the 'Vibe', 'Pacing', and 'Stimulation' of these texts.**
    
    {materials['success_raw_text']}

    [Trend & Rules]
    {materials['setting_trend']}

    [User Request]
    "{user_input}"

    [Feedback from Red Team (Previous Round)]
    "{feedback}"

    [Thinking Process (CoT)]
    1. **Analyze the Reference**: How do the hits start? What is the 'Hook'?
    2. **Apply to User Idea**: Inject that 'Hook Style' into the user's concept.
    3. **World Building**: Ensure the settings follow the [Rules].
    4. **Character Design**: Create 5 distinct characters with conflicting desires.
    5. **SWOT Analysis**: Evaluate the commercial potential.
    6. **Synopsis Structuring**: Plan the story flow, specifically detailing Ep 1-5.

    [CRITICAL REQUIREMENT - DO NOT IGNORE]
    1. **Synopsis**: Must cover **Episode 1 to 5** in detail. Do NOT stop at Ep 3.
    2. **Future Plot**: Summarize the story arc after Ep 5.
    3. **Language**: **KOREAN ONLY**.

    [Output JSON Structure]
    {{
        "title": "Title (Catchy & Trendy)",
        "genre": "Genre",
        "keywords": ["Keyword1", "Keyword2", ...],
        "logline": "One sentence summary that hooks readers.",
        "planning_intent": "Strategic reason why this works commercially.",
        "world_view": "Detailed setting rules.",
        "swot_analysis": {{
            "strength": "Strong point...",
            "weakness": "Weak point...",
            "opportunity": "Market opportunity...",
            "threat": "Competition..."
        }},
        "characters": [
            {{ "name": "Name", "role": "Main Protagonist", "desc": "Personality, Desire, Ability" }},
            {{ "name": "Name", "role": "Main Antagonist", "desc": "..." }},
            {{ "name": "Name", "role": "Sub (Helper)", "desc": "..." }},
            {{ "name": "Name", "role": "Sub (Rival)", "desc": "..." }},
            {{ "name": "Name", "role": "Sub (Extra)", "desc": "..." }}
        ],
        "synopsis": "Full story summary (Introduction -> Development -> Turn -> Climax -> Ending)",
        "episode_plots": [
            {{ "ep": 1, "title": "Ep 1 Title", "summary": "Detailed event..." }},
            {{ "ep": 2, "title": "Ep 2 Title", "summary": "Detailed event..." }},
            {{ "ep": 3, "title": "Ep 3 Title", "summary": "Detailed event..." }},
            {{ "ep": 4, "title": "Ep 4 Title", "summary": "Detailed event..." }},
            {{ "ep": 5, "title": "Ep 5 Title", "summary": "Detailed event..." }}
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