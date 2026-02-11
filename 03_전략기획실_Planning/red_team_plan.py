import os
import json
import sys
import random
from pathlib import Path
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# 👹 [레드팀] Red Team Critic (V8. Path Fixed)
# 역할: 논리적 오류, 타임라인 모순, 고증 실패 정밀 타격
# 엔진: GPT-5.1 (Main) -> GPT-4o (Sub) -> Gemini (Backup)
# =========================================================

# 1. 환경 및 경로 설정 (여기가 핵심입니다)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent  # 한 단계 위(Root)로 이동

# .env 로드
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY_PLANNING")

if not OPENAI_KEY:
    print("❌ [Fatal] OpenAI 키가 없습니다.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_KEY)
if GEMINI_KEY: genai.configure(api_key=GEMINI_KEY)

# 🔥 [경로 수정] 부모 폴더(Root)를 시스템 경로에 추가
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# 🔥 [모델 로드] 중앙 통제실(Model Selector) 호출
GEMINI_BACKUP_MODEL = 'gemini-1.5-pro-latest' # 기본값

try:
    from model_selector import find_best_model
    # 분석용(Analyst)으로 가장 똑똑한 놈을 백업으로 준비
    GEMINI_BACKUP_MODEL = find_best_model() 
    print(f"👹 [Red Team] Gemini 백업 엔진 대기 중: {GEMINI_BACKUP_MODEL}")
except ImportError:
    print("⚠️ [경고] 루트 폴더에서 model_selector.py를 찾지 못했습니다.")
    print("   -> 백업 모델로 gemini-1.5-pro-latest를 사용합니다.")

# 데이터 경로
RUBRIC_FILE = PROJECT_ROOT / "00_기준정보_보물창고" / "standard-rubric.json"
TREND_REPORT = PROJECT_ROOT / "02_분석실_Analysis" / "00_통합_트렌드_리포트.json"
TIP_DIR = PROJECT_ROOT / "00_기준정보_보물창고" / "05_팁_보물창고"
DB_DIR = PROJECT_ROOT / "04_설정_자료집"


# ---------------------------------------------------------
# 📚 [RAG] 증거 수집 (팩트체크용 데이터 로드)
# ---------------------------------------------------------
def gather_evidence():
    # 1. 법전 (Rubric)
    rubric = RUBRIC_FILE.read_text(encoding='utf-8') if RUBRIC_FILE.exists() else "No Rubric"
    
    # 2. 트렌드 (Trend)
    trend = TREND_REPORT.read_text(encoding='utf-8') if TREND_REPORT.exists() else "No Trend"

    # 3. 팁 보물창고 (Logic/Plot Tips)
    tips_data = ""
    if TIP_DIR.exists():
        tip_files = list(TIP_DIR.rglob("*.md")) + list(TIP_DIR.rglob("*.txt"))
        if tip_files:
            selected = random.sample(tip_files, min(len(tip_files), 10))
            for f in selected:
                tips_data += f"\n[Writer's Tip: {f.name}]\n{f.read_text(encoding='utf-8')[:3000]}\n"
    
    # 4. 설정 자료집 (Historical Facts)
    fact_db = ""
    if DB_DIR.exists():
        for f in DB_DIR.rglob("*.md"):
             try: fact_db += f"\n[Fact DB: {f.name}]\n{f.read_text(encoding='utf-8')[:20000]}\n"
             except: pass
    
    return rubric, trend, tips_data, fact_db

# ---------------------------------------------------------
# 👹 [Main Logic] 비평 실행
# ---------------------------------------------------------
def critique_plan(plan_json, round_num):
    print(f"\n👹 [Red Team] 기획안 V{round_num} 정밀 타격 중... (Target: GPT-5.1)")
    
    rubric, trend, tips, fact_db = gather_evidence()

    prompt = f"""
    # Role (Role-Playing)
    You are **Korea's Top Web Novel Chief Editor & Logic Auditor**.
    Your job is NOT to praise. Find the **"Logical Holes"** that human readers will hate.
    
    # 📚 Evidence Locker (RAG)
    - **[The Law (Rubric)]**: {rubric[:1500]}
    - **[Market Trend]**: {trend[:1500]}
    - **[Writing Tips]**: {tips[:4000]}
    - **[Historical Facts (Truth)]**: {fact_db[:30000]}
    
    # 🎯 Target Proposal
    {plan_json}

    # 🕵️‍♀️ Audit Protocol (Chain of Thought)
    
    **Step 1: Timeline & Fact Audit (CRITICAL)**
    - Compare the proposal's timeline with [Historical Facts].
    - Example: Did the MC short-sell 'Hanbo Steel' in March 1997? (Fatal Error: Hanbo collapsed in Jan 1997).
    - **Constraint:** If the timeline is physically impossible, reject immediately.
    
    **Step 2: Logic & Causality Audit**
    - **Information Asymmetry:** Does the MC act like a regressor, while others act naturally? 
    - **Fatal Error Check:** Does the Villain/Boss act like they also know the future without explanation?
    - **Money Flow:** Is the seed money acquisition realistic?
    
    **Step 3: Commerciality Audit**
    - Does it follow the [Market Trend]? 
    - Is the "Cider" (satisfaction) too weak or too delayed?
    
    # 📝 Output Format (JSON Only)
    {{
        "score": (0-100),
        "status": "PASS" (>=85) or "REJECT",
        "critique_summary": "One ruthless sentence summarizing the biggest flaw.",
        "fatal_flaws": [
            "Timeline Error: Hanbo collapsed in Jan, not March.",
            "Logic Error: Boss knows the future unreasonably."
        ],
        "improvement_instructions": "Specific, actionable instructions for the Planner to fix these errors in the next round."
    }}
    """

    # 1차 시도: GPT-5.1
    try:
        response = client.chat.completions.create(
            model="gpt-5.1", 
            messages=[
                {"role": "system", "content": "You are a cold-blooded Logic Auditor. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
    
    except Exception as e:
        # GPT-5.1 실패 시
        # print(f"⚠️ [GPT-5.1 실패] {e} -> GPT-4o로 전환합니다.") # 로그 너무 길면 주석 처리 가능
        return critique_fallback_gpt4(plan_json, round_num, prompt)

# 2차 시도: GPT-4o (Fallback)
def critique_fallback_gpt4(plan_json, round_num, prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "JSON only."}, {"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
    except Exception as e:
        print(f"⚠️ [GPT-4o 실패] {e} -> Gemini ({GEMINI_BACKUP_MODEL})로 전환합니다.")
        return critique_fallback_gemini(prompt)

# 3차 시도: Gemini (Last Resort)
def critique_fallback_gemini(prompt):
    try:
        model = genai.GenerativeModel(GEMINI_BACKUP_MODEL)
        res = model.generate_content(prompt)
        return res.text.replace("```json", "").replace("```", "").strip()
    except:
        return json.dumps({"score": 0, "status": "ERROR", "critique_summary": "All AI Systems Failed."})

if __name__ == "__main__":
    print("이 파일은 strategy_judge.py에 의해 호출됩니다.")