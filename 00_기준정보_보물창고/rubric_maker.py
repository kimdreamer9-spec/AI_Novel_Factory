import os
import json
import sys
import re
import warnings
from pathlib import Path
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# ⚖️ [기준정보 팀] Rubric Maker (V7. Pure & Strict)
# 역할: 사장님의 비급(Tips)을 분석하여 '절대 법전(Rubric)'을 편찬함.
# 엔진: Gemini (via Selector Only) + GPT-5.1
# =========================================================

warnings.filterwarnings("ignore")

# 1. 환경 설정 및 키 로드
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

GEMINI_KEY = os.getenv("GEMINI_KEY_PLANNING")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not GEMINI_KEY or not OPENAI_KEY:
    print("❌ [오류] API 키가 없습니다. .env 파일을 확인하세요.")
    sys.exit(1)

genai.configure(api_key=GEMINI_KEY)
client = OpenAI(api_key=OPENAI_KEY)

OUTPUT_FILE = CURRENT_DIR / "standard-rubric.json"

# 🔥 [경로 수정] 루트 폴더를 시스템 경로에 최우선 추가
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# 🔥 [핵심] 1.5 타령 금지 -> 무조건 Selector에게 위임
try:
    from model_selector import find_best_model
    # 분석용(Analyst)으로 가장 똑똑한 놈을 호출
    GEMINI_MODEL_NAME = find_best_model() 
    print(f"🚀 [Rubric Engine] Gemini 분석가: {GEMINI_MODEL_NAME}")
    gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)

except ImportError:
    print("❌ [치명적 오류] 루트 폴더에 'model_selector.py'가 없습니다!")
    sys.exit(1) # 1.5 쓰느니 차라리 종료함
except Exception as e:
    print(f"❌ [치명적 오류] 모델 로드 실패: {e}")
    sys.exit(1)


# ---------------------------------------------------------
# 🧠 [실행] 법전 편찬 프로세스
# ---------------------------------------------------------
def create_rubric():
    print("\n⚖️ [Rubric Maker] 절대 법전 편찬 시작...")
    
    # 2. 자료 수집 (팁 보물창고 털기)
    print("   🕵️ [Gemini Analyst] 사장님의 비급(Tips)을 정밀 독해합니다...")
    all_tips = ""
    found_files = []
    
    # 현재 폴더(00_기준정보_보물창고) 및 하위 폴더의 모든 txt, md 파일 수집
    for f in CURRENT_DIR.rglob("*"):
        if f.suffix in [".txt", ".md"] and f.name not in ["rubric_maker.py", "standard-rubric.json", "requirements.txt"]:
            found_files.append(f)

    if not found_files:
        print("   ❌ 읽을 파일(팁)이 없습니다. '05_팁_보물창고'에 비급을 넣어주세요.")
        return

    for f in found_files:
        try:
            content = f.read_text(encoding='utf-8')
            all_tips += f"\n--- Tip Source: {f.name} ---\n{content}\n"
            print(f"      📖 Input: {f.name}")
        except: pass

    # 3. Gemini: 심층 분석 (ToT 기법 적용)
    print(f"\n   🧠 [Gemini ({GEMINI_MODEL_NAME})] 성공 요인 추출 중 (Tree of Thoughts)...")
    
    analysis_prompt = f"""
    You are an elite **Web Novel Trend Analyst**.
    Your task is to extract the **'Unwritten Rules of Success'** from the provided [Writing Tips].
    
    # 🌳 Tree of Thoughts Protocol (Think in 3 Branches)
    
    **Branch 1: Market Logic (Commerciality)**
    - What drives readers to pay? (e.g., Cliffhangers, Sizzling Tropes, Regressions)
    - Key Insight: Identify the 'Dopamine Triggers'.
    
    **Branch 2: Emotional Logic (Character)**
    - Why do readers love characters? (e.g., Misunderstanding, Competence, Lack)
    - Key Insight: Define the 'Fatal Flaw' and 'Charm'.
    
    **Branch 3: Structural Logic (Pacing)**
    - How fast should the plot move? (e.g., Cider every 3 eps, Hook every end)
    - Key Insight: The 'Rhythm of Satisfaction'.
    
    # Task
    Synthesize these 3 branches into a comprehensive report on **"What makes a Web Novel Sell in 2026?"**.
    Focus on specific keywords found in the [Data].
    
    [Data]
    {all_tips[:100000]}
    """
    
    try:
        analysis_res = gemini_model.generate_content(analysis_prompt)
        core_values = analysis_res.text
        print("      ✅ 분석 완료. 데이터 추출 성공.")
    except Exception as e:
        print(f"   ❌ Gemini 분석 단계 실패: {e}")
        return

    # 4. OpenAI: 법전 제정 (Self-Reflection 기법 적용)
    # 🔥 [업그레이드] GPT-5.1 호출
    print("\n   ⚖️ [OpenAI GPT-5.1] 최종 법전(Rubric) 제정 중 (Self-Reflection)...")
    
    legislator_prompt = f"""
    You are the **Supreme Legislator of Web Novels**.
    Your mission is to codify the Analyst's report into the **'Ultimate Evaluation Rubric' (JSON)**.
    
    # 🧠 Self-Reflection Protocol
    1. **Draft**: Create initial criteria based on the report.
    2. **Critique**: 
       - "Is 'Good Character' too vague?" -> Change to "Character acts on clear Desire & Lack".
       - "Is 'Fast Paced' ambiguous?" -> Change to "Major event occurs every 2 episodes".
    3. **Finalize**: Output the strictly defined JSON.
    
    # 🛡️ Input Report
    {core_values}
    
    # 📝 Output Requirement (JSON Keys)
    Create a JSON with exactly these 4 keys: 
    - "Commerciality" (Market fit, Title, Keywords)
    - "Character" (Agency, Charm, Villain)
    - "Plot_Pacing" (Cider frequency, Sweet potato limit)
    - "Episode_Hook" (Cliffhangers, Endings)
    
    Each key must have:
    - "score_1_description": What makes it fail?
    - "score_5_description": What makes it average?
    - "score_10_description": What makes it a Masterpiece?
    
    RETURN JSON ONLY.
    """
    
    try:
        # GPT-5.1 호출 (없으면 4o로 폴백)
        model_name = "gpt-5.1"
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a cold-blooded logic machine. Output JSON only."},
                    {"role": "user", "content": legislator_prompt}
                ],
                temperature=0.2
            )
        except:
            print("      ⚠️ [Info] GPT-5.1 호출 실패, gpt-4o로 전환합니다.")
            model_name = "gpt-4o"
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": "JSON only."}, {"role": "user", "content": legislator_prompt}],
                temperature=0.2
            )
        
        # 🔥 [안전 장치] 정규식으로 JSON만 추출
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            rubric_json = match.group(0)
        else:
            rubric_json = content.replace("```json", "").replace("```", "").strip()
        
        # 유효성 검사
        json.loads(rubric_json)
        
        OUTPUT_FILE.write_text(rubric_json, encoding='utf-8')
        print(f"\n   🎉 [완료] 절대 법전 'standard-rubric.json' 제정 완료.")
        print(f"      📂 저장 위치: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"   ❌ OpenAI 법전 제정 실패: {e}")

if __name__ == "__main__":
    create_rubric()