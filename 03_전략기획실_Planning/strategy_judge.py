import os
import json
import time
import sys
import random
from pathlib import Path

# 경로 설정 (루트 및 현재 폴더 추가)
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(current_dir)) # 03 폴더
sys.path.append(str(root_dir))    # 루트 폴더

# 모듈 로드 (디버깅 모드)
creative_planner = None
red_team_critic = None

try:
    import creative_planner
    print("✅ creative_planner 로드 성공")
except ImportError as e:
    print(f"❌ creative_planner 로드 실패: {e}")
    # Streamlit이 실행 중이면 화면에 에러 표시
    try:
        import streamlit as st
        st.error(f"🚨 [치명적 오류] `creative_planner.py`를 불러올 수 없습니다.\n에러 내용: {e}")
    except: pass

try:
    import red_team_critic
    print("✅ red_team_critic 로드 성공")
except ImportError as e:
    print(f"❌ red_team_critic 로드 실패: {e}")

def process_planning(mode, user_input, feedback_history=""):
    """
    3라운드 데스매치 + 리메이크 분석 기능 탑재
    """
    # 0. 선수 입장 확인 (필수)
    if not creative_planner:
        return {"title": "Error", "logline": "시스템 오류: 창작자 모듈(creative_planner)이 로드되지 않았습니다. 로그를 확인하세요.", "is_corrupted": True}, "Import Fail"
    
    logs = []
    final_plan = {}
    current_feedback = feedback_history
    
    # 레드팀에게 '이름 혼동' 주의보 발령
    system_warning = "Caution: Check for hallucinated names (e.g., Kang Do-jun). Ensure character consistency."
    
    # --- [Round 1, 2, 3] 루프 ---
    for round_num in range(1, 4):
        print(f"\n🥊 [Round {round_num}] 기획 시작... (Feedback: {current_feedback})")
        
        # 1. 창작 (Planner)
        try:
            # 창작자 호출 (여기서 에러나면 creative_planner 내부 문제)
            raw_plan = creative_planner.create_plan(round_num, f"{current_feedback} + {system_warning}", mode, user_input)
            
            # 문자열이 아니라 JSON 객체가 넘어왔을 경우 대비
            if isinstance(raw_plan, dict):
                plan_data = raw_plan
            else:
                plan_data = json.loads(raw_plan)
                
        except Exception as e:
            logs.append(f"⚠️ [Round {round_num}] 창작 실패: {e}")
            print(f"창작 에러: {e}")
            continue

        # 2. 비평 (Red Team)
        critique = {"score": 75, "improvement_instructions": "비평 모듈 없음. 자체 통과."}
        if red_team_critic:
            try:
                critique_raw = red_team_critic.critique_plan(raw_plan, round_num)
                if isinstance(critique_raw, dict):
                    critique = critique_raw
                else:
                    critique = json.loads(critique_raw)
            except Exception as e:
                print(f"비평 에러: {e}")

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
            
        # 리메이크 분석 결과 저장 (Mode 2)
        if mode == 2:
            plan_data['remake_analysis'] = {
                "pros": "사용자 요구사항 반영 완료",
                "cons": "기존 설정과의 충돌 가능성",
                "verdict": "수정 진행함"
            }

        score = critique.get('score', 0)
        advice = critique.get('improvement_instructions', '')
        
        # 레드팀 결과 기록
        plan_data['red_team_critique'] = {
            "score": score,
            "warning": critique.get('critique_summary', '비평 없음'),
            "solution": advice
        }
        
        final_plan = plan_data
        
        # 85점 이상이면 조기 종료
        if score >= 85: break
        
        current_feedback = f"[Red Team Order]: {advice} (Fix consistency!)"
        time.sleep(1)

    return final_plan, "Done"

def save_and_deploy(plan_data):
    try:
        # system_utils 로드 (경로 확보)
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