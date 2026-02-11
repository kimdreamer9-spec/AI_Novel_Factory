import os
import time
import json
import warnings
import re
import sys
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# 👑 [통합 분석관] Master Analyst (V7. Path Fixed & Strict)
# 기술: ToT + Reflection + RAG + ReAct + ★Few-Shot
# 엔진: Gemini 최강 모델 (via Selector Only)
# =========================================================

warnings.filterwarnings("ignore")

# 1. 환경 및 경로 설정 (가장 중요)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent  # 한 단계 위(Root)가 프로젝트 루트

# 🔥 [경로 수정] 루트 폴더를 시스템 경로에 최우선 추가
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# .env 로드
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_KEY_PLANNING") # 혹은 GEMINI_KEY_ANALYSIS
if not API_KEY:
    print("❌ [Fatal] API 키가 없습니다. 작업을 중단합니다.")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# 🔥 [핵심] 1.5 타령 금지 -> 무조건 Selector에게 위임
try:
    from model_selector import analyze_and_select_model
    
    # 분석용(Analyst)으로 가장 똑똑한 놈 호출 (Deep-Research or 3.0 Pro)
    MODEL_NAME = analyze_and_select_model(role='analyst')
    print(f"🚀 [Master Engine] Gemini 분석가: {MODEL_NAME}")
    
    model = genai.GenerativeModel(MODEL_NAME)

except ImportError:
    print("❌ [치명적 오류] 루트 폴더에 'model_selector.py'가 없습니다!")
    print(f"   탐색 경로: {PROJECT_ROOT}")
    sys.exit(1) # 1.5 쓰느니 차라리 종료함
except Exception as e:
    print(f"❌ [치명적 오류] 모델 로드 실패: {e}")
    sys.exit(1)


# 경로 설정
RAW_DATA_DIR = PROJECT_ROOT / "01_자료실_Raw_Data" / "00_성공작_아카이브"
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"
RUBRIC_FILE = PROJECT_ROOT / "00_기준정보_보물창고" / "standard-rubric.json"

# ---------------------------------------------------------
# 💾 리포트 저장
# ---------------------------------------------------------
def save_report(folder_name, category, content):
    target_dir = ANALYSIS_DIR / category
    target_dir.mkdir(parents=True, exist_ok=True)
    prefix = "STYLE" if "문체" in category else "CHAR" if "캐릭터" in category else "STORY"
    filename = f"{prefix}_{folder_name}.json"
    (target_dir / filename).write_text(content, encoding='utf-8')
    print(f"      💾 [저장 완료] {filename}")

# ---------------------------------------------------------
# 🏆 [Golden Example] AI에게 보여줄 '모범 답안' (Few-Shot)
# ---------------------------------------------------------
GOLDEN_EXAMPLE = """
{
    "title": "Example: The Youngest Son of a Conglomerate",
    "selected_hypothesis": "C (Psychology): The narrative constructs a 'Resentment-Payoff Loop'. It relies not just on regression, but on the structural dismantling of the modern class system using future knowledge as a cheat key.",
    "analysis_content": {
        "description": "The protagonist's charm isn't just 'knowing the future'; it's his 'Professional Revenge'. He uses corporate logic to destroy his emotional enemies. This satisfies the reader's desire for meritocratic justice in an unfair world.",
        "character_list": ["Jin Do-jun (MC)", "Jin Yang-cheol (Villain/Grandfather)", "Director Wi (Supporter)", "Mo Hyun-min (Rival)", "Seong-jun (Antagonist)"]
    },
    "evidence_from_text": "\"Is this the grandfather who abandoned me?\" - Shows immediate conflict setup. \"I will buy the Sunyang Group.\" - Defines the ultimate goal clearly in Ep 1.",
    "rubric_match_score": 10,
    "actionable_insight": "Ensure the protagonist's goal is 'systemic destruction' of the villain's legacy, not just personal wealth."
}
"""

# ---------------------------------------------------------
# 🧠 [Master Prompt] 완벽한 프롬프트 설계
# ---------------------------------------------------------
def create_master_prompt(task_type, rubric, data, text):
    special_instruction = ""
    if "Character" in task_type:
        special_instruction = """
        **[CRITICAL INSTRUCTION]**
        You MUST analyze exactly **5 Characters**:
        1. **The Protagonist** (Main Character)
        2. **Main Villain** (Antagonist)
        3. **Key Supporter 1**
        4. **Key Supporter 2**
        5. **Key Rival/Heroine**
        """
    
    return f"""
    # Role & Persona
    You are an elite **Web Novel Analyst Agent** (Powered by {MODEL_NAME}).
    Your goal is to extract the 'Winning Formula' from the text.

    # Context (RAG)
    [Rubric]: {rubric[:2000]}
    [Meta Data]: {data[:1000]}
    [Novel Text]: {text[:50000]}

    # Task: Analyze {task_type}
    {special_instruction}

    # ★ Few-Shot Example (Learn from this!)
    **Below is a 'Golden Example' of a high-quality analysis. Follow this depth and format.**
    [Example Output]:
    {GOLDEN_EXAMPLE}

    # Execution Protocol (Chain of Logic)
    **Step 1: Tree of Thoughts (Strategy)**
    - Hypothesis A: Does it follow the standard formula?
    - Hypothesis B: Is there a unique twist?
    - Hypothesis C: How does it trigger dopamine?
    *Select the best hypothesis.*

    **Step 2: Verification (ReAct)**
    - Quote specific lines from the text.
    - Check alignment with Rubric.

    **Step 3: Self-Reflection (Critique)**
    - "Is this too obvious?" -> Dig deeper.
    - "Did I list 5 characters?" (If character task) -> Verify count.
    - "Does it match the depth of the Golden Example?"

    **Step 4: Final Output (JSON)**
    Generate the final report in JSON.

    # Output Format (JSON Only)
    {{
        "title": "Novel Title",
        "selected_hypothesis": "...",
        "analysis_content": {{
            "description": "Detailed analysis here...",
            "character_list": ["MC", "Villain", "Role3", "Role4", "Role5"] (Only if character task)
        }},
        "evidence_from_text": "Direct quotes",
        "rubric_match_score": 0-10,
        "actionable_insight": "One key takeaway"
    }}
    """

# ---------------------------------------------------------
# 🔥 실행 로직
# ---------------------------------------------------------
def analyze_all():
    print(f"\n🔥 [Master Analyst] 심층 분석 시작 (ToT + Reflection + RAG + ★Few-Shot)")
    
    rubric_text = "No Rubric"
    if RUBRIC_FILE.exists(): rubric_text = RUBRIC_FILE.read_text(encoding='utf-8')

    targets = []
    if RAW_DATA_DIR.exists():
        for root, dirs, files in os.walk(RAW_DATA_DIR):
            if any(f.endswith('.md') for f in files): targets.append(Path(root))
    
    if not targets:
        print("❌ 분석할 작품이 없습니다. 01_자료실을 확인하세요.")
        return

    for folder in targets:
        print(f"   📘 [Analyzing] {folder.name}")
        
        md_files = sorted(list(folder.glob("*.md")))
        txt_sample = md_files[0].read_text(encoding='utf-8')[:50000] if md_files else ""
        
        meta_data = ""
        for json_f in folder.glob("*.json"):
            try: meta_data += json_f.read_text(encoding='utf-8')
            except: pass

        # (1) 문체 분석
        try:
            prompt = create_master_prompt("Writing Style & Pacing", rubric_text, meta_data, txt_sample)
            res = model.generate_content(prompt)
            save_report(folder.name, "01_문체_분석", res.text.replace("```json", "").replace("```", "").strip())
        except Exception as e: print(f"      🚨 문체 분석 실패: {e}")
        time.sleep(1)

        # (2) 캐릭터 분석 (5명 강제)
        try:
            prompt = create_master_prompt("Top 5 Characters (Protagonist + 4 Key Roles)", rubric_text, meta_data, txt_sample)
            res = model.generate_content(prompt)
            save_report(folder.name, "02_캐릭터_분석", res.text.replace("```json", "").replace("```", "").strip())
        except Exception as e: print(f"      🚨 캐릭터 분석 실패: {e}")
        time.sleep(1)

        # (3) 스토리 분석
        try:
            prompt = create_master_prompt("Episode 1 Hook & Cider Structure", rubric_text, meta_data, txt_sample)
            res = model.generate_content(prompt)
            save_report(folder.name, "03_스토리_분석", res.text.replace("```json", "").replace("```", "").strip())
        except Exception as e: print(f"      🚨 스토리 분석 실패: {e}")
        time.sleep(1)
        
        print("      ✅ 분석 완료.")

if __name__ == "__main__":
    analyze_all()