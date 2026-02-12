import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 설정
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

load_dotenv(dotenv_path=root_dir / ".env")
API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

# 모델 셀렉터 연동
try:
    import model_selector
    MODEL_NAME = model_selector.find_best_model()
except:
    MODEL_NAME = "gemini-1.5-pro-latest"

if API_KEY: genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

def process_planning(mode, user_input, feedback_history=""):
    """
    5단계 표준 기획안 생성 함수
    """
    
    # 모드별 프롬프트 설정
    mode_desc = ""
    if mode == 1: mode_desc = "Create a NEW original web novel plan."
    elif mode == 2: mode_desc = "Develop the user's rough idea into a commercial hit."
    elif mode == 3: mode_desc = "Fix the failed story based on the input."

    prompt = f"""
    You are the Chief Producer (CP) of a top-tier web novel studio.
    Create a **Commercial Web Novel Proposal** following the strictly defined structure below.
    
    [Input Data]
    - User Request: {user_input}
    - Mode: {mode_desc}
    - Feedback History: {feedback_history}
    
    [CRITICAL RULES]
    1. **Format:** Output MUST be a valid JSON object.
    2. **Language:** Korean (Natural, Professional Web Novel Industry Tone).
    3. **Character Limit:** Create exactly **5 Characters** (1 Protagonist + 4 Key Supporting Roles). 
       - Make them unique, with distinct desires and flaws. 
       - Do NOT bias towards Romance unless the genre is Romance.
    4. **Plot:** Outline the first 5 episodes specifically.
    
    [Output JSON Structure]
    {{
        "title": "Hooky Title",
        "genre": "Genre (e.g., Fantasy, Sci-Fi)",
        "keywords": ["#Tag1", "#Tag2", "#Tag3"],
        "logline": "1 sentence high-concept hook",
        "planning_intent": "Why this will sell (Commercial Strategy)",
        "characters": [
            {{
                "name": "Name",
                "role": "Main Protagonist",
                "mbti": "INTJ (Example)",
                "desc": "Personality, Ability, Desire, Flaw (Detailed)"
            }},
            {{
                "name": "Name",
                "role": "Key Antagonist / Helper",
                "desc": "Personality, Relationship with Main"
            }}
            // ... Total 5 characters
        ],
        "synopsis": "Full story summary (Beginning - Middle - End)",
        "episode_plots": [
            {{"ep": 1, "title": "Ep Title", "summary": "Core event"}},
            {{"ep": 2, "title": "Ep Title", "summary": "Core event"}},
            {{"ep": 3, "title": "Ep Title", "summary": "Core event"}},
            {{"ep": 4, "title": "Ep Title", "summary": "Core event"}},
            {{"ep": 5, "title": "Ep Title", "summary": "Core event"}}
        ],
        "sales_points": [
            "Point 1 (e.g., Cider satisfaction)",
            "Point 2 (e.g., Unique setting)",
            "Point 3"
        ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text), "Log: Success"
    except Exception as e:
        return {"title": "Error", "synopsis": str(e), "is_corrupted": True}, str(e)

def save_and_deploy(plan_data):
    # 저장 로직 (system_utils 이용 권장하나, 독립성 위해 간단 구현)
    try:
        # system_utils를 이용하는 것이 정석
        import system_utils as utils
        # 임시 폴더 생성 로직
        from datetime import datetime
        folder_name = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{plan_data.get('title', 'Untitled')[:10]}"
        path = root_dir / "03_전략기획실_Planning" / folder_name
        path.mkdir(parents=True, exist_ok=True)
        utils.create_new_version(path, plan_data)
        return True, "Saved"
    except Exception as e:
        return False, str(e)