import streamlit as st
import strategy_judge as engine
import sys
from pathlib import Path

# 상위 폴더의 system_utils를 불러오기 위한 경로 설정
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))
import system_utils as utils

def render_warehouse_tab(planning_dir):
    st.subheader("📦 기획안 보관소")
    try:
        projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        projs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: projs = []

    if not projs: st.warning("보관된 기획안이 없습니다.")
    else:
        for folder in projs:
            data = utils.load_project_data(folder)
            
            label = f"📁 {data.get('title')} ({folder.name})"
            if data.get('is_corrupted'): label = f"❌ [손상됨] {folder.name}"
            
            with st.expander(label):
                if data.get('is_corrupted'):
                    st.error(f"데이터 손상: {data.get('logline')}")
                else:
                    st.markdown(f"**장르:** {data.get('genre')} | **Ver:** `{data.get('version')}`")
                    st.info(f"**로그라인:** {data.get('logline')}")
                    with st.popover("상세 내용 보기"):
                        st.write(data.get('synopsis'))

                st.markdown("---")
                c_act, _ = st.columns([1, 1])
                with c_act:
                    # 제작 투입
                    if not data.get('is_corrupted'):
                        if folder.name in st.session_state.active_projects:
                            st.success("✅ 제작 중")
                        else:
                            if st.button("🚀 제작 투입", key=f"go_{folder.name}"):
                                if 'active_projects' not in st.session_state: st.session_state.active_projects = []
                                st.session_state.active_projects.append(folder.name)
                                st.toast("투입 완료!", icon="🔥")
                                st.rerun()
                    
                    # 리메이크
                    with st.popover("🛠️ 리메이크 / 복구"):
                        st.write("내용 수정 또는 복구를 수행합니다.")
                        req = st.text_area("지시사항", key=f"req_{folder.name}")
                        if st.button("수정 실행", key=f"do_{folder.name}", type="primary"):
                            with st.spinner("AI 작업 중..."):
                                ctx = f"제목: {data.get('title')}"
                                new_p, _ = engine.process_planning(2, ctx, feedback_history=req)
                                succ, msg = utils.create_new_version(folder, new_p)
                                if succ:
                                    st.success("완료! 새로고침합니다.")
                                    st.rerun()
                                else: st.error(msg)
                    
                    if st.button("🗑️ 삭제", key=f"del_{folder.name}"):
                        utils.delete_project(folder)
                        st.rerun()