import streamlit as st
import sys
import time
from pathlib import Path

# =========================================================
# 🏗️ [Setup] 환경 및 경로 설정
# =========================================================
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

if str(PLANNING_DIR) not in sys.path: sys.path.append(str(PLANNING_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# 🔥 [Core Engine] 신규 기획 담당 매니저 연결
try: import manager_creation as engine
except: engine = None

# =========================================================
# 🎨 [UI Components] 스타일링 및 헬퍼 함수
# =========================================================
def style_metric_card(label, value, delta=None, help_text=None):
    """2026 스타일 메트릭 카드"""
    st.metric(label=label, value=value, delta=delta, help=help_text)

def render_swot_matrix(swot):
    """SWOT 분석을 2x2 매트릭스로 시각화"""
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
# 🚀 [Main Page] 렌더링 로직
# =========================================================
def render():
    # [Header]
    st.markdown("## 🧠 전략 기획실 (Strategic Planning)")
    st.caption("🚀 **2026 AI Novel Factory** : 아이디어만 던지면, 3단계 검증을 거친 **[완결형 기획서]**가 출력됩니다.")

    if not engine:
        st.error("❌ **엔진 로드 실패**: `manager_creation.py` 파일이 없습니다.")
        return

    # -----------------------------------------------------
    # 1. [Input Zone] 아이디어 투입구 (접이식)
    # -----------------------------------------------------
    is_expanded = not st.session_state.get('current_plan') # 기획서가 없으면 열려있음
    
    with st.expander("💡 **신규 기획 아이디어 입력 (Creative Input)**", expanded=is_expanded):
        c_mode, c_input = st.columns([1, 4])
        
        with c_mode:
            st.markdown("##### ⚙️ 모드 설정")
            mode = st.radio("작업 모드", ["신규 기획", "소재 개발", "심폐소생"], index=0, label_visibility="collapsed")
            mode_map = {"신규 기획": 1, "소재 개발": 2, "심폐소생": 3}
        
        with c_input:
            user_input = st.text_area(
                "💡 아이디어 / 로그라인 / 키워드", 
                height=100, 
                placeholder="예: 재벌가 망나니로 회귀했는데 알고보니 시한부 천재 해커였다. (최소 20자 이상 입력 권장)"
            )
            
            if st.button("🔥 **기획 엔진 가동 (Start Engine)**", type="primary", use_container_width=True):
                if not user_input:
                    st.warning("⚠️ 아이디어를 입력해야 공장이 돌아갑니다.")
                else:
                    # [Processing UI]
                    with st.status("🤖 **전략기획팀이 회의를 시작합니다...**", expanded=True) as status:
                        st.write("🔍 **Phase 1:** 시장 트렌드 분석 & 레퍼런스(RAG) 탐색...")
                        time.sleep(1)
                        st.write("📝 **Phase 2:** 시놉시스 초안 작성 & 캐릭터 구축...")
                        time.sleep(1)
                        st.write("👹 **Phase 3:** 레드팀(Red Team) 비평 및 3라운드 검증...")
                        
                        # 🔥 엔진 호출 (시간이 좀 걸림)
                        final_plan, logs = engine.process_planning(mode_map[mode], user_input)
                        
                        # 회의록 저장 및 표시
                        st.divider()
                        st.text_area("📋 **상세 회의록 (Debug Log)**", logs, height=150)
                        
                        status.update(label="✅ **기획서 출력 완료!**", state="complete", expanded=False)
                        st.session_state.current_plan = final_plan
                        st.rerun()

    # -----------------------------------------------------
    # 2. [Report Zone] 원페이지 기획서 (One-Page Report)
    # -----------------------------------------------------
    if st.session_state.get('current_plan'):
        plan = st.session_state.current_plan
        
        if plan.get('is_corrupted'):
            st.error("🚨 **데이터 손상**: 기획 생성 중 오류가 발생했습니다. 다시 시도해주세요.")
            return

        st.markdown("---")

        # [A] Executive Summary (헤더 & 스코어보드)
        with st.container(border=True):
            col_info, col_score = st.columns([3, 1])
            
            # 레드팀 점수 파싱
            critique = plan.get('red_team_critique', {})
            score = critique.get('score', 0)
            score_delta = "통과 (Pass)" if score >= 85 else "보완 필요 (Weak)"
            score_color = "normal" if score >= 85 else "inverse"

            with col_info:
                st.subheader(f"📑 {plan.get('title', '제목 미정')}")
                st.caption(f"**장르:** {plan.get('genre')} | **타겟:** {plan.get('target_audience', '전체')} | **키워드:** {', '.join(plan.get('keywords', []))}")
                st.info(f"**Logline:** {plan.get('logline')}")

            with col_score:
                st.metric(label="👹 레드팀 종합 점수", value=f"{score}점", delta=score_delta)
                with st.popover("📢 비평 요약 보기"):
                    st.markdown(f"**총평:** {critique.get('critique_summary', '평가 대기 중')}")
                    st.markdown("**❌ 치명적 단점:**")
                    for flaw in critique.get('fatal_flaws', []):
                        st.text(f"- {flaw}")

        # [B] Detailed Report (본문)
        
        # 1. SWOT 분석 (상단 배치)
        render_swot_matrix(plan.get('swot_analysis', {}))

        # 2. 캐릭터 & 세계관 (병렬 배치)
        c_char, c_world = st.columns([1.3, 1])
        
        with c_char:
            st.markdown("### 2. 👥 핵심 등장인물 (Characters)")
            with st.container(border=True):
                for c in plan.get('characters', []):
                    role_badge = "👑" if "Main" in c.get('role', '') else "👤"
                    st.markdown(f"**{role_badge} {c.get('name')}** _({c.get('role')})_")
                    st.caption(c.get('desc'))
                    st.divider()
        
        with c_world:
            st.markdown("### 3. 🌍 세계관 & 세일즈 포인트")
            with st.container(border=True):
                st.markdown("**[세계관 설정]**")
                st.write(plan.get('world_view', '설정 데이터 없음'))
                st.divider()
                st.markdown("**[💰 세일즈 포인트]**")
                for sp in plan.get('sales_points', []):
                    st.markdown(f"✅ {sp}")

        # 3. 시놉시스 & 에피소드 (전체 폭 사용)
        st.markdown("### 4. 🎬 시놉시스 & 에피소드 플롯")
        with st.container(border=True):
            st.markdown("**[전체 줄거리]**")
            st.write(plan.get('synopsis'))
            st.markdown("---")
            
            # 에피소드별 카드뷰 (컬럼 활용)
            plots = plan.get('episode_plots', [])
            if plots:
                st.markdown("**[초반 5화 전개]**")
                # 5화니까 5개 컬럼으로 나누거나, 3개/2개로 나눔
                cols = st.columns(len(plots))
                for i, p in enumerate(plots):
                    with cols[i]:
                        with st.container(border=True):
                            st.markdown(f"**Ep {p.get('ep')}.**")
                            st.caption(f"**{p.get('title')}**")
                            st.write(p.get('summary'))

        # [C] Action Center (하단 버튼)
        st.markdown("---")
        col_save, col_discard = st.columns([1, 1])
        
        with col_save:
            btn_save = st.button("💾 **승인 및 창고 입고 (Save Project)**", type="primary", use_container_width=True)
            if btn_save:
                ok, msg = engine.save_and_deploy(plan)
                if ok:
                    st.toast("✅ 기획안이 창고(`03_전략기획실_Planning`)에 저장되었습니다!", icon="📦")
                    time.sleep(1.5)
                    st.session_state.current_plan = None
                    st.rerun()
                else:
                    st.error(f"저장 실패: {msg}")
        
        with col_discard:
            if st.button("🗑️ **폐기 및 재시작 (Discard)**", use_container_width=True):
                st.session_state.current_plan = None
                st.rerun()