import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import base64
import datetime
from datetime import date, datetime as dt

# 1. 페이지 기본 설정 및 와이드 레이아웃 적용
st.set_page_config(page_title="신건설 통합 결재 관리 시스템", layout="wide")

# 2. 구글 스프레드시트 실시간 연동
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
except Exception as e:
    st.error(f"구글 시트 연동에 실패했습니다. 스트림릿 클라우드의 Secrets 설정과 시트 공유 권한을 확인해 주세요. 에러 내용: {e}")
    st.stop()

# 💡 [안전장치] 시트에 필수 열이 없는 경우 자동으로 초기화하여 에러 원천 차단
required_cols = [
    "ID", "날짜", "현장명", "사고장소", "사고경위", "작업환경", "사고원인", 
    "사고유형", "상해피해정도", "피재자", "주민번호_앞자리", "소속_직급", 
    "직종", "채용일자", "국적_체류코드", "기술적대책", "관리적대책", "교육적대책",
    "안전담당", "공사/공무 담당", "현장소장", "안전팀", "공사팀", "PM", "대표이사"
]
for col in required_cols:
    if col not in df.columns:
        df[col] = "대기"

# 3. 인쇄 전용 고해상도 CSS 및 표 정렬 양식 선언
st.markdown("""
<style>
@media print {
    header, footer, nav, [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stViewerBadge"] { 
        display: none !important; 
    }
    html, body, #root, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
        display: block !important; width: 100% !important; height: auto !important; overflow: visible !important; position: static !important; padding: 0 !important; margin: 0 !important; 
    }
    .element-container:not(:has(.print-area)) { display: none !important; }
    .page-break { page-break-before: always !important; break-before: page !important; }
    .print-area { width: 100% !important; }
    .gapji-table { font-size: 11px !important; line-height: 1.3 !important; }
    .gapji-table th, .gapji-table td { padding: 4px 5px !important; }
    * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
    body { background-color: white !important; }
    @page { size: A4; margin: 10mm 15mm; }
}

.gapji-table { width: 100% !important; border-collapse: collapse !important; margin-top: 0px !important; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; color: #000; border: 2px solid #000 !important; }
.gapji-table th, .gapji-table td { border: 1px solid #000 !important; padding: 6px !important; text-align: center; vertical-align: middle; word-wrap: break-word; }
.gapji-header { background-color: #f0f0f0 !important; font-weight: bold; border: 1px solid #000 !important; }

.grid-photo { width: 100%; height: 280px; object-fit: contain; background-color: #fafafa; display: block; margin: 0 auto; }
.photo-blank { height: 280px; display: flex; justify-content: center; align-items: center; color: #999; font-size: 12px; background-color: #fafafa; }
</style>
""", unsafe_allow_html=True)

st.title("🚨 신건설 통합 관리 및 결재 시스템")
st.subheader("실시간 데이터베이스 기반 사고보고서 오피스")

# 7인 결재 라인 정의
approvers = ["안전담당", "공사/공무 담당", "현장소장", "안전팀", "공사팀", "PM", "대표이사"]

# 상단 메뉴 구성
menu = st.tabs(["📝 사고보고서 신규 등록", "📊 결재 처리 및 데이터 관리", "🖨️ 보고서 갑지/상황도 출력"])

with menu[0]:
    st.header("📝 사고보고서 신규 데이터 추가")
    with st.form("accident_input_form"):
        c1, c2 = st.columns(2)
        site_name = c1.text_input("현장명", value="이천부발현장")
        accident_date = c2.date_input("사고일자", value=date.today())
        
        c3, c4 = st.columns(2)
        accident_time = c3.time_input("사고시간", value=datetime.time(10, 0))
        accident_place = c4.text_input("사고장소", value="A1구간 지하1층")
        
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
        
        st.write("**🛡️ 재발방지대책**")
        prevent_tech = st.text_input("기술적 대책", value="1. 철근 근로자 찔림방지 방호조치 철저")
        prevent_admin = st.text_input("관리적 대책", value="")
        prevent_edu = st.text_input("교육적 대책", value="")
        
        formatted_time = accident_time.strftime('%H:%M')
        auto_detail = (
            f"{accident_date.strftime('%y.%m.%d')} {formatted_time}분경 / {accident_place}에서 / "
            f"소속 {p_team}의 {p_gongjong}인 피재자 {p_name_ko}({p_birth_code})이 {work_detail}, "
            f"{accident_cause} 요인에 의하여 인지하지 못하고 몸의 균형을 잃으면서 [{accident_type}] 사고가 발생함."
        )
        final_detail = st.text_area("사고경위 최종 확인 (자동 완성)", value=auto_detail, height=100)

        if st.form_submit_button("💾 시트에 데이터 추가하기"):
            new_id = int(df["ID"].max()) + 1 if not df.empty and "ID" in df.columns and pd.notna(df["ID"].max()) else 1
            new_row = pd.DataFrame([{
                "ID": new_id, "날짜": str(accident_date), "현장명": site_name, "사고장소": accident_place,
                "사고경위": final_detail, "작업환경": work_detail, "사고원인": accident_cause,
                "사고유형": accident_type, "상해피해정도": injury_degree, "피재자": p_name_ko,
                "주민번호_앞자리": p_birth_code, "소속_직급": p_team, "직종": p_gongjong,
                "채용일자": str(p_hire_date), "국적_체류코드": p_nation, "기술적대책": prevent_tech,
                "관리적대책": prevent_admin, "교육적대책": prevent_edu,
                **{app: "대기" for app in approvers}
            }])
            conn.update(data=pd.concat([df, new_row], ignore_index=True))
            st.success(f"성공적으로 대장번호 [{new_id}]번 보고서가 등록되었습니다! 페이지를 새로고침하세요.")

with menu[1]:
    st.header("📊 전사 사고 대장 및 7인 실시간 결재 현황")
    st.markdown("💡 *표 안의 셀을 더블클릭하여 내용을 직접 수정하거나 결재 상태를 '대기'에서 '승인'으로 바꾸고 아래 저장 버튼을 누르세요.*")
    
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
    
    btn_col1, btn_col2 = st.columns(2)
    if btn_col1.button("💾 변경된 모든 수정사항 및 결재 데이터 시트에 동기화"):
        conn.update(data=edited_df)
        st.success("구글 스프레드시트에 실시간으로 완벽하게 저장되었습니다!")
        st.rerun()
        
    st.markdown("---")
    st.subheader("🗑️ 특정 보고서 취소 및 삭제")
    if not df.empty:
        delete_target = st.selectbox("삭제할 보고서 선택", df.index, format_func=lambda x: f"[{df.loc[x, 'ID']}] {df.loc[x, '현장명']} - {df.loc[x, '사고경위'][:25]}...")
        if st.button("❌ 선택한 사고 보고서 데이터베이스에서 영구 삭제", type="primary"):
            df_dropped = df.drop(delete_target)
            conn.update(data=df_dropped)
            st.warning("데이터가 정상적으로 삭제되었습니다.")
            st.rerun()

with menu[2]:
    st.header("🖨️ 최종 재해발생보고서 서식 출력 페이지")
    if df.empty:
        st.info("출력할 데이터가 없습니다. 먼저 보고서를 작성해 주세요.")
    else:
        select_print_idx = st.selectbox("출력 서식을 생성할 보고서 선택", df.index, format_func=lambda x: f"[{df.loc[x, 'ID']}] {df.loc[x, '현장명']} ({df.loc[x, '날짜']})")
        row = df.loc[select_print_idx]
        
        st.markdown("### 📸 사진 대지 추가 이미지 업로드 (출력 전용)")
        up_col1, up_col2 = st.columns(2)
        files_situ = up_col1.file_uploader("🖼️ 사진 1: 사고상황도 이미지 선택 (다중 가능)", type=["png", "jpg", "jpeg"], key="p_situ")
        files_injury = up_col2.file_uploader("🩹 사진 2: 재해정도 이미지 선택 (다중 가능)", type=["png", "jpg", "jpeg"], key="p_injury")

        def process_images_to_tags(uploaded_files):
            tags = []
            if uploaded_files:
                for f in uploaded_files:
                    f.seek(0)
                    encoded = base64.b64encode(f.read()).decode()
                    tags.append(f'<img src="data:image/png;base64,{encoded}" class="grid-photo">')
            return tags

        def build_html_grid_rows(tags, label_title):
            clean_label = label_title.replace('<br>', ' ')
            if not tags:
                return f'<tr><td class="gapji-header">{label_title}</td><td style="padding:6px;"><div class="photo-blank">{clean_label} 사진 미등록</div></td></tr>'
            inner_html = '<table width="100%" border="0" cellpadding="0" cellspacing="0" style="table-layout:fixed; height:100%;">'
            total_rows = (len(tags) + 1) // 2
            for i in range(total_rows):
                idx1 = i * 2
                idx2 = idx1 + 1
                cell1 = tags[idx1]
                cell2 = tags[idx2] if idx2 < len(tags) else '<div class="photo-blank">추가 사진 대기</div>'
                border_bottom = 'border-bottom: 1px solid #000;' if i < total_rows - 1 else ''
                inner_html += f'<tr><td style="width:50%; border-right:1px solid #000; {border_bottom} padding:6px;">{cell1}</td><td style="width:50%; {border_bottom} padding:6px;">{cell2}</td></tr>'
            inner_html += '</table>'
            return f'<tr><td class="gapji-header">{label_title}</td><td style="padding:0;">{inner_html}</td></tr>'

        if st.button("🖨️ 사고보고서 1장(갑지) 및 사진상황도 서식 인쇄 서식 완성", type="primary", use_container_width=True):
            tags_situ = process_images_to_tags(files_situ)
            tags_injury = process_images_to_tags(files_injury)
            grid_rows_situ = build_html_grid_rows(tags_situ, "사진 1<br>사고상황도")
            grid_rows_injury = build_html_grid_rows(tags_injury, "사진 2<br>재해정도")

            def get_sign(val):
                return f"<b>[확인]<br><span style='font-size:9px; color:gray;'>signed</span></b>" if val == "승인" else ""

            sign_s1 = get_sign(row.get("안전담당", "대기"))
            sign_s2 = get_sign(row.get("공사/공무 담당", "대기"))
            sign_s3 = get_sign(row.get("현장소장", "대기"))
            sign_h1 = get_sign(row.get("안전팀", "대기"))
            sign_h2 = get_sign(row.get("공사팀", "대기"))
            sign_h3 = get_sign(row.get("PM", "대기"))
            sign_h4 = get_sign(row.get("대표이사", "대기"))

            # 🛠️ 1페이지 갑지 결합 (들여쓰기 버그 원천 배제)
            html_content_1 = ''.join([
                '<div class="print-area">',
                '<table class="gapji-table" border="1" cellpadding="5" cellspacing="0">',
                '<tr><td colspan="8" style="border: none !important; font-size: 26px; font-weight: bold; text-align: center; padding-bottom: 15px;">재해발생보고서</td></tr>',
                '<tr><td colspan="2" style="border: none !important; text-align: left; padding-left: 10px; font-size: 32px; font-weight: bold; vertical-align: middle;">신건설(주)</td>',
                '<td colspan="6" style="border: none !important; text-align: right; vertical-align: middle; padding-bottom: 5px;">',
                '<div style="display: inline-flex; justify-content: flex-end; align-items: center; gap: 0px;">',
                '<table border="1" cellpadding="0" cellspacing="0" style="text-align: center; border-collapse: collapse; font-size: 11px; margin-right: 10px;">',
                '<tr><td rowspan="2" style="background-color: #f0f0f0; font-weight: bold; width: 20px; padding: 2px !important;">현<br>장</td><td style="width: 55px; background-color: #f0f0f0; padding: 2px !important;">안전<br>담당</td><td style="width: 55px; background-color: #f0f0f0; padding: 2px !important;">공사/<br>공무</td><td style="width: 55px; background-color: #f0f0f0; padding: 2px !important;">현장<br>소장</td></tr>',
                f'<tr><td style="height: 42px; color: blue; vertical-align: middle;">{sign_s1}</td><td style="height: 42px; color: blue; vertical-align: middle;">{sign_s2}</td><td style="height: 42px; color: red; vertical-align: middle;">{sign_s3}</td></tr>',
                '</table>',
                '<table border="1" cellpadding="0" cellspacing="0" style="text-align: center; border-collapse: collapse; font-size: 11px;">',
                '<tr><td rowspan="2" style="background-color: #f0f0f0; font-weight: bold; width: 20px; padding: 2px !important;">본<br>사</td><td style="width: 55px; background-color: #f0f0f0; padding: 2px !important;">안전팀</td><td style="width: 55px; background-color: #f0f0f0; padding: 2px !important;">공사팀</td><td style="width: 55px; background-color: #f0f0f0; padding: 2px !important;">PM</td><td style="width: 55px; background-color: #f0f0f0; padding: 2px !important;">대표<br>이사</td></tr>',
                f'<tr><td style="height: 42px; color: blue; vertical-align: middle;">{sign_h1}</td><td style="height: 42px; color: blue; vertical-align: middle;">{sign_h2}</td><td style="height: 42px; color: blue; vertical-align: middle;">{sign_h3}</td><td style="height: 42px; color: red; vertical-align: middle;">{sign_h4}</td></tr>',
                '</table></div></td></tr>',
                f'<tr><td class="gapji-header" style="width: 12%;">현장명</td><td colspan="3" style="width: 38%; font-weight: bold; font-size: 14px;">{row.get("현장명", "")}</td><td class="gapji-header" style="width: 12%;">사고장소</td><td colspan="3" style="width: 38%;">{row.get("사고장소", "")}</td></tr>',
                f'<tr><td class="gapji-header">사고일시</td><td colspan="2">{row.get("날짜", "")}</td><td>확인대기</td><td class="gapji-header">작업환경</td><td colspan="3">{row.get("작업환경", "")}</td></tr>',
                f'<tr><td class="gapji-header" style="height: 75px;">사고경위<br>(6하원칙에<br>의거작성)</td><td colspan="7" style="text-align: left; line-height: 1.5; padding: 8px;">{row.get("사고경위", "")}</td></tr>',
                f'<tr><td class="gapji-header" style="height: 40px;">사고원인</td><td colspan="7" style="text-align: left; padding: 8px;">{row.get("사고원인", "")}</td></tr>',
                '<tr><td class="gapji-header">원청보고</td><td>사후구두보고</td><td class="gapji-header">보고일시</td><td colspan="2">24.12.20 18시 20분경</td><td class="gapji-header">보고방법</td><td colspan="2">전화보고</td></tr>',
                f'<tr><td class="gapji-header" style="height: 45px;">상해<br>피해정도<br>진단서</td><td colspan="7" style="text-align: left; padding: 8px;">{row.get("상해피해정도", "")}</td></tr>',
                f'<tr><td class="gapji-header">教育사항</td><td class="gapji-header">정기교육</td><td>실시</td><td class="gapji-header">특별교육</td><td>실시</td><td class="gapji-header">사고발생형태</td><td colspan="2">{row.get("사고유형", "")}</td></tr>',
                f'<tr><td rowspan="3" class="gapji-header">피재자<br>인적사항</td><td class="gapji-header">성명</td><td>{row.get("피재자", "")}</td><td class="gapji-header">주민등록번호</td><td>{row.get("주민번호_앞자리", "")}</td><td class="gapji-header">채용일자</td><td colspan="2">{row.get("채용일자", "")}</td></tr>',
                f'<tr><td class="gapji-header">소속/직급</td><td>{row.get("소속_직급", "")}</td><td class="gapji-header">직종</td><td>{row.get("직종", "")}</td><td class="gapji-header">채용기간</td><td colspan="2">상세관리</td></tr>',
                f'<tr><td class="gapji-header">주소</td><td colspan="3">사내 대장 전산 확인</td><td class="gapji-header">국적/체류코드</td><td colspan="2">{row.get("국적_체류코드", "")}</td></tr>',
                '<tr><td rowspan="2" class="gapji-header">목격자<br>인적사항<br>(주변근로자)</td><td class="gapji-header">성명</td><td colspan="2">홍길동</td><td class="gapji-header">주민등록번호</td><td colspan="3">630310-1</td></tr>',
                '<tr><td class="gapji-header">직종</td><td colspan="2"></td><td class="gapji-header">주소</td><td colspan="3"></td></tr>',
                f'<tr><td rowspan="3" class="gapji-header">재발방지<br>대책</td><td class="gapji-header">기술적</td><td colspan="6" style="text-align: left; padding-left: 10px;">{row.get("기술적대책", "")}</td></tr>',
                f'<tr><td class="gapji-header" style="height: 25px;">관리적</td><td colspan="6" style="text-align: left; padding-left: 10px;">{row.get("관리적대책", "")}</td></tr>',
                f'<tr><td class="gapji-header" style="height: 25px;">교육적</td><td colspan="6" style="text-align: left; padding-left: 10px;">{row.get("교육적대책", "")}</td></tr>',
                '<tr><td class="gapji-header" style="height: 35px;">첨부서류</td><td colspan="7" style="text-align: left; padding-left: 10px;">추후 진단서 첨부 예정</td></tr>',
                '</table></div>'
            ])

            # 🛠️ 2페이지 상황도 결합 (15% / 85% 절대 비율 및 2줄 정렬 선언)
            html_content_2 = ''.join([
                '<div class="print-area page-break">',
                '<table class="gapji-table" border="1" cellpadding="5" cellspacing="0" style="table-layout: fixed; width: 100%;">',
                '<colgroup><col style="width: 15%;"><col style="width: 85%;"></colgroup>',
                '<tr><td colspan="2" style="border: none !important; font-size: 26px; font-weight: bold; text-align: center; padding-bottom: 20px;">사고현장 상황도</td></tr>',
                '<tr><td class="gapji-header">일 시</td>',
                f'<td style="font-weight: bold; text-align: left; padding-left: 10px;">{row.get("날짜", "")} 분경</td></tr>',
                '<tr><td class="gapji-header">사고장소</td>',
                f'<td style="font-weight: bold; text-align: left; padding-left: 10px;">{row.get("사고장소", "")}</td></tr>',
                '<tr><td class="gapji-header">상황도 설명</td>',
                f'<td style="text-align: left; padding: 10px; line-height: 1.5;">{row.get("사고경위", "")}</td></tr>',
                grid_rows_situ,
                grid_rows_injury,
                '</table></div>'
            ])
            
            st.markdown(html_content_1, unsafe_allow_html=True)
            st.markdown(html_content_2, unsafe_allow_html=True)