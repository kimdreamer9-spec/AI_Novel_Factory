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
# ⚖️ [총괄 PD] Strategy Judge (V36. Data-Driven Analysis)
# 목표: RAG 기반의 냉철한 전략 분석 및 근거 제시
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
    """RAG: 분석 및 기획에 필요한 핵심 데이터 로드"""
    context = ""
    try:
        # 트렌드 리포트
        trend_file = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
        if trend_file.exists():
            context += f"\n[Market Trend Report (2026)]:\n{trend_file.read_text(encoding='utf-8')[:4000]}\n"
        
        # 평가 루브릭
        rubric_file = KNOWLEDGE_DIR / "standard-rubric.json"
        if rubric_file.exists():
            context += f"\n[Evaluation Rubric]:\n{rubric_file.read_text(encoding='utf-8')[:3000]}\n"
            
        # 성공 팁
        tip_file = KNOWLEDGE_DIR / "팁_보물창고.txt" # 가상의 파일명, 실제 파일이 있다면 연결
        if tip_file.exists():
             context += f"\n[Success Tips]:\n{tip_file.read_text(encoding='utf-8')[:2000]}\n"
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
    if mode == 1: task_desc = f"Create a BLOCKBUSTER web novel plan. Key: '{user_input}'."
    elif mode == 2: task_desc = f"Develop this user idea into a commercial hit: '{user_input}'."
    elif mode == 3: task_desc = f"Rescue this failed story setup: '{user_input}'."

    feedback_instruction = ""
    if feedback_history:
        feedback_instruction = f"""
        [BOSS FEEDBACK]: "{feedback_history}"
        [INSTRUCTION]: The Boss wants changes. 
        However, as a Strategy Officer, do NOT just blindly follow. 
        Analyze the request against [Market Trend Report] and [Evaluation Rubric].
        If the request hurts commerciality, warn about it in the 'strategy_analysis' section, but still reflect the changes in the plan.
        """

    # 🔥 [핵심] 전략 분석실(Strategy Office) 페르소나 주입
    prompt = f"""
    You are the **Chief Strategy Officer (CSO)** and **Red Team Leader** of a top-tier web novel studio.
    Your goal is to create a high-selling web novel plan that strictly follows market trends.
    
    [Reference Data (RAG)]
    {knowledge}
    
    [Task]
    {task_desc}
    {feedback_instruction}
    
    [Output Requirements]
    1.  **Format:** JSON Only (Korean).
    2.  **Detail:** 'composition' (Eps 1-25) MUST be detailed with specific events.
    3.  **Analysis:** You MUST provide a 'strategy_analysis' object that critiques this plan based on the provided [Reference Data]. Quote specific trends or rubric criteria.
    
    [Output JSON Structure]
    {{
        "title": "Title",
        "genre": "Genre",
        "keywords": ["Tag1", "Tag2"],
        "target_reader": "Target Audience",
        "logline": "1 sentence hook",
        "planning_intent": "Intent",
        "selling_points": ["Point 1", "Point 2"],
        "characters": [ {{"name": "Name", "role": "Role", "desc": "Desc"}} ],
        "synopsis": "Full Summary",
        "composition": {{
            "beginning": "1~25화: [발단] ... [전개] ... [위기] ... [절정] ... [결말] ...",
            "middle": "26~100화: ...",
            "end": "101화~: ..."
        }},
        "ep1_core_points": {{
            "opening": "...", "climax": "...", "ending": "..."
        }},
        "strategy_analysis": {{
            "trend_score": 95, 
            "trend_comment": "Analyzed based on [Market Trend Report]...",
            "rubric_evaluation": "Based on [Evaluation Rubric], the pacing is...",
            "red_team_warning": "Cold objective criticism (e.g., 'The villain is too weak').",
            "improvement_suggestion": "Actionable advice to fix the warning."
        }}
    }}
    """
    
    try:
        response = pd_model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(text)
        log("✅ 전략적 기획안 및 분석 보고서 생성 완료.")
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