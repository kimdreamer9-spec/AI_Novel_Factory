import os
import json
import sys
import warnings
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# =========================================================
# ⚖️ [총괄 PD] Strategy Judge (V27. Selector Integration)
# 목표: 사장님의 'model_selector'를 연동하여 최신 모델 사용
# =========================================================

warnings.filterwarnings("ignore")

# 1. 환경 및 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# 🚨 [경로 추가] 루트 폴더의 모듈(model_selector)을 불러오기 위함
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# API 키 로드
API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# 모델 전역 변수
pd_model = None
MODEL_NAME = "Unknown"

def init_engine():
    """
    [핵심] model_selector를 통해 '그 시점 최고의 모델'을 로드함
    """
    global pd_model, MODEL_NAME
    
    try:
        # 🔥 사장님이 만드신 Selector 호출!
        import model_selector
        MODEL_NAME = model_selector.find_best_model() # 여기서 'gemini-3.0-pro' 등을 가져옴
        
        pd_model = genai.GenerativeModel(MODEL_NAME)
        return True, f"Engine Online: {MODEL_NAME} (Selector Applied)"
    except ImportError:
        # 혹시나 selector가 없을 경우 비상용 (하지만 사장님 파일엔 있음)
        return False, "❌ model_selector.py를 찾을 수 없습니다."
    except Exception as e:
        return False, f"❌ Engine Fail: {str(e)}"

def process_planning(mode, user_input):
    """
    app.py에서 호출하는 메인 함수
    """
    logs = []
    def log(msg): logs.append(msg)

    # 엔진이 안 켜져 있으면 켬
    if not pd_model:
        success, msg = init_engine()
        log(msg)
        if not success:
            return {"title": "Error"}, msg

    log(f"🧠 [PD] 기획 엔진 가동 (Model: {MODEL_NAME})")
    log(f"📋 모드: {mode} / 입력: {user_input[:30]}...")

    # 1. 프롬프트 구성 (사장님의 지시를 반영하는 고도화된 프롬프트)
    role = "You are the **Chief Executive Producer (CP)** of a top-tier web novel studio."
    
    task_desc = ""
    if mode == 1: task_desc = f"Create a blockbuster web novel plan based on keyword: '{user_input}'. Use 2026 trends."
    elif mode == 2: task_desc = f"Develop this user idea into a commercial hit: '{user_input}'."
    elif mode == 3: task_desc = f"Rescue this failed story setup. Identify flaws and fix them: '{user_input}'."

    prompt = f"""
    {role}
    
    [Mission]
    {task_desc}
    
    [Output Requirement]
    Return ONLY a JSON object with the following structure (Korean):
    {{
        "title": "Impactful Title",
        "genre": "Specific Genre",
        "logline": "One sentence hook",
        "selling_points": ["Point 1", "Point 2", "Point 3"],
        "character_brief": "Main Character Description",
        "synopsis": "Short summary of the plot (3-5 sentences)"
    }}
    """

    # 2. Gemini 호출
    try:
        response = pd_model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(text)
        
        log("✅ 기획안 생성 완료.")
        return result_json, "\n".join(logs)

    except Exception as e:
        log(f"❌ 생성 중 에러 발생: {e}")
        # 에러 발생 시 로그 리턴
        dummy = {
            "title": f"생성 실패 ({MODEL_NAME})",
            "logline": f"에러: {str(e)}",
            "selling_points": ["API 키 확인 필요", "Quota 확인 필요"]
        }
        return dummy, "\n".join(logs)