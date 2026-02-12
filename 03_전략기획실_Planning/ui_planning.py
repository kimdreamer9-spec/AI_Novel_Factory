import streamlit as st
import strategy_judge as engine
import time

def render():
    st.subheader("🧠 신규 기획 생성 (High-End)")
    
    # --- 입력 섹션 ---
    with st.expander("🛠️ 기획 설정 (입력)", expanded=True):
        c1, c2 = st.columns([1, 3])
        with c1:
            mode = st.radio("모드 선택", ["1. 오리지널", "2. 유저 기획 디벨롭", "3. 망한 작품 심폐소생"], index=0)
        with c2:
            u_input = st.text_area("아이디어 / 키워드 / 로그라인 입력", height=100, placeholder="예: 재벌집 막내아들이 회귀해서 반도체 제국을 건설하는 이야기.")
            if st.button("🔥 5단계 표준 기획안 생성", type="primary", use_container_width=True):
                with st.spinner("PD가 시장 분석 후 5단계 기획안을 작성 중입니다..."): 
                    m_num = int(mode[0])
                    res, logs = engine.process_planning(m_num, u_input)
                    st.session_state.current_plan = res
                    st.rerun()

    # --- 결과 출력 섹션 ---
    if st.session_state.get('current_plan') and not st.session_state.current_plan.get('is_corrupted'):
        plan = st.session_state.current_plan
        
        st.divider()
        st.markdown(f"# 📑 {plan.get('title')}")
        st.caption(f"장르: {plan.get('genre')} | 키워드: {', '.join(plan.get('keywords', []))}")

        # 1. 기획의도 & 로그라인
        with st.container(border=True):
            st.markdown("### 1️⃣ 기획 의도 및 로그라인")
            st.info(f"**로그라인:** {plan.get('logline')}")
            st.write(f"**기획 의도:** {plan.get('planning_intent')}")

        # 2. 캐릭터 설정 (5인)
        st.markdown("### 2️⃣ 핵심 캐릭터 (5인)")
        chars = plan.get('characters', [])
        if chars:
            # 주인공 강조
            main_char = chars[0]
            with st.container(border=True):
                c_img, c_txt = st.columns([1, 4])
                with c_img: st.markdown("### 👑") # 나중에 이미지 생성 연동 가능
                with c_txt:
                    st.markdown(f"**{main_char.get('name')}** ({main_char.get('role')})")
                    st.caption(f"MBTI: {main_char.get('mbti', 'Unknown')}")
                    st.write(main_char.get('desc'))
            
            # 조연들 (2열 배치)
            cols = st.columns(2)
            for i, char in enumerate(chars[1:]):
                with cols[i % 2].container(border=True):
                    st.markdown(f"**{char.get('name')}**")
                    st.caption(char.get('role'))
                    st.write(char.get('desc'))

        # 3. 시놉시스
        with st.expander("3️⃣ 전체 줄거리 (시놉시스)", expanded=False):
            st.write(plan.get('synopsis'))

        # 4. 회차별 플롯 (1~5화)
        with st.expander("4️⃣ 초반 회차별 플롯 (1~5화)", expanded=True):
            plots = plan.get('episode_plots', [])
            for p in plots:
                st.markdown(f"**[{p.get('ep')}화] {p.get('title')}**")
                st.write(f"- {p.get('summary')}")

        # 5. 세일즈 포인트
        with st.container(border=True):
            st.markdown("### 5️⃣ 세일즈 포인트 (Selling Points)")
            for sp in plan.get('sales_points', []):
                st.markdown(f"✅ {sp}")

        # 하단 액션 버튼
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("💾 이 기획으로 승인 (저장)"):
            engine.save_and_deploy(plan)
            st.toast("기획안이 창고에 저장되었습니다!", icon="📦")
            st.session_state.current_plan = None
            time.sleep(1)
            st.rerun()
        
        if c_btn2.button("🗑️ 다시 만들기"):
            st.session_state.current_plan = None
            st.rerun()