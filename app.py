import streamlit as st
import sys
import time
from pathlib import Path

# 경로 설정
current_dir = Path(__file__).parent
planning_dir = current_dir / "03_전략기획실_Planning"
sys.path.append(str(planning_dir))

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 엔진 로드
try:
    import strategy_judge as engine
    engine.init_engine()
    ENGINE_STATUS = "🟢 엔진 정상"
except ImportError:
    ENGINE_STATUS = "🔴 엔진 연결 실패"

st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"시스템 상태: {ENGINE_STATUS} | Model: {getattr(engine, 'MODEL_NAME', 'Unknown')}")

if "plan_history" not in st.session_state:
    st.session_state.plan_history = [] # 기획 이력
if "current_plan" not in st.session_state:
    st.session_state.current_plan = None # 현재 보고 있는 기획안

tab_plan, tab_write, tab_qc = st.tabs(["💡 1. 기획실", "✍️ 2. 제작소", "⚖️ 3. 품질관리"])

with tab_plan:
    st.subheader("🧠 전략 기획실 (Strategy Room)")
    
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.info("🛠️ 작전 지시")
        mode_idx = st.radio("모드", ["1. 오리지널", "2. 유저 기획", "3. 심폐소생"], index=0)
        user_input = st.text_area("키워드 / 아이디어", height=100)
        
        if st.button("🔥 기획 엔진 가동", type="primary"):
            with st.spinner("PD가 머리를 굴리고 있습니다..."):
                mode_num = int(mode_idx[0])
                res, logs = engine.process_planning(mode_num, user_input)
                st.session_state.current_plan = res
                st.session_state.logs = logs
                st.rerun()

    with c2:
        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            
            st.markdown(f"## 📑 {plan.get('title', '제목 미정')}")
            st.caption(f"장르: {plan.get('genre')} | PD 점수: {plan.get('pd_score')}점")
            
            st.success(f"**로그라인:** {plan.get('logline')}")
            st.text_area("시놉시스", plan.get('synopsis'), height=150)
            
            st.write("**🔥 셀링 포인트:**")
            for p in plan.get('selling_points', []):
                st.write(f"- {p}")
            
            st.markdown("---")
            st.write("### 👑 사장님 결재")
            
            col_approve, col_reject, col_trash = st.columns(3)
            
            # 🟢 승인 버튼
            if col_approve.button("✅ 승인 (제작 착수)"):
                success, msg = engine.save_and_deploy(plan)
                if success:
                    st.toast("🎉 제작소로 이관되었습니다!", icon="🚀")
                    st.success(msg)
                    # (여기서 탭 이동 등 추가 액션 가능)
                else:
                    st.error(msg)
            
            # 🟡 반려 버튼 (피드백 입력창 열기)
            with col_reject.popover("⚠️ 반려 (수정 지시)"):
                feedback = st.text_area("수정 지시사항 (구체적으로)")
                if st.button("수정 요청 전송"):
                    with st.spinner("지시사항 반영하여 재기획 중..."):
                        mode_num = int(mode_idx[0])
                        # 기존 입력 + 피드백을 합쳐서 보냄
                        res, logs = engine.process_planning(mode_num, user_input, feedback_history=feedback)
                        st.session_state.current_plan = res
                        st.rerun()

            # 🔴 폐기 버튼
            if col_trash.button("🗑️ 폐기"):
                st.session_state.current_plan = None
                st.rerun()

        else:
            st.info("👈 왼쪽에서 엔진을 가동하면 기획안이 여기에 표시됩니다.")

# (탭 2, 3은 기존 유지)
with tab_write:
    st.info("기획실에서 [승인]된 작품이 이곳 큐(Queue)에 쌓입니다.")
with tab_qc:
    st.info("QC 대기 중")