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
# ⚖️ [총괄 PD] Strategy Judge (V31. The Partner)
# 목표: 사장님 지시에 대한 'Red Team 검증' 및 '전략적 반론' 기능 추가
# =========================================================

warnings.filterwarnings("ignore")

# 1. 환경 및 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
PLANNING_DIR = CURRENT_DIR 

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")
if API_KEY: genai.configure(api_key=API_KEY)

pd_model = None
MODEL_NAME = "Unknown"

# --- [Helper Functions] ---
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

# --- [Core Logic] ---
def process_planning(mode, user_input, feedback_history=""):
    global pd_model
    logs = []
    def log(msg): logs.append(msg)

    if not pd_model: init_engine()
    log(f"🧠 [PD] 기획 엔진 가동 (Model: {MODEL_NAME})")
    
    # 1. 태스크 정의
    task_desc = ""
    if mode == 1: task_desc = f"Create a BLOCKBUSTER web novel plan. Key: '{user_input}'."
    elif mode == 2: task_desc = f"Upgrade this idea into a HIT novel: '{user_input}'."
    elif mode == 3: task_desc = f"Fix this failed story logic: '{user_input}'."

    # 🔥 [핵심] 사장님 피드백에 대한 태도 정의 (Meta-Prompting)
    feedback_instruction = ""
    if feedback_history:
        feedback_instruction = f"""
        [BOSS FEEDBACK]: "{feedback_history}"
        
        [CRITICAL INSTRUCTION FOR PD]
        1. Do NOT blindy accept the feedback.
        2. Convene a 'Red Team' meeting internally to analyze the risks of this feedback.
        3. If the feedback creates a logical hole or hurts marketability:
           - You MUST express a "Strategic Opposition" (반론).
           - Provide a "Better Alternative" that respects the Boss's intent but fixes the flaw.
        4. If the feedback is perfect, just accept it and proceed.
        """

    prompt = f"""
    You are the Chief Producer of a top-tier web novel studio.
    Your goal is to create a **Perfect Proposal Report** for the CEO.
    
    [Task]
    {task_desc}
    {feedback_instruction}
    
    [Output Format]
    Output a single JSON object (Korean):
    {{
        "title": "Title",
        "genre": "Genre",
        "keywords": ["List"],
        "logline": "Hook",
        "planning_intent": "Intent",
        "characters": [ {{"name": "Name", "role": "Role", "desc": "Desc"}} ],
        "synopsis": "Plot",
        "selling_points": ["List"],
        
        "pd_score": 85,
        "pd_comment": "General comment",
        
        "risk_report": {{
            "detected": true/false,  // Set true if Boss's feedback was risky
            "red_team_warning": "Warning message from Red Team (Why it's dangerous)",
            "alternative_suggestion": "A better way to achieve Boss's goal"
        }}
    }}
    """
    
    try:
        response = pd_model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(text)
        log("✅ 기획 보고서 작성 및 리스크 분석 완료.")
        return result_json, "\n".join(logs)
    except Exception as e:
        log(f"❌ 에러: {e}")
        return {"title": "Error", "logline": str(e)}, "\n".join(logs)

def save_and_deploy(plan_data):
    try:
        path, title = manage_project_folder(plan_data)
        (path / "Approved_Plan.json").write_text(json.dumps(plan_data, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 사장님용 보고서 (TXT)
        readable_report = f"""
        [웹소설 기획안 보고서]
        제목: {plan_data.get('title')}
        장르: {plan_data.get('genre')}
        로그라인: {plan_data.get('logline')}
        
        [PD 리스크 리포트]
        리스크 감지: {plan_data.get('risk_report', {}).get('detected')}
        경고: {plan_data.get('risk_report', {}).get('red_team_warning', '없음')}
        대안: {plan_data.get('risk_report', {}).get('alternative_suggestion', '없음')}
        
        [시놉시스]
        {plan_data.get('synopsis')}
        """
        (path / "Project_Report.txt").write_text(readable_report, encoding='utf-8')
        return True, f"저장 완료: {path}"
    except Exception as e:
        return False, f"저장 실패: {e}"