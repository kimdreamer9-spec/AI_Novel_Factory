import os
import json
import sys
import shutil
from pathlib import Path
from datetime import datetime

# [Setup]
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(CURRENT_DIR) not in sys.path: sys.path.append(str(CURRENT_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# Worker 호출
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
    [AI Logic] 수정된 기획 데이터 생성 (덮어쓰기 아님)
    """
    if not creative_planner: return original_plan, "Planner Missing"
    
    print(f"🛠️ [Dev Manager] 리메이크 지시: {user_feedback}")
    
    try:
        # 수정 지시
        instruction = f"""
        [Original Plan]: {json.dumps(original_plan, ensure_ascii=False)[:4000]}...
        [Boss's Order]: {user_feedback}
        
        [Mission]: 
        1. Reflect the Boss's order perfectly.
        2. **Maintain the JSON structure** (Title, Logline, Characters, SWOT, Plots).
        3. Add 'remake_analysis' field explaining what changed.
        4. **OUTPUT KOREAN ONLY**.
        """
        
        raw = creative_planner.create_plan(1, instruction, mode=2, user_input="Remake")
        new_plan = raw if isinstance(raw, dict) else json.loads(raw)
        
        # 버전 업그레이드 (1.0 -> 1.1)
        new_plan = ensure_swot_data(new_plan)
        try:
            old_ver = float(original_plan.get('version', '1.0'))
            new_plan['version'] = str(round(old_ver + 0.1, 1))
        except: new_plan['version'] = "1.1"
        
        return new_plan, "Success"
        
    except Exception as e:
        print(f"⚠️ 리메이크 오류: {e}")
        return original_plan, str(e)

def save_as_new_branch(original_folder_path, new_plan_data):
    """
    [File Logic] 기존 폴더를 덮어쓰지 않고, '새 폴더'를 만들어 저장 (Branching)
    예: MyNovel_v1.0 -> MyNovel_v1.1 (별도 폴더 생성)
    """
    try:
        # 1. 새 폴더 이름 작명
        version = new_plan_data.get('version', '1.X')
        safe_title = "".join([c for c in new_plan_data.get('title', 'Untitled') if c.isalnum() or c==' ']).strip().replace(' ', '_')[:15]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        new_folder_name = f"{timestamp}_{safe_title}_v{version}"
        new_folder_path = original_folder_path.parent / new_folder_name
        
        # 2. 폴더 생성
        new_folder_path.mkdir(parents=True, exist_ok=True)
        
        # 3. 데이터 저장 (JSON)
        json_path = new_folder_path / "plan.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(new_plan_data, f, ensure_ascii=False, indent=4)
            
        # 4. (옵션) 원본 폴더에 있던 다른 파일들(이미지 등)이 있다면 복사할 수도 있음
        # for item in original_folder_path.iterdir():
        #     if item.name != "plan.json" and item.is_file():
        #         shutil.copy2(item, new_folder_path / item.name)
                
        return True, str(new_folder_path.name)
        
    except Exception as e:
        return False, str(e)