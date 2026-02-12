import os
import json
import time
import sys
import random
from pathlib import Path

# 경로 설정
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(current_dir) not in sys.path: sys.path.append(str(current_dir))
if str(root_dir) not in sys.path: sys.path.append(str(root_dir))

# 모듈 로드 (안전하게 시도)
creative_planner = None
red_team_critic = None

# 1. 창작자 로드
try:
    import creative_planner
except ImportError:
    pass # 일단 넘어감 (나중에 체크)

# 2. 레드팀 로드 (이름이 뭐든 다 찾아봄)
try:
    import red_team_plan as red_team_critic
except ImportError:
    try:
        import red_team_critic
    except ImportError:
        pass # 없으면 없는대로 진행

def process_planning(mode, user_input, feedback_history=""):
    """
    안전 모드: 모듈이 없으면 없는대로 동작
    """
    # 0. 필수 모듈 체크
    if not creative_planner:
        return {
            "title": "시스템 오류", 
            "logline": "creative_planner.py 파일을 찾을 수 없습니다.", 
            "is_corrupted": True
        }, "Error: Planner Missing"

    logs = []
    final_plan = {}
    current_feedback = feedback_history
    
    # 1. 기획 생성 (1라운드만 진행 - 일단 작동 확인용)
    print("🚀 기획 생성 시작...")
    try:
        raw_plan = creative_planner.create_plan(1, current_feedback, mode, user_input)
        
        if isinstance(raw_plan, dict): plan_data = raw_plan
        else: plan_data = json.loads(raw_plan)
        
        final_plan = plan_data
        
    except Exception as e:
        return {
            "title": "생성 실패", 
            "logline": f"에러 발생: {str(e)}", 
            "is_corrupted": True
        }, f"Error: {e}"

    # 2. 레드팀 비평 (있으면 하고, 없으면 패스)
    critique = {"score": 0, "improvement_instructions": "레드팀 없음"}
    if red_team_critic:
        try:
            critique_raw = red_team_critic.critique_plan(raw_plan, 1)
            if isinstance(critique_raw, dict): critique = critique_raw
            else: critique = json.loads(critique_raw)
        except: pass
    
    # 3. 데이터 보강 (육각형 그래프용)
    if 'stats' not in final_plan:
        final_plan['stats'] = {
            "대중성": 80, "독창성": 70, "캐릭터": 85, "개연성": 75, "확장성": 60
        }
    
    # 레드팀 결과 기록
    final_plan['red_team_critique'] = {
        "score": critique.get('score', 0),
        "warning": critique.get('critique_summary', '-'),
        "solution": critique.get('improvement_instructions', '-')
    }

    return final_plan, "Done"

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