import os
import json
import time
import sys
from pathlib import Path

# [Setup]
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(CURRENT_DIR) not in sys.path: sys.path.append(str(CURRENT_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# Worker 호출
try: import creative_planner
except: creative_planner = None
try: import red_team_plan as red_team_critic
except: red_team_critic = None

# 🔥 [New Standard] 5화 시놉시스 강제 포맷
TARGET_FORMAT_GUIDE = """
[OUTPUT FORMAT RULE - STRICTLY FOLLOW]
1. Title & Genre & Target Audience
2. Logline (One sentence hook)
3. Planning Intent (Marketability + Differentiation)
4. Characters (5 Key Persons: Protagonist, Helper, Rival/Antagonist, etc.)
5. World View & Settings (Rules of the game/world)
6. Synopsis (Must include **At least 5 Episodes** + Future Plot)
7. Sales Points (3 Core reasons to buy)
8. SWOT Analysis (Strength, Weakness, Opportunity, Threat)
"""

def ensure_swot_data(plan_data):
    if 'swot_analysis' not in plan_data or not plan_data['swot_analysis']:
        plan_data['swot_analysis'] = {
            "strength": "분석 대기 중...", "weakness": "보완 필요",
            "opportunity": "트렌드 검토", "threat": "경쟁작 분석"
        }
    return plan_data

def process_planning(mode, user_input, feedback_history=""):
    """
    [신규 기획 프로세스]
    Planner와 Red Team의 3라운드 데스매치
    """
    if not creative_planner: return {"title": "Error"}, "Planner Missing"
    
    logs = []
    final_plan = {}
    current_feedback = feedback_history
    
    for round_num in range(1, 4):
        msg = f"🥊 [Round {round_num}] 기획 생성 및 검증 중..."
        print(msg)
        logs.append(msg)
        
        # 1. 기획 생성 (Planner)
        try:
            instruction = f"Feedback: {current_feedback} | Constraint: {TARGET_FORMAT_GUIDE}"
            raw_plan = creative_planner.create_plan(round_num, instruction, mode, user_input)
            plan_data = raw_plan if isinstance(raw_plan, dict) else json.loads(raw_plan)
            plan_data = ensure_swot_data(plan_data)
        except Exception as e:
            logs.append(f"⚠️ Planner Error: {e}")
            continue

        # 2. 검증 (Red Team)
        critique = {"score": 0, "critique_summary": "비평 대기"}
        if red_team_critic:
            try:
                c_raw = red_team_critic.critique_plan(plan_data, round_num)
                critique = c_raw if isinstance(c_raw, dict) else json.loads(c_raw)
                logs.append(f"👹 Red Team: {critique.get('score')}점 - {critique.get('critique_summary')}")
            except Exception as e:
                logs.append(f"⚠️ Red Team Error: {e}")
        
        plan_data['red_team_critique'] = critique
        final_plan = plan_data
        
        # 3. 조기 종료 판단 (85점 이상)
        if critique.get('score', 0) >= 85:
            logs.append("🎉 [PASS] 레드팀 승인 완료!")
            break
            
        # 4. 피드백 루프
        flaws = critique.get('fatal_flaws', [])
        current_feedback = f"Critique: {critique.get('improvement_instructions')}. Fix flaws: {flaws}"
        time.sleep(1) 

    return final_plan, "\n".join(logs)

def save_and_deploy(plan_data):
    """ 기획안 저장 (신규 생성용) """
    try:
        if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))
        import system_utils as utils
        from datetime import datetime
        
        title = plan_data.get('title', 'Untitled')
        safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip().replace(' ', '_')[:15]
        folder_name = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}"
        
        save_path = CURRENT_DIR / folder_name
        save_path.mkdir(parents=True, exist_ok=True)
        
        utils.create_new_version(save_path, plan_data)
        return True, "Saved"
    except Exception as e:
        return False, str(e)