import streamlit as st
import sys
import time
from pathlib import Path

# =========================================================
# 🏗️ [Setup] 환경 및 경로 설정 (첨부된 디렉토리 구조 기준)
# =========================================================
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

# 디렉토리 연결 보장 (절대 경로)
if str(PLANNING_DIR) not in sys.path: sys.path.append(str(PLANNING_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# 🔥 [Core Engine] 사장님 말씀대로 strategy_judge로 연결!
try: 
    import strategy_judge as engine
except ImportError:
    engine = None

# =========================================================
# 📊 [UI Logic] 5대 사고 기법을 녹여낸 프론트엔드 컴포넌트
# =========================================================
def render_swot_matrix(swot):
    """전략 분석 매트릭스 (시인성 극대화)"""
    st.markdown("### 1. ⚔️ 전략 분석 (SWOT Matrix)")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.success(f"**💪 강점 (Strength)**\n\n{swot.get('strength', '-')}")
            st.info(f"**🚀 기회 (Opportunity)**\n\n{swot.get('opportunity', '-')}")
        with c2:
            st.error(f"**⚠️ 약점 (Weakness)**\n\n{swot.get('weakness', '-')}")
            st.warning(f"**🛡️ 위협 (Threat)**\n\n{swot.get('threat', '-')}")

# =========================================================
# 🚀 [Main UI] 원페이지 보고서 렌더링
# =========================================================
def render():
    st.markdown("## 🧠 전략 기획실 (Strategic Planning)")
    st.caption("🚀 **2026 AI Novel Factory** : 세계 최고 수준의 기획 프로세스가 가동됩니다.")

    if not engine:
        st.error("❌ **엔진 연결 실패**: `strategy_judge.py` 파일을 찾을 수 없습니다.")
        return

    # -----------------------------------------------------
    # 1. [Input Zone] 아이디어 투입
    # -----------------------------------------------------
    is_expanded = not st.session_state.get('current_plan')
    
    with st.expander("💡 **신규 기획 아이디어 입력**", expanded=is_expanded):
        c_mode, c_input = st.columns([1, 4])
        with c_mode:
            st.markdown("##### ⚙️ 모드")
            mode = st.radio("모드", ["신규 기획", "소재 개발", "심폐소생"], index=0, label_visibility="collapsed")
            mode_map = {"신규 기획": 1, "소재 개발": 2, "심폐소생": 3}
        
        with c_input:
            user_input = st.text_area("로그라인 / 키워드", height=100, placeholder="아이디어를 입력하세요.")
            
            if st.button("🔥 **기획 엔진 가동 (Start Engine)**", type="primary", use_container_width=True):
                if not user_input:
                    st.warning("⚠️ 아이디어를 입력해주세요.")
                else:
                    with st.status("🤖 **전략기획팀 협업 중 (ToT + RAG)...**", expanded=True) as status:
                        st.write("🔍 **Phase 1:** 성공작 DB 분석 및 트렌드 매칭...")
                        # 엔진 호출 (strategy_judge.process_planning)
                        final_plan, logs = engine.process_planning(mode_map[mode], user_input)
                        
                        st.divider()
                        st.text_area("📋 **내부 토론 회의록 (CoT Log)**", logs, height=150)
                        status.update(label="✅ **기획 완료!**", state="complete", expanded=False)
                        
                        st.session_state.current_plan = final_plan
                        st.rerun()

    # -----------------------------------------------------
    # 2. [Report Zone] 2026 최신형 원페이지 리포트
    # -----------------------------------------------------
    if st.session_state.get('current_plan'):
        plan = st.session_state.current_plan
        st.markdown("---")

        # [A] Dashboard Header
        with st.container(border=True):
            col_info, col_score = st.columns([3, 1])
            critique = plan.get('red_team_critique', {})
            score = critique.get('score', 0)

            with col_info:
                st.subheader(f"📑 {plan.get('title', '제목 미정')}")
                st.caption(f"**장르:** {plan.get('genre')} | **키워드:** {', '.join(plan.get('keywords', []))}")
                st.info(f"**Logline:** {plan.get('logline')}")

            with col_score:
                st.metric(label="👹 레드팀 점수", value=f"{score}점", delta="PASS" if score >= 85 else "NEED FIX")
                with st.popover("📢 비평 상세"):
                    st.write(critique.get('critique_summary', '데이터 없음'))

        # [B] Report Body
        render_swot_matrix(plan.get('swot_analysis', {}))

        c_char, c_world = st.columns([1.3, 1])
        with c_char:
            st.markdown("### 2. 👥 핵심 등장인물")
            with st.container(border=True):
                for c in plan.get('characters', []):
                    st.markdown(f"**{c.get('name')}** _({c.get('role')})_")
                    st.caption(c.get('desc'))
                    st.divider()
        
        with c_world:
            st.markdown("### 3. 🌍 세계관 & 포인트")
            with st.container(border=True):
                st.markdown("**[설정]**")
                st.write(plan.get('world_view', '-'))
                st.divider()
                st.markdown("**[💰 포인트]**")
                for sp in plan.get('sales_points', []):
                    st.markdown(f"✅ {sp}")

        st.markdown("### 4. 🎬 시놉시스 & 에피소드")
        with st.container(border=True):
            st.write(plan.get('synopsis'))
            st.markdown("---")
            plots = plan.get('episode_plots', [])
            if plots:
                cols = st.columns(len(plots))
                for i, p in enumerate(plots):
                    with cols[i]:
                        with st.container(border=True):
                            st.markdown(f"**Ep {p.get('ep')}.**")
                            st.caption(p.get('title'))
                            st.write(p.get('summary'))

        # [C] Action Center
        st.markdown("---")
        col_save, col_discard = st.columns(2)
        with col_save:
            if st.button("💾 **승인 및 창고 저장**", type="primary", use_container_width=True):
                ok, msg = engine.save_and_deploy(plan)
                if ok:
                    st.toast("✅ 저장 성공!", icon="📦")
                    time.sleep(1)
                    st.session_state.current_plan = None
                    st.rerun()
                else:
                    st.error(f"실패: {msg}")
        with col_discard:
            if st.button("🗑️ **기획 폐기**", use_container_width=True):
                st.session_state.current_plan = None
                st.rerun()