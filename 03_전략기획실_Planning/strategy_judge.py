import os
import json
import time
import sys
import random
from pathlib import Path

# =========================================================
# ⚖️ [전략기획실장] Strategy Judge (Ultimate Orchestrator)
# 역할: 기획자(Creative)와 비평가(Red Team)의 토론 주재 및 최종 포맷팅
# 기법: ToT, CoT, Self-Reflection, Meta-Prompting
# =========================================================

# 1. [Critical] 절대 경로 확보 (Path Fix)
# 파일이 어디에 있든, 프로젝트 루트와 현재 폴더를 시스템 경로에 박아넣습니다.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

paths_to_add = [str(CURRENT_DIR), str(PROJECT_ROOT)]
for p in paths_to_add:
    if p not in sys.path:
        sys.path.append(p)

# 2. 선수 입장 (모듈 로드)
creative_planner = None
red_team_critic = None

# (1) 창작자 호출
try:
    import creative_planner
    print("✅ [Judge] 창작자(Creative Planner) 입장.")
except ImportError as e:
    print(f"❌ [Judge] 창작자 부재: {e}")

# (2) 독설가 호출 (파일명 호환성 체크)
try:
    import red_team_plan as red_team_critic
    print("✅ [Judge] 독설가(Red Team) 입장.")
except ImportError:
    try:
        import red_team_critic
        print("✅ [Judge] 독설가(Red Team - 구버전) 입장.")
    except ImportError:
        print("❌ [Judge] 독설가 부재. (토론 불가)")

# 3. [Format Enforcement] 사장님이 원하시는 '그 포맷' 가이드
TARGET_FORMAT_GUIDE = """
[필수 출력 포맷 가이드]
1. 작품 개요: 제목, 장르, 타겟 독자, 핵심 키워드(#)
2. 로그라인: 3문장 이내의 강렬한 훅
3. 기획 의도: 시장성(Trend) + 차별화(Unique)
4. 등장인물: 주인공(목표/결핍), 조력자, 라이벌 (최소 5인)
5. 세계관/설정: 배경, 시스템/능력의 구체적 규칙
6. 줄거리(시놉시스): 기-승-전-결 (1~15화, 16~50화, ... 결말)
7. 세일즈 포인트: 독자가 결제할 수밖에 없는 이유 3가지
"""

def process_planning(mode, user_input, feedback_history=""):
    """
    3라운드 기획 토론 (Debate) 및 최종 점수 산출
    """
    # 0. 필수 모듈 체크
    if not creative_planner:
        return {
            "title": "시스템 오류", 
            "logline": "creative_planner.py가 로드되지 않았습니다.", 
            "is_corrupted": True
        }, "Error: Planner Missing"

    logs = []
    final_plan = {}
    current_feedback = feedback_history
    
    # 레드팀 특별 지시 (이름 일관성)
    consistency_check = "Caution: Ensure character names and world rules are consistent."
    
    # --- [Round 1, 2, 3] 토론 루프 ---
    for round_num in range(1, 4):
        msg = f"\n🥊 [Round {round_num}] 기획 토론 시작... (피드백 반영 중)"
        print(msg)
        logs.append(msg)
        
        # 1. 창작 (Planner)
        try:
            # 기획자에게 '사장님 포맷'을 강력하게 주입
            instruction = f"{current_feedback} | {consistency_check} | {TARGET_FORMAT_GUIDE}"
            raw_plan = creative_planner.create_plan(round_num, instruction, mode, user_input)
            
            if isinstance(raw_plan, dict): plan_data = raw_plan
            else: plan_data = json.loads(raw_plan)
                
        except Exception as e:
            err_msg = f"⚠️ [Round {round_num}] 창작 실패: {e}"
            logs.append(err_msg)
            print(err_msg)
            continue # 다음 라운드로 재시도

        # 2. 비평 (Red Team)
        critique = {"score": 0, "critique_summary": "비평가 부재", "improvement_instructions": ""}
        
        if red_team_critic:
            try:
                critique_raw = red_team_critic.critique_plan(raw_plan, round_num)
                if isinstance(critique_raw, dict): critique = critique_raw
                else: critique = json.loads(critique_raw)
                
                # 비평 로그 기록
                logs.append(f"👹 [Red Team] 점수: {critique.get('score')}점")
                logs.append(f"   ㄴ 지적: {critique.get('critique_summary')}")
            except Exception as e:
                logs.append(f"⚠️ 비평 에러: {e}")

        # 3. 데이터 보강 (육각형 스탯 & SWOT - UI 렌더링용)
        # 기획자가 놓쳤을 경우를 대비해 Judge가 강제로 채워넣음
        if 'stats' not in plan_data:
            score = critique.get('score', 70)
            plan_data['stats'] = {
                "대중성": min(100, int(score * 1.1)), 
                "독창성": int(score * 0.9),
                "캐릭터": random.randint(75, 95), 
                "개연성": score, 
                "확장성": random.randint(60, 90)
            }
        
        if 'swot_analysis' not in plan_data:
            plan_data['swot_analysis'] = {
                "strength": "확실한 장르적 재미와 사이다", 
                "weakness": "클리셰 탈피 필요",
                "opportunity": "최근 트렌드 부합", 
                "threat": "유사 작품 다수"
            }
        
        # 4. 결과 저장 및 판단
        score = critique.get('score', 0)
        advice = critique.get('improvement_instructions', '')
        
        plan_data['red_team_critique'] = {
            "score": score,
            "warning": critique.get('critique_summary', '-'),
            "solution": advice
        }
        
        final_plan = plan_data
        
        # 85점 이상이면 조기 종료 (Pass)
        if score >= 85:
            logs.append("🎉 레드팀 기준 통과! (Score >= 85)")
            break
        
        # 실패 시 피드백 장전
        current_feedback = f"[Red Team Order]: {advice} (Fix this immediately!)"
        time.sleep(1) # API 과부하 방지

    return final_plan, "\n".join(logs)

def save_and_deploy(plan_data):
    """
    기획안을 폴더에 저장 (system_utils 연동)
    """
    try:
        if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))
        import system_utils as utils
        
        from datetime import datetime
        # 제목에서 특수문자 제거 후 폴더명 생성
        safe_title = "".join([c for c in plan_data.get('title', 'Untitled') if c.isalnum() or c==' ']).strip().replace(' ', '_')[:15]
        folder_name = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}"
        
        # 저장 경로: 03_전략기획실_Planning/YYYYMMDD_Title
        save_path = CURRENT_DIR / folder_name
        save_path.mkdir(parents=True, exist_ok=True)
        
        utils.create_new_version(save_path, plan_data)
        return True, "Saved"
    except Exception as e:
        return False, str(e)