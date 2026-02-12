import streamlit as st
import sys
import pandas as pd
from pathlib import Path

# 경로 설정
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(root_dir) not in sys.path: sys.path.append(str(root_dir))

import system_utils as utils
import strategy_judge as engine

# 🔥 [핵심] Plotly 없어도 앱이 죽지 않게 방어
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

def draw_radar_chart(plan_data):
    if not HAS_PLOTLY: return None
    stats = plan_data.get('stats', {"A":1, "B":1, "C":1, "D":1, "E":1})
    df = pd.DataFrame(dict(r=list(stats.values()), theta=list(stats.keys())))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself', line_color='#FF4B4B')
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    return fig

def render(planning_dir):
    st.subheader("📊 기획안 데이터 상황실")
    
    if not HAS_PLOTLY:
        st.warning("⚠️ `pip install plotly`를 하시면 육각형 그래프를 볼 수 있습니다.")

    try:
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: projs = []

    if not projs:
        st.info("데이터 없음")
        return

    for folder in projs:
        data = utils.load_project_data(folder)
        with st.expander(f"📁 {data.get('title')}"):
            if HAS_PLOTLY:
                try:
                    fig = draw_radar_chart(data)
                    st.plotly_chart(fig, use_container_width=True)
                except: pass
            
            st.write(data.get('synopsis', '내용 없음'))
            
            # 버튼들
            c1, c2 = st.columns(2)
            if c1.button("폐기", key=f"del_{folder.name}"):
                utils.delete_project(folder)
                st.rerun()