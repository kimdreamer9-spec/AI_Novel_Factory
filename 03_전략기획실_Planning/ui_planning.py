import streamlit as st
import sys
import time
import pandas as pd
from pathlib import Path

current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(current_dir) not in sys.path: sys.path.append(str(current_dir))
if str(root_dir) not in sys.path: sys.path.append(str(root_dir))

try: import system_utils as utils
except: pass

try: import strategy_judge as engine
except ImportError: engine = None

try:
    import plotly.express as px
    HAS_PLOTLY = True
except: HAS_PLOTLY = False

def draw_radar_chart(plan_data):
    if not HAS_PLOTLY: return None
    stats = plan_data.get('stats', {"대중성": 50, "독창성": 50, "캐릭터": 50, "개연성": 50, "확장성": 50})
    df = pd.DataFrame(dict(r=list(stats.values()), theta=list(stats.keys())))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself', line_color='#FF4B4B')
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    return fig

def render(planning_dir):
    st.markdown("## 🗂️ 기획 창고 (Project Warehouse)")
    
    if not HAS_PLOTLY: st.warning("⚠️ Plotly 미설치")

    try:
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: projs = []

    if not projs:
        st.info("📭 보관된 기획안이 없습니다.")
        return

    for folder in projs:
        data = utils.load_project_data(folder)
        if not data: continue
        
        label = f"📁 {data.get('title', '무제')} (v{data.get('version', '1.0')})"
        
        if data.get('is_corrupted'):
            with st.expander(f"❌ [손상됨] {folder.name}"):
                if st.button("삭제", key=f"del_{folder.name}"):
                    utils.delete_project(folder)
                    st.rerun()
            continue

        with st.expander(label, expanded=False):
            c1, c2 = st.columns([1, 1.5])
            with c1:
                if HAS_PLOTLY:
                    fig = draw_radar_chart(data)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                else:
                    st.progress(50)
            
            with c2:
                st.info(f"**로그라인:** {data.get('logline')}")
                swot = data.get('swot_analysis', {})
                if swot:
                    sc, wc = st.columns(2)
                    sc.success(f"**강점:** {swot.get('strength')}")
                    wc.error(f"**약점:** {swot.get('weakness')}")

            st.divider()
            
            t1, t2, t3 = st.tabs(["📜 시놉시스", "👥 캐릭터", "💡 포인트"])
            with t1: st.write(data.get('synopsis'))
            with t2:
                for c in data.get('characters', []):
                    st.markdown(f"**{c.get('name')}** ({c.get('role')})")
            with t3:
                for sp in data.get('sales_points', []):
                    st.markdown(f"✅ {sp}")

            st.divider()
            
            cp, cd, cdel = st.columns([2, 2, 1])
            
            with cp:
                with st.popover("🚀 제작 투입"):
                    st.write("스튜디오 선택")
                    if st.button("제작 시작", key=f"go_{folder.name}"):
                        if 'active_projects' not in st.session_state: st.session_state.active_projects = []
                        st.session_state.active_projects.append(folder.name)
                        st.toast("투입 완료!")
            
            with cd:
                with st.popover("🛠️ 디벨롭"):
                    req = st.text_area("수정 지시사항", key=f"req_{folder.name}")
                    if st.button("수정 실행", key=f"do_{folder.name}"):
                        if not engine: st.error("엔진 로드 실패")
                        else:
                            with st.status("수정 중..."):
                                new_p, logs = engine.remake_planning(data, req)
                                if new_p.get('remake_analysis'):
                                    ra = new_p['remake_analysis']
                                    st.info(f"판단: {ra.get('verdict')}")
                                utils.create_new_version(folder, new_p)
                                st.rerun()
            
            with cdel:
                if st.button("🗑️", key=f"delbtn_{folder.name}"):
                    utils.delete_project(folder)
                    st.rerun()