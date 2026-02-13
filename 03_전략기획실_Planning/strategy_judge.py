import os
import json
import time
import sys
import random
from pathlib import Path

# =========================================================
# ⚖️ [전략기획실장] Strategy Judge (Ultimate Orchestrator)
# =========================================================

CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

paths_to_add = [str(CURRENT_DIR), str(PROJECT_ROOT)]
for p in paths_to_add:
    if p not in sys.path:
        sys.path.append(p)

creative_planner = None
red_team_critic = None

try:
    import creative_planner
except ImportError: pass

try:
    import red_team_plan as red_team_critic
except ImportError: pass

TARGET_FORMAT_GUIDE = """
[필수 출력 포맷 가이드 (반드시 이 항목들을 포함할 것)]
1. 작품 개요: 제목, 장르, 타겟 독자, 핵심 키워드(#)
2. 로그라인: 3문장 이내의 강렬한 훅 (Hook)
3. 기획 의도: 시장성(Trend) + 차별화(Unique) 전략
4. 등장인물: 
   - 주인공(목표/결핍/능력)
   - 조력자(Helper)
   - 라이벌(Antagonist) 
   - (최소 5인 이상의 입체적 캐릭터)
5. 세계관/설정: 배경, 시스템/능력의 구체적 규칙(Rule)
6. 줄거리(시놉시스): 기-승-전-결 (1~15화, 16~50화, ... 결말까지)
7. 세일즈 포인트: 독자가 결제할 수밖에 없는 이유 3가지
"""

def process_planning(mode, user_input, feedback_history=""):
    """ [신규 기획] 3라운드 기획 토론 및 최종 점수 산출 """
    if not creative_planner:
        return {"title": "Error", "logline": "Planner Missing", "is_corrupted": True}, "Error"

    logs = []
    final_plan = {}
    current_feedback = feedback_history
    consistency_check = "Caution: Ensure character names and world rules are consistent."
    
    for round_num in range(1, 4):
        msg = f"\n🥊 [Round {round_num}] 기획 토론 시작..."
        print(msg)
        logs.append(msg)
        
        try:
            instruction = f"Feedback: {current_feedback} | Constraint: {consistency_check} | Format: {TARGET_FORMAT_GUIDE}"
            raw_plan = creative_planner.create_plan(round_num, instruction, mode, user_input)
            
            if isinstance(raw_plan, dict): plan_data = raw_plan
            else: plan_data = json.loads(raw_plan)
            
        except Exception as e:
            logs.append(f"⚠️ 창작 실패: {e}")
            continue

        critique = {"score": 0, "critique_summary": "비평가 부재", "improvement_instructions": ""}
        if red_team_critic:
            try:
                critique_raw = red_team_critic.critique_plan(raw_plan, round_num)
                if isinstance(critique_raw, dict): critique = critique_raw
                else: critique = json.loads(critique_raw)
                logs.append(f"👹 레드팀 점수: {critique.get('score')}점")
            except Exception as e:
                logs.append(f"⚠️ 비평 에러: {e}")

        # 데이터 보강
        if 'stats' not in plan_data:
            score = critique.get('score', 70)
            plan_data['stats'] = {
                "대중성": min(100, int(score * 1.1)), "독창성": int(score * 0.9),
                "캐릭터": random.randint(75, 95), "개연성": score, "확장성": random.randint(60, 90)
            }
        
        if 'swot_analysis' not in plan_data:
            plan_data['swot_analysis'] = {
                "strength": "장르적 재미", "weakness": "클리셰 탈피 필요",
                "opportunity": "트렌드 부합", "threat": "경쟁작 다수"
            }
        
        plan_data['red_team_critique'] = {
            "score": critique.get('score', 0),
            "warning": critique.get('critique_summary', '-'),
            "solution": critique.get('improvement_instructions', '')
        }
        
        final_plan = plan_data
        
        if critique.get('score', 0) >= 85:
            logs.append("🎉 통과!")
            break
        
        current_feedback = f"[Red Team Order]: {critique.get('improvement_instructions')} (Fix this!)"
        time.sleep(1)

    return final_plan, "\n".join(logs)

def remake_planning(original_plan, user_feedback):
    """ [리메이크] 기존 기획안 수정 (Smart Remake) """
    if not creative_planner:
        return {"is_corrupted": True, "logline": "Planner Missing"}, "Error"

    print(f"\n🛠️ [Judge] 리메이크 모드 가동... (피드백: {user_feedback})")
    logs = [f"🛠️ 리메이크 요청: {user_feedback}"]

    try:
        instruction = f"""
        [Original Plan]: {json.dumps(original_plan, ensure_ascii=False)}
        [User Feedback]: {user_feedback}
        
        [Mission]: 
        1. Modify the plan based on feedback.
        2. Keep the JSON structure.
        3. Add 'remake_analysis': {{ "pros": "...", "cons": "...", "verdict": "..." }}
        """
        
        raw_result = creative_planner.create_plan(1, instruction, mode=2, user_input="Remake")
        
        if isinstance(raw_result, dict): new_plan = raw_result
        else: new_plan = json.loads(raw_result)
        
        logs.append("✅ 기획자: 수정 완료")

    except Exception as e:
        return original_plan, f"⚠️ 수정 실패: {e}"

    if red_team_critic:
        try:
            critique_raw = red_team_critic.critique_plan(new_plan, 1)
            critique = json.loads(critique_raw) if isinstance(critique_raw, str) else critique_raw
            
            new_plan['red_team_critique'] = {
                "score": critique.get('score'),
                "warning": critique.get('critique_summary'),
                "solution": critique.get('improvement_instructions')
            }
            logs.append(f"👹 레드팀 재검토: {critique.get('score')}점")
        except: pass

    try:
        old_ver = float(original_plan.get('version', '1.0'))
        new_plan['version'] = str(round(old_ver + 0.1, 1))
    except:
        new_plan['version'] = "1.1"

    return new_plan, "\n".join(logs)

def save_and_deploy(plan_data):
    """ 기획안 저장 """
    try:
        if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))
        try: import system_utils as utils
        except: pass

        from datetime import datetime
        safe_title = "".join([c for c in plan_data.get('title', 'Untitled') if c.isalnum() or c==' ']).strip().replace(' ', '_')[:20]
        folder_name = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}"
        
        save_path = CURRENT_FILE_PATH.parent / folder_name
        save_path.mkdir(parents=True, exist_ok=True)
        
        with open(save_path / "plan.json", "w", encoding="utf-8") as f:
            json.dump(plan_data, f, ensure_ascii=False, indent=4)
            
        return True, f"Saved to {folder_name}"
    except Exception as e:
        return False, str(e)