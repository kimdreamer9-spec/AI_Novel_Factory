import streamlit as st
import sys
import time
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V6 (The Partner UI)
# =========================================================

# 1. 경로 설정
current_dir = Path(__file__).parent
planning_dir = current_dir / "03_전략기획실_Planning"
sys.path.append(str(planning_dir))

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 2. 엔진 로드
try:
    import strategy_judge as engine
    engine.init_engine()
    ENGINE_STATUS = "🟢 엔진 정상"
    MODEL_INFO = getattr(engine, 'MODEL_NAME', 'Unknown')
except ImportError:
    ENGINE_STATUS = "🔴 엔진 연결 실패"
    MODEL_INFO = "Unknown"

st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"시스템 상태: {ENGINE_STATUS} | Model: {MODEL_INFO}")

if "plan_history" not in st.session_state: st.session_state.plan_history = [] 
if "current_plan" not in st.session_state: st.session_state.current_plan = None 

tab_plan, tab_write, tab_qc = st.tabs(["💡 1. 기획실", "✍️ 2. 제작소", "⚖️ 3. 품질관리"])

# =========================================================
# 💡 1. 기획실
# =========================================================
with tab_plan:
    st.subheader("🧠 전략 기획실 (Strategy Room)")
    c1, c2 = st.columns([1, 1.5])
    
    # [왼쪽] 입력
    with c1:
        st.info("🛠️ 작전 지시")
        mode_idx = st.radio("모드 선택", ["1. 오리지널 (자동)", "2. 유저 기획 (발전)", "3. 심폐소생 (수정)"], index=0)
        user_input = st.text_area("키워드 / 아이디어 / 문제점 입력", height=150)
        
        if st.button("🔥 기획 엔진 가동", type="primary"):
            if "🔴" in ENGINE_STATUS:
                st.error("엔진 연결 실패")
            else:
                with st.spinner("PD가 레디팀과 회의 중입니다..."):
                    mode_num = int(mode_idx[0])
                    res, logs = engine.process_planning(mode_num, user_input)
                    st.session_state.current_plan = res
                    st.session_state.logs = logs
                    st.rerun()

    # [오른쪽] 보고서
    with c2:
        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            
            # 🔥 [New] 리스크 리포트 (PD의 직언)
            risk = plan.get('risk_report', {})
            if risk.get('detected') == True:
                st.error("🚨 [Red Team 긴급 제언] 사장님, 잠시만요!")
                st.markdown(f"""
                <div style="background-color:#fff5f5; padding:15px; border-radius:5px; border:1px solid #fc8181; color:#c53030;">
                    <b>⛔ 경고:</b> {risk.get('red_team_warning')}<br><br>
                    <b>💡 대안 제시:</b> {risk.get('alternative_suggestion')}
                </div>
                """, unsafe_allow_html=True)
                st.write("") # 여백
            
            # 기본 정보
            st.markdown(f"# 📑 {plan.get('title', '제목 미정')}")
            keywords = plan.get('keywords', [])
            kw_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
            st.markdown(f"**장르:** {plan.get('genre')} | **키워드:** {kw_str}")
            st.info(f"💡 **로그라인:** {plan.get('logline')}")
            
            # 상세 내용
            with st.expander("📌 3. 기획 의도", expanded=True):
                st.write(plan.get('planning_intent', '내용 없음'))
            with st.expander("👥 4. 등장인물", expanded=True):
                for char in plan.get('characters', []):
                    if isinstance(char, dict):
                        st.markdown(f"**{char.get('name')}** ({char.get('role')}): {char.get('desc')}")
                    else: st.write(f"- {char}")
            with st.expander("📜 5. 줄거리", expanded=True):
                st.write(plan.get('synopsis', '내용 없음'))
            with st.expander("🔥 6. 차별화 포인트", expanded=True):
                for p in plan.get('selling_points', []):
                    st.write(f"- {p}")
            
            st.caption(f"🏁 PD 코멘트: {plan.get('pd_comment')}")
            st.markdown("---")
            
            # 결재 버튼
            st.write("### 👑 사장님 결재")
            col_approve, col_reject, col_trash = st.columns(3)
            
            if col_approve.button("✅ 승인 (제작 착수)"):
                success, msg = engine.save_and_deploy(plan)
                if success:
                    st.toast("제작소 이관 완료!", icon="🚀")
                    st.success(msg)
                else: st.error(msg)
            
            with col_reject.popover("⚠️ 반려 (수정 지시)"):
                feedback = st.text_area("수정 지시사항")
                if st.button("수정 요청 전송"):
                    with st.spinner("지시사항 재검토 중..."):
                        mode_num = int(mode_idx[0])
                        res, logs = engine.process_planning(mode_num, user_input, feedback_history=feedback)
                        st.session_state.current_plan = res
                        st.rerun()

            if col_trash.button("🗑️ 폐기"):
                st.session_state.current_plan = None
                st.rerun()
        else:
            st.info("👈 왼쪽 패널에서 엔진을 가동해주세요.")

# (탭 2, 3 유지)
with tab_write: st.info("제작소 대기 중")
with tab_qc: st.info("QC 대기 중")