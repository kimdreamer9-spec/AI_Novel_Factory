import streamlit as st
import strategy_judge as engine

# 함수 이름을 'render'로 통일
def render():
    st.subheader("🧠 신규 기획 생성")
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.info("🛠️ 작전 지시")
        mode = st.radio("모드", ["1. 오리지널", "2. 유저 기획", "3. 심폐소생"], index=0)
        u_input = st.text_area("키워드 / 아이디어", height=150)
        
        if st.button("🔥 기획 엔진 가동", type="primary"):
            with st.spinner("PD가 분석 중..."): 
                m_num = int(mode[0])
                res, logs = engine.process_planning(m_num, u_input)
                st.session_state.current_plan = res
                st.rerun()

    with c2:
        if st.session_state.get('current_plan'):
            plan = st.session_state.current_plan
            st.markdown(f"## 📑 {plan.get('title')}")
            st.info(f"{plan.get('logline')}")
            with st.expander("상세 내용"):
                st.write(plan.get('synopsis'))
            
            if st.button("💾 승인 및 입고"):
                engine.save_and_deploy(plan)
                st.toast("저장 완료!", icon="📦")
                st.session_state.current_plan = None
                st.rerun()