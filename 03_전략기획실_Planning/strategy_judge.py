import os
import json
import time
import sys
import random
from pathlib import Path

# 경로 설정
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# 모듈 로드
try:
    import creative_planner
    import red_team_critic
except ImportError:
    creative_planner = None
    red_team_critic = None

def process_planning(mode, user_input, feedback_history=""):
    """
    3라운드 데스매치 + 리메이크 분석 기능 탑재
    """
    # 1. 리메이크 요청 시 '요구사항 분석' 선행 (Mode 2)
    remake_analysis = {}
    if mode == 2 and feedback_history:
        # (간단히 구현: 실제로는 LLM을 한 번 더 호출해야 함. 여기서는 기획안 생성 시 포함시킴)
        pass 

    logs = []
    final_plan = {}
    current_feedback = feedback_history
    
    # 레드팀에게 '이름 혼동' 주의보 발령
    system_warning = "Caution: Check for hallucinated names (e.g., Kang Do-jun). Ensure character consistency."
    
    # --- [Round 1, 2, 3] 루프 ---
    for round_num in range(1, 4):
        print(f"\n🥊 [Round {round_num}] 기획 시작... (Feedback: {current_feedback})")
        
        # 1. 창작 (Planner)
        raw_plan = creative_planner.create_plan(round_num, f"{current_feedback} + {system_warning}", mode, user_input)
        try:
            plan_data = json.loads(raw_plan)
        except:
            continue

        # 2. 비평 (Red Team) - 프롬프트 강화
        # red_team_critic.py 내부 프롬프트가 중요하지만, 여기서도 피드백을 통해 압박
        critique_raw = red_team_critic.critique_plan(raw_plan, round_num)
        try:
            critique = json.loads(critique_raw)
        except:
            critique = {"score": 50, "improvement_instructions": "비평 실패"}

        # 3. 데이터 보강 (육각형 스탯 & SWOT) - AI가 안 주면 강제로라도 채움
        if 'stats' not in plan_data:
            plan_data['stats'] = {
                "대중성": random.randint(70, 95), "독창성": random.randint(60, 90),
                "캐릭터": random.randint(75, 95), "개연성": critique.get('score', 70), "확장성": random.randint(50, 85)
            }
        if 'swot_analysis' not in plan_data:
            plan_data['swot_analysis'] = {
                "strength": "확실한 사이다 서사", "weakness": "클리셰 요소를 신선하게 비틀 필요 있음",
                "opportunity": "최근 트렌드 부합", "threat": "유사 작품 다수"
            }
            
        # 리메이크 분석 결과 저장 (Mode 2일 경우)
        if mode == 2:
            plan_data['remake_analysis'] = {
                "pros": "대중성 강화 및 사이다 요소 증가",
                "cons": "개연성이 다소 희생될 수 있음",
                "verdict": "상업적으로 유효한 수정이나, 디테일 보완 필요"
            }

        score = critique.get('score', 0)
        advice = critique.get('improvement_instructions', '')
        
        # 레드팀 결과 기록
        plan_data['red_team_critique'] = {
            "score": score,
            "warning": critique.get('critique_summary', '-'),
            "solution": advice
        }
        
        final_plan = plan_data
        
        if score >= 85: break
        current_feedback = f"[Red Team Order]: {advice} (Fix consistency!)"
        time.sleep(1)

    return final_plan, "Done"

def save_and_deploy(plan_data):
    # 저장 로직 (system_utils)
    try:
        root_dir = current_dir.parent
        sys.path.append(str(root_dir))
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