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

# 모델 셀렉터 연동 (사장님 지시 준수)
try:
    import model_selector
    MODEL_NAME = model_selector.find_best_model()
except:
    MODEL_NAME = "gemini-1.5-pro-latest"

if API_KEY: genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# --- [RAG System] 데이터 수집가 ---
def fetch_knowledge_base():
    """창고에 있는 보물들을 긁어옵니다."""
    context = ""
    try:
        # 1. 트렌드 리포트 (분석실)
        trend_file = root_dir / "02_분석실_Analysis" / "00_통합_트렌드_리포트.json"
        if trend_file.exists():
            context += f"\n[Market Trend Report]:\n{trend_file.read_text(encoding='utf-8')[:3000]}\n"
        
        # 2. 평가 루브릭 (기준정보)
        rubric_file = root_dir / "00_기준정보_보물창고" / "standard-rubric.json"
        if rubric_file.exists():
            context += f"\n[Evaluation Rubric]:\n{rubric_file.read_text(encoding='utf-8')[:2000]}\n"
            
        # 3. 팁 보물창고 (핵심 팁)
        tip_dir = root_dir / "00_기준정보_보물창고" / "05_팁_보물창고"
        tips = list(tip_dir.glob("*.md")) + list(tip_dir.glob("*.txt"))
        for tip in tips[:5]: # 너무 많으면 토큰 터지니까 5개만 엄선
            context += f"\n[Pro Tip: {tip.name}]:\n{tip.read_text(encoding='utf-8')[:1000]}\n"
            
    except Exception as e:
        print(f"RAG Error: {e}")
    return context

# --- [Core Logic] 기획 생성 ---
def process_planning(mode, user_input, feedback_history=""):
    
    # RAG 가동
    knowledge_context = fetch_knowledge_base()
    
    mode_desc = ""
    if mode == 1: mode_desc = "Create a NEW original web novel plan."
    elif mode == 2: mode_desc = "Develop the user's rough idea into a commercial hit."
    elif mode == 3: mode_desc = "Fix the failed story based on the input."

    prompt = f"""
    You are the **Chief Producer (CP)** and **Red Team Leader** of a top-tier web novel studio.
    
    [Reference Data (RAG) - MUST APPLY]
    {knowledge_context}
    
    [Task]
    Create a **Commercial Web Novel Proposal** based on:
    - Input: {user_input}
    - Mode: {mode_desc}
    
    [CRITICAL RULES]
    1. **Format:** Output MUST be a valid JSON object.
    2. **Language:** Korean (Web Novel Industry Tone).
    3. **Characters:** Exactly **5 Characters** (1 Main + 4 Sub). Unique, vivid, distinct desires.
    4. **Plot:** Episodes 1-5 detailed outline.
    5. **Red Team Check:** You MUST critique your own plan in the 'red_team_critique' section based on the [Rubric].
    
    [Output JSON Structure]
    {{
        "title": "Hooky Title",
        "genre": "Genre",
        "keywords": ["#Tag1", "#Tag2"],
        "logline": "1 sentence hook",
        "planning_intent": "Commercial Strategy",
        "characters": [
            {{ "name": "Name", "role": "Main", "mbti": "Type", "desc": "Detailed profile" }},
            {{ "name": "Name", "role": "Sub", "desc": "Detailed profile" }}
        ],
        "synopsis": "Full Story (Gi-Seung-Jeon-Gyeol)",
        "episode_plots": [
            {{ "ep": 1, "title": "...", "summary": "..." }},
            {{ "ep": 2, "title": "...", "summary": "..." }},
            {{ "ep": 3, "title": "...", "summary": "..." }},
            {{ "ep": 4, "title": "...", "summary": "..." }},
            {{ "ep": 5, "title": "...", "summary": "..." }}
        ],
        "sales_points": ["Point 1", "Point 2"],
        "red_team_critique": {{
            "score": 85,
            "warning": "Critical weakness of this plan",
            "solution": "How to fix it"
        }}
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text), "Success"
    except Exception as e:
        return {"title": "Error", "synopsis": str(e), "is_corrupted": True}, str(e)

def save_and_deploy(plan_data):
    try:
        import system_utils as utils
        from datetime import datetime
        # 폴더명 생성 (특수문자 제거)
        safe_title = "".join([c for c in plan_data.get('title', 'Untitled') if c.isalnum() or c==' ']).strip().replace(' ', '_')[:20]
        folder_name = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}"
        
        path = root_dir / "03_전략기획실_Planning" / folder_name
        path.mkdir(parents=True, exist_ok=True)
        
        utils.create_new_version(path, plan_data)
        return True, "Saved"
    except Exception as e:
        return False, str(e)