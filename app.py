import streamlit as st
import time
import datetime

# =========================================================
# 🏭 AI Novel Factory V3 (Google Docs Collaboration Mode)
# 사장님 지시: 3개 부서 분리 + 구글 닥스 연동 시뮬레이션
# =========================================================

st.set_page_config(page_title="AI 소설 공장 (Pro)", layout="wide", page_icon="🏭")

# --- [1. 메모리 초기화] ---
# 각 방(Tab)마다 별도의 채팅 기록을 가집니다. (섞이면 안 되니까요!)

if "chat_planning" not in st.session_state:
    st.session_state.chat_planning = [{"role": "assistant", "content": "반갑습니다. 기획 실장입니다. 이번 신작의 장르나 소재는 무엇입니까?"}]

if "chat_writer" not in st.session_state:
    st.session_state.chat_writer = [{"role": "assistant", "content": "제작 1팀장입니다. 기획실에서 넘어온 설정대로 집필을 시작할까요?"}]

if "chat_qc" not in st.session_state:
    st.session_state.chat_qc = [{"role": "assistant", "content": "품질관리(QC) 팀입니다. 구글 닥스에서 수정하신 원고를 검토해 드릴까요?"}]

# 작업물 상태 관리
if "current_doc_link" not in st.session_state:
    st.session_state.current_doc_link = None # 아직 생성된 문서 없음

st.title("🏭 AI 소설 공장 통합 관제탑 (CEO Mode)")
st.caption("🚀 System Status: Online | 🔗 Google Workspace: Connected (Simulation)")

# 탭 구성 (사장님 지시대로 완벽 분리)
tab_plan, tab_write, tab_qc = st.tabs(["💡 1. 기획실 (Planning)", "✍️ 2. 제작소 (Production)", "⚖️ 3. 품질관리 (QC)"])

# =========================================================
# 💡 1. 기획실 (세계관, 시놉시스, 캐릭터 설정)
# =========================================================
with tab_plan:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("💬 기획 회의 (Brainstorming)")
        # 기획 전용 채팅창
        for msg in st.session_state.chat_planning:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if prompt := st.chat_input("기획 지시 사항 입력...", key="input_plan"):
            st.session_state.chat_planning.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            # AI 응답 시뮬레이션
            time.sleep(1)
            response = f"네, '{prompt}'에 대한 설정을 구체화하여 '설정 자료집'에 업데이트하겠습니다."
            st.session_state.chat_planning.append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)
            st.rerun()

    with c2:
        st.info("📚 **현재 확정된 설정**")
        st.text_area("세계관 요약", "2050년, AI가 지배하는 디스토피아 서울...", height=150)
        st.text_area("주인공 설정", "김철수 (29세): 전직 해커, 현재는 AI 징수관", height=150)
        st.button("💾 설정 저장 후 제작소로 전달")


# =========================================================
# ✍️ 2. 제작소 (본문 집필 -> 구글 닥스 생성)
# =========================================================
with tab_write:
    st.subheader("✍️ 메인 집필실 (Writer's Room)")
    
    col_chat, col_monitor = st.columns([1, 1])
    
    with col_chat:
        st.markdown("##### 💬 집필 지시")
        # 작가 전용 채팅창
        for msg in st.session_state.chat_writer:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if prompt := st.chat_input("집필 지시 (예: 1화 써줘)", key="input_write"):
            st.session_state.chat_writer.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            # AI 집필 시뮬레이션
            with st.spinner("AI 작가들이 타자기를 두드리는 중입니다... ⌨️"):
                time.sleep(2)
                response = f"사장님, 지시하신 내용으로 초고 작성을 완료했습니다. 구글 닥스에 업로드했습니다."
                # 가짜 문서 링크 생성
                st.session_state.current_doc_link = "https://docs.google.com/document/d/1xXxXx_Fake_Link_For_Demo"
            
            st.session_state.chat_writer.append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)
            st.rerun()

    with col_monitor:
        st.markdown("##### 📄 원고 모니터링")
        if st.session_state.current_doc_link:
            st.success("✅ 초고 생성이 완료되었습니다!")
            st.markdown(f"""
            <div style="background-color:#e8f0fe; padding:20px; border-radius:10px; border:1px solid #4285f4;">
                <h4>📄 [제1화] 생성된 원고</h4>
                <p>구글 닥스에서 직접 수정, 코멘트, 협업이 가능합니다.</p>
                <a href="{st.session_state.current_doc_link}" target="_blank" style="text-decoration:none;">
                    <button style="background-color:#4285f4; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer;">
                        🚀 <b>Google Docs 열기 (수정/검토)</b>
                    </button>
                </a>
            </div>
            """, unsafe_allow_html=True)
            st.info("💡 Tip: 구글 닥스에서 맘껏 수정하십시오. QC팀은 수정된 버전을 읽어옵니다.")
        else:
            st.warning("아직 생성된 원고가 없습니다. 왼쪽 채팅창에서 집필을 지시하세요.")


# =========================================================
# ⚖️ 3. 품질관리 (QC) (수정된 닥스 읽기 -> 검수)
# =========================================================
with tab_qc:
    st.subheader("⚖️ 최종 검수 (Quality Control)")
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("##### 💬 QC팀 피드백")
        # QC 전용 채팅창
        for msg in st.session_state.chat_qc:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if prompt := st.chat_input("검수 요청 (예: 오타 확인해줘)", key="input_qc"):
            st.session_state.chat_qc.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            # AI 검수 시뮬레이션
            with st.spinner("구글 닥스의 최신 수정본을 읽어오는 중... 🧐"):
                time.sleep(2)
                response = "구글 닥스 내용을 확인했습니다. 사장님이 수정하신 부분은 문맥이 아주 자연스럽습니다. 다만, 3번째 문단에 맞춤법 오류가 있어 수정 제안을 문서에 코멘트로 남겼습니다."
            
            st.session_state.chat_qc.append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)
            st.rerun()
            
    with c2:
        st.markdown("##### 📊 품질 리포트")
        if st.session_state.current_doc_link:
            st.metric(label="표절률 (Plagiarism)", value="0.0%", delta="Safe")
            st.metric(label="문맥 일관성", value="98/100", delta="+2 (수정 후 상승)")
            st.error("🚨 발견된 이슈: 없음 (출고 가능)")
            st.button("✅ 최종 승인 및 파일 다운로드 (.txt)")
        else:
            st.caption("원고가 있어야 검수를 진행할 수 있습니다.")