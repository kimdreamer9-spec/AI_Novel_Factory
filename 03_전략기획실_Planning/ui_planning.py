import streamlit as st
import strategy_judge as engine

def render_planning_tab():
    st.subheader("🧠 신규 기획 생성")
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.info("🛠️ 작전 지시")
        mode = st.radio("모드 선택", ["1. 오리지널", "2. 유저 기획", "3. 심폐소생"], index=0)
        u_input = st.text_area("키워드 / 아이디어", height=150)
        
        if st.button("🔥 기획 엔진 가동", type="primary"):
            with st.spinner("PD가 7단계 표준 기획안을 작성 중..."):
                m_num = int(mode[0])
                res, logs = engine.process_planning(m_num, u_input)
                st.session_state.current_plan = res
                st.rerun()

    with c2:
        if st.session_state.get('current_plan'):
            plan = st.session_state.current_plan
            # (여기서 render_plan_report 함수를 공통으로 쓰면 좋지만, 일단 간단히 구현)
            st.markdown(f"## 📑 {plan.get('title')}")
            st.info(f"로그라인: {plan.get('logline')}")
            with st.expander("상세 내용"):
                st.write(plan.get('synopsis'))
            
            b1, b2 = st.columns(2)
            if b1.button("💾 승인 및 입고"):
                succ, msg = engine.save_and_deploy(plan)
                if succ:
                    st.toast("저장 완료!", icon="📦")
                    st.session_state.current_plan = None
                    time.sleep(1)
                    st.rerun()
                else: st.error(msg)
            
            if b2.button("🗑️ 폐기"):
                st.session_state.current_plan = None
                st.rerun()