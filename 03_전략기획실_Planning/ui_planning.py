import streamlit as st
import sys
import time
from pathlib import Path

# 경로 설정
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

if str(PLANNING_DIR) not in sys.path: sys.path.append(str(PLANNING_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# 엔진 로드
try: import strategy_judge as engine
except: engine = None

def render():
    st.markdown("## 🧠 전략 기획실 (Planning Room)")
    st.caption("🚀 아이디어를 입력하면 AI 팀이 3단계 회의를 거쳐 기획안을 만듭니다.")

    if not engine:
        st.error("❌ 엔진 로드 실패 (`strategy_judge.py` 확인 필요)")
        return

    # 1. 입력 패널
    with st.container(border=True):
        col_mode, col_input = st.columns([1, 4])
        with col_mode:
            mode = st.radio("모드 선택", ["신규 기획", "소재 개발", "심폐소생"], index=0)
            mode_map = {"신규 기획": 1, "소재 개발": 2, "심폐소생": 3}
        
        with col_input:
            user_input = st.text_area("💡 아이디어 / 로그라인 / 키워드", height=100, placeholder="예: 재벌가 망나니로 회귀했는데 알고보니 시한부.")
            
            if st.button("🔥 기획 엔진 가동", type="primary", use_container_width=True):
                if not user_input:
                    st.warning("아이디어를 입력하세요.")
                else:
                    with st.status("🤖 AI 기획팀이 회의 중입니다...", expanded=True) as status:
                        st.write("🔍 트렌드 분석 중...")
                        time.sleep(1)
                        st.write("🥊 레드팀 비평 진행 중...")
                        
                        # 엔진 호출
                        final_plan, logs = engine.process_planning(mode_map[mode], user_input)
                        
                        st.text_area("📝 회의록", logs, height=150)
                        status.update(label="✅ 기획 완료!", state="complete", expanded=False)
                        
                        st.session_state.current_plan = final_plan
                        st.rerun()

    # 2. 결과 리포트
    if st.session_state.get('current_plan'):
        plan = st.session_state.current_plan
        
        if plan.get('is_corrupted'):
            st.error("기획 생성 실패")
            return

        st.divider()
        st.header(f"📑 {plan.get('title', '제목 미정')}")
        st.info(f"**로그라인:** {plan.get('logline', '생성 중...')}")

        # 탭 뷰 (내용이 없어도 깨지지 않도록 예외처리)
        t1, t2, t3 = st.tabs(["상세 설정", "플롯", "전략 (SWOT)"])
        
        with t1:
            st.markdown("#### 👥 캐릭터")
            chars = plan.get('characters', [])
            if chars:
                for c in chars:
                    st.markdown(f"**{c.get('name')}** ({c.get('role')}): {c.get('desc')}")
            else:
                st.caption("캐릭터 데이터 없음")

            st.markdown("#### 🌍 세계관")
            st.write(plan.get('world_view', '설정 데이터 없음'))

        with t2:
            plots = plan.get('episode_plots', [])
            if plots:
                for p in plots:
                    with st.expander(f"{p.get('ep')}화: {p.get('title')}"):
                        st.write(p.get('summary'))
            else:
                st.caption("플롯 데이터 없음")

        with t3:
            swot = plan.get('swot_analysis', {})
            if swot:
                c1, c2 = st.columns(2)
                with c1:
                    st.success(f"**강점 (Strength):**\n{swot.get('strength', '-')}")
                    st.info(f"**기회 (Opportunity):**\n{swot.get('opportunity', '-')}")
                with c2:
                    st.error(f"**약점 (Weakness):**\n{swot.get('weakness', '-')}")
                    st.warning(f"**위협 (Threat):**\n{swot.get('threat', '-')}")
            else:
                st.warning("SWOT 분석 데이터가 없습니다. (재생성 권장)")

            st.markdown("#### 💰 세일즈 포인트")
            for sp in plan.get('sales_points', []):
                st.markdown(f"✅ {sp}")

        # 저장 액션
        st.divider()
        if st.button("💾 이 기획안을 [창고]에 저장", type="primary", use_container_width=True):
            ok, msg = engine.save_and_deploy(plan)
            if ok:
                st.toast("✅ 저장 완료! [기획 창고] 탭에서 확인하세요.")
                st.session_state.current_plan = None
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"저장 실패: {msg}")