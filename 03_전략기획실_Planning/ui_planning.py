import streamlit as st
import strategy_judge as engine
import time

def render():
    st.subheader("🧠 신규 기획 생성 (High-End RAG)")
    
    # 입력창
    with st.expander("🛠️ 기획 설정", expanded=True):
        c1, c2 = st.columns([1, 3])
        with c1:
            mode = st.radio("모드", ["1. 오리지널", "2. 유저 기획", "3. 심폐소생"], index=0)
        with c2:
            u_input = st.text_area("아이디어 입력", height=100, placeholder="예: 시한부 악녀가 흑막 공작과 결혼해서 제국을 접수함.")
            if st.button("🔥 5단계 표준 기획안 생성", type="primary", use_container_width=True):
                with st.spinner("데이터 분석(RAG) 및 레드팀 검증 중..."):
                    m_num = int(mode[0])
                    res, logs = engine.process_planning(m_num, u_input)
                    st.session_state.current_plan = res
                    st.rerun()

    # 결과창
    if st.session_state.get('current_plan') and not st.session_state.current_plan.get('is_corrupted'):
        plan = st.session_state.current_plan
        
        st.divider()
        
        # 🚨 레드팀 분석 리포트 (최상단 노출)
        rt = plan.get('red_team_critique', {})
        if rt:
            with st.expander("🚨 레드팀(Red Team) 비평 리포트", expanded=True):
                col_r1, col_r2 = st.columns([1, 3])
                col_r1.metric("예상 점수", f"{rt.get('score', 0)}점")
                col_r2.error(f"**경고:** {rt.get('warning', '-')}")
                col_r2.success(f"**해결책:** {rt.get('solution', '-')}")

        st.markdown(f"# 📑 {plan.get('title')}")
        st.caption(f"장르: {plan.get('genre')} | 키워드: {plan.get('keywords')}")

        # 1. 기획의도 & 로그라인
        with st.container(border=True):
            st.markdown("### 1️⃣ 기획 의도 및 로그라인")
            st.info(f"**로그라인:** {plan.get('logline')}")
            st.write(f"**기획 의도:** {plan.get('planning_intent')}")

        # 2. 캐릭터 (5인)
        st.markdown("### 2️⃣ 핵심 캐릭터 (5인)")
        chars = plan.get('characters', [])
        if chars:
            main = chars[0]
            with st.container(border=True):
                st.markdown(f"**👑 {main.get('name')}** ({main.get('role')})")
                st.caption(f"MBTI: {main.get('mbti')}")
                st.write(main.get('desc'))
            
            # 조연 4명
            cols = st.columns(2)
            for i, c in enumerate(chars[1:]):
                with cols[i%2].container(border=True):
                    st.markdown(f"**{c.get('name')}**")
                    st.caption(c.get('role'))
                    st.write(c.get('desc'))

        # 3. 시놉시스
        with st.expander("3️⃣ 전체 줄거리", expanded=False):
            st.write(plan.get('synopsis'))

        # 4. 플롯 (1~5화)
        with st.expander("4️⃣ 초반 1~5화 플롯", expanded=True):
            for p in plan.get('episode_plots', []):
                st.markdown(f"**[{p.get('ep')}화] {p.get('title')}**")
                st.write(f"- {p.get('summary')}")

        # 5. 세일즈 포인트
        with st.container(border=True):
            st.markdown("### 5️⃣ 세일즈 포인트")
            for sp in plan.get('sales_points', []):
                st.markdown(f"✅ {sp}")

        # 버튼 (저장 / 폐기)
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("💾 기획 창고로 입고 (저장)", use_container_width=True):
            succ, msg = engine.save_and_deploy(plan)
            if succ:
                st.toast("저장 완료! 창고 탭에서 확인하세요.", icon="📦")
                st.session_state.current_plan = None
                time.sleep(1)
                st.rerun()
            else: st.error(f"저장 실패: {msg}")
        
        if c_btn2.button("🗑️ 폐기 (다시 만들기)", use_container_width=True):
            st.session_state.current_plan = None
            st.rerun()