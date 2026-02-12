import os
import json
import sys
import random
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# 🏗️ [Setup] 경로 및 환경 설정 (절대 경로 보장)
# =========================================================

# 1. 경로 정의 (파일 트리 기반 정밀 타격)
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent                # 03_전략기획실_Planning
PROJECT_ROOT = PLANNING_DIR.parent                     # Root (AI_Novel_Factory)

# 2. 시스템 경로 추가
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# 3. 환경변수 로드
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

# =========================================================
# 🧠 [Core] 모델 로드 (Zero Tolerance Policy)
# =========================================================
try:
    import model_selector
    # 🚨 사장님 지시: 무조건 model_selector가 정한 모델만 쓴다.
    MODEL_NAME = model_selector.find_best_model()
    
    if not MODEL_NAME:
        raise ValueError("model_selector returned None! Check check_models.py")

except ImportError:
    print("❌ [Critical] 'model_selector.py'를 찾을 수 없습니다. 루트 경로를 확인하세요.")
    sys.exit(1)

except Exception as e:
    print(f"❌ [Critical] 모델 로드 중 알 수 없는 오류: {e}")
    MODEL_NAME = "gemini-3-pro" # 최후의 보루

# AI 설정
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

print(f"🧠 [System] Creative Planner 가동 | Engine: {MODEL_NAME}")


# =========================================================
# 📂 [RAG] 데이터 수집 (타겟팅 정밀 보정 완료)
# =========================================================
# 🚨 사장님 지시: 설정집(X) -> 작법서(O), 성공작 분석(O), 트렌드(O)
BASE_INFO_DIR = PROJECT_ROOT / "00_기준정보_보물창고"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"

# 1. 기준 정보 타겟
RUBRIC_FILE = BASE_INFO_DIR / "standard-rubric.json"
TIP_DIR = BASE_INFO_DIR / "05_팁_보물창고"
THEORY_DIR = BASE_INFO_DIR / "작법_이론서"  # [추가] 이론서 포함

# 2. 분석 데이터 타겟
TREND_REPORT = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
CHAR_ANALYSIS_DIR = ANALYSIS_DIR / "02_캐릭터_분석" # [추가] 성공작 캐릭터 구조
STORY_ANALYSIS_DIR = ANALYSIS_DIR / "03_스토리_분석" # [추가] 성공작 플롯 구조

def gather_materials(mode):
    """
    분석실 데이터(성공작)와 보물창고 팁(작법)을 RAG로 가져옵니다.
    """
    context_data = {
        "rubric": "Standard Rubric Not Found.",
        "trend": "Trend Report Not Found.",
        "tips_and_theory": "",
        "success_dna": ""  # 성공작들의 DNA (캐릭터/스토리 구조)
    }

    # 1. 루브릭 & 트렌드 로드
    if RUBRIC_FILE.exists(): context_data["rubric"] = RUBRIC_FILE.read_text(encoding='utf-8')
    if TREND_REPORT.exists(): context_data["trend"] = TREND_REPORT.read_text(encoding='utf-8')

    # 2. 팁 & 이론서 로드 (랜덤 샘플링으로 다양성 확보)
    tip_files = []
    if TIP_DIR.exists(): tip_files.extend(list(TIP_DIR.glob("*.md")) + list(TIP_DIR.glob("*.txt")))
    if THEORY_DIR.exists(): tip_files.extend(list(THEORY_DIR.glob("*.txt")))
    
    if tip_files:
        # 이론서 1개 + 팁 3개 정도 섞어서 제공
        selected_tips = random.sample(tip_files, min(len(tip_files), 4))
        for tip in selected_tips:
            content = tip.read_text(encoding='utf-8')
            context_data["tips_and_theory"] += f"\n[Writing Guide: {tip.name}]\n{content[:1500]}...\n"

    # 3. 성공작 분석 데이터 로드 (캐릭터/스토리) -> "성공 공식" 주입
    analysis_files = []
    if CHAR_ANALYSIS_DIR.exists(): analysis_files.extend(list(CHAR_ANALYSIS_DIR.glob("*.json")))
    if STORY_ANALYSIS_DIR.exists(): analysis_files.extend(list(STORY_ANALYSIS_DIR.glob("*.json")))
    
    if analysis_files:
        # 성공작 2개 정도를 참고하여 "이런 느낌으로 짜라"고 지시
        selected_analysis = random.sample(analysis_files, min(len(analysis_files), 2))
        for a in selected_analysis:
            try:
                content = json.loads(a.read_text(encoding='utf-8'))
                # 전체 다 넣으면 너무 기니까 핵심 요약이나 구조 부분만 추출
                summary = json.dumps(content.get("core_analysis", {}) or content, ensure_ascii=False)
                context_data["success_dna"] += f"\n[Success Case Reference: {a.name}]\n{summary[:2000]}...\n"
            except: pass

    return context_data

# =========================================================
# ✍️ [Generator] 기획안 생성 (Advanced Prompting)
# =========================================================

def create_plan(round_num, feedback, mode=1, user_input=""):
    """
    CoT(생각의 사슬) + Role-Playing + Few-Shot이 적용된 고지능 기획 함수
    """
    materials = gather_materials(mode)

    mode_instruction = ""
    if mode == 1:
        mode_instruction = "Create a Brand New Original Hit. Focus on Marketability."
    elif mode == 2:
        mode_instruction = "Develop based on User's Idea perfectly. Enhance logic."
    elif mode == 3:
        mode_instruction = "Fix the Ruined Story. Analyze the flaw and reconstruct."

    # ------------------------------------------------------------------
    # ⚡ [Meta-Prompting] 최고의 결과를 위한 프롬프트 설계
    # ------------------------------------------------------------------
    prompt = f"""
    You are **Korea's No.1 Web Novel CP (Chief Producer)**. 
    You have analyzed 10,000 hit novels and possess strict, data-driven insight.
    
    [Mission]
    {mode_instruction}
    
    [Information Architecture (RAG) - Your Database]
    1. **Market Trend**: {materials['trend'][:2000]} (Reflect this strictly)
    2. **Success DNA (Benchmarks)**: {materials['success_dna']} (Mimic the structure of these hits)
    3. **Writing Theory & Tips**: {materials['tips_and_theory']}
    4. **Evaluation Standard**: {materials['rubric'][:1000]}

    [User Request]
    "{user_input}"
    
    [Critical Feedback History]
    "{feedback}" (You MUST fix these points in this draft)

    ------------------------------------------------------------------
    [Reasoning Process (Chain of Thought)]
    Before generating the JSON, you must think in this order (Implicitly):
    1. **Trend Check**: Analyze the user request against the 'Market Trend'.
    2. **Character Build**: Design **EXACTLY 5 characters** that create conflict (Protagonist vs Antagonist). Use the 'Success DNA' to build attractive traits.
    3. **Structure**: Apply the '3-Act Structure' found in the Writing Theory.
    4. **Self-Evaluation**: Provide Stats (0-100) and SWOT analysis objectively.
    ------------------------------------------------------------------

    [Output Requirement]
    - Language: **Korean (한국어)**
    - Format: **JSON Only** (Do not add markdown comments outside JSON)
    
    [JSON Structure Template]
    {{
        "title": "Impactful Title",
        "genre": "Main Genre / Sub Genre",
        "keywords": ["#Keyword1", "#Keyword2", "#Keyword3"],
        "logline": "A single sentence that pierces the reader's heart.",
        "planning_intent": "Strategic reason why this will sell (commercial analysis).",
        "world_view": "Specific World Setting & System Rules (e.g., Reward System, Regression Rule)",
        "stats": {{
            "대중성": 85,
            "독창성": 70,
            "캐릭터": 90,
            "개연성": 80,
            "확장성": 75
        }},
        "swot_analysis": {{
            "strength": "Strong point...",
            "weakness": "Potential risk...",
            "opportunity": "Market chance...",
            "threat": "Competition..."
        }},
        "characters": [
            {{ "name": "Name", "role": "Main Protagonist", "mbti": "Type", "desc": "Desire(Want) vs Fear, Special Ability, Fatal Flaw" }},
            {{ "name": "Name", "role": "Main Antagonist", "desc": "Conflict trigger, Opposing value to Protagonist" }},
            {{ "name": "Name", "role": "Sub (Helper)", "desc": "Support role" }},
            {{ "name": "Name", "role": "Sub (Rival)", "desc": "Competition role" }},
            {{ "name": "Name", "role": "Sub (Key Extra)", "desc": "Plot device role" }}
        ],
        "synopsis": "Structured Summary (Intro -> Development -> Crisis -> Climax)",
        "episode_plots": [
            {{ "ep": 1, "title": "Title", "summary": "Hook point & Cliffhanger" }},
            {{ "ep": 2, "title": "Title", "summary": "..." }},
            {{ "ep": 3, "title": "Title", "summary": "..." }},
            {{ "ep": 4, "title": "Title", "summary": "..." }},
            {{ "ep": 5, "title": "Title", "summary": "..." }}
        ],
        "sales_points": [
            "Reason 1: Why readers will pay",
            "Reason 2: Differentiation strategy",
            "Reason 3: Target audience appeal"
        ]
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.85, # 창의성 약간 상향
                top_p=0.9,
                top_k=40
            )
        )
        
        text = response.text.strip()
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.replace("```", "").strip()
            
        return json.loads(text)

    except Exception as e:
        print(f"❌ [Error] Generation Failed: {e}")
        return {
            "title": "Error in Planning",
            "logline": f"Generation Logic Failed: {str(e)}",
            "is_corrupted": True
        }

# (테스트 실행용)
if __name__ == "__main__":
    print("🧪 Testing Creative Planner (Targeting Success DNA)...")
    # ...