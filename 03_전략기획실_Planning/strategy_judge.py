import os
import json
import sys
import re
import warnings
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# =========================================================
# ⚖️ [총괄 PD] Strategy Judge (V35. Detailed Plot)
# 목표: 초반 25화 구체적 플롯 강제 생성 (Lazy AI 방지)
# =========================================================

warnings.filterwarnings("ignore")

# 1. 절대 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
PLANNING_DIR = CURRENT_DIR 

KNOWLEDGE_DIR = PROJECT_ROOT / "00_기준정보_보물창고"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")
if API_KEY: genai.configure(api_key=API_KEY)

pd_model = None
MODEL_NAME = "Unknown"

# --- [초기화 및 유틸] ---
def init_engine():
    global pd_model, MODEL_NAME
    try:
        import model_selector
        MODEL_NAME = model_selector.find_best_model()
        pd_model = genai.GenerativeModel(MODEL_NAME)
        return True, f"Engine Online: {MODEL_NAME}"
    except:
        MODEL_NAME = "gemini-1.5-pro-latest"
        pd_model = genai.GenerativeModel(MODEL_NAME)
        return True, f"Engine Online: {MODEL_NAME} (Fallback)"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")[:40]

def manage_project_folder(plan_data):
    raw_title = plan_data.get('title', '무제')
    safe_title = sanitize_filename(raw_title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    folder_name = f"{timestamp}_{safe_title}"
    new_path = PLANNING_DIR / folder_name
    new_path.mkdir(parents=True, exist_ok=True)
    return new_path, safe_title

def fetch_knowledge():
    context = ""
    try:
        trend_file = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
        if trend_file.exists():
            context += f"\n[Market Trend]:\n{trend_file.read_text(encoding='utf-8')[:3000]}\n"
    except: pass
    return context

# --- [핵심 로직] ---
def process_planning(mode, user_input, feedback_history=""):
    global pd_model
    logs = []
    def log(msg): logs.append(msg)

    if not pd_model: init_engine()
    log(f"🧠 [PD] 기획 엔진 가동 (Model: {MODEL_NAME})")
    
    knowledge = fetch_knowledge()
    
    task_desc = ""
    if mode == 1: task_desc = f"Create a HIT Novel Plan. Keyword: '{user_input}'."
    elif mode == 2: task_desc = f"Develop User Idea: '{user_input}'."
    elif mode == 3: task_desc = f"Fix Failed Story: '{user_input}'."

    feedback_instruction = ""
    if feedback_history:
        feedback_instruction = f"""
        [BOSS FEEDBACK]: "{feedback_history}"
        [INSTRUCTION]: Reflect this feedback perfectly.
        """

    # 🔥 [핵심 변경] composition 필드에 대한 구체적 지시 추가
    prompt = f"""
    You are the Chief Producer of a top-tier web novel studio in Korea.
    Generate a **Web Novel Planning Proposal** strictly following the format below.
    
    [Reference]
    {knowledge}
    
    [Task]
    {task_desc}
    {feedback_instruction}
    
    [CRITICAL RULE]
    - **Never leave 'composition' empty.** - The 'beginning' (Eps 1-25) MUST be detailed. Describe the Inciting Incident, Awakening, First Antagonist, and the Resolution of the first arc.
    
    [Output JSON Format (Korean)]
    Return ONLY a JSON object with these exact keys:
    {{
        "title": "Title (Hooky)",
        "genre": "Genre",
        "keywords": ["Tag1", "Tag2"],
        "target_reader": "Target Audience",
        "logline": "1 sentence hook",
        "planning_intent": "Commercial Strategy",
        "selling_points": ["Point 1", "Point 2"],
        "characters": [
            {{"name": "Name", "role": "Role", "desc": "Personality"}}
        ],
        "synopsis": "Full Summary",
        "composition": {{
            "beginning": "1~25화: [발단] 주인공의 각성 계기 -> [전개] 첫 번째 위기 및 능력 획득 -> [절정] 첫 빌런/라이벌 등장 및 사이다 해결 -> [결말] 더 큰 세계로의 진입 암시",
            "middle": "26~100화: 세력 확장, 새로운 조력자 영입, 중간 보스와의 대립 심화",
            "end": "101화~: 최종 흑막 등장, 세계관의 비밀 해소, 완벽한 엔딩"
        }},
        "ep1_core_points": {{
            "opening": "Opening Scene",
            "climax": "Episode 1 Climax",
            "ending": "Cliffhanger Ending"
        }},
        "risk_report": {{
            "detected": true/false,
            "red_team_warning": "Warning message",
            "alternative_suggestion": "Solution"
        }}
    }}
    """
    
    try:
        response = pd_model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(text)
        log("✅ 표준 기획안 생성 완료.")
        return result_json, "\n".join(logs)
    except Exception as e:
        log(f"❌ 에러: {e}")
        return {"title": "Error", "logline": str(e), "genre": "Error"}, "\n".join(logs)

def save_and_deploy(plan_data):
    try:
        path, title = manage_project_folder(plan_data)
        (path / "Approved_Plan.json").write_text(json.dumps(plan_data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True, f"저장 완료: {path.name}"
    except Exception as e:
        return False, f"저장 실패: {e}"