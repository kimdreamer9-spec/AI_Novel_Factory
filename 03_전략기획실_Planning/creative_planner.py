import os
import json
import sys
import random
import re
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 환경 및 경로 설정 (Path Fix)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# 루트 경로 추가 (model_selector 찾기 위함)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# 모델 로드
try:
    from model_selector import find_best_model
    MODEL_NAME = find_best_model()
except ImportError:
    MODEL_NAME = 'gemini-1.5-pro-latest'

model = genai.GenerativeModel(MODEL_NAME)

RUBRIC_FILE = PROJECT_ROOT / "00_기준정보_보물창고" / "standard-rubric.json"
TREND_REPORT = PROJECT_ROOT / "02_분석실_Analysis" / "00_통합_트렌드_리포트.json"
TIP_DIR = PROJECT_ROOT / "00_기준정보_보물창고" / "05_팁_보물창고"
DB_DIR = PROJECT_ROOT / "04_설정_자료집"

# ... (Golden Template 및 gather_materials 함수는 동일) ...
GOLDEN_TEMPLATE = """
{
  "title": "Title",
  "genre": "Genre",
  "logline": "Logline",
  "planning_intent": "Intent",
  "characters": [
    {"name": "Main", "role": "Protagonist", "desc": "Desc"},
    {"name": "Sub1", "role": "Antagonist", "desc": "Desc"},
    {"name": "Sub2", "role": "Helper", "desc": "Desc"},
    {"name": "Sub3", "role": "Rival", "desc": "Desc"},
    {"name": "Sub4", "role": "Extra", "desc": "Desc"}
  ],
  "synopsis": "Synopsis",
  "episode_plots": [{"ep": 1, "title": "T", "summary": "S"}],
  "sales_points": ["P1", "P2"]
}
"""

def gather_materials(mode):
    rubric = RUBRIC_FILE.read_text(encoding='utf-8') if RUBRIC_FILE.exists() else ""
    trend = TREND_REPORT.read_text(encoding='utf-8') if TREND_REPORT.exists() else ""
    tips_data = ""
    try:
        if TIP_DIR.exists():
            tip_files = list(TIP_DIR.rglob("*.md"))
            for f in tip_files[:5]:
                tips_data += f"\n[Tip: {f.name}]\n{f.read_text(encoding='utf-8')[:1000]}\n"
    except: pass
    return rubric, trend, tips_data

def create_plan(round_num, feedback, mode=1, user_input=""):
    rubric, trend, tips = gather_materials(mode)
    
    prompt = f"""
    Role: Web Novel Planner.
    Task: Create a plan based on user input: '{user_input}'.
    Mode: {mode} (1:New, 2:Develop, 3:Fix).
    Feedback: {feedback}
    
    [Requirements]
    1. Output JSON ONLY.
    2. EXACTLY 5 Characters (1 Main + 4 Sub).
    3. Follow the Golden Template structure.
    
    [Template]
    {GOLDEN_TEMPLATE}
    """
    
    try:
        res = model.generate_content(prompt)
        text = res.text.replace("```json", "").replace("```", "").strip()
        # JSON 파싱 시도
        try:
            return json.loads(text)
        except:
            # 중괄호만 추출
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: return json.loads(match.group(0))
            return {"title": "Error", "logline": "JSON Parsing Failed", "is_corrupted": True}
    except Exception as e:
        return {"title": "Error", "logline": str(e), "is_corrupted": True}