import streamlit as st
import sys
import pandas as pd
from pathlib import Path

# [Path Safety]
CURRENT_FILE_PATH = Path(__file__).resolve()
PLANNING_DIR = CURRENT_FILE_PATH.parent
PROJECT_ROOT = PLANNING_DIR.parent

if str(PLANNING_DIR) not in sys.path: sys.path.append(str(PLANNING_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.append(str(PROJECT_ROOT))

# [Module Load]
try: import system_utils as utils
except: pass
try: import strategy_judge as engine
except: engine = None

# [Plotly Check]
try:
    import plotly.express as px
    HAS_PLOTLY = True
except: HAS_PLOTLY = False

def draw_radar_chart(plan_data):
    if not HAS_PLOTLY: return None
    stats = plan_data.get('stats', {"대중성":50,"독창성":50,"캐릭터":50,"개연성":50,"확장성":50})
    df = pd.DataFrame(dict(r=list(stats.values()), theta=list(stats.keys())))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself', line_color='#FF4B4B')
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100]), bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
        height=250
    )
    return fig

def render(planning_dir):
    st.markdown("## 🗂️ 기획 창고 (Warehouse)")
    st.caption("📦 보관된 IP 관리 • 🏭 제작소 투입 • 🛠️ 기획 디벨롭")

    # 1. 파일 스캔
    try:
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: projs = []

    if not projs:
        st.info("📭 창고가 비었습니다. [전략기획실]에서 새로운 IP를 발굴하세요.")
        return

    # 2. 프로젝트 리스트 카드뷰
    for folder in projs:
        data = utils.load_project_data(folder)
        if not data: continue
        
        # 카드 헤더 (제목 + 버전)
        version = data.get('version', '1.0')
        title_label = f"📁 {data.get('title', '무제')} (v{version})"
        
        with st.expander(title_label, expanded=False):
            # --- [Upper Dashboard] ---
            c1, c2 = st.columns([1, 2])
            
            with c1: # 레이더 차트
                if HAS_PLOTLY:
                    fig = draw_radar_chart(data)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.metric("종합 점수", f"{sum(data.get('stats',{}).values())/5:.1f}점")

            with c2: # 핵심 정보
                st.info(f"**Logline:** {data.get('logline')}")
                st.caption(f"장르: {data.get('genre')} | 타겟: {data.get('target_reader', '전체')}")
                # 분석 결과 (디벨롭 코멘트 등)
                if data.get('remake_analysis'):
                    ra = data['remake_analysis']
                    st.success(f"🔔 **최근 수정 내역:** {ra.get('verdict', '수정 완료')}")

            st.divider()

            # --- [Detail Tabs] ---
            t1, t2, t3, t4 = st.tabs(["📜 시놉시스", "👥 캐릭터", "🗺️ 플롯", "💰 세일즈 포인트"])
            with t1: st.write(data.get('synopsis'))
            with t2:
                for c in data.get('characters', []):
                    st.markdown(f"**{c.get('name')}** ({c.get('role')}) - {c.get('desc')}")
            with t3:
                for p in data.get('episode_plots', []):
                    with st.expander(f"{p.get('ep')}화: {p.get('title')}"):
                        st.write(p.get('summary'))
            with t4:
                for sp in data.get('sales_points', []):
                    st.markdown(f"✅ {sp}")

            st.markdown("---")

            # --- [Control Center] ---
            col_prod, col_dev, col_del = st.columns([2, 2, 1])

            # [Action A] 제작소 투입 (슬롯 선택)
            with col_prod:
                with st.popover("🏭 제작 투입 (Send to Studio)"):
                    st.markdown("#### 스튜디오 배정")
                    
                    # 현재 활성 슬롯 확인
                    active = st.session_state.get('active_projects', [])
                    
                    # 1~10번 슬롯 UI
                    slot = st.selectbox("슬롯 선택", [f"Studio {i}" for i in range(1, 11)])
                    
                    if st.button("🚀 제작 시작", key=f"go_{folder.name}", type="primary"):
                        if folder.name not in active:
                            st.session_state.active_projects.append(folder.name)
                            st.toast(f"'{data.get('title')}' -> {slot} 배정 완료!", icon="✅")
                            time.sleep(1)
                        else:
                            st.warning("이미 제작 중인 프로젝트입니다.")

            # [Action B] 스마트 디벨롭 (수정)
            with col_dev:
                with st.popover("🛠️ 디벨롭 (Smart Remake)"):
                    st.markdown("#### 👨‍🏫 기획 수정 지시")
                    req = st.text_area("수정 사항을 입력하세요", key=f"req_{folder.name}", placeholder="예: 주인공 성격을 좀 더 냉철하게 바꿔줘.")
                    
                    if st.button("⚡ 수정 실행", key=f"do_{folder.name}"):
                        if not engine:
                            st.error("기획 엔진(Strategy Judge) 로드 실패")
                        else:
                            with st.status("🧠 기획자가 문서를 수정하고 있습니다...", expanded=True) as status:
                                st.write("분석 중...")
                                new_p, msg = engine.remake_planning(data, req)
                                if "Success" in msg:
                                    utils.create_new_version(folder, new_p)
                                    status.update(label="✅ 수정 완료! (v1.x -> v1.y)", state="complete")
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error(f"오류: {msg}")

            # [Action C] 폐기
            with col_del:
                if st.button("🗑️ 폐기", key=f"del_{folder.name}"):
                    utils.delete_project(folder)
                    st.rerun()