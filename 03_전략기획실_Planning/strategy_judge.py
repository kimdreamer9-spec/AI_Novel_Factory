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
# ⚖️ [총괄 PD] Strategy Judge (V30. Report Master)
# 목표: 사장님이 원하시는 '완벽한 기획 보고서' 포맷 출력
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

    if feedback_history:
        task_desc += f"\n[BOSS FEEDBACK]: {feedback_history} (Must Reflect!)"

    # 🔥 [핵심] 사장님 맞춤형 보고서 프롬프트
    prompt = f"""
    You are the Chief Producer of a top-tier web novel studio.
    Your goal is to create a **Perfect Proposal Report** for the CEO.
    
    [Task]
    {task_desc}
    
    [Output Format]
    You must output a single JSON object containing the following structure (Language: Korean):
    
    {{
        "title": "Impactful Title (가제)",
        "genre": "Main Genre / Sub Genre",
        "keywords": ["#Keyword1", "#Keyword2", "#Keyword3", "#Keyword4"],
        "logline": "One sentence hook that grabs attention immediately.",
        "planning_intent": "Why this story? (Target audience & Commercial strategy)",
        "characters": [
            {{
                "name": "Name",
                "role": "Protagonist/Antagonist",
                "desc": "Detailed personality & motivation"
            }}
        ],
        "synopsis": "Full plot summary (Beginning - Middle - Climax - Ending)",
        "selling_points": [
            "Differentiation Point 1",
            "Differentiation Point 2"
        ],
        "pd_score": 85,
        "pd_comment": "Final evaluation from the CP perspective."
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
        
        # 1. JSON 저장
        (path / "Approved_Plan.json").write_text(json.dumps(plan_data, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 2. 사장님용 읽기 편한 보고서(TXT) 저장
        readable_report = f"""
        [웹소설 기획안 보고서]
        
        1. 작품 정보
        - 제목: {plan_data.get('title')}
        - 장르: {plan_data.get('genre')}
        - 키워드: {', '.join(plan_data.get('keywords', []))}
        
        2. 로그라인
        "{plan_data.get('logline')}"
        
        3. 기획 의도
        {plan_data.get('planning_intent')}
        
        4. 등장인물
        """
        for char in plan_data.get('characters', []):
            readable_report += f"- {char['name']} ({char['role']}): {char['desc']}\n"
            
        readable_report += f"""
        5. 줄거리 (시놉시스)
        {plan_data.get('synopsis')}
        
        6. 차별화 포인트
        """
        for p in plan_data.get('selling_points', []):
            readable_report += f"- {p}\n"
            
        (path / "Project_Report.txt").write_text(readable_report, encoding='utf-8')
        
        return True, f"저장 완료: {path}"
    except Exception as e:
        return False, f"저장 실패: {e}"