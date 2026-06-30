import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import base64
import datetime
from datetime import date
import re
import textwrap

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="신건설 통합 관리 시스템", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. 구글 스프레드시트 실시간 연동 및 DB 초기화
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=5) 
    df = df.fillna("")
except Exception as e:
    st.error(f"구글 시트 연동 실패: {e}")
    st.stop()

required_cols = [
    "ID", "날짜", "현장명", "사고장소", "사고경위", "작업환경", "사고원인", 
    "사고유형", "상해피해정도", "피재자", "생년월일", "소속_직급", 
    "직종", "채용일자", "국적_체류코드", "기술적대책", "관리적대책", "교육적대책",
    "안전담당", "공사/공무 담당", "현장소장", "안전팀", "공사팀", "PM", "대표이사",
    "사고보고서_제출", "재발방지대책_제출", "산재표_제출", "합의서_작성", "진행상태"
]

for col in required_cols:
    if col not in df.columns:
        if col == "사고보고서_제출": df[col] = "O"
        elif col in ["재발방지대책_제출", "산재표_제출", "합의서_작성"]: df[col] = "X"
        elif col == "진행상태": df[col] = "진행중"
        else: df[col] = "대기"

approvers = ["안전담당", "공사/공무 담당", "현장소장", "안전팀", "공사팀", "PM", "대표이사"]

# ==========================================
# 3. 전체 UI 커스텀 CSS & 공통 헬퍼 함수
# ==========================================
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1E4D6B; }
[data-testid="stSidebar"] * { color: white !important; }
.gapji-table { width: 100% !important; border-collapse: collapse !important; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; color: #000; border: 2px solid #000 !important; margin-bottom: 20px; table-layout: fixed; word-break: break-word; }
.gapji-table th, .gapji-table td { border: 1px solid #000 !important; padding: 6px !important; text-align: center; vertical-align: middle; }
.gapji-header { background-color: #f0f0f0 !important; font-weight: bold; }
.grid-photo { width: 100%; height: 400px; object-fit: contain; background-color: #fafafa; display: block; margin: 0 auto; }
.photo-blank { height: 400px; display: flex; justify-content: center; align-items: center; color: #999; font-size: 13px; background-color: #fafafa; }
div[data-testid="stForm"] { padding: 1rem; border: 2px solid #ddd; border-radius: 8px;}
.stTextInput, .stDateInput, .stTimeInput, .stSelectbox, .stTextArea { margin-bottom: -10px; }
.page-break { page-break-before: always; }
</style>
""", unsafe_allow_html=True)

def process_images_for_html(uploaded_files, height="200px"):
    tags = []
    if uploaded_files:
        for f in uploaded_files:
            encoded = base64.b64encode(f.getvalue()).decode()
            tags.append(f'<img src="data:image/jpeg;base64,{encoded}" style="width:100%; height:{height}; object-fit:contain; background-color:#fafafa;">')
    return tags

def build_grid(tags, label):
    clean_label = label.replace('<br>', ' ')
    if not tags: return f'<tr style="page-break-inside: avoid; break-inside: avoid;"><td class="gapji-header" style="width:20%;">{label}</td><td style="padding:6px; width:80%;"><div class="photo-blank">{clean_label} 미등록</div></td></tr>'
    inner = '<table width="100%" border="0" cellpadding="0" cellspacing="0" style="table-layout:fixed; height:100%;">'
    for i in range((len(tags) + 1) // 2):
        c1 = tags[i*2]
        c2 = tags[i*2+1] if (i*2+1) < len(tags) else '<div class="photo-blank">대기</div>'
        bb = 'border-bottom: 1px solid #000;' if i < ((len(tags)+1)//2 - 1) else ''
        inner += f'<tr style="page-break-inside: avoid; break-inside: avoid;"><td style="width:50%; border-right:1px solid #000; {bb} padding:6px;">{c1}</td><td style="width:50%; {bb} padding:6px;">{c2}</td></tr>'
    inner += '</table>'
    return f'<tr style="page-break-inside: avoid; break-inside: avoid;"><td class="gapji-header" style="width:20%;">{label}</td><td style="padding:0; width:80%;">{inner}</td></tr>'

def get_sign(val):
    if str(val).strip() in ["승인", "확인"]: return "<b>[확인]<br><span style='font-size:9px; color:gray;'>signed</span></b>"
    return ""

# ==========================================
# 4. 왼쪽 사이드바
# ==========================================
with st.sidebar:
    st.title("🏗️ 신건설 통합관리 시스템")
    st.markdown("---")
    
    main_menu = st.radio("메뉴 선택", ["1. 위험성평가", "2. TBM", "3. 사고보고서", "4. 안전보건교육", "5. 작업표준화"], index=0)
    
    if main_menu == "3. 사고보고서":
        st.markdown("---")
        sub_menu = st.radio(
            "사고보고서 상세 업무",
            ["📝 최초 사고보고서 작성", "📎 후속 서류 업데이트", "📊 통합 DB (구글시트 뷰어)", "🖨️ 최종 보고서 출력"]
        )

# ==========================================
# 5. 중앙 메인 화면 로직
# ==========================================

# ---------------------------------------------------------
# [모듈 1] 위험성평가 (기획서 반영 업그레이드 장착)
# ---------------------------------------------------------
if main_menu == "1. 위험성평가":
    st.header("📝 위험성평가 회의록 및 사진 등록")
    
    col_input, col_preview = st.columns([4, 6])
    
    with col_input:
        st.subheader("🔸 회의 내용 및 사진 입력창")
        
        with st.form("risk_assessment_form"):
            st.markdown("**1. 회의 개요**")
            c1, c2 = st.columns(2)
            ra_site = c1.text_input("현장명", value="아크로 드 서초")
            ra_place = c2.text_input("장소", value="회의실")
            
            c3, c4 = st.columns(2)
            ra_date_start = c3.date_input("작업기간(시작)", value=date(2026, 6, 29))
            ra_date_end = c4.date_input("작업기간(종료)", value=date(2026, 7, 11))
            
            c5, c6 = st.columns(2)
            ra_meeting_date = c5.date_input("회의일", value=date(2026, 6, 24))
            ra_attendees_count = c6.text_input("참석인원", value="16명")
            
            ra_writer = st.text_input("작성자 (직접입력)", value="전성배")
            
            st.markdown("**전자결재 서명 란 (클릭하여 승인)**")
            c_sign1, c_sign2, c_sign3 = st.columns(3)
            sign_manager = c_sign1.checkbox("관리감독자 서명 🖋️")
            sign_safety = c_sign2.checkbox("안전관리자 서명 🖋️")
            sign_director = c_sign3.checkbox("현장소장 서명 🖋️")
            
            default_attendees = "소장 장도호, 품질 김정곤, 공사 조상호, 철근 오종훈, 형틀 김을탁, 형틀 강태웅, 형틀 박나경, 형틀 김범수, 타설 김선열, 알폼 김강호, 공무 한승훈, 공무 김현근, 안전 박정원, 안전 전성배, 해체 황호근"
            ra_attendees_list = st.text_area("참석자 명단 (반점 ','으로 구분)", value=default_attendees, height=100)
            
            st.markdown("---")
            st.markdown("**2. 주요위험 관리 POINT**")
            ra_agenda = st.text_input("주요안건", value="사전 유해.위험 점검, 논의 / 고위험 작업, 상습 부적합 사항")
            
            ra_risk_1 = st.text_area("1. 시스템", value="비계에 벽이음 가새 미설치 작업 중 붕괴 위험\nㄴ 설치 작업시 벽이음 선행 후 작업 실시 및 규정에 맞는 간격으로 설치 할 것", height=65)
            ra_risk_2 = st.text_area("2. 알폼", value="말비계상부 작업시 끝단부 작업 및 불안전한 행동으로 인한 추락 위험\nㄴ 낙상경보기 설치 및 승강 발판 미끄럼 방지 조치", height=65)
            ra_risk_3 = st.text_area("3. 철근", value="계단 철근 배근 후 이동 경사발판 미설치상태 철근을 밟고 이동 중 미끄러져 넘어짐\nㄴ 계단 경사철근 배근 직후 이동용 경사발판 설치 후 이동", height=65)
            ra_risk_4 = st.text_area("4. PC", value="슬리브 타입 앙카 설치 후 돌출물에 걸려 넘어짐\nㄴ 앙카 설치 후 앙카부위 가시성 확보", height=65)
            ra_risk_5 = st.text_area("5. 해체정리", value="거푸집 동바리 해체 작업 구간 조도확보 미흡으로 인한 전도 및 충돌 위험\nㄴ 투광등 지급 및 LED 설치 후 작업 실시", height=65)
            ra_risk_6 = st.text_area("6. 형틀", value="고소작업대 상승 후 연장 발판 사용 후 그대로 하강 도중 하부 구조물에 충돌하여 장비 전도 위험\nㄴ 연장 발판 내민상태로 내려오지않게 작업자 특별교육 실시", height=65)
            
            st.markdown("---")
            st.markdown("**3. 의견 청취 및 종합 의견**")
            default_opinions = "[형틀 강태웅] 현장 내 소변기 뿐만 아니라 간이 화장실이 더 늘었으면 좋겠음.\nㄴ LDSPM 회의 소장님 참가 시 DL측에 전달하여 답변을 기다리고 있으며 해당 근로자에겐 DL측 답변이 오면 전달해주기로함\n\n[보통인부 이길수] 대기소에서 사무실까지오는 발판 비계가 꺼진부분이 너무 많습니다. 교체해주세요\nㄴ DL 시설팀에 전달하여 06.29 교체예정이라고 답변 받음"
            ra_worker_opinion = st.text_area("근로자 의견청취", value=default_opinions, height=120)
            
            ra_manager_opinion = st.text_input("관리감독자 의견", value="공정 진행에 따라 지하층 작업이 많아지고있는데 지하층 작업 전 조도 확보 후 작업 실시 할 것")
            ra_safety_opinion = st.text_input("안전관리자 의견", value="현장 내 휴게소 설치가 완료되었음에도 불구하고 휴게시간에 현장에 있는 인원이 많이 보이는데 각 팀 팀장님들은 휴게소 사용 할 수 있게 적극적으로 권유 할 것")
            ra_director_opinion = st.text_input("안전보건관리책임자 의견", value="날씨가 더워짐에 따라 근로자 개인 건강관리에 유념하며 몸에 이상이 있을시 바로 조치될 수 있도록 할것")
            
            st.markdown("---")
            st.markdown("**4. 사진대지 첨부**")
            ra_photos_meeting = st.file_uploader("회의 및 교육 사진 업로드", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
            
            ra_submitted = st.form_submit_button("💾 서명 및 위험성평가 양식 생성", type="primary", use_container_width=True)

    with col_preview:
        st.subheader("🔸 위험성평가 회의록 (실제 양식 매칭 뷰)")
        
        def format_text(text):
            return text.replace('\n', '<br>')
            
        attendee_nodes = [name.strip() for name in ra_attendees_list.split(",") if name.strip()]
        attendee_rows_html = ""
        for i in range(0, len(attendee_nodes), 5):
            row_nodes = attendee_nodes[i:i+5]
            tds = []
            for node in row_nodes:
                tds.append(f'<td style="width:20%; text-align:left; padding:6px 10px;">{node} <span style="float:right; font-size:10px; color:#1E4D6B; border:1px solid #1E4D6B; padding:0 2px; border-radius:3px;">(인)</span></td>')
            while len(tds) < 5:
                tds.append('<td style="width:20%;"></td>')
            attendee_rows_html += f"<tr>{''.join(tds)}</tr>"

        sign_html_manager = "[확인]<br><span style='font-size:8px; color:gray;'>signed</span>" if sign_manager else ""
        sign_html_safety = "[확인]<br><span style='font-size:8px; color:gray;'>signed</span>" if sign_safety else ""
        sign_html_director = "[확인]<br><span style='font-size:8px; color:gray;'>signed</span>" if sign_director else ""

        ra_html_page1 = f"""
        <div style="background-color: white; padding: 20px; border: 1px solid #ccc; color: #000; font-family: 'Malgun Gothic', sans-serif;">
            <table style="width:100%; border-collapse:collapse; border:none; margin-bottom:10px;">
                <tr>
                    <td style="border:none; text-align:left; vertical-align:middle;">
                        <span style="font-size: 24px; font-weight: bold; letter-spacing:-1px;">위험성평가 회의록</span>
                    </td>
                    <td style="border:none; text-align:right;">
                        <table border="1" style="display:inline-block; border-collapse:collapse; font-size:11px; text-align:center; color:#000; border:1px solid #000;">
                            <tr style="background-color:#f0f0f0; font-weight:bold;">
                                <td rowspan="2" style="width:20px; padding:2px;">결<br>재</td>
                                <td style="width:65px; padding:3px;">작성</td>
                                <td style="width:65px; padding:3px;">관리감독자</td>
                                <td style="width:65px; padding:3px;">안전관리자</td>
                                <td style="width:65px; padding:3px;">현장소장</td>
                            </tr>
                            <tr>
                                <td style="height:38px; font-size:12px; font-weight:bold; vertical-align:middle;">{ra_writer}</td>
                                <td style="color:#1E4D6B; font-size:10px; font-weight:bold; vertical-align:middle;">{sign_html_manager}</td>
                                <td style="color:#1E4D6B; font-size:10px; font-weight:bold; vertical-align:middle;">{sign_html_safety}</td>
                                <td style="color:#b91c1c; font-size:10px; font-weight:bold; vertical-align:middle;">{sign_html_director}</td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>

            <table class="gapji-table" style="background-color: white; margin-bottom:15px;">
                <tr>
                    <td class="gapji-header" style="width:15%;">현장명</td><td style="width:35%; font-weight:bold; text-align:left; padding-left:10px;">{ra_site}</td>
                    <td class="gapji-header" style="width:15%;">작업기간</td><td style="width:35%; text-align:left; padding-left:10px;">{ra_date_start.strftime('%Y.%m.%d')} ~ {ra_date_end.strftime('%Y.%m.%d')}</td>
                </tr>
                <tr>
                    <td class="gapji-header">장 소</td><td style="text-align:left; padding-left:10px;">{ra_place}</td>
                    <td class="gapji-header">회의일</td><td style="text-align:left; padding-left:10px;">{ra_meeting_date.strftime('%Y.%m.%d')}</td>
                </tr>
                <tr>
                    <td class="gapji-header">참석인원</td><td style="text-align:left; padding-left:10px;">{ra_attendees_count}</td>
                    <td class="gapji-header">작성자</td><td style="text-align:left; padding-left:10px;">{ra_writer}</td>
                </tr>
            </table>

            <p style="margin:5px 0; font-weight:bold; font-size:13px;">【 참석자 명단 】</p>
            <table class="gapji-table" style="background-color: white; margin-bottom:20px;">
                {attendee_rows_html}
            </table>

            <table class="gapji-table" style="background-color: white; margin-bottom:15px;">
                <tr>
                    <td class="gapji-header" style="width:15%;" rowspan="7">주요위험<br>관리POINT</td>
                    <td colspan="2" style="text-align:left; font-weight:bold; background-color:#f5f5f5; padding:8px;">[주요안건] {ra_agenda}</td>
                </tr>
                <tr><td style="width:15%; background-color:#fafafa; font-weight:bold;">시스템</td><td style="text-align:left; padding:8px;">{format_text(ra_risk_1)}</td></tr>
                <tr><td style="background-color:#fafafa; font-weight:bold;">알폼</td><td style="text-align:left; padding:8px;">{format_text(ra_risk_2)}</td></tr>
                <tr><td style="background-color:#fafafa; font-weight:bold;">철근</td><td style="text-align:left; padding:8px;">{format_text(ra_risk_3)}</td></tr>
                <tr><td style="background-color:#fafafa; font-weight:bold;">PC</td><td style="text-align:left; padding:8px;">{format_text(ra_risk_4)}</td></tr>
                <tr><td style="background-color:#fafafa; font-weight:bold;">해체정리</td><td style="text-align:left; padding:8px;">{format_text(ra_risk_5)}</td></tr>
                <tr><td style="background-color:#fafafa; font-weight:bold;">형틀</td><td style="text-align:left; padding:8px;">{format_text(ra_risk_6)}</td></tr>
            </table>

            <table class="gapji-table" style="background-color: white;">
                <tr>
                    <td class="gapji-header" style="width:15%;">근로자<br>의견청취</td>
                    <td style="text-align:left; padding:10px; background-color:#fffdf7;">{format_text(ra_worker_opinion)}</td>
                </tr>
                <tr>
                    <td class="gapji-header">관리감독자<br>의견</td>
                    <td style="text-align:left; padding:10px;">{ra_manager_opinion}</td>
                </tr>
                <tr>
                    <td class="gapji-header">안전관리자<br>의견</td>
                    <td style="text-align:left; padding:10px;">{ra_safety_opinion}</td>
                </tr>
                <tr>
                    <td class="gapji-header">책임자총평</td>
                    <td style="text-align:left; padding:10px; font-weight:bold; color:#b91c1c;">{ra_director_opinion}</td>
                </tr>
            </table>
            <div style="text-align:right; font-size:12px; font-weight:bold; margin-top:15px; color:#555;">신건설주식회사</div>
        </div>
        """
        
        photo_tags = process_images_for_html(ra_photos_meeting if 'ra_photos_meeting' in locals() and ra_photos_meeting else [])
        photo_grid_html = ""
        if photo_tags:
            photo_grid_html += '<table class="gapji-table" style="background-color: white; margin-top:15px; page-break-inside: auto; break-inside: auto;"><tr><td colspan="2" class="gapji-header" style="font-size: 16px; padding:10px;">【사진대지 - 위험성평가 전파교육】</td></tr>'
            for i in range(0, len(photo_tags), 2):
                img1 = photo_tags[i]
                img2 = photo_tags[i+1] if i+1 < len(photo_tags) else '<div class="photo-blank">대기</div>'
                photo_grid_html += f'<tr style="page-break-inside: avoid; break-inside: avoid;"><td style="width:50%; padding:10px;">{img1}</td><td style="width:50%; padding:10px;">{img2}</td></tr>'
            photo_grid_html += '</table>'
        else:
            photo_grid_html += '<div style="text-align:center; padding:20px; color:gray; border: 1px dashed #ccc; margin-top:10px; background-color:white;">첨부된 교육 전파 사진이 없습니다. 좌측에서 등록해 주세요.</div>'

        clean_render_html = re.sub(r'>\s+<', '><', ra_html_page1 + photo_grid_html)
        st.markdown(clean_render_html, unsafe_allow_html=True)
        
        if ra_submitted:
            ra_standalone_html = f"""
            <!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>위험성평가 회의록</title>
            <style>
                @page {{ size: A4 portrait; margin: 12mm 15mm; }} 
                body {{ background: #fff; font-family: 'Malgun Gothic', sans-serif; font-size:12px; color:#000; margin:0; padding:0; }} 
                .gapji-table {{ width: 100%; border-collapse: collapse; border: 2px solid #000; margin-bottom: 15px; table-layout: fixed; word-break: break-word; }} 
                .gapji-table th, .gapji-table td {{ border: 1px solid #000; padding: 6px; text-align: center; vertical-align: middle; }} 
                .gapji-header {{ background-color: #f0f0f0; font-weight: bold; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                @media print {{
                    tr, td, th {{ page-break-inside: avoid !important; break-inside: avoid !important; }}
                    table {{ page-break-inside: auto !important; break-inside: auto !important; }}
                }}
            </style>
            </head><body onload=\"window.print()\">
            {ra_html_page1}
            <br>
            {photo_grid_html}
            </body></html>
            """
            ra_b64 = base64.b64encode(ra_standalone_html.encode('utf-8')).decode('utf-8')
            st.markdown(f'<div style="text-align:center; margin-top:20px;"><a href="data:text/html;base64,{ra_b64}" download="위험성평가_회의록_{ra_meeting_date.strftime("%Y%m%d")}.html" style="padding:12px 25px; background-color:#1E4D6B; color:white; text-decoration:none; border-radius:6px; font-weight:bold; font-size:14px;">🖨️ 현장제출용 A4 양식 출력하기</a></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# [모듈 3] 사고보고서 (기존 원본 로직 100% 동일 가동)
# ---------------------------------------------------------
elif main_menu == "3. 사고보고서":
    
    if sub_menu == "📝 최초 사고보고서 작성":
        st.header("📝 최초 사고보고서 등록")
        col_input, col_preview = st.columns([5, 5])
        
        with col_input:
            st.subheader("🔸 현장 입력창")
            with st.form("input_form"):
                site_name = st.text_input("현장명", value="수원당수현장")
                c1, c2 = st.columns(2)
                accident_date = c1.date_input("사고일자", value=date.today())
                accident_time = c2.time_input("사고시간", value=datetime.time(10, 30))
                accident_place = st.text_input("사고장소", value="201동 B2F 주차장 구간")
                work_detail = st.text_input("작업환경", value="데크보 설치 작업중")
                accident_cause = st.text_input("사고원인", value="하부 동바리 설치 중에 슬링벨트를 풀면서 데크보가 무너짐")
                accident_type = st.selectbox("사고발생형태", ["떨어짐", "낙하·비래(맞음)", "넘어짐", "부딪힘/찔림", "절단·베임", "기타"], index=1)
                injury_degree = st.text_input("상해피해정도 진단서", value="주상병 : 좌측 제12 늑골 골절, 폐쇄성")
                
                st.markdown("---")
                
                p1, p2 = st.columns(2)
                p_name_ko = p1.text_input("피재자 성명", value="나형들")
                p_birth_code = p2.text_input("생년월일 (6자리)", value="781231")
                p3, p4 = st.columns(2)
                p_team = p3.text_input("소속/직급", value="김개똥팀")
                p_gongjong = p4.text_input("직종", value="형틀공")
                p5, p6 = st.columns(2)
                p_hire_date = p5.date_input("채용일자", value=date(2024, 5, 2))
                p_nation = p6.text_input("국적/체류코드", value="베트남 / F-6")

                formatted_date_time = f"{accident_date.strftime('%y.%m.%d')} {accident_time.strftime('%H:%M')}분경"
                auto_detail = f"{formatted_date_time} / {accident_place}에서 / {p_team} {p_gongjong} {p_name_ko}({p_birth_code})이(가) {work_detail} 중, {accident_cause} 발생하여 [{accident_type}] 사고가 발생함."
                
                submitted = st.form_submit_button("💾 1단계: 사고보고서 등록", type="primary", use_container_width=True)
                if submitted:
                    new_id = int(df["ID"].max()) + 1 if not df.empty and pd.to_numeric(df["ID"], errors='coerce').notna().any() else 1
                    new_row = pd.DataFrame([{
                        "ID": new_id, "날짜": formatted_date_time, "현장명": site_name, "사고장소": accident_place,
                        "사고경위": auto_detail, "작업환경": work_detail, "사고원인": accident_cause,
                        "사고유형": accident_type, "상해피해정도": injury_degree, "피재자": p_name_ko,
                        "생년월일": p_birth_code, "소속_직급": p_team, "직종": p_gongjong,
                        "채용일자": str(p_hire_date), "국적_체류코드": p_nation,
                        **{app: "대기" for app in approvers},
                        "사고보고서_제출": "O", "재발방지대책_제출": "X", "산재표_제출": "X", "합의서_작성": "X", "진행상태": "진행중"
                    }])
                    conn.update(data=pd.concat([df, new_row], ignore_index=True))
                    st.success("✅ 사고보고서 제출 완료! 상태가 '진행중'으로 등록되었습니다.")
                    st.rerun()

        with col_preview:
            st.subheader("🔸 결과 확인창")
            preview_html = f"""
            <div style="background-color: white; padding: 15px; border: 2px solid #4CAF50; border-radius: 8px;">
                <table class="gapji-table" style="background-color: white;">
                    <tr><td colspan="4" style="font-size: 18px; font-weight: bold; background-color:#e8f5e9;">최초 재해발생보고서 (미리보기)</td></tr>
                    <tr><td class="gapji-header" style="width:20%;">현장명</td><td style="width:30%;">{site_name}</td>
                        <td class="gapji-header" style="width:20%;">사고일시</td><td style="width:30%;">{formatted_date_time}</td></tr>
                    <tr><td class="gapji-header">사고장소</td><td>{accident_place}</td>
                        <td class="gapji-header">작업환경</td><td>{work_detail}</td></tr>
                    <tr><td class="gapji-header">피재자</td><td>{p_team} {p_gongjong} {p_name_ko}</td>
                        <td class="gapji-header">사고형태</td><td>{accident_type}</td></tr>
                    <tr><td class="gapji-header">사고경위</td>
                        <td colspan="3" style="text-align:left; background-color:#fff3e0; font-weight:bold;">{auto_detail}</td></tr>
                </table>
            </div>
            """
            clean_preview = re.sub(r'>\s+<', '><', preview_html)
            st.markdown(clean_preview, unsafe_allow_html=True)
            st.info("최초 저장 시 1단계(보고서 제출)만 완료되며, 나머지 서류는 [후속 서류 업데이트] 메뉴에서 진행합니다.")

    elif sub_menu == "📎 후속 서류 업데이트":
        st.header("📎 후속 서류 및 사진 제출")
        if df.empty:
            st.warning("등록된 사고 기록이 없습니다.")
        else:
            def update_status(idx, col_name, val):
                df.loc[idx, col_name] = val
                c1 = df.loc[idx, "사고보고서_제출"] == "O"
                c2 = df.loc[idx, "재발방지대책_제출"] == "O"
                c3 = df.loc[idx, "산재표_제출"] == "O"
                c4 = df.loc[idx, "합의서_작성"] in ["O", "N/A"]
                df.loc[idx, "진행상태"] = "종결" if (c1 and c2 and c3 and c4) else "진행중"
                conn.update(data=df)
                st.toast(f"✅ {col_name} 업데이트 완료!")

            select_idx = st.selectbox("업데이트할 사고 건을 선택하세요", df.index, format_func=lambda x: f"[{df.loc[x, 'ID']}] {df.loc[x, '현장명']} - {df.loc[x, '피재자']} ({df.loc[x, '진행상태']})")
            row = df.loc[select_idx]

            st.markdown("---")
            st.subheader(f"📊 현재 제출 현황 (상태: **{row['진행상태']}**)")
            
            status_df = pd.DataFrame([{
                "사고보고서": row['사고보고서_제출'], "재발방지대책": row['재발방지대책_제출'], 
                "산재표 제출": row['산재표_제출'], "합의서 작성": row['합의서_작성']
            }])
            st.table(status_df)

            tab1, tab2, tab3 = st.tabs(["🛡️ 재발방지대책", "🏥 산재표 제출", "🤝 합의서 작성"])
            
            with tab1:
                st.markdown("**재발방지대책 (입력 + 사진업로드)**")
                tech = st.text_input("기술적 대책", value=row.get('기술적대책', ''))
                admin = st.text_input("관리적 대책", value=row.get('관리적대책', ''))
                edu = st.text_input("교육적 대책", value=row.get('교육적대책', ''))
                file1 = st.file_uploader("재발방지대책 관련 사진 업로드", type=["jpg", "png", "jpeg"])
                if st.button("재발방지대책 제출 (완료 처리)"):
                    df.loc[select_idx, "기술적대책"] = tech
                    df.loc[select_idx, "관리적대책"] = admin
                    df.loc[select_idx, "교육적대책"] = edu
                    update_status(select_idx, "재발방지대책_제출", "O")
                    st.rerun()

            with tab2:
                st.markdown("**산재표 제출 (사진업로드)**")
                file2 = st.file_uploader("산재표 원본 사진 업로드", type=["jpg", "png", "pdf"])
                if st.button("산재표 제출 (완료 처리)"):
                    update_status(select_idx, "산재표_제출", "O")
                    st.rerun()

            with tab3:
                st.markdown("**합의서 작성 (사진업로드 또는 N/A 처리)**")
                file3 = st.file_uploader("합의서 원본 사진 업로드", type=["jpg", "png", "pdf"])
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("합의서 제출 (완료 처리)"):
                    update_status(select_idx, "합의서_작성", "O")
                    st.rerun()
                if c_btn2.button("N/A 처리 (본사 권한)", type="secondary"):
                    update_status(select_idx, "합의서_작성", "N/A")
                    st.rerun()

    elif sub_menu == "📊 통합 DB (구글시트 뷰어)":
        st.header("📊 전사 사고 대장 통합 뷰어")
        st.caption("구글 스프레드시트에 접속할 필요 없이, 웹에서 전체 데이터를 확인하고 직접 수정(결재)할 수 있습니다.")
        
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=500, hide_index=True)
        
        if st.button("💾 데이터베이스 직접 저장 (결재 정보 업데이트)", type="primary"):
            for idx in edited_df.index:
                d1, d2, d3, d4 = [str(edited_df.loc[idx, c]).strip().upper() for c in ["사고보고서_제출", "재발방지대책_제출", "산재표_제출", "합의서_작성"]]
                edited_df.loc[idx, "진행상태"] = "종결" if (d1=="O" and d2=="O" and d3=="O" and d4 in ["O", "N/A"]) else "진행중"
            
            conn.update(data=edited_df)
            st.success("✅ 구글 스프레드시트에 동기화 완료!")
            st.rerun()

    elif sub_menu == "🖨️ 최종 보고서 출력":
        st.header("🖨️ 상황도 작성 및 보고서 최종 인쇄")
        if df.empty:
            st.info("출력할 데이터가 없습니다.")
        else:
            select_print_idx = st.selectbox("출력할 보고서 선택", df.index, format_func=lambda x: f"[{df.loc[x, 'ID']}] {df.loc[x, '현장명']} ({df.loc[x, '진행상태']})")
            row = df.loc[select_print_idx]
            
            st.markdown("### 📷 출력용 현장 사진 구성 (갑지 뒷면용)")
            up_col1, up_col2 = st.columns(2)
            files_situ = up_col1.file_uploader("🖼️ 상황도 사진", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            files_injury = up_col2.file_uploader("🩹 재해정도 사진", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

            if st.button("🖨️ A4 보고서 생성 및 인쇄 다운로드", type="primary", use_container_width=True):
                s_color = "blue" if row.get('진행상태', '') == "종결" else "red"

                html_1 = ''.join([
                    '<table class="gapji-table" style="width:100%; table-layout:fixed; border-collapse:collapse; border:2px solid #000;">',
                    '<tr><td colspan="8" style="font-size: 26px; font-weight: bold; border:none; padding-bottom: 15px;">재해발생보고서</td></tr>',
                    '<tr><td colspan="3" style="font-size: 32px; font-weight: bold; border:none; text-align:left; vertical-align:bottom; padding-left:10px;">신건설(주)</td>',
                    '<td colspan="5" style="border:none; text-align:right; white-space:nowrap; vertical-align:bottom; padding-bottom:5px; padding-right:5px;">',
                    '<table border="1" style="display:inline-table; border-collapse:collapse; font-size:12px; margin-right:8px; text-align:center; width:260px; table-layout:fixed;">',
                    '<tr><td rowspan="2" class="gapji-header" style="width:30px; padding:4px;">현<br>장</td><td class="gapji-header" style="padding:4px;">안전담당</td><td class="gapji-header" style="padding:4px;">공사/공무</td><td class="gapji-header" style="padding:4px;">현장소장</td></tr>',
                    f'<tr><td style="height:50px; color:blue; padding:0;">{get_sign(row.get("안전담당", ""))}</td><td style="color:blue; padding:0;">{get_sign(row.get("공사/공무 담당", ""))}</td><td style="color:red; padding:0;">{get_sign(row.get("현장소장", ""))}</td></tr></table>',
                    '<table border="1" style="display:inline-table; border-collapse:collapse; font-size:12px; text-align:center; width:320px; table-layout:fixed;">',
                    '<tr><td rowspan="2" class="gapji-header" style="width:30px; padding:4px;">본<br>사</td><td class="gapji-header" style="padding:4px;">안전팀</td><td class="gapji-header" style="padding:4px;">공사팀</td><td class="gapji-header" style="padding:4px;">PM</td><td class="gapji-header" style="padding:4px;">대표이사</td></tr>',
                    f'<tr><td style="height:50px; color:blue; padding:0;">{get_sign(row.get("안전팀", ""))}</td><td style="color:blue; padding:0;">{get_sign(row.get("공사팀", ""))}</td><td style="color:blue; padding:0;">{get_sign(row.get("PM", ""))}</td><td style="color:red; padding:0;">{get_sign(row.get("대표이사", ""))}</td></tr></table>',
                    '</td></tr>',
                    f'<tr><td class="gapji-header" style="width:12%;">현장명</td><td colspan="3" style="width:38%; font-weight:bold;">{row.get("현장명", "")}</td><td class="gapji-header" style="width:12%;">사고장소</td><td colspan="3" style="width:38%;">{row.get("사고장소", "")}</td></tr>',
                    f'<tr><td class="gapji-header" style="height:60px;">사고경위</td><td colspan="7" style="text-align:left; padding:8px;">{row.get("사고경위", "")}</td></tr>',
                    f'<tr><td class="gapji-header">사고원인</td><td colspan="7" style="text-align:left; padding:8px;">{row.get("사고원인", "")}</td></tr>',
                    f'<tr><td rowspan="3" class="gapji-header">피재자</td><td class="gapji-header">성명</td><td style="width:13%;">{row.get("피재자", "")}</td><td class="gapji-header" style="width:12%;">생년월일</td><td style="width:13%;">{row.get("생년월일", "")}</td><td class="gapji-header" style="width:12%;">채용일자</td><td colspan="2">{row.get("채용일자", "")}</td></tr>',
                    f'<tr><td class="gapji-header">소속/직급</td><td>{row.get("소속_직급", "")}</td><td class="gapji-header">직종</td><td>{row.get("직종", "")}</td><td class="gapji-header">채용기간</td><td colspan="2">상세관리</td></tr>',
                    f'<tr><td class="gapji-header">주소</td><td colspan="3">사내 대장 전산 확인</td><td class="gapji-header">국적</td><td colspan="2">{row.get("국적_체류코드", "")}</td></tr>',
                    f'<tr><td rowspan="3" class="gapji-header">재발방지</td><td class="gapji-header">기술적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("기술적대책", "")}</td></tr>',
                    f'<tr><td class="gapji-header">관리적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("관리적대책", "")}</td></tr>',
                    f'<tr><td class="gapji-header">교육적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("교육적대책", "")}</td></tr>',
                    '<tr><td colspan="8" style="padding:0; border:none;">',
                    '<table style="width:100%; border-collapse:collapse; text-align:center; margin-top:10px; margin-bottom:10px; table-layout:fixed;">',
                    '<tr><td colspan="5" class="gapji-header">사고 서류 제출 현황</td></tr>',
                    '<tr><td class="gapji-header">사고보고서 제출</td><td class="gapji-header">재발방지대책</td><td class="gapji-header">산재표 제출</td><td class="gapji-header">합의서 작성</td><td class="gapji-header">진행상태</td></tr>',
                    f'<tr><td>{row.get("사고보고서_제출", "O")}</td><td>{row.get("재발방지대책_제출", "X")}</td><td>{row.get("산재표_제출", "X")}</td><td>{row.get("합의서_작성", "X")}</td><td style="font-weight:bold; color:{s_color};">{row.get("진행상태", "진행중")}</td></tr>',
                    '</table></td></tr></table>'
                ])

                html_2 = ''.join([
                    '<table class="gapji-table" style="width:100%; table-layout:fixed; border-collapse:collapse; border:2px solid #000;">',
                    '<tr><td colspan="2" style="font-size:26px; font-weight:bold; border:none; padding-bottom:20px;">사고현장 상황도</td></tr>',
                    build_grid(process_images_for_html(files_situ, "400px"), "사진 1<br>사고상황도"),
                    build_grid(process_images_for_html(files_injury, "400px"), "사진 2<br>재해정도"),
                    '</table>'
                ])

                final_print_html = re.sub(r'>\s+<', '><', html_1 + "<br><br>" + html_2)
                st.markdown(final_print_html, unsafe_allow_html=True)

                standalone_html = f"""
                <!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>보고서 인쇄</title>
                <style>
                    @page {{ size: A4 portrait; margin: 10mm; }} 
                    * {{ box-sizing: border-box; }}
                    body {{ background: #fff; width: 100%; margin: 0; padding: 0; font-family: 'Malgun Gothic', sans-serif; }} 
                    .gapji-table {{ width: 100%; max-width: 100%; border-collapse: collapse; font-size: 13px; border: 2px solid #000; margin-bottom: 20px; table-layout: fixed; word-break: break-word; }} 
                    .gapji-table th, .gapji-table td {{ border: 1px solid #000; padding: 6px; text-align: center; vertical-align: middle; }} 
                    .gapji-header {{ background-color: #f0f0f0 !important; font-weight: bold; -webkit-print-color-adjust: exact; print-color-adjust: exact; }} 
                    .grid-photo {{ width: 100%; height: 400px; object-fit: contain; display: block; margin: 0 auto; }}
                    .photo-blank {{ height: 400px; display: flex; justify-content: center; align-items: center; color: #999; font-size: 14px; background-color: #fafafa; }}
                    
                    /* 인쇄 시 줄 짤림 방지 핵심 CSS */
                    @media print {{
                        tr, td, th {{ page-break-inside: avoid !important; break-inside: avoid !important; }}
                        table {{ page-break-inside: auto !important; break-inside: auto !important; }}
                    }}
                </style>
                </head><body onload="window.print()">{html_1}<br>{html_2}</body></html>
                """
                b64_html = base64.b64encode(standalone_html.encode('utf-8')).decode('utf-8')
                st.markdown(f'<div style="text-align:center;"><a href="data:text/html;base64,{b64_html}" download="보고서.html" style="padding:15px; background-color:#4CAF50; color:white; text-decoration:none; border-radius:8px; font-weight:bold;">🖨️ 인쇄용 파일 다운로드</a></div>', unsafe_allow_html=True)

else:
    st.header(f"🚧 {main_menu} 모듈")
    st.info("현재 기획 및 개발 진행 중입니다.")