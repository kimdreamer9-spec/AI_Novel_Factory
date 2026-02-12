import streamlit as st
import sys
import time
from pathlib import Path

# =========================================================
# 🏗️ [Path Safety] 경로 자동 보정 (어디서 실행하든 작동)
# =========================================================
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(current_dir) not in sys.path: sys.path.append(str(current_dir))
if str(root_dir) not in sys.path: sys.path.append(str(root_dir))

try:
    import strategy_judge as engine
except ImportError:
    engine = None

def render():
    # --- [Header] 타이틀 섹션 ---
    st.markdown("## 🧠 전략 기획실 (Strategic Planning)")
    st.caption("🚀 Trend Analysis • Logic Verification • Commercial Strategy")

    # 엔진 로드 실패 시 경고
    if not engine:
        st.error("❌ `strategy_judge.py` 모듈을 찾을 수 없습니다.")
        return

    # --- [Input] 기획 지시 섹션 ---
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])
        with c1:
            st.info("🛠️ **Mode Selection**")
            mode = st.radio("작업 모드", ["1. 신규 기획", "2. 소재 개발", "3. 심폐소생"], label_visibility="collapsed")
        
        with c2:
            st.info("📝 **Ideation Input**")
            u_input = st.text_area(
                "아이디어, 키워드, 혹은 로그라인을 입력하세요.", 
                height=100, 
                placeholder="예: 재벌가 망나니로 회귀했는데 알고보니 시한부였다. 1년 안에 그룹을 장악해야 산다."
            )
            
            # 실행 버튼 (Full Width)
            if st.button("🔥 **기획 엔진 가동 (3-Round Debate)**", type="primary", use_container_width=True):
                if not u_input.strip():
                    st.warning("⚠️ 아이디어를 입력해주세요.")
                else:
                    with st.status("🤖 **AI 기획팀이 회의를 시작했습니다...**", expanded=True) as status:
                        st.write("🔍 트렌드 데이터 분석 중...")
                        time.sleep(1)
                        st.write("🥊 레드팀(Red Team) 비평 및 검증 중...")
                        
                        m_num = int(mode[0])
                        res, logs = engine.process_planning(m_num, u_input)
                        
                        st.write("✨ 최종 리포트 작성 완료!")
                        status.update(label="✅ **기획 완료!**", state="complete", expanded=False)
                        
                        st.session_state.current_plan = res
                        st.rerun()

    # --- [Output] 결과 리포트 섹션 ---
    if st.session_state.get('current_plan') and not st.session_state.current_plan.get('is_corrupted'):
        plan = st.session_state.current_plan
        
        st.markdown("---")
        
        # 🚨 [Red Team Report] 최상단 중요 표시
        rt = plan.get('red_team_critique', {})
        if rt:
            score = rt.get('score', 0)
            score_color = "green" if score >= 85 else "orange" if score >= 70 else "red"
            
            with st.container(border=True):
                st.markdown(f"### 🚨 **Red Team Audit Report** (Score: :{score_color}[{score}점])")
                rc1, rc2 = st.columns([1, 3])
                with rc1:
                    st.metric("논리 완성도", f"{score}/100")
                with rc2:
                    st.error(f"**⚠️ 지적사항:** {rt.get('warning', '-')}")
                    st.success(f"**💡 해결방안:** {rt.get('solution', '-')}")

        # 📑 [Main Report] 기획안 본문
        st.markdown(f"# 📑 {plan.get('title', '무제')}")
        st.caption(f"**장르:** {plan.get('genre')} | **키워드:** {', '.join(plan.get('keywords', []))}")

        # 1. 핵심 요약 (Logline & Intent)
        with st.container(border=True):
            st.markdown("#### 1️⃣ 기획 의도 및 로그라인")
            st.info(f"**🎯 로그라인:** {plan.get('logline')}")
            st.write(f"**💡 기획 의도:** {plan.get('planning_intent')}")

        # 2. 캐릭터 라인업 (Cards Layout)
        st.markdown("#### 2️⃣ 캐릭터 라인업 (Character Cast)")
        chars = plan.get('characters', [])
        
        if chars:
            # 주인공 (강조)
            main_char = chars[0]
            with st.container(border=True):
                c_img, c_info = st.columns([1, 5])
                with c_img: st.markdown("# 👑")
                with c_info:
                    st.markdown(f"**{main_char.get('name')}** (주인공)")
                    st.caption(f"MBTI: {main_char.get('mbti', 'Unknown')} | 역할: {main_char.get('role')}")
                    st.write(main_char.get('desc'))

            # 조연들 (Grid)
            sub_cols = st.columns(2)
            for i, char in enumerate(chars[1:]):
                with sub_cols[i % 2].container(border=True):
                    st.markdown(f"**{char.get('name')}**")
                    st.caption(f"{char.get('role')}")
                    st.write(char.get('desc'))

        # 3. 스토리 전개 (Tabs)
        st.markdown("#### 3️⃣ 스토리 전개 (Storyline)")
        tab_synop, tab_plot = st.tabs(["📜 전체 시놉시스", "🎬 초반 회차별 플롯"])
        
        with tab_synop:
            st.write(plan.get('synopsis'))
        
        with tab_plot:
            plots = plan.get('episode_plots', [])
            for p in plots:
                with st.expander(f"**[{p.get('ep')}화] {p.get('title')}**", expanded=True):
                    st.write(p.get('summary'))

        # 4. 세일즈 포인트 (Checklist)
        with st.container(border=True):
            st.markdown("#### 💰 세일즈 포인트 (Selling Points)")
            for sp in plan.get('sales_points', []):
                st.markdown(f"✅ {sp}")

        # --- [Action] 하단 버튼 ---
        st.divider()
        col_save, col_discard = st.columns([1, 1])
        
        with col_save:
            if st.button("💾 **승인 및 창고 저장 (Save Project)**", type="primary", use_container_width=True):
                success, msg = engine.save_and_deploy(plan)
                if success:
                    st.toast("✅ 기획안이 창고에 안전하게 저장되었습니다!", icon="📦")
                    time.sleep(1.5)
                    st.session_state.current_plan = None
                    st.rerun()
                else:
                    st.error(f"저장 실패: {msg}")
        
        with col_discard:
            if st.button("🗑️ **폐기 (Discard)**", use_container_width=True):
                st.session_state.current_plan = None
                st.rerun()