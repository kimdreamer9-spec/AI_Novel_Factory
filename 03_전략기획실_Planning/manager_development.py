import os
import json
import sys
from pathlib import Path

# [Setup]
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(CURRENT_DIR) not in sys.path: sys.path.append(str(CURRENT_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# Worker 호출 (Planner만 있으면 됨)
try: import creative_planner
except: creative_planner = None

def ensure_swot_data(plan_data):
    if 'swot_analysis' not in plan_data or not plan_data['swot_analysis']:
        plan_data['swot_analysis'] = {
            "strength": "분석 대기 중...", "weakness": "보완 필요",
            "opportunity": "트렌드 검토", "threat": "경쟁작 분석"
        }
    return plan_data

def remake_planning(original_plan, user_feedback):
    """
    [기획 수정 프로세스]
    기존 기획안을 바탕으로 사장님의 지시사항(Feedback)을 반영하여 업그레이드
    """
    if not creative_planner: return original_plan, "Planner Missing"
    
    print(f"🛠️ [Dev Manager] 리메이크 지시: {user_feedback}")
    
    try:
        # 수정 지시 (Mode 2: Modify)
        instruction = f"""
        [Original Plan]: {json.dumps(original_plan, ensure_ascii=False)[:4000]}...
        [Boss's Order]: {user_feedback}
        
        [Mission]: 
        1. Reflect the Boss's order perfectly.
        2. Maintain the JSON structure (Title, Logline, Characters, SWOT, Plots).
        3. Add 'remake_analysis' field explaining what changed.
        4. Output JSON Only.
        """
        
        raw = creative_planner.create_plan(1, instruction, mode=2, user_input="Remake")
        new_plan = raw if isinstance(raw, dict) else json.loads(raw)
        
        # 데이터 보정 및 버전 업
        new_plan = ensure_swot_data(new_plan)
        try:
            old_ver = float(original_plan.get('version', '1.0'))
            new_plan['version'] = str(round(old_ver + 0.1, 1))
        except: new_plan['version'] = "1.1"
        
        return new_plan, "Success"
        
    except Exception as e:
        print(f"⚠️ 리메이크 오류: {e}")
        return original_plan, str(e)