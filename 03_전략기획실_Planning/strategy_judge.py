import os
import json
import time
import sys
import random
from pathlib import Path

# =========================================================
# ⚖️ [전략기획실장] Strategy Judge (Ultimate Orchestrator)
# 역할: 기획자(Gemini)와 비평가(GPT)의 3라운드 데스매치 주재 및 최종 포맷팅
# 기법: ToT (Tree of Thoughts), CoT (Chain of Thought), Self-Reflection
# =========================================================

# 1. [Critical] 절대 경로 확보 (Path Fix)
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent                # 03_전략기획실_Planning
PROJECT_ROOT = PLANNING_DIR.parent                     # Root (AI_Novel_Factory)

paths_to_add = [str(CURRENT_DIR), str(PROJECT_ROOT)]
for p in paths_to_add:
    if p not in sys.path:
        sys.path.append(p)

# 2. 선수 입장 (모듈 로드)
creative_planner = None
red_team_critic = None

# (1) 창작자 호출 (Creative Planner - Gemini 3 Pro)
try:
    import creative_planner
    print("✅ [Judge] 창작자(Creative Planner) 입장 완료.")
except ImportError as e:
    print(f"❌ [Judge] 창작자 부재: {e}")

# (2) 독설가 호출 (Red Team - GPT-5.2)
try:
    import red_team_plan as red_team_critic
    print("✅ [Judge] 독설가(Red Team) 입장 완료.")
except ImportError:
    print("❌ [Judge] 독설가 부재. (토론 불가)")

# 3. [Format Enforcement] 사장님이 원하시는 '그 포맷' 가이드
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
    """
    [신규 기획] 3라운드 기획 토론 (Debate) 및 최종 점수 산출
    """
    if not creative_planner:
        return {
            "title": "시스템 오류", 
            "logline": "creative_planner.py가 로드되지 않았습니다.", 
            "is_corrupted": True
        }, "Error: Planner Missing"

    logs = []
    final_plan = {}
    current_feedback = feedback_history
    consistency_check = "Caution: Ensure character names and world rules are consistent."
    
    print("\n⚖️ [Judge] 기획 회의 시작합니다. (Mode: {})".format(mode))

    for round_num in range(1, 4):
        msg = f"\n🥊 [Round {round_num}] 기획 토론 시작... (피드백 반영 중)"
        print(msg)
        logs.append(msg)
        
        # 1. 창작
        try:
            instruction = f"Feedback: {current_feedback} | Constraint: {consistency_check} | Format: {TARGET_FORMAT_GUIDE}"
            raw_plan = creative_planner.create_plan(round_num, instruction, mode, user_input)
            
            if isinstance(raw_plan, dict): plan_data = raw_plan
            else: plan_data = json.loads(raw_plan)
            
            print(f"   ㄴ 📝 [Planner] 기획안 초안 작성 완료 (제목: {plan_data.get('title')})")
                
        except Exception as e:
            err_msg = f"⚠️ [Round {round_num}] 창작 실패: {e}"
            logs.append(err_msg)
            print(err_msg)
            continue

        # 2. 비평
        critique = {"score": 0, "critique_summary": "비평가 부재", "improvement_instructions": ""}
        if red_team_critic:
            try:
                print("   ㄴ 👹 [Red Team] 비평 중...")
                critique_raw = red_team_critic.critique_plan(raw_plan, round_num)
                if isinstance(critique_raw, dict): critique = critique_raw
                else: critique = json.loads(critique_raw)
                
                logs.append(f"👹 [Red Team] 점수: {critique.get('score')}점")
                logs.append(f"   ㄴ 지적: {critique.get('critique_summary')}")
                print(f"   ㄴ 👹 점수: {critique.get('score')} / 지적: {critique.get('critique_summary')}")
            except Exception as e:
                logs.append(f"⚠️ 비평 에러: {e}")

        # 3. 데이터 보강
        if 'stats' not in plan_data:
            score = critique.get('score', 70)
            plan_data['stats'] = {
                "대중성": min(100, int(score * 1.1)), 
                "독창성": int(score * 0.9),
                "캐릭터": random.randint(75, 95), 
                "개연성": score, 
                "확장성": random.randint(60, 90)
            }
        
        if 'swot_analysis' not in plan_data:
            plan_data['swot_analysis'] = {
                "strength": "확실한 장르적 재미와 사이다", 
                "weakness": "클리셰 탈피 필요",
                "opportunity": "최근 트렌드 부합", 
                "threat": "유사 작품 다수"
            }
        
        score = critique.get('score', 0)
        advice = critique.get('improvement_instructions', '')
        
        plan_data['red_team_critique'] = {
            "score": score,
            "warning": critique.get('critique_summary', '-'),
            "solution": advice
        }
        
        final_plan = plan_data
        
        if score >= 85:
            success_msg = f"🎉 [Round {round_num}] 레드팀 기준 통과! (Score: {score})"
            logs.append(success_msg)
            print(success_msg)
            break
        
        current_feedback = f"[Red Team Order]: {advice} (Fix this immediately!)"
        
        if round_num == 3 and score < 85:
            fail_msg = f"⚠️ [Final] 3라운드 종료. 기준 점수 미달이나 최선 버전을 제출합니다."
            logs.append(fail_msg)
            print(fail_msg)

        time.sleep(1)

    return final_plan, "\n".join(logs)

def remake_planning(original_plan, user_feedback):
    """
    [리메이크] 기존 기획안을 유저 피드백에 맞춰 수정 (Smart Remake)
    """
    if not creative_planner:
        return {"is_corrupted": True, "logline": "Planner Missing"}, "Error"

    print(f"\n🛠️ [Judge] 리메이크 모드 가동... (피드백: {user_feedback})")
    logs = [f"🛠️ 리메이크 요청: {user_feedback}"]

    # 1. 기획자에게 수정 요청 (Analyst Mode)
    try:
        # 원본과 피드백을 주고, 수정된 JSON과 분석 리포트를 동시에 요구
        instruction = f"""
        [Original Plan]: {json.dumps(original_plan, ensure_ascii=False)}
        [User Feedback]: {user_feedback}
        
        [Mission]: 
        1. Analyze the pros and cons of this feedback.
        2. Modify the plan ONLY where necessary based on feedback.
        3. Keep the original JSON structure.
        4. Add a 'remake_analysis' field inside JSON: {{ "pros": "...", "cons": "...", "verdict": "..." }}
        """
        
        # 기획자 호출 (Mode 2: Develop/Remake)
        raw_result = creative_planner.create_plan(1, instruction, mode=2, user_input="Remake Request")
        
        if isinstance(raw_result, dict): new_plan = raw_result
        else: new_plan = json.loads(raw_result)
        
        logs.append("✅ 기획자: 수정안 도출 완료")

    except Exception as e:
        return original_plan, f"⚠️ 수정 실패: {e}"

    # 2. 레드팀 검증 (간소화 - 1회)
    if red_team_critic:
        try:
            critique_raw = red_team_critic.critique_plan(new_plan, 1)
            critique = json.loads(critique_raw) if isinstance(critique_raw, str) else critique_raw
            
            # 레드팀 의견 반영
            new_plan['red_team_critique'] = {
                "score": critique.get('score'),
                "warning": critique.get('critique_summary'),
                "solution": critique.get('improvement_instructions')
            }
            logs.append(f"👹 레드팀 재검토: {critique.get('score')}점")
        except: pass

    # 버전 업 (v1.0 -> v1.1)
    try:
        old_ver = float(original_plan.get('version', '1.0'))
        new_plan['version'] = str(round(old_ver + 0.1, 1))
    except:
        new_plan['version'] = "1.1"

    return new_plan, "\n".join(logs)

def save_and_deploy(plan_data):
    """
    기획안을 폴더에 저장 (system_utils 연동)
    """
    try:
        if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))
        try:
            import system_utils as utils
        except ImportError:
            pass

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

if __name__ == "__main__":
    print("⚖️ Testing Strategy Judge...")
    # 테스트 실행
    # result, log = process_planning(1, "재벌집 막내아들이 회귀해서 게이트를 막는 이야기")
    # print(json.dumps(result, indent=2, ensure_ascii=False))