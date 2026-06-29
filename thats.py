import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import base64
import datetime
from datetime import date, datetime as dt

# 1. 페이지 기본 설정
st.set_page_config(page_title="신건설 통합 결재 관리 시스템", layout="wide")

# 2. 구글 스프레드시트 실시간 연동
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 잦은 화면 새로고침 시 API 제한 방지를 위해 ttl 설정 권장 (필요시 ttl=0 유지)
    df = conn.read(ttl=5) 
    df = df.fillna("")
except Exception as e:
    st.error(f"구글 시트 연동 실패: {e}")
    st.stop()

required_cols = [
    "ID", "날짜", "현장명", "사고장소", "사고경위", "작업환경", "사고원인", 
    "사고유형", "상해피해정도", "피재자", "주민번호_앞자리", "소속_직급", 
    "직종", "채용일자", "국적_체류코드", "기술적대책", "관리적대책", "교육적대책",
    "안전담당", "공사/공무 담당", "현장소장", "안전팀", "공사팀", "PM", "대표이사"
]
for col in required_cols:
    if col not in df.columns:
        df[col] = "대기"

# 3. Streamlit 화면 미리보기용 CSS (모바일 반응형 포함)
st.markdown("""
<style>
/* 미리보기 테이블 */
.gapji-table { width: 100% !important; border-collapse: collapse !important; font-family: 'Malgun Gothic', sans-serif; font-size: 14px; color: #000; border: 2px solid #000 !important; margin-bottom: 20px; }
.gapji-table th, .gapji-table td { border: 1px solid #000 !important; padding: 7px !important; text-align: center; vertical-align: middle; }
.gapji-header { background-color: #f0f0f0 !important; font-weight: bold; }
.grid-photo { width: 100%; height: 280px; object-fit: contain; background-color: #fafafa; display: block; margin: 0 auto; }
.photo-blank { height: 280px; display: flex; justify-content: center; align-items: center; color: #999; font-size: 13px; background-color: #fafafa; }

/* 입력 필드 여백 축소로 가독성 향상 */
div[data-testid="stForm"] { padding: 1rem; }
.stTextInput, .stDateInput, .stTimeInput, .stSelectbox { margin-bottom: -15px; }
</style>
""", unsafe_allow_html=True)

st.title("🚨 신건설 통합 관리 및 결재 시스템")
approvers = ["안전담당", "공사/공무 담당", "현장소장", "안전팀", "공사팀", "PM", "대표이사"]

# 기존 3탭 구조 복구
menu = st.tabs(["📝 사고보고서 등록", "📊 결재 처리", "🖨️ 보고서 출력"])

# ==========================================
# 탭 1: 사고보고서 등록 (화면 2등분 & 문구 최적화 적용)
# ==========================================
with menu[0]:
    # 모바일에서는 자동으로 상하 배치, PC에서는 좌(4) 우(6) 분할
    col_input, col_preview = st.columns([4, 6])
    
    with col_input:
        st.subheader("📝 사고 정보 입력")
        # 입력 중 새로고침을 방지하고 한 번에 저장하기 위해 form 사용
        with st.form("input_form"):
            with st.expander("📍 현장 및 일시", expanded=True):
                c1, c2 = st.columns(2)
                site_name = c1.text_input("현장명", value="이천부발현장")
                accident_date = c2.date_input("사고일자", value=date.today())
                c3, c4 = st.columns(2)
                accident_time = c3.time_input("사고시간", value=datetime.time(10, 0))
                accident_place = c4.text_input("사고장소", value="A1구간 지하1층")
            
            with st.expander("👤 피재자 정보", expanded=True):
                p1, p2 = st.columns(2)
                p_name_ko = p1.text_input("성명", value="김개똥")
                p_birth_code = p2.text_input("주민번호 앞자리", value="630310-1")
                
                p3, p4 = st.columns(2)
                p_team = p3.text_input("소속/직급", value="수도인력")
                p_gongjong = p4.text_input("직종", value="보통인부")
                
                p5, p6 = st.columns(2)
                p_hire_date = p5.date_input("채용일자", value=date(2024, 11, 5))
                p_nation = p6.text_input("국적/체류코드", value="베트남 / F-6")
            
            with st.expander("🎬 사고 내용", expanded=True):
                work_detail = st.text_input("작업환경", value="거푸집 설치 작업")
                accident_cause = st.text_input("사고원인", value="박리제 도포된 알폼 슬라브 미보양 상태에서 미끄러짐")
                accident_type = st.selectbox("사고발생형태", ["떨어짐", "낙하·비래(맞음)", "넘어짐", "부딪힘/찔림", "절단·베임", "기타"], index=2)
                injury_degree = st.text_input("상해피해정도 (진단서)", value="주상병 : 좌측 제12 늑골 골절, 폐쇄성")
            
            # 최초 보고서에 집중하되 칸은 남겨둠
            with st.expander("🛡️ 재발방지대책 (선택)"):
                prevent_tech = st.text_input("기술적 대책", value="철근 근로자 찔림방지 방호조치 철저")
                prevent_admin = st.text_input("관리적 대책", value="")
                prevent_edu = st.text_input("교육적 대책", value="")

            # 문구 최적화: '조사', '소속', '피재자', '요인에 의하여' 등 군더더기 제거
            formatted_date_time = f"{accident_date.strftime('%y.%m.%d')} {accident_time.strftime('%H:%M')}분경"
            auto_detail = f"{formatted_date_time} / {accident_place}에서 / {p_team} {p_gongjong} {p_name_ko}({p_birth_code})이(가) {work_detail} 중, {accident_cause} 발생하여 [{accident_type}] 사고가 발생함."
            
            final_detail = st.text_area("사고경위 최종 확인 (수정 가능)", value=auto_detail, height=90)

            submitted = st.form_submit_button("💾 시트에 데이터 추가하기", type="primary", use_container_width=True)
            if submitted:
                new_id = int(df["ID"].max()) + 1 if not df.empty and pd.to_numeric(df["ID"], errors='coerce').notna().any() else 1
                new_row = pd.DataFrame([{
                    "ID": new_id, "날짜": formatted_date_time, "현장명": site_name, "사고장소": accident_place,
                    "사고경위": final_detail, "작업환경": work_detail, "사고원인": accident_cause,
                    "사고유형": accident_type, "상해피해정도": injury_degree, "피재자": p_name_ko,
                    "주민번호_앞자리": p_birth_code, "소속_직급": p_team, "직종": p_gongjong,
                    "채용일자": str(p_hire_date), "국적_체류코드": p_nation, "기술적대책": prevent_tech,
                    "관리적대책": prevent_admin, "교육적대책": prevent_edu,
                    **{app: "대기" for app in approvers}
                }])
                conn.update(data=pd.concat([df, new_row], ignore_index=True))
                st.success("✅ 등록 완료! 우측 미리보기 탭이 업데이트됩니다.")
                st.rerun()

    with col_preview:
        st.subheader("👀 실시간 작성 내용 확인")
        # 폼 입력값을 실시간으로 반영하여 간이 갑지 형태로 보여줌
        preview_html = f"""
        <table class="gapji-table">
            <tr><td colspan="4" style="font-size: 20px; font-weight: bold; background-color:#fff;">재해발생보고서 (임시 미리보기)</td></tr>
            <tr><td class="gapji-header" style="width:20%;">현장명</td><td style="width:30%;">{site_name}</td>
                <td class="gapji-header" style="width:20%;">사고일시</td><td style="width:30%;">{formatted_date_time}</td></tr>
            <tr><td class="gapji-header">사고장소</td><td>{accident_place}</td>
                <td class="gapji-header">작업환경</td><td>{work_detail}</td></tr>
            <tr><td class="gapji-header">피재자</td><td>{p_team} {p_gongjong} {p_name_ko}</td>
                <td class="gapji-header">사고형태</td><td>{accident_type}</td></tr>
            <tr><td class="gapji-header">사고경위</td><td colspan="3" style="text-align:left;">{final_detail}</td></tr>
        </table>
        """
        st.markdown(preview_html, unsafe_allow_html=True)
        st.info("💡 좌측 폼에서 '시트에 데이터 추가하기'를 누르면 데이터베이스에 저장되며, [🖨️ 보고서 출력] 탭에서 사진과 함께 공식 양식 출력이 가능합니다.")

# ==========================================
# 탭 2: 결재 처리 (기존 기능 100% 유지)
# ==========================================
with menu[1]:
    st.header("📊 전사 사고 대장 및 실시간 결재 현황")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 변경된 사항 저장"):
        conn.update(data=edited_df)
        st.success("저장 완료!")
        st.rerun()

# ==========================================
# 탭 3: 보고서 출력 (사진 업로드 및 HTML 인쇄 기능 100% 복구)
# ==========================================
with menu[2]:
    st.header("🖨️ 보고서 출력 및 사진 첨부")
    if df.empty:
        st.info("출력할 데이터가 없습니다.")
    else:
        select_print_idx = st.selectbox("출력할 보고서 선택", df.index, format_func=lambda x: f"[{df.loc[x, 'ID']}] {df.loc[x, '현장명']} ({df.loc[x, '날짜']})")
        row = df.loc[select_print_idx]
        
        up_col1, up_col2 = st.columns(2)
        files_situ = up_col1.file_uploader("🖼️ 상황도 사진 (사진 1)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        files_injury = up_col2.file_uploader("🩹 재해정도 사진 (사진 2)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

        def process_images(uploaded_files):
            tags = []
            for f in uploaded_files:
                encoded = base64.b64encode(f.getvalue()).decode()
                tags.append(f'<img src="data:image/png;base64,{encoded}" class="grid-photo">')
            return tags

        def build_grid(tags, label):
            clean_label = label.replace('<br>', ' ')
            if not tags:
                return f'<tr><td class="gapji-header">{label}</td><td style="padding:6px;"><div class="photo-blank">{clean_label} 사진 미등록</div></td></tr>'
            inner = '<table width="100%" border="0" cellpadding="0" cellspacing="0" style="table-layout:fixed; height:100%;">'
            for i in range((len(tags) + 1) // 2):
                c1 = tags[i*2]
                c2 = tags[i*2+1] if (i*2+1) < len(tags) else '<div class="photo-blank">대기</div>'
                bb = 'border-bottom: 1px solid #000;' if i < ((len(tags)+1)//2 - 1) else ''
                inner += f'<tr><td style="width:50%; border-right:1px solid #000; {bb} padding:6px;">{c1}</td><td style="width:50%; {bb} padding:6px;">{c2}</td></tr>'
            inner += '</table>'
            return f'<tr><td class="gapji-header">{label}</td><td style="padding:0;">{inner}</td></tr>'

        if st.button("🖨️ 최종 보고서 생성 및 인쇄 준비", type="primary", use_container_width=True):
            def get_sign(val):
                if str(val).strip() in ["승인", "확인"]:
                    return "<b>[확인]<br><span style='font-size:9px; color:gray;'>signed</span></b>"
                return ""
            
            # 갑지 HTML (문구 간소화 로직 반영)
            html_1 = ''.join([
                '<table class="gapji-table">',
                '<tr><td colspan="8" style="font-size: 26px; font-weight: bold; border:none; padding-bottom: 15px;">재해발생보고서</td></tr>',
                '<tr><td colspan="2" style="font-size: 32px; font-weight: bold; border:none; text-align:left;">신건설(주)</td>',
                '<td colspan="6" style="border:none; text-align:right;">',
                '<table border="1" style="display:inline-block; border-collapse:collapse; font-size:11px; margin-right:5px; text-align:center;">',
                '<tr><td rowspan="2" class="gapji-header" style="width:20px;">현<br>장</td><td class="gapji-header" style="width:55px;">안전담당</td><td class="gapji-header" style="width:55px;">공사/공무</td><td class="gapji-header" style="width:55px;">현장소장</td></tr>',
                f'<tr><td style="height:42px; color:blue;">{get_sign(row.get("안전담당", ""))}</td><td style="color:blue;">{get_sign(row.get("공사/공무 담당", ""))}</td><td style="color:red;">{get_sign(row.get("현장소장", ""))}</td></tr></table>',
                '<table border="1" style="display:inline-block; border-collapse:collapse; font-size:11px; text-align:center;">',
                '<tr><td rowspan="2" class="gapji-header" style="width:20px;">본<br>사</td><td class="gapji-header" style="width:55px;">안전팀</td><td class="gapji-header" style="width:55px;">공사팀</td><td class="gapji-header" style="width:55px;">PM</td><td class="gapji-header" style="width:55px;">대표이사</td></tr>',
                f'<tr><td style="height:42px; color:blue;">{get_sign(row.get("안전팀", ""))}</td><td style="color:blue;">{get_sign(row.get("공사팀", ""))}</td><td style="color:blue;">{get_sign(row.get("PM", ""))}</td><td style="color:red;">{get_sign(row.get("대표이사", ""))}</td></tr></table>',
                '</td></tr>',
                f'<tr><td class="gapji-header" style="width:12%;">현장명</td><td colspan="3" style="width:38%; font-weight:bold;">{row.get("현장명", "")}</td><td class="gapji-header" style="width:12%;">사고장소</td><td colspan="3" style="width:38%;">{row.get("사고장소", "")}</td></tr>',
                f'<tr><td class="gapji-header">사고일시</td><td colspan="3">{row.get("날짜", "")}</td><td class="gapji-header">작업환경</td><td colspan="3">{row.get("작업환경", "")}</td></tr>',
                f'<tr><td class="gapji-header" style="height:60px;">사고경위</td><td colspan="7" style="text-align:left; padding:8px;">{row.get("사고경위", "")}</td></tr>',
                f'<tr><td class="gapji-header">사고원인</td><td colspan="7" style="text-align:left; padding:8px;">{row.get("사고원인", "")}</td></tr>',
                f'<tr><td class="gapji-header">피해정도</td><td colspan="7" style="text-align:left; padding:8px;">{row.get("상해피해정도", "")}</td></tr>',
                f'<tr><td class="gapji-header">교육사항</td><td class="gapji-header">정기교육</td><td>실시</td><td class="gapji-header">특별교육</td><td>실시</td><td class="gapji-header">사고발생형태</td><td colspan="2">{row.get("사고유형", "")}</td></tr>',
                
                # 피재자 섹션 양식 유지 (불필요한 "조사" 등 제외)
                f'<tr><td rowspan="3" class="gapji-header">피재자</td><td class="gapji-header">성명</td><td>{row.get("피재자", "")}</td><td class="gapji-header">주민번호</td><td>{row.get("주민번호_앞자리", "")}</td><td class="gapji-header">채용일자</td><td colspan="2">{row.get("채용일자", "")}</td></tr>',
                f'<tr><td class="gapji-header">소속/직급</td><td>{row.get("소속_직급", "")}</td><td class="gapji-header">직종</td><td>{row.get("직종", "")}</td><td class="gapji-header">채용기간</td><td colspan="2">상세관리</td></tr>',
                f'<tr><td class="gapji-header">주소</td><td colspan="3">사내 대장 전산 확인</td><td class="gapji-header">국적</td><td colspan="2">{row.get("국적_체류코드", "")}</td></tr>',
                
                # 재발방지대책 유지
                f'<tr><td rowspan="3" class="gapji-header">재발방지</td><td class="gapji-header">기술적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("기술적대책", "")}</td></tr>',
                f'<tr><td class="gapji-header">관리적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("관리적대책", "")}</td></tr>',
                f'<tr><td class="gapji-header">교육적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("교육적대책", "")}</td></tr>',
                '<tr><td class="gapji-header">첨부서류</td><td colspan="7" style="text-align:left; padding-left:5px;">추후 진단서 첨부 예정</td></tr>',
                '</table>'
            ])

            # 을지 (사진 및 상황도) HTML
            html_2 = ''.join([
                '<table class="gapji-table" style="table-layout:fixed; width:100%;">',
                '<colgroup><col style="width:15%;"><col style="width:85%;"></colgroup>',
                '<tr><td colspan="2" style="font-size:26px; font-weight:bold; border:none; padding-bottom:20px;">사고현장 상황도</td></tr>',
                f'<tr><td class="gapji-header">일 시</td><td style="text-align:left; font-weight:bold; padding-left:10px;">{row.get("날짜", "")}</td></tr>',
                f'<tr><td class="gapji-header">사고장소</td><td style="text-align:left; font-weight:bold; padding-left:10px;">{row.get("사고장소", "")}</td></tr>',
                f'<tr><td class="gapji-header">상황도 설명</td><td style="text-align:left; padding:10px; line-height:1.5;">{row.get("사고경위", "")}</td></tr>',
                build_grid(process_images(files_situ), "사진 1<br>사고상황도"),
                build_grid(process_images(files_injury), "사진 2<br>재해정도"),
                '</table>'
            ])

            # 스트림릿 내 미리보기
            st.markdown(html_1 + "<br><br>" + html_2, unsafe_allow_html=True)

            # 다운로드 및 자동 인쇄용 HTML 빌드
            standalone_html = f"""
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <title>재해발생보고서 인쇄</title>
                <style>
                    @page {{ size: A4; margin: 10mm 15mm; }}
                    body {{ margin: 0; padding: 0; background: #fff; }}
                    .gapji-table {{ width: 100%; border-collapse: collapse; font-family: 'Malgun Gothic', sans-serif; font-size: 14px; color: #000; border: 2px solid #000; margin-bottom: 20px; }}
                    .gapji-table th, .gapji-table td {{ border: 1px solid #000; padding: 7px; text-align: center; vertical-align: middle; }}
                    .gapji-header {{ background-color: #f0f0f0; font-weight: bold; }}
                    .grid-photo {{ width: 100%; height: 280px; object-fit: contain; background-color: #fafafa; display: block; margin: 0 auto; }}
                    .photo-blank {{ height: 280px; display: flex; justify-content: center; align-items: center; color: #999; font-size: 13px; background-color: #fafafa; }}
                    .page-break {{ page-break-before: always; }}
                </style>
            </head>
            <body onload="window.print()">
                {html_1}
                <div class="page-break"></div>
                {html_2}
            </body>
            </html>
            """
            
            b64_html = base64.b64encode(standalone_html.encode('utf-8')).decode('utf-8')
            download_link = f"""
            <div style="text-align: center; margin-top: 20px; margin-bottom: 40px;">
                <a href="data:text/html;base64,{b64_html}" download="재해발생보고서_{row.get('날짜', '')[:8]}.html" 
                   style="display: inline-block; padding: 15px 30px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 8px; font-size: 18px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                   🖨️ 여기를 클릭하여 완벽한 비율로 인쇄하기 (파일 다운로드)
                </a>
                <p style="margin-top: 10px; color: gray; font-size: 14px;">다운로드된 HTML 파일을 열면 여백 없이 깔끔하게 자동 인쇄 창이 뜹니다.</p>
            </div>
            """
            st.markdown(download_link, unsafe_allow_html=True)
            st.success("미리보기가 생성되었습니다. 확인 후 위 초록색 버튼을 눌러 인쇄 파일을 다운로드하세요.")