import os
import json
import time
import sys
import random
from pathlib import Path

# =========================================================
# ⚖️ [전략기획실장] Strategy Judge (Full Version)
# 역할: 신규 기획(Create) + 기획 수정(Remake) 총괄
# =========================================================

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(CURRENT_DIR) not in sys.path: sys.path.append(str(CURRENT_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

try: import creative_planner
except: creative_planner = None
try: import red_team_plan as red_team_critic
except: red_team_critic = None

# 신규 기획용 포맷 가이드
TARGET_FORMAT_GUIDE = """
[Strategy Judge's Order]
1. Logline (Killer Hook)
2. 5 Characters (Main, Antagonist, Helper, Rival, Extra)
3. World View (Rules)
4. Commercial Strategy
"""

def process_planning(mode, user_input, feedback_history=""):
    """ [신규 기획] 3라운드 토론 """
    if not creative_planner: return {"title": "Error"}, "Planner Missing"
    
    logs = []
    final_plan = {}
    current_feedback = feedback_history
    
    for round_num in range(1, 4):
        try:
            instruction = f"Feedback: {current_feedback} | Constraint: {TARGET_FORMAT_GUIDE}"
            raw_plan = creative_planner.create_plan(round_num, instruction, mode, user_input)
            plan_data = raw_plan if isinstance(raw_plan, dict) else json.loads(raw_plan)
        except Exception as e:
            continue

        critique = {"score": 0}
        if red_team_critic:
            try:
                c_raw = red_team_critic.critique_plan(plan_data, round_num)
                critique = c_raw if isinstance(c_raw, dict) else json.loads(c_raw)
            except: pass
            
        plan_data['red_team_critique'] = critique
        final_plan = plan_data
        
        if critique.get('score', 0) >= 85: break
        current_feedback = critique.get('improvement_instructions', 'Better logic.')
        time.sleep(1)

    return final_plan, "Done"

def remake_planning(original_plan, user_feedback):
    """ 
    [기획 수정] 사장님의 지시(Feedback)를 받아 기획안을 업그레이드합니다.
    (Model Selector를 사용하는 Creative Planner를 호출하므로 1.5 문제는 없습니다.)
    """
    if not creative_planner: return original_plan, "Planner Missing"
    
    print(f"🛠️ [Judge] 리메이크 지시 접수: {user_feedback}")
    
    try:
        # 기획자에게 수정 지시 (Mode 2: Modify)
        instruction = f"""
        [Original Plan]: {json.dumps(original_plan, ensure_ascii=False)[:3000]}...
        [Boss's Order]: {user_feedback}
        
        [Mission]: 
        1. Reflect the Boss's order perfectly.
        2. Maintain the JSON structure.
        3. Add 'remake_analysis' field explaining what changed.
        """
        
        # 라운드 1회만 진행 (속도 최적화)
        raw_result = creative_planner.create_plan(1, instruction, mode=2, user_input="Remake Request")
        new_plan = raw_result if isinstance(raw_result, dict) else json.loads(raw_result)
        
        # 버전 업
        try:
            old_ver = float(original_plan.get('version', '1.0'))
            new_plan['version'] = str(round(old_ver + 0.1, 1))
        except: new_plan['version'] = "1.1"
        
        return new_plan, "Success"
        
    except Exception as e:
        print(f"⚠️ 리메이크 실패: {e}")
        return original_plan, str(e)

def save_and_deploy(plan_data):
    """ 기획안 저장 """
    try:
        if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))
        import system_utils as utils
        from datetime import datetime
        
        # 제목 안전 처리
        title = plan_data.get('title', 'Untitled')
        safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip().replace(' ', '_')[:15]
        
        # 타임스탬프 폴더 생성
        folder_name = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}"
        save_path = CURRENT_DIR / folder_name
        save_path.mkdir(parents=True, exist_ok=True)
        
        utils.create_new_version(save_path, plan_data)
        return True, "Saved"
    except Exception as e:
        return False, str(e)