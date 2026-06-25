import streamlit as st
import pandas as pd
import database as db
import google.generativeai as genai
import os
from datetime import datetime
import io

# 1. 페이지 레이아웃 및 테마 기본 설정
st.set_page_config(
    page_title="성원글로벌카고 AI ERP",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 데이터베이스 초기화
db.init_db()

# 3. 맞춤형 스타일링 (Shared Design Standards - Zinc & Minimal Chrome)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    .stCodeBlock, code, pre {
        font-family: 'JetBrains Mono', monospace;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 0.75rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
    }
    .badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 75%;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.25rem;
    }
    .badge-primary { background-color: #3b82f6; color: white; }
    .badge-success { background-color: #10b981; color: white; }
    .badge-warning { background-color: #f59e0b; color: white; }
    .badge-danger { background-color: #ef4444; color: white; }
</style>
""", unsafe_allow_html=True)

# 4. 세션 상태 관리 (Session States)
if "user_dept" not in st.session_state:
    st.session_state.user_dept = "영업"
if "user_rank" not in st.session_state:
    st.session_state.user_rank = "대리"
if "user_name" not in st.session_state:
    st.session_state.user_name = "sales_kim"
if "api_key_input" not in st.session_state:
    st.session_state.api_key_input = os.environ.get("GEMINI_API_KEY", "")

# 5. 사이드바 구현 (부서 권한 및 API 키 설정)
with st.sidebar:
    st.image("https://img.icons8.com/clouds/100/cargo-ship.png", width=100)
    st.title("성원글로벌카고 ERP")
    st.write("---")
    
    st.subheader("👤 부서 및 사용자 설정 (RBAC)")
    
    # 가상 로그인 유저 선택 기능
    users_list = [
        {"name": "sales_kim", "dept": "영업", "rank": "대리"},
        {"name": "ops_lee", "dept": "물류운송", "rank": "과장"},
        {"name": "customs_park", "dept": "통관", "rank": "사원"},
        {"name": "fin_choi", "dept": "재무", "rank": "부장"},
        {"name": "admin", "dept": "관리자", "rank": "대표"}
    ]
    
    selected_user = st.selectbox(
        "로그인 사용자 선택",
        options=users_list,
        format_func=lambda x: f"{x['name']} ({x['dept']}부 / {x['rank']})"
    )
    
    st.session_state.user_name = selected_user["name"]
    st.session_state.user_dept = selected_user["dept"]
    st.session_state.user_rank = selected_user["rank"]
    
    st.info(f"**접근 부서**: {st.session_state.user_dept}\n\n**보안 직급**: {st.session_state.user_rank}")
    
    st.write("---")
    st.subheader("🔑 AI 설정")
    st.text_input(
        "Gemini API API Key",
        key="api_key_input",
        help="Google AI Studio에서 발급받은 API 키를 입력하세요."
    )

# 6. AI 생성 헬퍼 함수
def ask_gemini(prompt):
    api_key = st.session_state.api_key_input
    if not api_key:
        return "⚠️ 오류: Gemini API 키가 입력되지 않았습니다. 사이드바 하단에서 API 키를 입력한 뒤 다시 시도해 주세요."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Gemini API 호출 중 오류가 발생했습니다:\n{str(e)}"

# 7. 메인 화면 구성
st.markdown("<div class='main-header'>🚢 SUNGWON GLOBAL CARGO AI ERP</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>성원글로벌카고 물류 자동화 및 AI 협업 플랫폼</div>", unsafe_allow_html=True)

# 메인 탭 정의
tab_names = [
    "📊 대시보드",
    "📦 화물 트래킹 (FMS)",
    "💬 부서 소통 게시판",
    "📅 회의록 관리",
    "✨ AI 오토메이션 센터"
]
is_admin = (st.session_state.user_dept == "관리자")
if is_admin:
    tab_names.append("⚙️ 직원 관리 (어드민)")

tabs = st.tabs(tab_names)

if is_admin:
    tab_dashboard, tab_tracking, tab_board, tab_meetings, tab_ai, tab_admin = tabs
else:
    tab_dashboard, tab_tracking, tab_board, tab_meetings, tab_ai = tabs


# ----------------- Tab 1: 대시보드 -----------------
with tab_dashboard:
    st.subheader("업무 요약 및 실시간 성과 지표")
    
    # 데이터 로드
    cargo_list = db.get_cargo_list()
    df_cargo = pd.DataFrame(cargo_list)
    
    # 1. 지표 카드 영역 (권한별 민감 정보 마스크)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>📦 진행 중인 총 선적 건수</div>
            <div class='metric-value'>{len(df_cargo)} 건</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        total_weight = df_cargo["cargo_weight"].sum() if not df_cargo.empty else 0
        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>⚖️ 총 화물 중량</div>
            <div class='metric-value'>{total_weight:.1f} Tons</div>
        </div>
        """, unsafe_allow_html=True)

    # 재무/관리자 권한만 매출/마진 확인 가능
    with col3:
        if st.session_state.user_dept in ["재무", "관리자"]:
            total_rev = df_cargo["revenue"].sum() if not df_cargo.empty else 0
            st.markdown(f"""
            <div class='card'>
                <div class='card-title'>💰 총 선적 매출액</div>
                <div class='metric-value'>₩ {total_rev:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='card'>
                <div class='card-title'>💰 총 선적 매출액</div>
                <div class='metric-value' style='color:#94a3b8;'>🔒 권한 없음</div>
            </div>
            """, unsafe_allow_html=True)

    with col4:
        if st.session_state.user_dept in ["재무", "관리자"]:
            total_margin = df_cargo["margin"].sum() if not df_cargo.empty else 0
            st.markdown(f"""
            <div class='card'>
                <div class='card-title'>📈 예상 누적 마진</div>
                <div class='metric-value'>₩ {total_margin:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='card'>
                <div class='card-title'>📈 예상 누적 마진</div>
                <div class='metric-value' style='color:#94a3b8;'>🔒 권한 없음</div>
            </div>
            """, unsafe_allow_html=True)

    # 2. 통계 그래프 및 공지사항
    col_graph, col_notice = st.columns([3, 2])
    
    with col_graph:
        st.write("### ✈️ 상태별 화물 분포")
        if not df_cargo.empty:
            status_counts = df_cargo["status"].value_counts().reset_index()
            status_counts.columns = ["상태", "건수"]
            st.bar_chart(status_counts.set_index("상태"), color="#3b82f6")
        else:
            st.info("등록된 화물이 없습니다.")
            
    with col_notice:
        st.write("### 📢 전사 공지사항 및 최근 업데이트")
        posts = db.get_posts(st.session_state.user_dept)
        public_posts = [p for p in posts if p["is_private"] == 0]
        
        if public_posts:
            for p in public_posts[:3]:
                st.markdown(f"""
                <div class='card'>
                    <div style='display:flex; justify-content:space-between;'>
                        <strong>{p['title']}</strong>
                        <span class='badge badge-primary'>{p['department']}</span>
                    </div>
                    <p style='font-size:0.9rem; color:#475569; margin-top:0.5rem;'>{p['content']}</p>
                    <span style='font-size:0.8rem; color:#94a3b8;'>작성자: {p['author']} | {p['created_at']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("공지사항이 없습니다.")

# ----------------- Tab 2: 화물 트래킹 (FMS) -----------------
with tab_tracking:
    st.subheader("화물 실시간 배송 추적 및 관리")
    
    # 1. 필터 및 검색
    search_query = st.text_input("🔍 Booking No, B/L No, 혹은 화주명으로 검색", "")
    
    cargo_list = db.get_cargo_list()
    df_disp = pd.DataFrame(cargo_list)
    
    if not df_disp.empty and search_query:
        df_disp = df_disp[
            df_disp["booking_no"].str.contains(search_query, case=False) |
            df_disp["bl_no"].str.contains(search_query, case=False) |
            df_disp["client_name"].str.contains(search_query, case=False)
        ]
        
    # 재무/관리자가 아닐 경우 마진 열 제외
    if st.session_state.user_dept not in ["재무", "관리자"] and not df_disp.empty:
        df_disp = df_disp.drop(columns=["margin"])
        if st.session_state.user_dept not in ["영업"]:
            df_disp = df_disp.drop(columns=["revenue"])

    if not df_disp.empty:
        st.dataframe(df_disp, use_container_width=True)
        
        # 엑셀 다운로드 파일 준비
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_disp.to_excel(writer, index=False, sheet_name='CargoList')
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 현재 필터링된 화물 목록 엑셀(Excel) 다운로드",
            data=excel_data,
            file_name=f"sungwon_cargo_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("검색 조건에 맞는 화물이 없습니다.")

    st.write("---")
    
    # 2. 추가 및 수정 권한
    col_add, col_edit = st.columns(2)
    
    with col_add:
        if st.session_state.user_dept in ["영업", "관리자"]:
            st.write("### ➕ 신규 선적(Cargo) 등록")
            with st.form("add_cargo_form", clear_on_submit=True):
                b_no = st.text_input("Booking No.", placeholder="예: BK20260606")
                bl_no = st.text_input("B/L No.", placeholder="예: BLXYZ9988")
                client = st.text_input("화주사명", placeholder="예: (주)한라상사")
                org = st.text_input("출발지 (Origin)", placeholder="예: 부산(Busan)")
                dest = st.text_input("도착지 (Destination)", placeholder="예: 뉴욕(New York)")
                vessel = st.text_input("선박/항공편명", placeholder="예: SUNGWON HOPE V.01")
                weight = st.number_input("중량 (Tons)", min_value=0.1, step=0.1)
                
                # 재무 및 마진은 영업/관리자만 입력
                rev = st.number_input("매출 (KRW)", min_value=0, step=10000)
                marg = st.number_input("마진 (KRW)", min_value=0, step=10000)
                
                status_sel = st.selectbox("진행 상태", ["입고완료", "출항", "운송중", "통관중", "인도완료"])
                
                submit_add = st.form_submit_button("선적 정보 등록")
                if submit_add:
                    if b_no and bl_no and client:
                        success = db.add_cargo(b_no, bl_no, client, org, dest, vessel, status_sel, weight, marg, rev)
                        if success:
                            st.success(f"선적 {b_no}이(가) 등록되었습니다.")
                            st.rerun()
                        else:
                            st.error("이미 존재하는 Booking No. 또는 B/L No.입니다.")
                    else:
                        st.error("필수 정보를 입력해 주세요.")
        else:
            st.write("### ➕ 신규 선적 등록")
            st.info("🔒 영업부 및 관리자만 신규 화물을 등록할 수 있습니다.")
            
    with col_edit:
        if st.session_state.user_dept in ["물류운송", "통관", "관리자"]:
            st.write("### 🔄 배송 상태 변경")
            cargo_options = db.get_cargo_list()
            if cargo_options:
                target_cargo = st.selectbox(
                    "상태를 변경할 화물 선택",
                    options=cargo_options,
                    format_func=lambda x: f"[{x['booking_no']}] {x['client_name']} -> {x['destination']} ({x['status']})"
                )
                
                new_status = st.selectbox(
                    "새로운 진행 상태",
                    ["입고완료", "출항", "운송중", "통관중", "인도완료"],
                    index=["입고완료", "출항", "운송중", "통관중", "인도완료"].index(target_cargo["status"])
                )
                
                if st.button("상태 업데이트 적용"):
                    db.update_cargo_status(target_cargo["id"], new_status)
                    st.success(f"[{target_cargo['booking_no']}] 화물의 상태가 '{new_status}'(으)로 업데이트되었습니다.")
                    st.rerun()
            else:
                st.info("등록된 화물이 없습니다.")
        else:
            st.write("### 🔄 배송 상태 변경")
            st.info("🔒 물류운송부, 통관부 및 관리자만 상태를 업데이트할 수 있습니다.")

# ----------------- Tab 3: 부서 소통 게시판 -----------------
with tab_board:
    st.subheader(f"💬 {st.session_state.user_dept}부 업무 소통 게시판")
    
    col_post_list, col_post_add = st.columns([3, 2])
    
    with col_post_list:
        st.write("### 최근 업무 공유 사항")
        posts = db.get_posts(st.session_state.user_dept)
        if posts:
            for p in posts:
                is_private_badge = "<span class='badge badge-danger'>부서비공개</span>" if p["is_private"] == 1 else "<span class='badge badge-success'>전체공개</span>"
                st.markdown(f"""
                <div class='card'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <strong style='font-size:1.1rem;'>{p['title']}</strong>
                        <div>
                            {is_private_badge}
                            <span class='badge badge-primary'>{p['department']}</span>
                        </div>
                    </div>
                    <p style='margin-top:0.5rem; color:#334155;'>{p['content']}</p>
                    <div style='font-size:0.8rem; color:#94a3b8;'>
                        작성자: {p['author']} | 작성시간: {p['created_at']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("게시글이 없습니다.")
            
    with col_post_add:
        st.write("### ✍️ 소통/업무 내용 공유하기")
        with st.form("add_post_form", clear_on_submit=True):
            p_title = st.text_input("글 제목")
            p_content = st.text_area("공유할 내용")
            is_private_check = st.checkbox("우리 부서원에게만 공개 (비공개)", value=False)
            
            submit_post = st.form_submit_button("글 등록")
            if submit_post:
                if p_title and p_content:
                    db.add_post(p_title, p_content, st.session_state.user_name, st.session_state.user_dept, 1 if is_private_check else 0)
                    st.success("게시물이 성공적으로 등록되었습니다.")
                    st.rerun()
                else:
                    st.error("제목과 내용을 채워주세요.")

# ----------------- Tab 4: 회의록 관리 -----------------
with tab_meetings:
    st.subheader(f"📅 {st.session_state.user_dept}부 부서 회의록")
    
    col_meet_list, col_meet_add = st.columns([3, 2])
    
    with col_meet_list:
        st.write("### 부서 회의록 아카이브")
        meetings = db.get_meetings(st.session_state.user_dept)
        if meetings:
            for m in meetings:
                st.markdown(f"""
                <div class='card'>
                    <div style='display:flex; justify-content:space-between;'>
                        <strong style='font-size:1.05rem;'>{m['title']}</strong>
                        <span class='badge badge-primary'>{m['department']}</span>
                    </div>
                    <p style='margin-top:0.5rem; color:#475569; font-size:0.95rem; white-space:pre-wrap;'>{m['content']}</p>
                    <div style='font-size:0.8rem; color:#94a3b8;'>
                        작성자: {m['author']} | 작성시간: {m['created_at']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("조회할 수 있는 회의록이 없습니다. 부서 권한에 따라 본인 부서의 회의록만 접근 가능합니다.")
            
    with col_meet_add:
        st.write("### 📝 새 회의록 작성")
        with st.form("add_meeting_form", clear_on_submit=True):
            m_title = st.text_input("회의 주제 (예: 주간 업무 진척도 조율)")
            m_content = st.text_area("회의 상세 내용 및 결정 사항", height=150)
            
            submit_meet = st.form_submit_button("회의록 등록")
            if submit_meet:
                if m_title and m_content:
                    db.add_meeting(m_title, m_content, st.session_state.user_name, st.session_state.user_dept)
                    st.success("회의록이 성공적으로 등록되었습니다.")
                    st.rerun()
                else:
                    st.error("회의 주제와 상세 내용을 채워주세요.")

# ----------------- Tab 5: AI 오토메이션 센터 -----------------
with tab_ai:
    st.subheader("✨ Gemini AI 기반 문서 및 보고서 자동화")
    
    # API 키 경고 안내
    if not st.session_state.api_key_input:
        st.warning("⚠️ AI 기능을 사용하시려면 사이드바 하단에서 **Gemini API Key**를 설정해 주십시오.")
        
    ai_sub_tab1, ai_sub_tab2, ai_sub_tab3 = st.tabs([
        "📄 AI 기안서(전자결재) 생성",
        "📝 AI 업무일지 자동 다듬기",
        "📈 데이터 기반 AI 물량/매출 보고서"
    ])
    
    # Sub-tab 1: AI 기안서
    with ai_sub_tab1:
        st.write("### 사내 전자결재용 공식 기안문 초안 작성")
        with st.form("ai_draft_form"):
            draft_title = st.text_input("기안 제목 / 주제", placeholder="예: 북미 신규 대리점 계약 체결 승인 요청")
            draft_summary = st.text_area(
                "핵심 내용 및 예산/조건 요약", 
                placeholder="예: 미국 LA 지점 계약 기간 1년, 선대 수수료 5% 인하 조건으로 현지 포워딩 업체 파트너십 추진 건. 신속한 허가 요망.",
                height=100
            )
            submit_draft_ai = st.form_submit_button("🤖 AI 기안서 양식 생성")
            
        if submit_draft_ai:
            if not draft_title or not draft_summary:
                st.error("기안 제목과 내용을 작성해 주세요.")
            else:
                prompt = f"""
                당신은 물류 회사 '성원글로벌카고'의 스마트한 AI 비서입니다.
                아래 입력 데이터를 바탕으로 회사 공식 기안서(전자결재) 양식에 맞는 정형화되고 정중한 기안서 초안을 한국어로 작성해 주세요.
                
                기안서 양식에 포함할 사항:
                1. 문서 번호: (AI 자동 생성 코드 기재)
                2. 기안 부서: {st.session_state.user_dept}부 / 기안자: {st.session_state.user_name} {st.session_state.user_rank}
                3. 기안 일자: {datetime.now().strftime('%Y년 %m월 %d일')}
                4. 제목: {draft_title}
                5. 기안 목적 및 필요성
                6. 상세 내용 및 기대 효과
                7. 예산 및 특이사항 (언급되었을 경우만 상세히)
                8. 결재란 및 합의 부서 의견란 가이드
                
                [입력 내용]:
                {draft_summary}
                """
                with st.spinner("AI가 격식 있는 기안서를 작성 중입니다..."):
                    result = ask_gemini(prompt)
                    st.success("기안서 초안 작성이 완료되었습니다!")
                    st.text_area("결과물 확인 및 복사", value=result, height=400)
                    st.download_button("📥 기안서 다운로드 (텍스트)", data=result, file_name="ai_draft.txt", mime="text/plain")

    # Sub-tab 2: AI 업무일지
    with ai_sub_tab2:
        st.write("### 일일 업무 내역을 바탕으로 깔끔한 업무일지 정제")
        with st.form("ai_worklog_form"):
            work_notes = st.text_area(
                "오늘 한 업무들을 간단하게 나열해 주세요 (개조식 또는 문장형)",
                placeholder="예: 오전 9시 B/L 발행 건 선사 확인, 거래처 선우무역 영업 미팅 진행하여 운임 500달러 네고 완료, 통관부 박사원 연락해서 도쿄행 화물 신고 상황 체크함.",
                height=120
            )
            submit_log_ai = st.form_submit_button("🤖 AI 업무일지 자동 다듬기")
            
        if submit_log_ai:
            if not work_notes:
                st.error("오늘 수행한 업무 내용을 입력해 주세요.")
            else:
                prompt = f"""
                당신은 '성원글로벌카고'의 사내 업무 생산성 AI 비서입니다.
                다음 사용자가 두서없이 입력한 일일 업무 메모를 바탕으로, 대기업 표준 양식의 정형화된 '일일 업무일지(Daily Activity Report)'로 정제하여 작성해 주세요.
                가독성이 높도록 시간순 또는 업무 분류별로 정제하고, 전문 물류 용어를 사용하여 비즈니스 언어로 다듬어 주시기 바랍니다.
                
                - 작성자: {st.session_state.user_name} ({st.session_state.user_dept}부 / {st.session_state.user_rank})
                - 일자: {datetime.now().strftime('%Y-%m-%d')}
                
                [메모 내용]:
                {work_notes}
                """
                with st.spinner("AI가 업무일지를 포맷팅 중입니다..."):
                    result = ask_gemini(prompt)
                    st.success("업무일지 다듬기가 완료되었습니다!")
                    st.text_area("결과물 확인 및 복사", value=result, height=350)
                    st.download_button("📥 업무일지 다운로드 (텍스트)", data=result, file_name="ai_worklog.txt", mime="text/plain")

    # Sub-tab 3: AI 보고서
    with ai_sub_tab3:
        st.write("### 현재 물류 트래킹 데이터를 분석하여 경영진 보고서 자동 작성")
        st.info("시스템 DB에 등록된 실시간 선적 및 화물 목록 데이터를 바탕으로 AI가 물동량 및 현황 요약 보고서를 작성합니다.")
        
        # 현재 DB 데이터 요약 추출
        cargo_list_report = db.get_cargo_list()
        
        if cargo_list_report:
            df_rep = pd.DataFrame(cargo_list_report)
            # 마진 정보 가공 (권한 확인)
            if st.session_state.user_dept not in ["재무", "관리자"]:
                # 재무/관리자가 아닐 경우 가짜 정보 전달하여 보안 유지
                df_rep["margin"] = "보안 마스크"
                df_rep["revenue"] = "보안 마스크"
                
            data_summary = df_rep.to_string()
            
            if st.button("🤖 AI 종합 보고서 초안 생성"):
                prompt = f"""
                당신은 '성원글로벌카고'의 수석 물류 데이터 분석관이자 AI 어시스턴트입니다.
                현재 등록되어 있는 아래의 실시간 화물 선적 현황 데이터를 정량적으로 분석하고, 경영진 보고용 '화물 운송 및 매출 실적 요약 보고서'를 한국어로 성의 있게 작성해 주세요.
                
                [현재 화물 실시간 원본 데이터]:
                {data_summary}
                
                보고서 요구 조건:
                1. 보고서 제목: 성원글로벌카고 물류 운송 실적 및 현황 요약 보고
                2. 작성 부서: {st.session_state.user_dept}부
                3. 분석 핵심 요약 (정량적 통계 제공: 총 건수, 주요 루트, 상태별 분포 등)
                4. 수익성 분석 (재무/관리자가 아닌 경우 매출/마진 데이터가 '보안 마스크' 처리되므로, 데이터가 가려진 경우 매출/마진 항목 분석을 생략하거나 권한 제한으로 마스크 처리되었음을 명시하고 물동량 위주로 분석할 것. 숫자가 있다면 구체적으로 총 매출액 및 마진 비율 분석 진행)
                5. 주요 물류 보틀넥 분석 및 대응 의견 (예: 특정 루트나 배송 정체 상태인 건에 대한 대처 조치 제안)
                """
                with st.spinner("데이터 분석 및 보고서 작성 중..."):
                    result = ask_gemini(prompt)
                    st.success("데이터 기반 보고서 생성이 완료되었습니다!")
                    st.text_area("결과물 확인 및 복사", value=result, height=450)
                    st.download_button("📥 보고서 다운로드 (텍스트)", data=result, file_name="ai_business_report.txt", mime="text/plain")
        else:
            st.error("데이터베이스에 등록된 화물이 없어 보고서를 작성할 수 없습니다.")

# ----------------- Tab 6: 직원 관리 (어드민) -----------------
if is_admin:
    with tab_admin:
        st.subheader("⚙️ 전사 직원 관리 및 권한 설정")
        
        # 1. 직원 목록 표
        st.write("### 현재 등록된 직원 목록")
        users = db.get_users()
        df_users = pd.DataFrame(users)
        st.dataframe(df_users, use_container_width=True)
        
        col_u_add, col_u_edit = st.columns(2)
        
        # 2. 직원 추가
        with col_u_add:
            st.write("### ➕ 신규 직원 등록")
            with st.form("add_user_form", clear_on_submit=True):
                new_username = st.text_input("아이디 (ID)")
                new_password = st.text_input("비밀번호 (Password)", type="password")
                new_dept = st.selectbox("소속 부서", ["영업", "물류운송", "통관", "재무", "관리자"])
                new_rank = st.selectbox("직급", ["사원", "대리", "과장", "부장", "대표"])
                new_role = st.selectbox("시스템 권한 (Role)", ["user", "manager", "admin"])
                
                submit_user = st.form_submit_button("직원 추가")
                if submit_user:
                    if new_username and new_password:
                        success = db.add_user(new_username, new_password, new_dept, new_rank, new_role)
                        if success:
                            st.success(f"직원 '{new_username}'이(가) 등록되었습니다.")
                            st.rerun()
                        else:
                            st.error("이미 존재하는 사용자 아이디입니다.")
                    else:
                        st.error("아이디와 비밀번호를 입력해 주세요.")
                        
        # 3. 직원 정보 수정 및 삭제
        with col_u_edit:
            st.write("### 🔄 직원 권한 및 정보 변경")
            user_options = db.get_users()
            if user_options:
                target_user = st.selectbox(
                    "정보를 변경할 직원 선택",
                    options=user_options,
                    format_func=lambda x: f"{x['username']} ({x['department']}부 / {x['rank']})"
                )
                
                up_dept = st.selectbox("새 소속 부서", ["영업", "물류운송", "통관", "재무", "관리자"], index=["영업", "물류운송", "통관", "재무", "관리자"].index(target_user["department"]))
                up_rank = st.selectbox("새 직급", ["사원", "대리", "과장", "부장", "대표"], index=["사원", "대리", "과장", "부장", "대표"].index(target_user["rank"]))
                up_role = st.selectbox("새 권한 (Role)", ["user", "manager", "admin"], index=["user", "manager", "admin"].index(target_user["role"]))
                
                col_btn_update, col_btn_delete = st.columns(2)
                
                with col_btn_update:
                    if st.button("정보 업데이트"):
                        db.update_user(target_user["id"], up_dept, up_rank, up_role)
                        st.success(f"'{target_user['username']}' 직원의 정보가 업데이트되었습니다.")
                        st.rerun()
                        
                with col_btn_delete:
                    # 대표 계정인 admin은 삭제 차단
                    if target_user["username"] == "admin":
                        st.warning("경고: 최고 관리자(admin) 계정은 삭제할 수 없습니다.")
                    else:
                        if st.button("❌ 직원 삭제"):
                            db.delete_user(target_user["id"])
                            st.success(f"'{target_user['username']}' 직원이 삭제되었습니다.")
                            st.rerun()
