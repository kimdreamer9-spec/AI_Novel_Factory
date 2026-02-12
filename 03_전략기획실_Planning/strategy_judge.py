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
# ⚖️ [총괄 PD] Strategy Judge (V28. Full Factory Logic)
# 목표: 기획 -> 비평 -> 폴더링 -> 사장님 결재 프로세스 완비
# =========================================================

warnings.filterwarnings("ignore")

# 1. 환경 및 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
PLANNING_DIR = CURRENT_DIR # 기획안 저장소

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")
if API_KEY: genai.configure(api_key=API_KEY)

# 모델 전역 변수
pd_model = None
MODEL_NAME = "Unknown"

# --- [Helper Functions] ---
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")[:40]

def manage_project_folder(plan_data):
    """승인된 기획안을 저장할 폴더 생성"""
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
    except Exception as e:
        return False, f"Engine Fail: {str(e)}"

# --- [Core Logic] ---
def process_planning(mode, user_input, feedback_history=""):
    """
    기획 + (내부적 비평) + 결과 도출
    feedback_history: 반려 시 사장님의 수정 지시사항
    """
    logs = []
    def log(msg): logs.append(msg)

    if not pd_model: init_engine()
    
    log(f"🧠 [PD] 기획 엔진 가동 (Model: {MODEL_NAME})")
    
    # 1. 프롬프트 구성
    task_desc = ""
    if mode == 1: task_desc = f"Create a hit web novel plan. Keyword: '{user_input}'."
    elif mode == 2: task_desc = f"Develop user idea: '{user_input}'."
    elif mode == 3: task_desc = f"Rescue failed story: '{user_input}'."

    # 재기획(반려)일 경우 추가 지시
    if feedback_history:
        task_desc += f"\n[CRITICAL FEEDBACK from BOSS]: {feedback_history} (Reflect this strictly!)"

    prompt = f"""
    You are the Chief Producer.
    Task: {task_desc}
    
    [Requirements]
    1. Analyze trends and create a commercially viable plan.
    2. Critique your own plan (Self-Reflection) and improve it before outputting.
    
    [Output JSON Format (Korean)]
    {{
        "title": "Title",
        "genre": "Genre",
        "logline": "1 sentence hook",
        "selling_points": ["Point 1", "Point 2", "Point 3"],
        "synopsis": "Plot summary",
        "characters": [
            {{"name": "Main Char", "role": "Protagonist", "trait": "Personality"}}
        ],
        "pd_score": 85 (0-100),
        "pd_comment": "Why this will succeed or fail"
    }}
    """
    
    try:
        response = pd_model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(text)
        log("✅ 기획안 생성 및 자체 비평 완료.")
        return result_json, "\n".join(logs)
    except Exception as e:
        log(f"❌ 에러: {e}")
        return {"title": "Error"}, "\n".join(logs)

def save_and_deploy(plan_data):
    """
    [승인] 버튼 누를 때 호출. 폴더 만들고 파일 저장.
    """
    try:
        path, title = manage_project_folder(plan_data)
        
        # 1. 기획안 저장
        (path / "Approved_Plan.json").write_text(json.dumps(plan_data, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 2. 제작소(Production)를 위한 지시서 생성
        order_sheet = f"""
        [제작 지시서]
        제목: {title}
        장르: {plan_data.get('genre')}
        로그라인: {plan_data.get('logline')}
        캐릭터: {json.dumps(plan_data.get('characters'), ensure_ascii=False)}
        """
        (path / "Production_Order.txt").write_text(order_sheet, encoding='utf-8')
        
        return True, f"저장 완료: {path}"
    except Exception as e:
        return False, f"저장 실패: {e}"