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
    df = conn.read(ttl=0)
    df = df.fillna("") # 빈칸(NaN) 에러 방지
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

# 3. 🌟 [잘림 완전 방지] 스나이퍼 프린트 CSS 기법 적용
st.markdown("""
<style>
@media print {
    /* 웹페이지의 모든 기본 요소를 투명하게 숨김 */
    body * {
        visibility: hidden !important;
    }
    
    /* 오직 우리가 만든 보고서(printable-report)와 그 안의 내용만 보이게 설정 */
    #printable-report, #printable-report * {
        visibility: visible !important;
    }
    
    /* 보고서를 화면 맨 위, 왼쪽 끝으로 강제 고정하여 잘림 현상 원천 차단 */
    #printable-report {
        position: absolute !important;
        left: 0 !important;
        top: 0 !important;
        width: 100% !important;
        height: auto !important;
    }
    
    html, body {
        height: auto !important;
        overflow: visible !important;
    }
    
    .page-break { 
        page-break-before: always !important; 
        break-before: page !important; 
    }
    @page { size: A4; margin: 10mm; }
}

.gapji-table { width: 100% !important; border-collapse: collapse !important; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; color: #000; border: 2px solid #000 !important; margin-bottom: 20px; }
.gapji-table th, .gapji-table td { border: 1px solid #000 !important; padding: 6px !important; text-align: center; vertical-align: middle; }
.gapji-header { background-color: #f0f0f0 !important; font-weight: bold; }
.grid-photo { width: 100%; height: 280px; object-fit: contain; background-color: #fafafa; display: block; margin: 0 auto; }
.photo-blank { height: 280px; display: flex; justify-content: center; align-items: center; color: #999; font-size: 12px; background-color: #fafafa; }
</style>
""", unsafe_allow_html=True)

st.title("🚨 신건설 통합 관리 및 결재 시스템")
approvers = ["안전담당", "공사/공무 담당", "현장소장", "안전팀", "공사팀", "PM", "대표이사"]
menu = st.tabs(["📝 사고보고서 등록", "📊 결재 처리", "🖨️ 보고서 출력"])

with menu[0]:
    with st.form("input_form"):
        c1, c2, c3 = st.columns(3)
        site_name = c1.text_input("현장명", value="이천부발현장")
        accident_date = c2.date_input("사고일자", value=date.today())
        accident_time = c3.time_input("사고시간", value=datetime.time(10, 0))
        
        accident_place = st.text_input("사고장소", value="A1구간 지하1층")
        work_detail = st.text_input("작업환경", value="거푸집 설치 작업 중")
        accident_cause = st.text_input("사고원인", value="박리제 도포된 알폼 슬라브, 벽체 철근 미보양 상태")
        accident_type = st.selectbox("사고발생형태", ["떨어짐", "낙하·비래(맞음)", "넘어짐", "부딪힘/찔림", "절단·베임", "기타"], index=3)
        injury_degree = st.text_input("상해피해정도 진단서", value="주상병 : 좌측 제12 늑골 골절, 폐쇄성")
        
        p1, p2, p3 = st.columns(3)
        p_name_ko = p1.text_input("피재자 성명", value="김개똥")
        p_birth_code = p2.text_input("주민번호 앞자리", value="630310-1")
        p_team = p3.text_input("소속/직급", value="수도인력")
        
        p4, p5, p6 = st.columns(3)
        p_gongjong = p4.text_input("직종", value="보통인부")
        p_hire_date = p5.date_input("채용일자", value=date(2024, 11, 5))
        p_nation = p6.text_input("국적/체류코드", value="베트남 / F-6")
        
        prevent_tech = st.text_input("기술적 대책", value="1. 철근 근로자 찔림방지 방호조치 철저")
        prevent_admin = st.text_input("관리적 대책", value="")
        prevent_edu = st.text_input("교육적 대책", value="")
        
        formatted_date_time = f"{accident_date.strftime('%y.%m.%d')} {accident_time.strftime('%H:%M')}분경"
        auto_detail = f"{formatted_date_time} / {accident_place}에서 / 소속 {p_team}의 {p_gongjong}인 피재자 {p_name_ko}({p_birth_code})이 {work_detail}, {accident_cause} 요인에 의하여 인지하지 못하고 몸의 균형을 잃으면서 [{accident_type}] 사고가 발생함."
        final_detail = st.text_area("사고경위 최종 확인", value=auto_detail, height=100)

        if st.form_submit_button("💾 시트에 데이터 추가하기"):
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
            st.success("등록 완료! 페이지를 새로고침하세요.")

with menu[1]:
    st.header("📊 전사 사고 대장 및 7인 실시간 결재 현황")
    edited_df = st.data_editor(df, use_container_width=True)
    if st.button("💾 변경된 사항 저장"):
        conn.update(data=edited_df)
        st.success("저장 완료!")
        st.rerun()

with menu[2]:
    st.header("🖨️ 보고서 출력")
    if df.empty:
        st.info("출력할 데이터가 없습니다.")
    else:
        select_print_idx = st.selectbox("출력할 보고서 선택", df.index, format_func=lambda x: f"[{df.loc[x, 'ID']}] {df.loc[x, '현장명']} ({df.loc[x, '날짜']})")
        row = df.loc[select_print_idx]
        
        up_col1, up_col2 = st.columns(2)
        files_situ = up_col1.file_uploader("🖼️ 상황도 사진", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        files_injury = up_col2.file_uploader("🩹 재해정도 사진", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

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

        if st.button("🖨️ 보고서 서식 완성하기 (클릭 후 Ctrl+P)", type="primary", use_container_width=True):
            
            # 🌟 [버그 해결] "승인" 또는 "확인" 이라는 글자가 있으면 도장을 찍도록 수정
            def get_sign(val):
                val_str = str(val).strip()
                if val_str in ["승인", "확인"]:
                    return "<b>[확인]<br><span style='font-size:9px; color:gray;'>signed</span></b>"
                return ""
            
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
                f'<tr><td class="gapji-header">사고일시</td><td colspan="2">{str(row.get("날짜", "")).split(" ")[0]}</td><td>{str(row.get("날짜", "")).split(" ")[1] if len(str(row.get("날짜", "")).split(" ")) > 1 else ""}</td><td class="gapji-header">작업환경</td><td colspan="3">{row.get("작업환경", "")}</td></tr>',
                f'<tr><td class="gapji-header" style="height:60px;">사고경위</td><td colspan="7" style="text-align:left; padding:8px;">{row.get("사고경위", "")}</td></tr>',
                f'<tr><td class="gapji-header">사고원인</td><td colspan="7" style="text-align:left; padding:8px;">{row.get("사고원인", "")}</td></tr>',
                '<tr><td class="gapji-header">원청보고</td><td>사후구두보고</td><td class="gapji-header">보고일시</td><td colspan="2">24.12.20 18시 20분</td><td class="gapji-header">보고방법</td><td colspan="2">전화보고</td></tr>',
                f'<tr><td class="gapji-header">피해정도</td><td colspan="7" style="text-align:left; padding:8px;">{row.get("상해피해정도", "")}</td></tr>',
                f'<tr><td class="gapji-header">교육사항</td><td class="gapji-header">정기교육</td><td>실시</td><td class="gapji-header">특별교육</td><td>실시</td><td class="gapji-header">사고발생형태</td><td colspan="2">{row.get("사고유형", "")}</td></tr>',
                f'<tr><td rowspan="3" class="gapji-header">피재자</td><td class="gapji-header">성명</td><td>{row.get("피재자", "")}</td><td class="gapji-header">주민번호</td><td>{row.get("주민번호_앞자리", "")}</td><td class="gapji-header">채용일자</td><td colspan="2">{row.get("채용일자", "")}</td></tr>',
                f'<tr><td class="gapji-header">소속/직급</td><td>{row.get("소속_직급", "")}</td><td class="gapji-header">직종</td><td>{row.get("직종", "")}</td><td class="gapji-header">채용기간</td><td colspan="2">상세관리</td></tr>',
                f'<tr><td class="gapji-header">주소</td><td colspan="3">사내 대장 전산 확인</td><td class="gapji-header">국적</td><td colspan="2">{row.get("국적_체류코드", "")}</td></tr>',
                '<tr><td rowspan="2" class="gapji-header">목격자</td><td class="gapji-header">성명</td><td colspan="2">홍길동</td><td class="gapji-header">주민번호</td><td colspan="3">630310-1</td></tr>',
                '<tr><td class="gapji-header">직종</td><td colspan="2"></td><td class="gapji-header">주소</td><td colspan="3"></td></tr>',
                f'<tr><td rowspan="3" class="gapji-header">재발방지</td><td class="gapji-header">기술적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("기술적대책", "")}</td></tr>',
                f'<tr><td class="gapji-header">관리적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("관리적대책", "")}</td></tr>',
                f'<tr><td class="gapji-header">교육적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("교육적대책", "")}</td></tr>',
                '<tr><td class="gapji-header">첨부서류</td><td colspan="7" style="text-align:left; padding-left:5px;">추후 진단서 첨부 예정</td></tr>',
                '</table>'
            ])

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

            # 🌟 [잘림 방지 핵심 로직] 하나의 거대한 #printable-report 컨테이너로 묶어서 출력
            final_html = f"""
            <div id="printable-report">
                {html_1}
                <div class="page-break"></div>
                {html_2}
            </div>
            """
            
            st.markdown(final_html.replace('\n', ''), unsafe_allow_html=True)