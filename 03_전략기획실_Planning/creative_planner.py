import os
import json
import re
import sys
import random
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# 🧠 [기획 팀장] Creative Planner (V21. Import Fix)
# =========================================================

# 1. 환경 및 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# 🔥 [경로 수정]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
API_KEY = os.getenv("GEMINI_KEY_PLANNING")
genai.configure(api_key=API_KEY)

# 🔥 [핵심 수정] model_selector에서 확실히 있는 함수(find_best_model)를 호출
try:
    from model_selector import find_best_model
    MODEL_NAME = find_best_model()
    print(f"🚀 [Planner Engine] Gemini 창작자: {MODEL_NAME}")
    model = genai.GenerativeModel(MODEL_NAME)

except ImportError as e:
    print(f"❌ [치명적 오류] model_selector를 불러올 수 없습니다.")
    print(f"   에러 내용: {e}")
    print(f"   탐색 경로: {sys.path}")
    sys.exit(1)
except Exception as e:
    print(f"❌ [치명적 오류] 모델 로드 실패: {e}")
    sys.exit(1)

# ... (이하 코드는 V20과 동일하지만, 편의를 위해 풀코드 제공) ...

RUBRIC_FILE = PROJECT_ROOT / "00_기준정보_보물창고" / "standard-rubric.json"
TREND_REPORT = PROJECT_ROOT / "02_분석실_Analysis" / "00_통합_트렌드_리포트.json"
TIP_DIR = PROJECT_ROOT / "00_기준정보_보물창고" / "05_팁_보물창고"
DB_DIR = PROJECT_ROOT / "04_설정_자료집"

GOLDEN_TEMPLATE = """
{
  "1_작품_기본_정보": {
    "제목": "제목 (가제)",
    "장르": "예: 현대 판타지, 재벌물",
    "핵심_키워드": "#키워드1 #키워드2 #키워드3",
    "타겟_독자": "20~40대 남성"
  },
  "2_기획_의도_및_셀링_포인트": {
    "의도": "기획 의도",
    "셀링_포인트": ["1) 포인트", "2) 포인트", "3) 포인트"]
  },
  "3_작품_소개_로그라인": "3줄 요약",
  "4_캐릭터_설정": {
    "주인공": {
      "이름": "OOO",
      "나이_변화": "현생 -> 회귀",
      "성격": "...",
      "매력_포인트": "..."
    },
    "주요_조연_5인": [
      {"이름": "조연1", "역할": "메인_빌런", "설정": "..."},
      {"이름": "조연2", "역할": "조력자", "설정": "..."},
      {"이름": "조연3", "역할": "라이벌", "설정": "..."},
      {"이름": "조연4", "역할": "충신", "설정": "..."},
      {"이름": "조연5", "역할": "히로인/특수", "설정": "..."}
    ]
  },
  "5_핵심_줄거리_시놉시스": {
    "도입부_1_15화": "내용...",
    "전개_16화_이후": "내용...",
    "위기_및_절정": "내용...",
    "결말": "내용..."
  },
  "6_연재_계획": {
    "목표": "200화 이상",
    "연재_속도": "주 5회",
    "초반_전략": "..."
  },
  "6_고증_및_전략": "..."
}
"""

def gather_materials(mode):
    rubric = RUBRIC_FILE.read_text(encoding='utf-8') if RUBRIC_FILE.exists() else ""
    trend = TREND_REPORT.read_text(encoding='utf-8') if TREND_REPORT.exists() else ""
    tips_data = ""
    if TIP_DIR.exists():
        tip_files = list(TIP_DIR.rglob("*.md")) + list(TIP_DIR.rglob("*.txt"))
        if tip_files:
            selected_tips = random.sample(tip_files, min(len(tip_files), 15))
            for f in selected_tips:
                tips_data += f"\n[Secret Tip: {f.name}]\n{f.read_text(encoding='utf-8')[:5000]}\n"
    db_context = ""
    if DB_DIR.exists():
        for f in DB_DIR.rglob("*.md"):
             try: db_context += f"\n[Source DB: {f.name}]\n{f.read_text(encoding='utf-8')[:15000]}\n"
             except: pass
    return rubric, trend, tips_data, db_context

def create_plan(round_num, feedback, mode=1, user_input=""):
    print(f"   🚀 [Planner] 기획안 V{round_num} 작성 중... (Engine: {MODEL_NAME})")
    rubric, trend, tips, db_context = gather_materials(mode)
    mode_instruction = ""
    if mode == 1: mode_instruction = "Task: Create a BRAND NEW Hit Novel."
    elif mode == 2: mode_instruction = f"Task: Develop USER IDEA: '{user_input}'."
    elif mode == 3: mode_instruction = f"Task: Rescue FAILED STORY: '{user_input}'."

    prompt = f"""
    # Role
    You are **Korea's Top Web Novel Planner** (Powered by {MODEL_NAME}).
    # Task
    {mode_instruction}
    Draft a proposal (V{round_num}) strictly following the **[Golden Template]**.
    # REQUIREMENTS
    1. **Character Count**: Exactly **5 Supporting Characters**.
    2. **Format**: JSON ONLY.
    3. **Synopsis**: Detailed breakdown (Intro/Dev/Crisis/End).
    # RAG Context
    [Tips]: {tips}
    [Trend]: {trend[:1000]}
    [DB]: {db_context[:30000]}
    [Feedback]: {feedback}
    # Golden Template
    {GOLDEN_TEMPLATE}
    # Output
    JSON ONLY.
    """
    try:
        res = model.generate_content(prompt)
        text = res.text.replace("```json", "").replace("```", "").strip()
        try: json.loads(text); return text
        except:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: return match.group(0)
            return json.dumps({"error": "JSON Parsing Error", "raw": text})
    except Exception as e:
        return json.dumps({"error": f"API Error: {str(e)}"})