import os
import json
import time
import sys
import re
import random
import warnings
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# =========================================================
# ⚖️ [총괄 PD] Strategy Judge (V25. Smart Director)
# 목표: 제목 변경 시 폴더 자동 분리 + 대화형 피드백 완벽 구현
# =========================================================

warnings.filterwarnings("ignore")
import google.generativeai as genai

# 1. 환경 및 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_KEY_PLANNING")
if not API_KEY:
    print("❌ [Fatal] API 키가 없습니다.")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# 🔥 [경로 수정]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# 변수 초기화
pd_model = None
MODEL_NAME = "Unknown"

try:
    from model_selector import find_best_model
    MODEL_NAME = find_best_model()
    print(f"⚖️ [Grandmaster Engine] Gemini 총괄 PD: {MODEL_NAME}")
    pd_model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    print(f"❌ [치명적 오류] 모델 로드 실패: {e}")
    sys.exit(1)

try:
    import creative_planner as planner
    from red_team_plan import critique_plan
except ImportError:
    sys.path.append(str(CURRENT_DIR))
    import creative_planner as planner
    from red_team_plan import critique_plan

# 경로 설정
PLANNING_DIR = CURRENT_DIR
RUBRIC_FILE = PROJECT_ROOT / "00_기준정보_보물창고" / "standard-rubric.json"
TREND_REPORT = PROJECT_ROOT / "02_분석실_Analysis" / "00_통합_트렌드_리포트.json"
TIP_DIR = PROJECT_ROOT / "00_기준정보_보물창고" / "05_팁_보물창고" 

# ---------------------------------------------------------
# 📂 스마트 폴더 매니저
# ---------------------------------------------------------
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")[:40]

def manage_project_folder(plan_data, current_folder=None):
    """
    제목이 바뀌었거나 폴더가 없으면 새로 만든다.
    제목이 같으면 기존 폴더를 유지한다.
    """
    raw_title = plan_data.get('1_작품_기본_정보', {}).get('제목', '무제')
    safe_title = sanitize_filename(raw_title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    # 새 폴더 이름 후보
    new_folder_name = f"{timestamp}_{safe_title}"
    
    # 1. 현재 폴더가 없으면 -> 무조건 생성
    if current_folder is None:
        new_path = PLANNING_DIR / new_folder_name
        new_path.mkdir(parents=True, exist_ok=True)
        return new_path, safe_title
    
    # 2. 현재 폴더가 있는데, 제목이 바뀌었는가?
    # 기존 폴더명에서 제목 부분 추출 (타임스탬프 뒤)
    try:
        old_title_part = current_folder.name.split('_', 2)[2] # YYYYMMDD_HHMM_제목
    except:
        old_title_part = ""

    if safe_title != old_title_part:
        # 제목이 다르면 -> 새 컨셉이므로 새 폴더 생성!
        print(f"\n✨ [감지] 기획 방향 변경 감지! ({old_title_part} -> {safe_title})")
        print(f"   -> 새로운 프로젝트 폴더를 생성합니다.")
        new_path = PLANNING_DIR / new_folder_name
        new_path.mkdir(parents=True, exist_ok=True)
        return new_path, safe_title
    else:
        # 제목이 같으면 -> 기존 폴더 유지
        return current_folder, safe_title

def load_pd_knowledge():
    rubric = RUBRIC_FILE.read_text(encoding='utf-8') if RUBRIC_FILE.exists() else "No Rubric"
    trend = TREND_REPORT.read_text(encoding='utf-8') if TREND_REPORT.exists() else "No Trend Data"
    
    tips_data = ""
    if TIP_DIR.exists():
        tip_files = list(TIP_DIR.rglob("*.md")) + list(TIP_DIR.rglob("*.txt"))
        if tip_files:
            selected = random.sample(tip_files, min(len(tip_files), 20))
            for f in selected:
                tips_data += f"\n[Tip: {f.name}]\n{f.read_text(encoding='utf-8')[:3000]}\n"
    
    if not tips_data: tips_data = "팁 보물창고가 비어있습니다."
    return rubric, trend, tips_data

# ---------------------------------------------------------
# 🧠 PD Logic
# ---------------------------------------------------------
def generate_strategy_directive(mode, user_input, rubric, trend, tips):
    print(f"   🧠 [PD] 초기 작전 수립 중... (Mode {mode})")
    base_role = "You are the **Chief Executive Producer (CP)**."
    task = ""
    if mode == 1: task = "Create a BRAND NEW Hit Story."
    elif mode == 2: task = f"Upgrade User Idea: {user_input}"
    elif mode == 3: task = f"Rescue Failed Story: {user_input}"

    meta_prompt = f"""
    {base_role}
    [Context]: {trend[:1000]}
    [Tips]: {tips[:3000]}
    Task: {task}
    Goal: Write a Prompt for the Planner.
    """
    try:
        res = pd_model.generate_content(meta_prompt)
        return res.text
    except Exception as e:
        return f"Strategy Error: {e}"

def finalize_masterpiece(last_plan, last_critique):
    print("\n✨ [PD] 최종 기획안 후가공(Polishing) 중...")
    prompt = f"""
    # Role: Chief Producer
    Refine this draft into a **Perfect Masterpiece**.
    [Draft]: {last_plan}
    [Critique]: {last_critique}
    Task: Fix flaws, Polish Logline, Ensure valid JSON.
    Output: JSON Only.
    """
    try:
        res = pd_model.generate_content(prompt)
        text = res.text.replace("```json", "").replace("```", "").strip()
        json.loads(text) 
        return text
    except:
        return last_plan

def print_briefing(plan_json):
    info = plan_json.get('1_작품_기본_정보', {})
    points = plan_json.get('2_기획_의도_및_셀링_포인트', {}).get('셀링_포인트', [])
    logline = plan_json.get('3_작품_소개_로그라인', "")
    
    print("\n" + "="*70)
    print(f"📢 [PD 브리핑] {info.get('제목', '제목 미정')}")
    print("="*70)
    print(f"🔹 장르: {info.get('장르')} / 타겟: {info.get('타겟_독자')}")
    print(f"🔹 키워드: {info.get('핵심_키워드')}")
    print("-" * 70)
    print(f"💡 [로그라인]:\n   {logline}")
    print("-" * 70)
    print(f"🔥 [셀링 포인트]:")
    for p in points:
        print(f"   - {p}")
    print("="*70)

# ---------------------------------------------------------
# 🏃 Main Loop (Infinite Tiktaka)
# ---------------------------------------------------------
def select_mode():
    print("\n" + "="*60)
    print(f"🎬 [전략기획실] AI 총괄 PD (Powered by {MODEL_NAME})")
    print("="*60)
    print("1. 🆕 [오리지널]: 완전 자동 기획")
    print("2. 💡 [유저기획]: 아이디어 발전")
    print("3. 🚑 [심폐소생]: 망한 글 살리기")
    print("-" * 60)
    while True:
        c = input("👉 모드 선택 (1/2/3): ").strip()
        if c in ['1','2','3']: return int(c)

def get_user_input(mode):
    if mode == 1: return "Auto-Mode"
    elif mode == 2: return input("📝 아이디어 입력: ").strip()
    elif mode == 3: return input("🚑 문제점 입력: ").strip()

def run_meeting():
    try:
        rubric, trend, tips = load_pd_knowledge()
        mode = select_mode()
        user_input_text = get_user_input(mode)
        
        # 초기 전략
        strategy_prompt = generate_strategy_directive(mode, user_input_text, rubric, trend, tips)
        current_feedback = f"[[PD's Initial Order]]: {strategy_prompt}"
        
        # 상태 변수
        project_path = None 
        safe_title = "Project"
        round_num = 0
        
        # 🔥 [무한 루프] 사장님이 OK 할 때까지 돈다
        while True:
            round_num += 1
            print(f"\n=== Round {round_num} ===")
            
            # (A) 기획
            plan_str = planner.create_plan(round_num, current_feedback, mode, user_input_text)
            if "API Error" in plan_str:
                print(f"🚨 [치명적 에러] {plan_str}")
                return

            try:
                plan_json = json.loads(plan_str)
                
                # 🔥 [스마트 폴더 관리] 제목이 바뀌면 새 폴더를 판다
                project_path, safe_title = manage_project_folder(plan_json, project_path)
                print(f"   📂 저장 위치: {project_path}")
                
                # 파일 저장
                (project_path / f"기획안_Draft_V{round_num}.json").write_text(plan_str, encoding='utf-8')
                
                # (B) 비평
                critique_str = critique_plan(plan_str, round_num)
                (project_path / f"비평서_V{round_num}.json").write_text(critique_str, encoding='utf-8')
                
                critique = json.loads(critique_str)
                score = critique.get("score", 0)
                print(f"   📊 AI 점수: {score}점")
                
                # (C) 브리핑 및 결재 (Chatbot Interface)
                print_briefing(plan_json)
                
                print(f"\n👺 [Red Team 의견]: {critique.get('critique_summary')}")
                print("-" * 60)
                print(" [y] 승인 (최종 저장 후 종료)")
                print(" [n] 단순 재시도 (비평 반영하여 다시)")
                print(" [텍스트] 지시사항 입력 (예: 회귀 빼고 능력물로 바꿔)")
                print("-" * 60)
                
                user_cmd = input("👑 사장님 지시: ").strip()
                
                if user_cmd.lower() == 'y':
                    # 최종 확정
                    print(f"\n✨ [최종 확정] PD가 마무리를 짓습니다...")
                    final_json_str = finalize_masterpiece(plan_str, critique_str)
                    
                    final_filename = f"00_최종_확정_기획안_{safe_title}.json"
                    (project_path / final_filename).write_text(final_json_str, encoding='utf-8')
                    
                    print("\n" + "="*60)
                    print(f"🎉 [프로젝트 완료] {final_filename}")
                    print(f"🚀 제작 스튜디오(04_제작소)로 이관 준비 끝.")
                    print("="*60)
                    break
                
                elif user_cmd.lower() == 'n' or user_cmd == "":
                    # 단순 재시도
                    print("🔄 피드백을 반영하여 디벨롭합니다...")
                    current_feedback = f"[[Boss Decision]]: Retry based on critique.\n[[RedTeam]]: {critique.get('improvement_instructions')}"
                
                else:
                    # 구체적 지시사항 (Pivoting)
                    print(f"🗣️ [지시 접수]: '{user_cmd}'")
                    print("🔄 지시사항을 반영하여 기획을 전면 수정합니다...")
                    # 사장님 명령이 최우선
                    current_feedback = f"[[BOSS COMMAND (Priority 1)]]: {user_cmd}\n[[RedTeam Advice]]: {critique.get('improvement_instructions')}"

            except json.JSONDecodeError:
                print("   ⚠️ [형식 오류] 재시도...")
                time.sleep(1)

    except Exception as e:
        print(f"\n❌ [시스템 에러]: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_meeting()