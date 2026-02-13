import os
import json
import time
import sys
import random
from pathlib import Path

# =========================================================
# ⚖️ [전략기획실장] Strategy Judge (System Logic)
# =========================================================

# 1. [Fix] 절대 경로 변수명 통일 (CURRENT_DIR)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# 시스템 경로 추가
if str(CURRENT_DIR) not in sys.path: sys.path.append(str(CURRENT_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# 2. 모듈 로드
try: import creative_planner
except: creative_planner = None
try: import red_team_plan as red_team_critic
except: red_team_critic = None

# ... (TARGET_FORMAT_GUIDE 등 기존 상수 유지) ...
TARGET_FORMAT_GUIDE = """
[필수 출력 포맷]
1. 작품 개요 (제목, 장르, 키워드)
2. 로그라인 (3문장)
3. 기획 의도 (시장성)
4. 세계관 (Rule)
5. 등장인물 (5인)
6. 줄거리 (기승전결)
7. 세일즈 포인트
"""

def process_planning(mode, user_input, feedback_history=""):
    """ 신규 기획 생성 (3라운드 토론) """
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
            logs.append(f"Round {round_num} Error: {e}")
            continue

        critique = {"score": 0}
        if red_team_critic:
            try:
                c_raw = red_team_critic.critique_plan(plan_data, round_num)
                critique = c_raw if isinstance(c_raw, dict) else json.loads(c_raw)
            except: pass
            
        plan_data['red_team_critique'] = critique
        final_plan = plan_data
        
        # 85점 이상이면 조기 종료
        if critique.get('score', 0) >= 85: break
        current_feedback = critique.get('improvement_instructions', 'Better logic.')
        time.sleep(1)

    return final_plan, "\n".join(logs)

def remake_planning(original_plan, user_feedback):
    """ 기획 수정 (리메이크) """
    if not creative_planner: return original_plan, "Planner Missing"
    try:
        instruction = f"""
        [Original]: {json.dumps(original_plan, ensure_ascii=False)[:3000]}...
        [Order]: {user_feedback}
        [Rule]: Keep JSON structure. Add 'remake_analysis'.
        """
        raw = creative_planner.create_plan(1, instruction, mode=2, user_input="Remake")
        return (raw if isinstance(raw, dict) else json.loads(raw)), "Success"
    except Exception as e:
        return original_plan, str(e)

def save_and_deploy(plan_data):
    """ 
    [Fix] CURRENT_DIR 변수 사용 확인 
    """
    try:
        if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))
        import system_utils as utils
        from datetime import datetime
        
        title = plan_data.get('title', 'Untitled')
        safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip().replace(' ', '_')[:15]
        folder_name = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}"
        
        # 🔥 [여기가 문제였습니다] 이제 CURRENT_DIR이 위에서 정의되었으므로 에러 안 남
        save_path = CURRENT_DIR / folder_name
        save_path.mkdir(parents=True, exist_ok=True)
        
        utils.create_new_version(save_path, plan_data)
        return True, "Saved"
    except Exception as e:
        return False, str(e)