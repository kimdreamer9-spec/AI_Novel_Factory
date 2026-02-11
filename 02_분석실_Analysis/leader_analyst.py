import os
import json
import re
import sys
import glob
from pathlib import Path
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# 🎖️ [분석 팀장] Leader Analyst (V7. No More 1.5)
# 역할: Gemini(자료취합/초안) -> OpenAI(정밀타격/최종본)
# 엔진: Gemini 최강 모델 (via Selector) + GPT-5.1
# =========================================================

# 1. 환경 및 경로 설정 (엄격 모드)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent  # 한 단계 위(Root)가 프로젝트 루트

# 🔥 [경로 수정] 루트 폴더를 시스템 경로에 최우선 추가
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# .env 로드
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

GEMINI_KEY = os.getenv("GEMINI_KEY_PLANNING")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not GEMINI_KEY or not OPENAI_KEY:
    print("❌ [Fatal] API 키가 부족합니다. .env를 확인하세요.")
    sys.exit(1)

genai.configure(api_key=GEMINI_KEY)
client = OpenAI(api_key=OPENAI_KEY)

# 🔥 [핵심] 1.5 타령 금지 -> 무조건 Selector에게 위임
try:
    from model_selector import analyze_and_select_model
    
    # 분석용(Analyst)으로 가장 똑똑한 놈을 호출 (Deep-Research or 3.0 Pro)
    GEMINI_MODEL_NAME = analyze_and_select_model(role='analyst')
    print(f"🚀 [Leader Engine] Gemini 분석가: {GEMINI_MODEL_NAME}")
    
    gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)

except ImportError:
    print("❌ [치명적 오류] 루트 폴더에 'model_selector.py'가 없습니다!")
    print(f"   탐색 경로: {PROJECT_ROOT}")
    sys.exit(1) # 1.5 쓰느니 차라리 종료함
except Exception as e:
    print(f"❌ [치명적 오류] 모델 로드 실패: {e}")
    sys.exit(1)


# 경로 설정
ANALYSIS_DIR = PROJECT_ROOT / "02_분석실_Analysis"
OUTPUT_FILE = ANALYSIS_DIR / "00_통합_트렌드_리포트.json"
RUBRIC_FILE = PROJECT_ROOT / "00_기준정보_보물창고" / "standard-rubric.json"

# ---------------------------------------------------------
# 🏆 [Golden Example] 팀장이 만들어야 할 이상적인 결과물
# ---------------------------------------------------------
GOLDEN_REPORT_EXAMPLE = """
{
    "trend_version": "2026_Trend_Analysis",
    "winning_formula": {
        "core_philosophy": "Reader Dopamine First. No slow build-up. Instant gratification via competence.",
        "style_guideline": "Short sentences (under 50 chars). Dialogue driven (60%+). Focus on sensory details of wealth and power."
    },
    "character_constitution": {
        "protagonist_archetype": "The 'System-Audit Expert' or 'Vengeful Regressor'. Must have a clear 'Lack' (poverty, betrayal) and a 'Cheat' (Future Knowledge/System).",
        "villain_archetype": "The 'Arrogant Establishment'. Must be annoying but logically defeatable.",
        "role_distribution": "MC (80%), Villain (10%), Supporters (10%)."
    },
    "plot_structure_law": {
        "hook_rule": "Ep 1 must end with a 'Life-or-Death' crisis or a 'Game-Changing' reward.",
        "pacing_rule": "One conflict and resolution every 3000 characters (Cider loop)."
    }
}
"""

# ---------------------------------------------------------
# 🧠 [Step 1] Gemini: 자료 취합 및 초안 작성 (ToT)
# ---------------------------------------------------------
def step1_gather_and_draft(rubric, styles, chars, stories):
    print(f"   🧠 [Gemini ({GEMINI_MODEL_NAME})] 모든 보고서를 읽고 초안을 작성합니다...")
    
    prompt = f"""
    # Role
    You are a **Senior Web Novel Trend Researcher**.
    Your task is to read all these field reports (Style, Character, Story) and extract the **'Common Success Factors'**.

    # Context (RAG)
    [Rubric]: {rubric[:1000]}
    [Style Reports]: {styles[:50000]} 
    [Character Reports]: {chars[:50000]}
    [Story Reports]: {stories[:50000]}

    # Task: Draft a Trend Summary
    Don't just summarize. Find the **Intersection** of all successful works.
    
    # Process (Tree of Thoughts)
    1. **Pattern A (Characters)**: What do all Protagonists have in common? (e.g., Are they all regressors?)
    2. **Pattern B (Pacing)**: How fast is the story? (e.g., Fast hook in Ep 1?)
    3. **Pattern C (Tone)**: Is it serious or light?
    
    # Output
    Summarize these patterns into a detailed text draft.
    """
    try:
        res = gemini_model.generate_content(prompt)
        return res.text
    except Exception as e:
        print(f"   ❌ Gemini 초안 작성 실패: {e}")
        return None

# ---------------------------------------------------------
# ⚖️ [Step 2] OpenAI: 최종 정제 및 규격화 (Self-Reflection)
# ---------------------------------------------------------
def step2_finalize_report(draft):
    print("   ⚖️ [OpenAI GPT-5.1] 초안을 검수하고 '필승 공식'을 확정합니다...")
    
    prompt = f"""
    # Role
    You are the **Chief Editor (Final Decision Maker)**.
    Convert the researcher's draft into a strict **'Winning Formula JSON'** for the Writer AI.

    # Input Data (Draft)
    {draft}

    # Golden Example (Follow this format & depth)
    {GOLDEN_REPORT_EXAMPLE}

    # Execution Protocol (Self-Reflection)
    1. **Critique**: Is the draft too vague? (e.g., "Write well" -> Reject).
    2. **Refine**: Change it to specific instructions (e.g., "Sentences must be < 40 chars").
    3. **Finalize**: Output the JSON strictly.

    # Output Format (JSON Only)
    Produce the JSON structure defined in the Golden Example.
    """
    
    try:
        # GPT-5.1 호출 (없으면 4o 폴백)
        model_name = "gpt-5.1"
        try:
            response = client.chat.completions.create(
                model=model_name, 
                messages=[
                    {"role": "system", "content": "You are a strict logic machine. Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
        except:
            print("      ⚠️ [Info] GPT-5.1 호출 실패, gpt-4o로 전환합니다.")
            model_name = "gpt-4o"
            response = client.chat.completions.create(
                model=model_name, 
                messages=[{"role": "system", "content": "JSON only."}, {"role": "user", "content": prompt}],
                temperature=0.2
            )
        
        # 🔥 [안전 장치] 정규식을 사용하여 JSON만 추출 (AI가 잡담을 섞을 경우 대비)
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return match.group(0)
        else:
            return content.replace("```json", "").replace("```", "").strip()

    except Exception as e:
        print(f"   ❌ OpenAI 정제 실패: {e}")
        return None

# ---------------------------------------------------------
# 🔥 메인 실행 로직
# ---------------------------------------------------------
def run_leader():
    print(f"\n🎖️ [Leader Analyst] 하이브리드 분석 시스템 가동...")
    
    # 1. 파일 읽기 (rglob으로 하위 폴더까지 탐색!)
    rubric_text = "No Rubric"
    if RUBRIC_FILE.exists(): rubric_text = RUBRIC_FILE.read_text(encoding='utf-8')

    # 하위 폴더의 모든 JSON 수집
    styles = []
    chars = []
    stories = []
    
    for f in ANALYSIS_DIR.rglob("STYLE_*.json"):
        try: styles.append(f.read_text(encoding='utf-8'))
        except: pass
        
    for f in ANALYSIS_DIR.rglob("CHAR_*.json"):
        try: chars.append(f.read_text(encoding='utf-8'))
        except: pass
        
    for f in ANALYSIS_DIR.rglob("STORY_*.json"):
        try: stories.append(f.read_text(encoding='utf-8'))
        except: pass

    if not (styles or chars or stories):
        print("❌ [오류] 분석할 보고서가 없습니다. master_analyst.py가 제대로 돌았는지 확인하세요.")
        print(f"   탐색 경로: {ANALYSIS_DIR}")
        return

    print(f"   📂 분석 대상: 총 {len(styles) + len(chars) + len(stories)}개의 보고서 (하위 폴더 포함)")

    # 2. Step 1: Gemini 초안
    draft = step1_gather_and_draft(rubric_text, str(styles), str(chars), str(stories))
    if not draft: return

    # 3. Step 2: OpenAI 최종본
    final_json = step2_finalize_report(draft)
    
    if final_json:
        # 4. 저장
        try:
            # JSON 유효성 검사
            json.loads(final_json)
            OUTPUT_FILE.write_text(final_json, encoding='utf-8')
            print(f"   🎉 [성공] 통합 트렌드 리포트 발행 완료!")
            print(f"      📄 파일 경로: {OUTPUT_FILE}")
        except:
            print("   ⚠️ [경고] JSON 형식이 깨졌습니다. 원본 텍스트로 저장합니다.")
            OUTPUT_FILE.write_text(final_json, encoding='utf-8')

if __name__ == "__main__":
    run_leader()