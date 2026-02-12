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
# ⚖️ [총괄 PD] Strategy Judge (V32. Knowledge Integration)
# 목표: 트렌드, 팁, 루브릭을 RAG로 참조하여 기획
# =========================================================

warnings.filterwarnings("ignore")

# 1. 환경 및 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
PLANNING_DIR = CURRENT_DIR 

# [RAG] 참조할 지식 창고 경로
KNOWLEDGE_DIR = PROJECT_ROOT / "00_기준정보_보물창고"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"

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

# 🔥 [NEW] RAG: 지식 가져오기 함수
def fetch_knowledge():
    context = ""
    
    # 1. 트렌드 리포트 (필수)
    trend_file = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
    if trend_file.exists():
        try:
            context += f"\n[Market Trend Report]:\n{trend_file.read_text(encoding='utf-8')[:3000]}\n"
        except: pass
        
    # 2. 루브릭 (필수)
    rubric_file = KNOWLEDGE_DIR / "standard-rubric.json"
    if rubric_file.exists():
        try:
            context += f"\n[Evaluation Rubric]:\n{rubric_file.read_text(encoding='utf-8')[:2000]}\n"
        except: pass
        
    # 3. 팁 (랜덤 or 핵심)
    tip_file = KNOWLEDGE_DIR / "팁_도입부.md"
    if tip_file.exists():
         context += f"\n[Writing Tips]:\n{tip_file.read_text(encoding='utf-8')[:1000]}\n"
         
    return context

# --- [Core Logic] ---
def process_planning(mode, user_input, feedback_history=""):
    global pd_model
    logs = []
    def log(msg): logs.append(msg)

    if not pd_model: init_engine()
    log(f"🧠 [PD] 기획 엔진 가동 (Model: {MODEL_NAME})")
    
    # 1. 지식 로드 (RAG)
    knowledge_context = fetch_knowledge()
    log("📚 트렌드 리포트 및 작법 팁 참조 완료.")

    # 2. 태스크 정의
    task_desc = ""
    if mode == 1: task_desc = f"Create a BLOCKBUSTER web novel plan. Key: '{user_input}'."
    elif mode == 2: task_desc = f"Upgrade this idea into a HIT novel: '{user_input}'."
    elif mode == 3: task_desc = f"Fix this failed story logic: '{user_input}'."

    feedback_instruction = ""
    if feedback_history:
        feedback_instruction = f"""
        [BOSS FEEDBACK]: "{feedback_history}"
        [CRITICAL INSTRUCTION]: Do NOT blindy accept. Use Red Team logic to verify risks.
        If risky, suggest alternatives. If perfect, accept.
        """

    prompt = f"""
    You are the Chief Producer of a top-tier web novel studio (Korea).
    
    [Reference Knowledge]
    {knowledge_context}
    
    [Task]
    {task_desc}
    {feedback_instruction}
    
    [Requirements]
    1. Reflect the [Market Trend Report] to ensure commercial success.
    2. Follow the [Writing Tips] for character and plot structure.
    
    [Output Format (Korean)]
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
        "pd_comment": "Based on Rubric",
        "risk_report": {{
            "detected": true/false,
            "red_team_warning": "msg",
            "alternative_suggestion": "msg"
        }}
    }}
    """
    
    try:
        response = pd_model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(text)
        log("✅ 기획 보고서 작성 완료.")
        return result_json, "\n".join(logs)
    except Exception as e:
        log(f"❌ 에러: {e}")
        return {"title": "Error", "logline": str(e)}, "\n".join(logs)

def save_and_deploy(plan_data):
    try:
        path, title = manage_project_folder(plan_data)
        (path / "Approved_Plan.json").write_text(json.dumps(plan_data, indent=2, ensure_ascii=False), encoding='utf-8')
        
        readable_report = f"""
        [웹소설 기획안 보고서]
        제목: {plan_data.get('title')}
        장르: {plan_data.get('genre')}
        로그라인: {plan_data.get('logline')}
        
        [PD 코멘트] {plan_data.get('pd_comment')}
        [시놉시스] {plan_data.get('synopsis')}
        """
        (path / "Project_Report.txt").write_text(readable_report, encoding='utf-8')
        return True, f"저장 완료: {path}"
    except Exception as e:
        return False, f"저장 실패: {e}"