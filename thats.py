import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import base64
import datetime
from datetime import date

# 1. 페이지 기본 설정
st.set_page_config(page_title="신건설 통합 관리 시스템", layout="wide", initial_sidebar_state="expanded")

# 2. 구글 스프레드시트 실시간 연동
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=5) 
    df = df.fillna("")
except Exception as e:
    st.error(f"구글 시트 연동 실패: {e}")
    st.stop()

# ★ 필수 컬럼에 서류 제출 현황 추가
required_cols = [
    "ID", "날짜", "현장명", "사고장소", "사고경위", "작업환경", "사고원인", 
    "사고유형", "상해피해정도", "피재자", "주민번호_앞자리", "소속_직급", 
    "직종", "채용일자", "국적_체류코드", "기술적대책", "관리적대책", "교육적대책",
    "안전담당", "공사/공무 담당", "현장소장", "안전팀", "공사팀", "PM", "대표이사",
    "사고보고서_제출", "재발방지대책_제출", "산재표_제출", "합의서_작성", "진행상태"
]

# 누락된 컬럼이 있으면 기본값으로 채우기
for col in required_cols:
    if col not in df.columns:
        if col == "사고보고서_제출": df[col] = "O"
        elif col in ["재발방지대책_제출", "산재표_제출", "합의서_작성"]: df[col] = "X"
        elif col == "진행상태": df[col] = "진행중"
        else: df[col] = "대기"

approvers = ["안전담당", "공사/공무 담당", "현장소장", "안전팀", "공사팀", "PM", "대표이사"]

# 3. 전체 UI 커스텀 CSS
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1E4D6B; }
[data-testid="stSidebar"] * { color: white !important; }
.gapji-table { width: 100% !important; border-collapse: collapse !important; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; color: #000; border: 2px solid #000 !important; margin-bottom: 20px; }
.gapji-table th, .gapji-table td { border: 1px solid #000 !important; padding: 6px !important; text-align: center; vertical-align: middle; }
.gapji-header { background-color: #f0f0f0 !important; font-weight: bold; }
.grid-photo { width: 100%; height: 280px; object-fit: contain; background-color: #fafafa; display: block; margin: 0 auto; }
.photo-blank { height: 280px; display: flex; justify-content: center; align-items: center; color: #999; font-size: 13px; background-color: #fafafa; }
div[data-testid="stForm"] { padding: 1rem; border: 2px solid #ddd; border-radius: 8px;}
.stTextInput, .stDateInput, .stTimeInput, .stSelectbox { margin-bottom: -10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 왼쪽 사이드바 (Navigation Menu)
# ==========================================
with st.sidebar:
    st.title("🏗️ 신건설 통합관리 시스템")
    st.markdown("---")
    
    main_menu = st.radio(
        "메뉴 선택",
        ["1. 위험성평가", "2. TBM", "3. 사고보고서", "4. 안전보건교육", "5. 작업표준화"],
        index=2
    )
    
    if main_menu == "3. 사고보고서":
        st.markdown("---")
        sub_menu = st.radio(
            "사고보고서 상세 메뉴",
            ["📝 보고서 작성", "📊 결재 및 진행 현황", "🖨️ 사진 첨부 및 출력"]
        )

# ==========================================
# 5. 중앙 메인 화면 로직
# ==========================================
if main_menu == "3. 사고보고서":
    
    # ----------------------------------------
    # [메뉴 1] 보고서 작성 (입력창 / 결과 확인창 2분할)
    # ----------------------------------------
    if sub_menu == "📝 보고서 작성":
        st.header("📝 사고보고서 등록")
        col_input, col_preview = st.columns([5, 5])
        
        with col_input:
            st.subheader("🔸 입력창")
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
                p_birth_code = p2.text_input("주민번호 앞자리", value="781231")
                p3, p4 = st.columns(2)
                p_team = p3.text_input("소속/직급", value="김개똥팀")
                p_gongjong = p4.text_input("직종", value="형틀공")
                p5, p6 = st.columns(2)
                p_hire_date = p5.date_input("채용일자", value=date(2024, 5, 2))
                p_nation = p6.text_input("국적/체류코드", value="베트남 / F-6")

                with st.expander("🛡️ 재발방지대책 (선택사항)"):
                    prevent_tech = st.text_input("기술적 대책", value="하부 동바리 및 가고정 완비 전 슬링벨트 해제 금지")
                    prevent_admin = st.text_input("관리적 대책", value="작업지휘자 상주를 통한 '지지 확인 후 해제' 작업 승인제 시행")
                    prevent_edu = st.text_input("교육적 대책", value="조기 해제 위험성 및 표준 작업 순서 준수 TBM 교육 실시")

                formatted_date_time = f"{accident_date.strftime('%y.%m.%d')} {accident_time.strftime('%H:%M')}분경"
                auto_detail = f"{formatted_date_time} / {accident_place}에서 / {p_team} {p_gongjong} {p_name_ko}({p_birth_code})이(가) {work_detail} 중, {accident_cause} 발생하여 [{accident_type}] 사고가 발생함."
                
                submitted = st.form_submit_button("💾 시트에 데이터 저장", type="primary", use_container_width=True)
                if submitted:
                    new_id = int(df["ID"].max()) + 1 if not df.empty and pd.to_numeric(df["ID"], errors='coerce').notna().any() else 1
                    new_row = pd.DataFrame([{
                        "ID": new_id, "날짜": formatted_date_time, "현장명": site_name, "사고장소": accident_place,
                        "사고경위": auto_detail, "작업환경": work_detail, "사고원인": accident_cause,
                        "사고유형": accident_type, "상해피해정도": injury_degree, "피재자": p_name_ko,
                        "주민번호_앞자리": p_birth_code, "소속_직급": p_team, "직종": p_gongjong,
                        "채용일자": str(p_hire_date), "국적_체류코드": p_nation, "기술적대책": prevent_tech,
                        "관리적대책": prevent_admin, "교육적대책": prevent_edu,
                        **{app: "대기" for app in approvers},
                        # ★ 최초 작성 시 기본 상태값 세팅
                        "사고보고서_제출": "O", "재발방지대책_제출": "X", "산재표_제출": "X", "합의서_작성": "X", "진행상태": "진행중"
                    }])
                    conn.update(data=pd.concat([df, new_row], ignore_index=True))
                    st.success("✅ 등록 완료!")
                    st.rerun()

        with col_preview:
            st.subheader("🔸 결과 확인창")
            preview_html = f"""
            <div style="background-color: white; padding: 15px; border: 2px solid #4CAF50; border-radius: 8px;">
                <table class="gapji-table" style="background-color: white;">
                    <tr><td colspan="4" style="font-size: 18px; font-weight: bold; background-color:#e8f5e9;">재해발생보고서 (미리보기)</td></tr>
                    <tr><td class="gapji-header" style="width:20%;">현장명</td><td style="width:30%;">{site_name}</td>
                        <td class="gapji-header" style="width:20%;">사고일시</td><td style="width:30%;">{formatted_date_time}</td></tr>
                    <tr><td class="gapji-header">사고장소</td><td>{accident_place}</td>
                        <td class="gapji-header">작업환경</td><td>{work_detail}</td></tr>
                    <tr><td class="gapji-header">피재자</td><td>{p_team} {p_gongjong} {p_name_ko}</td>
                        <td class="gapji-header">사고형태</td><td>{accident_type}</td></tr>
                    <tr><td class="gapji-header">재해정도</td><td colspan="3" style="color:red; font-weight:bold;">{injury_degree}</td></tr>
                    <tr><td class="gapji-header">사고원인</td><td colspan="3" style="text-align:left;">{accident_cause}</td></tr>
                    <tr><td class="gapji-header">사고경위<br><span style="font-size:10px; font-weight:normal;">(자동완성)</span></td>
                        <td colspan="3" style="text-align:left; background-color:#fff3e0; font-weight:bold;">{auto_detail}</td></tr>
                    <tr><td colspan="4" style="padding:0; border:none;">
                        <table style="width:100%; border-collapse:collapse; text-align:center; margin-top:10px;">
                            <tr style="background-color:#f0f0f0; font-weight:bold;">
                                <td>사고보고서</td><td>재발방지대책</td><td>산재표 제출</td><td>합의서 작성</td><td>진행상태</td>
                            </tr>
                            <tr>
                                <td>O</td><td>X</td><td>X</td><td>X</td><td style="color:red; font-weight:bold;">진행중</td>
                            </tr>
                        </table>
                    </td></tr>
                </table>
            </div>
            """
            st.markdown(preview_html, unsafe_allow_html=True)
            st.info("작성이 끝나면 하단의 [저장] 버튼을 누르세요. 최초 저장 시 '진행중'으로 등록됩니다.")

    # ----------------------------------------
    # [메뉴 2] 결재 및 진행 현황 (★ 자동 종결 계산 로직 추가)
    # ----------------------------------------
    elif sub_menu == "📊 결재 및 진행 현황":
        st.header("📊 전사 사고 대장 및 서류 제출 현황")
        st.caption("안내: '합의서 작성'은 본사 권한에서만 N/A 처리가 가능하며, 필요 서류가 모두(O 또는 N/A) 제출되면 자동으로 '종결' 처리됩니다.")
        
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
        
        if st.button("💾 변경된 사항 저장", type="primary"):
            # ★ 모든 행을 돌면서 서류가 다 제출되었는지 검사 후 '진행상태' 자동 업데이트
            for idx in edited_df.index:
                doc1 = str(edited_df.loc[idx, "사고보고서_제출"]).strip().upper()
                doc2 = str(edited_df.loc[idx, "재발방지대책_제출"]).strip().upper()
                doc3 = str(edited_df.loc[idx, "산재표_제출"]).strip().upper()
                doc4 = str(edited_df.loc[idx, "합의서_작성"]).strip().upper()

                if doc1 == "O" and doc2 == "O" and doc3 == "O" and doc4 in ["O", "N/A"]:
                    edited_df.loc[idx, "진행상태"] = "종결"
                else:
                    edited_df.loc[idx, "진행상태"] = "진행중"

            conn.update(data=edited_df)
            st.success("✅ 상태가 저장되고 종결 여부가 자동 업데이트되었습니다!")
            st.rerun()

    # ----------------------------------------
    # [메뉴 3] 사진 첨부 및 출력 (★ 서류 제출 현황 표 삽입)
    # ----------------------------------------
    elif sub_menu == "🖨️ 사진 첨부 및 출력":
        st.header("🖨️ 보고서 출력 및 사진 첨부")
        if df.empty:
            st.info("출력할 데이터가 없습니다.")
        else:
            select_print_idx = st.selectbox("출력할 보고서 선택", df.index, format_func=lambda x: f"[{df.loc[x, 'ID']}] {df.loc[x, '현장명']} ({df.loc[x, '날짜']})")
            row = df.loc[select_print_idx]
            
            st.markdown("### 📷 현장 사진 업로드")
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
                
                status_color = "blue" if row.get('진행상태', '') == "종결" else "red"

                # ★ 갑지에 서류 제출 현황 추가됨
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
                    f'<tr><td class="gapji-header">피해정도</td><td colspan="7" style="text-align:left; padding:8px; color:red; font-weight:bold;">{row.get("상해피해정도", "")}</td></tr>',
                    f'<tr><td class="gapji-header">교육사항</td><td class="gapji-header">정기교육</td><td>실시</td><td class="gapji-header">특별교육</td><td>실시</td><td class="gapji-header">사고발생형태</td><td colspan="2">{row.get("사고유형", "")}</td></tr>',
                    f'<tr><td rowspan="3" class="gapji-header">피재자</td><td class="gapji-header">성명</td><td>{row.get("피재자", "")}</td><td class="gapji-header">주민번호</td><td>{row.get("주민번호_앞자리", "")}</td><td class="gapji-header">채용일자</td><td colspan="2">{row.get("채용일자", "")}</td></tr>',
                    f'<tr><td class="gapji-header">소속/직급</td><td>{row.get("소속_직급", "")}</td><td class="gapji-header">직종</td><td>{row.get("직종", "")}</td><td class="gapji-header">채용기간</td><td colspan="2">상세관리</td></tr>',
                    f'<tr><td class="gapji-header">주소</td><td colspan="3">사내 대장 전산 확인</td><td class="gapji-header">국적</td><td colspan="2">{row.get("국적_체류코드", "")}</td></tr>',
                    f'<tr><td rowspan="3" class="gapji-header">재발방지</td><td class="gapji-header">기술적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("기술적대책", "")}</td></tr>',
                    f'<tr><td class="gapji-header">관리적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("관리적대책", "")}</td></tr>',
                    f'<tr><td class="gapji-header">교육적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("교육적대책", "")}</td></tr>',
                    
                    # 서류 제출 현황 추가 영역
                    '<tr><td colspan="8" style="padding:0; border:none;">',
                    '<table style="width:100%; border-collapse:collapse; text-align:center; margin-top:10px; margin-bottom:10px;">',
                    '<tr><td colspan="5" class="gapji-header">사고 서류 제출 현황</td></tr>',
                    '<tr><td class="gapji-header">사고보고서 제출</td><td class="gapji-header">재발방지대책</td><td class="gapji-header">산재표 제출</td><td class="gapji-header">합의서 작성</td><td class="gapji-header">진행상태</td></tr>',
                    f'<tr><td>{row.get("사고보고서_제출", "O")}</td><td>{row.get("재발방지대책_제출", "X")}</td><td>{row.get("산재표_제출", "X")}</td><td>{row.get("합의서_작성", "X")}</td><td style="font-weight:bold; color:{status_color};">{row.get("진행상태", "진행중")}</td></tr>',
                    '</table>',
                    '</td></tr>',

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

                st.markdown(html_1 + "<br><br>" + html_2, unsafe_allow_html=True)

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
                st.success("✅ 미리보기가 생성되었습니다. 초록색 버튼을 눌러 파일을 다운로드하세요.")

else:
    st.header(f"🚧 {main_menu} 모듈")
    st.info("현재 기획 및 개발이 진행 중인 메뉴입니다.")