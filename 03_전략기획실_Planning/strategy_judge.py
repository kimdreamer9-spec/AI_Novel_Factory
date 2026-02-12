import os
import json
import time
import sys
from pathlib import Path

# 같은 폴더의 모듈 로드
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

try:
    import creative_planner
    import red_team_critic
except ImportError as e:
    print(f"❌ [Error] 선수들이 입장하지 않았습니다: {e}")
    # 파일이 없을 경우를 대비한 더미 처리 (앱 셧다운 방지)
    creative_planner = None
    red_team_critic = None

def process_planning(mode, user_input, feedback_history=""):
    """
    3라운드 데스매치 (Debate) 주재 함수
    """
    if not creative_planner or not red_team_critic:
        return {"title": "Error", "logline": "모듈 누락: creative_planner.py 또는 red_team_critic.py가 03 폴더에 없습니다."}, "Error"

    logs = []
    final_plan = {}
    current_feedback = feedback_history
    
    # --- [Round 1, 2, 3] 루프 시작 ---
    for round_num in range(1, 4): # 1, 2, 3회전
        log_msg = f"\n🥊 [Round {round_num}] 기획 회의 시작..."
        logs.append(log_msg)
        print(log_msg)

        # 1. 창작자(Planner)가 기획안 작성
        raw_plan = creative_planner.create_plan(round_num, current_feedback, mode, user_input)
        
        # JSON 파싱 (실패 시 에러 처리)
        try:
            plan_data = json.loads(raw_plan)
        except:
            logs.append(f"⚠️ [Round {round_num}] JSON 파싱 실패. 재시도합니다.")
            continue # 이번 라운드 무효, 다음으로

        # 2. 레드팀(Red Team)이 무자비하게 비평
        critique_raw = red_team_critic.critique_plan(raw_plan, round_num)
        
        try:
            critique_data = json.loads(critique_raw)
        except:
            critique_data = {"score": 50, "status": "ERROR", "improvement_instructions": "비평 데이터 오류."}

        # 3. 결과 기록 및 판단
        score = critique_data.get('score', 0)
        status = critique_data.get('status', 'FAIL')
        advice = critique_data.get('improvement_instructions', 'No advice')
        
        # 기획안에 레드팀 비평 심어주기 (UI 표시용)
        plan_data['red_team_critique'] = {
            "round": round_num,
            "score": score,
            "warning": critique_data.get('critique_summary', '비평 없음'),
            "solution": advice
        }
        
        final_plan = plan_data # 일단 현재 버전 저장
        logs.append(f"📊 [Score: {score}점] 판정: {status}")

        # 4. 조기 통과 (85점 이상이면 퇴근)
        if score >= 85:
            logs.append("🎉 [PASS] 레드팀 기준을 통과했습니다! 3라운드 전에 종료합니다.")
            break
        
        # 5. 실패 시 피드백 장전 (다음 라운드용)
        current_feedback = f"[Red Team Feedback]: {advice} (Fix this logic hole!)"
        logs.append(f"🔄 [Retry] 레드팀의 독설: {advice}")
        time.sleep(1) # API 부하 방지

    return final_plan, "\n".join(logs)

def save_and_deploy(plan_data):
    # 저장 로직 (system_utils 호출)
    try:
        root_dir = current_dir.parent
        sys.path.append(str(root_dir))
        import system_utils as utils
        
        from datetime import datetime
        safe_title = "".join([c for c in plan_data.get('title', 'Untitled') if c.isalnum() or c==' ']).strip().replace(' ', '_')[:20]
        folder_name = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}"
        path = current_dir / folder_name
        path.mkdir(parents=True, exist_ok=True)
        
        utils.create_new_version(path, plan_data)
        return True, "Saved"
    except Exception as e:
        return False, str(e)