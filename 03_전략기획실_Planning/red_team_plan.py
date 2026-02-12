import os
import json
import sys
import random
from pathlib import Path
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# 👹 [레드팀] Red Team Critic (Ultimate Version)
# 역할: 논리적 오류, 타임라인 모순, 고증 실패 정밀 타격
# 적용 기법: ToT, CoT, RAG, Few-Shot, Self-Reflection
# =========================================================

# 1. 환경 및 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY_PLANNING") or os.getenv("GEMINI_API_KEY")

# 클라이언트 설정
client = None
if OPENAI_KEY:
    try: client = OpenAI(api_key=OPENAI_KEY)
    except: pass

if GEMINI_KEY: genai.configure(api_key=GEMINI_KEY)

# 백업 모델 설정
GEMINI_BACKUP_MODEL = 'gemini-1.5-pro-latest'
try:
    from model_selector import find_best_model
    GEMINI_BACKUP_MODEL = find_best_model()
except: pass

# 2. RAG 데이터 경로
RUBRIC_FILE = PROJECT_ROOT / "00_기준정보_보물창고" / "standard-rubric.json"
TREND_REPORT = PROJECT_ROOT / "02_분석실_Analysis" / "00_통합_트렌드_리포트.json"
TIP_DIR = PROJECT_ROOT / "00_기준정보_보물창고" / "05_팁_보물창고"
DB_DIR = PROJECT_ROOT / "04_설정_자료집"

# 3. [Few-Shot] 논리적 오류 적발 예시
FEW_SHOT_CRITIQUES = """
[Case 1 - Timeline Error]
Input: "1997년 1월, 주인공은 스마트폰으로 주식을 거래하며..."
Critique: "FATAL ERROR. 1997년에는 스마트폰이 존재하지 않음. MTS는커녕 HTS도 초기 단계임. 고증 실패."

[Case 2 - Causality Error]
Input: "주인공이 회귀하여 경쟁사의 기밀을 빼돌려 선점했다. 그런데 경쟁사는 아무런 대응도 하지 않고 망했다."
Critique: "LOGIC ERROR. 나비효과 누락. 경쟁사가 바보가 아닌 이상 기밀 유출에 대해 내부 감사를 하거나 대응 전략을 짰어야 함. 작위적 전개."
"""

def gather_evidence():
    """
    [RAG System] 비평에 필요한 법전(Rubric)과 증거(Fact DB)를 수집
    """
    rubric = RUBRIC_FILE.read_text(encoding='utf-8') if RUBRIC_FILE.exists() else "No Rubric"
    trend = TREND_REPORT.read_text(encoding='utf-8') if TREND_REPORT.exists() else "No Trend"
    
    # 설정 자료집 (Historical Facts) - 무작위 1개 참조 (토큰 절약)
    fact_db = ""
    if DB_DIR.exists():
        facts = list(DB_DIR.rglob("*.md")) + list(DB_DIR.rglob("*.txt"))
        if facts:
            target = random.choice(facts)
            fact_db = f"\n[Fact DB: {target.name}]\n{target.read_text(encoding='utf-8')[:3000]}\n"

    # 작법 팁 (Logic)
    tips_data = ""
    if TIP_DIR.exists():
        tips = list(TIP_DIR.rglob("*.md"))
        if tips:
            target = random.choice(tips)
            tips_data = f"\n[Writing Tip: {target.name}]\n{target.read_text(encoding='utf-8')[:1000]}\n"
            
    return rubric, trend, tips_data, fact_db

def critique_plan(plan_json, round_num):
    """
    [Core Logic] 3단계 사고 과정(CoT)을 통해 정밀 타격
    """
    print(f"\n👹 [Red Team] 기획안 V{round_num} 검증 프로세스 가동...")
    
    rubric, trend, tips, fact_db = gather_evidence()

    # 🔥 [Ultimate Prompt]
    prompt = f"""
    # Role (Persona)
    You are **Korea's Most Ruthless Web Novel Chief Editor**.
    You specialize in finding "Plot Holes", "Time Paradoxes", and "Lazy Writing".
    Your goal is to ensure the story is logically flawless and commercially viable.

    # RAG Context
    - **[Evaluation Rubric]**: {rubric[:1000]}
    - **[Market Trend]**: {trend[:1000]}
    - **[Fact Check DB]**: {fact_db}
    - **[Writing Standard]**: {tips}

    # Target Proposal
    {plan_json}

    # Audit Protocol (Chain of Thought & Tree of Thoughts)
    1. **Timeline Simulation**: Construct a mental timeline of the plot. Are the events physically possible? (e.g., Technology level, Historical events).
    2. **Causality Check (ReAct)**: "If Protagonist does X, World must react with Y." Did the world react realistically? Or are the enemies too dumb?
    3. **Character Consistency**: Does the protagonist's personality (MBTI/Flaw) match their actions?
    4. **Market Fit**: Compare with [Market Trend]. Is this cliche or fresh?

    # Few-Shot Examples (How to critique)
    {FEW_SHOT_CRITIQUES}

    # Output Requirement
    - Output **JSON ONLY**.
    - Language: Korean (Sharp, Critical Tone).

    # Output JSON Structure
    {{
        "score": (0-100 Integer),
        "status": "PASS" (if score >= 85) or "REJECT",
        "critique_summary": "One sentence summary of the biggest flaw.",
        "fatal_flaws": [
            "1. Timeline Error: ...",
            "2. Logic Error: ..."
        ],
        "improvement_instructions": "Specific, actionable instructions for the Planner to fix these errors."
    }}
    """

    # 1. GPT-5.1 (or 4o) 시도
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-5.1", # 없는 경우 gpt-4o로 자동 fallback 처리 필요하나, 여기선 명시적 시도
                messages=[
                    {"role": "system", "content": "You are a Logic Auditor. JSON Only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3 # 논리 검증이므로 창의성(온도)을 낮춤
            )
            return response.choices[0].message.content.strip().replace("```json", "").replace("```", "")
        except:
            # GPT-4o Fallback
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "JSON Only."}, {"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content.strip().replace("```json", "").replace("```", "")
            except: pass

    # 2. Gemini Fallback (최후의 보루)
    try:
        model = genai.GenerativeModel(GEMINI_BACKUP_MODEL)
        res = model.generate_content(prompt)
        return res.text.strip().replace("```json", "").replace("```", "")
    except Exception as e:
        return json.dumps({
            "score": 0, 
            "status": "ERROR", 
            "critique_summary": f"AI Error: {str(e)}",
            "improvement_instructions": "시스템 오류로 비평 불가."
        })

if __name__ == "__main__":
    # 테스트용
    print("Red Team Module Loaded.")