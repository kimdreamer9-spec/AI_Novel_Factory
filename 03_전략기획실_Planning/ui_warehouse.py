import streamlit as st
import strategy_judge as engine
import sys
from pathlib import Path

# 루트 경로 설정
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

import system_utils as utils

# 함수 이름을 'render'로 통일
def render(planning_dir):
    st.subheader("📦 기획안 보관소")
    try:
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: projs = []

    if not projs:
        st.warning("보관된 기획안이 없습니다.")
    else:
        for folder in projs:
            data = utils.load_project_data(folder)
            label = f"📁 {data.get('title')} ({folder.name})"
            if data.get('is_corrupted'): label = f"❌ [손상] {folder.name}"
            
            with st.expander(label):
                if not data.get('is_corrupted'):
                    st.info(data.get('logline'))
                    with st.popover("내용 보기"):
                        st.write(data.get('synopsis'))
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    if not data.get('is_corrupted'):
                        if st.button("🚀 제작 투입", key=f"go_{folder.name}"):
                            if 'active_projects' not in st.session_state: st.session_state.active_projects = []
                            st.session_state.active_projects.append(folder.name)
                            st.toast("투입 완료!")
                            st.rerun()
                
                with st.popover("🛠️ 리메이크 / 복구"):
                    req = st.text_area("지시사항", key=f"req_{folder.name}")
                    if st.button("실행", key=f"do_{folder.name}"):
                        with st.spinner("수정 중..."):
                            ctx = f"제목: {data.get('title')}"
                            new_p, _ = engine.process_planning(2, ctx, feedback_history=req)
                            utils.create_new_version(folder, new_p)
                            st.success("완료")
                            st.rerun()
                
                if st.button("🗑️ 삭제", key=f"del_{folder.name}"):
                    utils.delete_project(folder)
                    st.rerun()