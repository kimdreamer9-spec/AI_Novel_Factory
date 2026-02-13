import streamlit as st
import sys
import time
from pathlib import Path

# [Setup]
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

if str(PLANNING_DIR) not in sys.path: sys.path.append(str(PLANNING_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# 엔진 로드
try: import strategy_judge as engine
except: engine = None

def render():
    st.markdown("## 🧠 전략 기획실 (Strategic Planning)")
    st.caption("🚀 아이디어 투입 ➔ AI 기획/비평 ➔ **[전략 기획서]** 출력")

    if not engine:
        st.error("❌ 엔진 로드 실패")
        return

    # 1. [Input] 아이디어 입력 (상단 고정)
    with st.expander("💡 **신규 기획 아이디어 입력**", expanded=not st.session_state.get('current_plan')):
        col_mode, col_input = st.columns([1, 4])
        with col_mode:
            mode = st.radio("모드", ["신규 기획", "소재 개발", "심폐소생"], index=0)
            mode_map = {"신규 기획": 1, "소재 개발": 2, "심폐소생": 3}
        
        with col_input:
            user_input = st.text_area("로그라인 / 키워드", height=70, placeholder="예: 재벌가 망나니로 회귀했는데 시한부다.")
            
            if st.button("🔥 **기획서 생성 (Start)**", type="primary", use_container_width=True):
                if not user_input:
                    st.warning("내용을 입력하세요.")
                else:
                    with st.status("🤖 **전략기획팀 가동 중...**", expanded=True) as status:
                        st.write("🔍 시장 트렌드 분석 & 레퍼런스 탐색...")
                        time.sleep(1)
                        st.write("📝 초안 작성 중...")
                        time.sleep(1)
                        st.write("👹 **레드팀(Red Team)** 비평 및 검증 수행...")
                        
                        # 엔진 호출
                        final_plan, logs = engine.process_planning(mode_map[mode], user_input)
                        
                        st.text_area("📋 **내부 회의록 (Process Log)**", logs, height=150)
                        status.update(label="✅ **기획서 출력 완료!**", state="complete", expanded=False)
                        
                        st.session_state.current_plan = final_plan
                        st.rerun()

    # 2. [Output] One-Page Report View
    if st.session_state.get('current_plan'):
        plan = st.session_state.current_plan
        
        if plan.get('is_corrupted'):
            st.error("기획 데이터 손상")
            return

        st.markdown("---")
        
        # [A] 헤더: 제목 & 레드팀 스코어
        c_title, c_score = st.columns([3, 1])
        
        critique = plan.get('red_team_critique', {})
        score = critique.get('score', 0)
        
        with c_title:
            st.subheader(f"📑 {plan.get('title', '제목 미정')}")
            st.caption(f"**장르:** {plan.get('genre')} | **키워드:** {', '.join(plan.get('keywords', []))}")
            st.info(f"**Logline:** {plan.get('logline')}")

        with c_score:
            st.metric(label="👹 레드팀 점수", value=f"{score}점", delta="합격" if score >= 85 else "보완 필요")
            with st.popover("비평 상세 보기"):
                st.write(critique.get('critique_summary', '평가 대기 중'))
                st.write(f"**치명적 단점:** {critique.get('fatal_flaws', [])}")

        # [B] 본문: 보고서 스타일 (컨테이너 활용)
        
        # 1. 전략 분석 (SWOT)
        st.markdown("#### 1. 전략 분석 (SWOT Analysis)")
        with st.container(border=True):
            swot = plan.get('swot_analysis', {})
            s = swot.get('strength') or "-"
            w = swot.get('weakness') or "-"
            o = swot.get('opportunity') or "-"
            t = swot.get('threat') or "-"
            
            r1, r2 = st.columns(2)
            with r1:
                st.success(f"**💪 강점 (Strength)**\n\n{s}")
                st.info(f"**🚀 기회 (Opportunity)**\n\n{o}")
            with r2:
                st.error(f"**⚠️ 약점 (Weakness)**\n\n{w}")
                st.warning(f"**🛡️ 위협 (Threat)**\n\n{t}")

        # 2. 캐릭터 & 세계관
        c_char, c_world = st.columns([1.5, 1])
        
        with c_char:
            st.markdown("#### 2. 핵심 등장인물 (Characters)")
            with st.container(border=True):
                for c in plan.get('characters', []):
                    role_badge = "👑" if "Main" in c.get('role', '') else "👤"
                    st.markdown(f"**{role_badge} {c.get('name')}** ({c.get('role')})")
                    st.caption(c.get('desc'))
                    st.markdown("---")
        
        with c_world:
            st.markdown("#### 3. 세계관 (World View)")
            with st.container(border=True):
                st.write(plan.get('world_view', '설정 데이터 없음'))
                st.markdown("#### 💰 세일즈 포인트")
                for sp in plan.get('sales_points', []):
                    st.markdown(f"✅ {sp}")

        # 3. 스토리 플롯
        st.markdown("#### 4. 시놉시스 & 전개 (Plot)")
        with st.container(border=True):
            st.write(plan.get('synopsis'))
            st.divider()
            
            # 회차별 요약 (가로 스크롤 느낌 대신 컬럼으로)
            plots = plan.get('episode_plots', [])
            if plots:
                cols = st.columns(len(plots))
                for i, p in enumerate(plots):
                    with cols[i]:
                        st.markdown(f"**[{p.get('ep')}화] {p.get('title')}**")
                        st.caption(p.get('summary'))

        # [Footer] 액션 버튼
        st.markdown("---")
        col_save, col_discard = st.columns([1, 1])
        
        with col_save:
            if st.button("💾 **승인 및 창고 입고 (Save Project)**", type="primary", use_container_width=True):
                ok, msg = engine.save_and_deploy(plan)
                if ok:
                    st.toast("✅ 기획안이 창고에 안전하게 입고되었습니다!", icon="📦")
                    time.sleep(1.5)
                    st.session_state.current_plan = None
                    st.rerun()
                else:
                    st.error(f"저장 실패: {msg}")
        
        with col_discard:
            if st.button("🗑️ **폐기 (Discard)**", use_container_width=True):
                st.session_state.current_plan = None
                st.rerun()