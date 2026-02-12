import os
import json
import time
import sys
import random
from pathlib import Path

# 1. 경로 설정 (루트 및 현재 폴더 추가)
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(current_dir)) # 03 폴더
sys.path.append(str(root_dir))    # 루트 폴더

# 2. 모듈 로드 (이름표 수정 완료)
creative_planner = None
red_team_critic = None

# (1) 창작자 로드
try:
    import creative_planner
    print("✅ [Load] 창작자(creative_planner) 입장 완료")
except ImportError as e:
    print(f"❌ [Error] 창작자 로드 실패: {e}")

# (2) 레드팀 로드 (파일명 수정: red_team_plan)
try:
    import red_team_plan as red_team_critic # 🔥 여기가 핵심 수정사항입니다!
    print("✅ [Load] 독설가(red_team_plan) 입장 완료")
except ImportError as e:
    # 혹시 파일명이 다를까봐 2차 시도
    try:
        import red_team_critic
        print("✅ [Load] 독설가(red_team_critic) 입장 완료")
    except ImportError:
        print(f"❌ [Error] 레드팀 로드 실패: {e}")

def process_planning(mode, user_input, feedback_history=""):
    """
    3라운드 데스매치 (Debate System)
    """
    # 0. 선수 입장 확인
    if not creative_planner:
        return {"title": "Error", "logline": "창작자 모듈이 없습니다.", "is_corrupted": True}, "Planner Missing"
    
    logs = []
    final_plan = {}
    current_feedback = feedback_history
    
    # 레드팀에게 '이름 혼동' 주의보 발령
    system_warning = "Caution: Check for hallucinated names (e.g., Kang Do-jun). Ensure character consistency."
    
    # --- [Round 1, 2, 3] 루프 ---
    for round_num in range(1, 4):
        msg = f"\n🥊 [Round {round_num}] 기획 토론 시작... (Feedback: {current_feedback[:30]}...)"
        print(msg)
        logs.append(msg)
        
        # 1. 창작 (Planner + RAG)
        try:
            # 창작자는 내부적으로 gather_materials를 통해 RAG(팁, 분석자료)를 이미 쓰고 있습니다.
            raw_plan = creative_planner.create_plan(round_num, f"{current_feedback} + {system_warning}", mode, user_input)
            
            if isinstance(raw_plan, dict): plan_data = raw_plan
            else: plan_data = json.loads(raw_plan)
                
        except Exception as e:
            err_msg = f"⚠️ [Round {round_num}] 창작 실패: {e}"
            logs.append(err_msg)
            print(err_msg)
            continue

        # 2. 비평 (Red Team)
        critique = {"score": 0, "improvement_instructions": "비평 모듈 없음", "critique_summary": "레드팀 부재"}
        
        if red_team_critic:
            try:
                # 레드팀이 GPT-5.1(또는 4o)로 무자비하게 까요
                critique_raw = red_team_critic.critique_plan(raw_plan, round_num)
                if isinstance(critique_raw, dict): critique = critique_raw
                else: critique = json.loads(critique_raw)
                
                logs.append(f"👹 [Red Team] 점수: {critique.get('score')}점 | 지적: {critique.get('critique_summary')}")
            except Exception as e:
                logs.append(f"⚠️ 비평 에러: {e}")
        else:
            logs.append("⚠️ 레드팀 모듈을 찾지 못해 비평을 건너뜁니다.")

        # 3. 데이터 보강 (육각형 스탯 & SWOT)
        if 'stats' not in plan_data:
            plan_data['stats'] = {
                "대중성": random.randint(70, 95), "독창성": random.randint(60, 90),
                "캐릭터": random.randint(75, 95), "개연성": critique.get('score', 70), "확장성": random.randint(50, 85)
            }
        if 'swot_analysis' not in plan_data:
            plan_data['swot_analysis'] = {
                "strength": "확실한 장르적 재미", "weakness": "클리셰 보완 필요",
                "opportunity": "트렌드 부합", "threat": "경쟁작 다수"
            }
        
        # 리메이크 분석 결과 (Mode 2)
        if mode == 2:
            plan_data['remake_analysis'] = {
                "pros": "사용자 요구사항 반영 완료",
                "cons": "기존 설정과의 충돌 가능성 존재",
                "verdict": "수정안 채택"
            }

        score = critique.get('score', 0)
        advice = critique.get('improvement_instructions', '')
        
        # 레드팀 결과 기록 (UI 표시용)
        plan_data['red_team_critique'] = {
            "score": score,
            "warning": critique.get('critique_summary', '비평 없음'),
            "solution": advice
        }
        
        final_plan = plan_data
        
        # 85점 이상이면 조기 종료
        if score >= 85:
            logs.append("🎉 레드팀 기준 통과! 조기 종료합니다.")
            break
        
        current_feedback = f"[Red Team Order]: {advice} (Fix consistency!)"
        time.sleep(1)

    return final_plan, "\n".join(logs)

def save_and_deploy(plan_data):
    try:
        if str(root_dir) not in sys.path: sys.path.append(str(root_dir))
        import system_utils as utils
        
        from datetime import datetime
        safe = "".join([c for c in plan_data.get('title', 'Untitled') if c.isalnum() or c==' ']).strip().replace(' ', '_')[:15]
        folder = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe}"
        path = current_dir / folder
        path.mkdir(parents=True, exist_ok=True)
        
        utils.create_new_version(path, plan_data)
        return True, "Saved"
    except Exception as e:
        return False, str(e)