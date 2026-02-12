import streamlit as st
import sys
import time
import json
import os
import shutil
import re
from pathlib import Path

# =========================================================
# 🏭 AI Novel Factory V11 (The Final Architecture)
# =========================================================

# 1. 경로 설정 (나노 단위 확인)
current_dir = Path(__file__).resolve().parent
planning_dir = current_dir / "03_전략기획실_Planning"
production_dir = current_dir / "05_제작_스튜디오_Production"

# 03번 방의 모듈을 가져오기 위한 경로 추가
if str(planning_dir) not in sys.path:
    sys.path.append(str(planning_dir))

st.set_page_config(page_title="AI 소설 공장 (CEO Mode)", layout="wide", page_icon="🏭")

# 2. 엔진 로드 (안전장치)
try:
    import strategy_judge as engine
    engine.init_engine()
    ENGINE_STATUS = "🟢 엔진 정상"
    MODEL_INFO = getattr(engine, 'MODEL_NAME', 'Unknown')
except ImportError:
    ENGINE_STATUS = "🔴 엔진 연결 실패 (경로 확인 필요)"
    MODEL_INFO = "Unknown"

# 3. Helper Functions (버전 관리 & 데이터 로드)
def get_latest_plan_file(folder_path):
    """가장 최신 기획안 파일 찾기 (Versioning)"""
    # v1, v2... 파일 찾기
    versioned_files = list(folder_path.glob("Approved_Plan_v*.json"))
    if versioned_files:
        versioned_files.sort(key=lambda x: int(re.search(r'v(\d+)', x.name).group(1)), reverse=True)
        return versioned_files[0]

    # 오리지널 파일
    original = folder_path / "Approved_Plan.json"
    if original.exists(): return original

    # 구형 드래프트
    drafts = list(folder_path.glob("기획안_Draft*.json"))
    if drafts:
        drafts.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return drafts[0]
    
    return None

def load_project_data(folder_path):
    """폴더에서 기획 데이터 로드 (호환성 패치 적용)"""
    target_file = get_latest_plan_file(folder_path)
    
    if target_file:
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content: raise ValueError("Empty File") # 빈 파일 처리
                data = json.loads(content)
                
                # 구형 데이터 호환 처리
                if '1_작품_기본_정보' in data:
                    flat = {}
                    info = data.get('1_작품_기본_정보', {})
                    flat['title'] = info.get('제목', folder_path.name)
                    flat['genre'] = info.get('장르', '미상')
                    flat['logline'] = data.get('3_작품_소개_로그라인', '로그라인 없음')
                    flat['synopsis'] = "구형 데이터입니다. 리메이크를 권장합니다."
                    flat['characters'] = []
                    flat['version'] = "Old"
                    return flat
                
                data['version'] = target_file.name # 버전 정보 주입
                return data
        except Exception as e:
            return {
                "title": folder_path.name,
                "logline": f"❌ 데이터 손상: {str(e)}",
                "genre": "Error",
                "synopsis": "파일을 읽을 수 없습니다. [리메이크] 버튼을 눌러 복구하십시오.",
                "characters": []
            }
            
    return {"title": folder_path.name, "logline": "데이터 파일 없음", "genre": "Empty"}

def create_new_version(folder_path, new_plan_data):
    """새 버전(v+1)으로 저장 (데이터 보호)"""
    try:
        latest = get_latest_plan_file(folder_path)
        next_v = 1
        if latest:
            match = re.search(r'v(\d+)', latest.name)
            if match: next_v = int(match.group(1)) + 1
            elif latest.name == "Approved_Plan.json": next_v = 2
            
        new_name = f"Approved_Plan_v{next_v}.json"
        (folder_path / new_name).write_text(json.dumps(new_plan_data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True, f"v{next_v} 저장 완료"
    except Exception as e:
        return False, str(e)

def delete_project(folder_path):
    try:
        shutil.rmtree(folder_path)
        return True
    except: return False

def move_to_production(project_name):
    if 'active_projects' not in st.session_state: st.session_state.active_projects = []
    if project_name not in st.session_state.active_projects:
        st.session_state.active_projects.append(project_name)

# 4. 헤더 및 세션
st.title("🏭 AI 소설 공장 통합 관제탑")
st.caption(f"시스템 상태: {ENGINE_STATUS} | Model: {MODEL_INFO}")

if "current_plan" not in st.session_state: st.session_state.current_plan = None
if "active_projects" not in st.session_state: st.session_state.active_projects = []

# 5. 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["💡 1. 기획실", "🗂️ 2. 기획 창고", "✍️ 3. 제작소(가동중)", "⚖️ 4. 품질관리"])

# =========================================================
# 💡 1. 기획실 (Strategy Room)
# =========================================================
with tab1:
    st.subheader("🧠 신규 기획 생성")
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.info("🛠️ 작전 지시")
        mode = st.radio("모드", ["1. 오리지널", "2. 유저 기획", "3. 심폐소생"], index=0)
        u_input = st.text_area("키워드 / 아이디어", height=150)
        
        if st.button("🔥 기획 엔진 가동", type="primary"):
            if "🔴" in ENGINE_STATUS: st.error("엔진 에러")
            else:
                with st.spinner("PD가 분석 중..."):
                    m_num = int(mode[0])
                    res, logs = engine.process_planning(m_num, u_input)
                    st.session_state.current_plan = res
                    st.rerun()

    with c2:
        if st.session_state.current_plan:
            p = st.session_state.current_plan
            st.markdown(f"## 📑 {p.get('title')}")
            st.info(f"**로그라인:** {p.get('logline')}")
            
            # 리스크 리포트
            risk = p.get('risk_report', {})
            if risk.get('detected'):
                st.error(f"🚨 경고: {risk.get('red_team_warning')}")
                st.info(f"💡 대안: {risk.get('alternative_suggestion')}")

            with st.expander("상세 내용 보기", expanded=True):
                st.write(f"**기획의도:** {p.get('planning_intent')}")
                st.write(f"**시놉시스:** {p.get('synopsis')}")
            
            # 결재 버튼
            btn1, btn2 = st.columns(2)
            if btn1.button("💾 승인 (창고 입고)"):
                succ, msg = engine.save_and_deploy(p)
                if succ:
                    st.toast("저장 완료!", icon="📦")
                    st.session_state.current_plan = None
                    time.sleep(1)
                    st.rerun()
                else: st.error(msg)
            
            if btn2.button("🗑️ 폐기"):
                st.session_state.current_plan = None
                st.rerun()

# =========================================================
# 🗂️ 2. 기획 창고 (Warehouse) - [리메이크 센터]
# =========================================================
with tab2:
    st.subheader("📦 기획안 보관소")
    try:
        # 폴더만 가져오기 (파일 제외)
        all_projs = [f for f in planning_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
        all_projs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    except: all_projs = []

    if not all_projs:
        st.warning("보관된 기획안이 없습니다.")
    else:
        for folder in all_projs:
            d = load_project_data(folder)
            
            # 카드 UI
            with st.expander(f"📁 {d.get('title')} ({folder.name})"):
                c_info, c_act = st.columns([2.5, 1])
                
                with c_info:
                    st.caption(f"Ver: `{d.get('version', 'Unknown')}` | Genre: {d.get('genre')}")
                    if "❌" in d.get('logline', ''): st.error(d.get('logline'))
                    else: st.info(d.get('logline'))
                    
                    with st.popover("상세 내용"):
                        st.write(d.get('synopsis'))
                        st.json(d.get('characters'))

                with c_act:
                    # 제작 투입
                    if folder.name in st.session_state.active_projects:
                        st.success("✅ 가동 중")
                    else:
                        if st.button("🚀 제작 투입", key=f"go_{folder.name}"):
                            move_to_production(folder.name)
                            st.toast("투입 완료!", icon="🔥")
                            st.rerun()
                    
                    # 🔥 리메이크 (버전업)
                    with st.popover("🛠️ 리메이크"):
                        st.write("내용을 수정하여 새 버전(v+1)을 만듭니다.")
                        req = st.text_area("지시사항", key=f"req_{folder.name}")
                        if st.button("수정 실행", key=f"do_{folder.name}", type="primary"):
                            with st.spinner("AI 수정 중..."):
                                ctx = f"제목: {d.get('title')}\n내용: {d.get('synopsis')}"
                                new_p, _ = engine.process_planning(2, ctx, feedback_history=req)
                                
                                succ, msg = create_new_version(folder, new_p)
                                if succ:
                                    st.success(msg)
                                    time.sleep(1)
                                    st.rerun()
                                else: st.error(msg)

                    if st.button("🗑️ 삭제", key=f"del_{folder.name}"):
                        delete_project(folder)
                        st.rerun()

# =========================================================
# ✍️ 3. 제작소 (Production)
# =========================================================
with tab3:
    st.subheader("🏭 실시간 제작 현황")
    active = st.session_state.active_projects
    
    if not active:
        st.info("가동 중인 라인이 없습니다. 창고에서 투입해주세요.")
    else:
        tabs = st.tabs([n.split('_')[-1][:8]+".." for n in active])
        for i, pname in enumerate(active):
            with tabs[i]:
                path = planning_dir / pname
                d = load_project_data(path)
                
                st.markdown(f"### 🎬 {d.get('title')}")
                st.caption(f"Ver: `{d.get('version')}`")
                
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.info("📊 진행률")
                    st.progress(10)
                    st.write("현재: **시놉시스 분석**")
                    if st.button("⏹️ 중단", key=f"stop_{pname}"):
                        st.session_state.active_projects.remove(pname)
                        st.rerun()
                with c2:
                    st.chat_message("assistant").write(f"'{d.get('title')}' 집필 준비 완료.")
                    st.chat_input("지시 입력...", key=f"chat_{pname}")

# =========================================================
# ⚖️ 4. 품질관리 (QC)
# =========================================================
with tab4:
    st.info("QC팀 대기 중")