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
# ⚖️ [총괄 PD] Strategy Judge (V33. Final Engine)
# =========================================================

warnings.filterwarnings("ignore")

# 1. 절대 경로 설정 (나노 단위 고정)
CURRENT_DIR = Path(__file__).resolve().parent # 03_전략기획실 폴더
PROJECT_ROOT = CURRENT_DIR.parent             # 최상위 루트
PLANNING_DIR = CURRENT_DIR                    # 기획안 저장될 곳

# 지식 참조 경로
KNOWLEDGE_DIR = PROJECT_ROOT / "00_기준정보_보물창고"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"

# 루트 경로 인식 (model_selector 찾기 위함)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# API 키 로드
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
    """RAG: 트렌드와 루브릭을 읽어옵니다."""
    context = ""
    try:
        trend_file = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
        if trend_file.exists():
            context += f"\n[Market Trend]:\n{trend_file.read_text(encoding='utf-8')[:3000]}\n"
        
        rubric_file = KNOWLEDGE_DIR / "standard-rubric.json"
        if rubric_file.exists():
            context += f"\n[Rubric]:\n{rubric_file.read_text(encoding='utf-8')[:2000]}\n"
    except: pass
    return context

# --- [핵심 로직] ---
def process_planning(mode, user_input, feedback_history=""):
    global pd_model
    logs = []
    def log(msg): logs.append(msg)

    if not pd_model: init_engine()
    log(f"🧠 [PD] 기획 엔진 가동 (Model: {MODEL_NAME})")
    
    # 지식 주입
    knowledge = fetch_knowledge()
    
    # 모드별 태스크
    task_desc = ""
    if mode == 1: task_desc = f"Create a WEB NOVEL PLAN. Keyword: '{user_input}'."
    elif mode == 2: task_desc = f"Develop this idea: '{user_input}'."
    elif mode == 3: task_desc = f"Fix this story: '{user_input}'."

    # 피드백 반영 (리메이크 시)
    feedback_instruction = ""
    if feedback_history:
        feedback_instruction = f"""
        [BOSS FEEDBACK]: "{feedback_history}"
        [INSTRUCTION]: Reflect this feedback perfectly.
        If it conflicts with trends, verify risks but prioritize the Boss's intent.
        """

    prompt = f"""
    You are the Chief Producer of a top-tier web novel studio in Korea.
    
    [Knowledge Base]
    {knowledge}
    
    [Task]
    {task_desc}
    {feedback_instruction}
    
    [Output Format (JSON Only, Korean)]
    {{
        "title": "Title (Catchy)",
        "genre": "Main / Sub Genre",
        "keywords": ["#Tag1", "#Tag2"],
        "logline": "1 sentence hook",
        "planning_intent": "Target audience & commercial strategy",
        "characters": [ {{"name": "Name", "role": "Role", "desc": "Personality & Ability"}} ],
        "synopsis": "Plot summary (Intro-Mid-Climax-End)",
        "selling_points": ["Point 1", "Point 2"],
        "pd_score": 85,
        "pd_comment": "Evaluation",
        "risk_report": {{
            "detected": true/false,
            "red_team_warning": "Warning if any",
            "alternative_suggestion": "Suggestion if any"
        }}
    }}
    """
    
    try:
        response = pd_model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        if not text: raise ValueError("Empty response from AI")
        
        result_json = json.loads(text)
        log("✅ 기획 보고서 작성 완료.")
        return result_json, "\n".join(logs)
    except Exception as e:
        log(f"❌ 에러: {e}")
        # 에러 발생 시 UI가 깨지지 않게 더미 데이터 반환
        return {
            "title": "Error Generating Plan",
            "logline": f"시스템 오류: {str(e)}",
            "genre": "System Error",
            "synopsis": "AI 응답을 받아오지 못했습니다. 다시 시도해주세요.",
            "characters": [],
            "risk_report": {"detected": True, "red_team_warning": str(e)}
        }, "\n".join(logs)

def save_and_deploy(plan_data):
    """최초 승인 시 폴더 생성 및 저장"""
    try:
        path, title = manage_project_folder(plan_data)
        
        # JSON 저장
        (path / "Approved_Plan.json").write_text(json.dumps(plan_data, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 텍스트 보고서 저장
        report = f"제목: {title}\n로그라인: {plan_data.get('logline')}\n\n[시놉시스]\n{plan_data.get('synopsis')}"
        (path / "Project_Report.txt").write_text(report, encoding='utf-8')
        
        return True, f"저장 완료: {path.name}"
    except Exception as e:
        return False, f"저장 실패: {e}"