import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import base64
import datetime
from datetime import date

# 1. 페이지 기본 설정
st.set_page_config(page_title="신건설 통합 관리 시스템", layout="wide", initial_sidebar_state="expanded")

# 2. 구글 스프레드시트 연동
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=5) 
    df = df.fillna("")
except Exception as e:
    st.error(f"구글 시트 연동 실패: {e}")
    st.stop()

# 필수 컬럼 검사 및 초기화
required_cols = [
    "ID", "날짜", "현장명", "사고장소", "사고경위", "작업환경", "사고원인", 
    "사고유형", "상해피해정도", "피재자", "주민번호_앞자리", "소속_직급", 
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

# 3. 전체 UI 커스텀 CSS
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1E4D6B; }
[data-testid="stSidebar"] * { color: white !important; }
.gapji-table { width: 100% !important; border-collapse: collapse !important; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; color: #000; border: 2px solid #000 !important; margin-bottom: 20px; }
.gapji-table th, .gapji-table td { border: 1px solid #000 !important; padding: 6px !important; text-align: center; vertical-align: middle; }
.gapji-header { background-color: #f0f0f0 !important; font-weight: bold; }
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
    
    main_menu = st.radio("메뉴 선택", ["1. 위험성평가", "2. TBM", "3. 사고보고서", "4. 안전보건교육", "5. 작업표준화"], index=2)
    
    if main_menu == "3. 사고보고서":
        st.markdown("---")
        sub_menu = st.radio(
            "사고보고서 상세 업무",
            ["📝 최초 사고보고서 작성", "📎 후속 서류 업데이트", "📊 통합 DB (구글시트 뷰어)", "🖨️ 최종 보고서 출력"]
        )

# ==========================================
# 5. 중앙 메인 화면 로직
# ==========================================
if main_menu == "3. 사고보고서":
    
    # ----------------------------------------
    # [메뉴 1] 최초 사고보고서 작성 (1단계 제출)
    # ----------------------------------------
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
                p_birth_code = p2.text_input("주민번호 앞자리", value="781231")
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
                        "주민번호_앞자리": p_birth_code, "소속_직급": p_team, "직종": p_gongjong,
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
            st.markdown(preview_html, unsafe_allow_html=True)
            st.info("최초 저장 시 1단계(보고서 제출)만 완료되며, 나머지 서류는 [후속 서류 업데이트] 메뉴에서 진행합니다.")

    # ----------------------------------------
    # [메뉴 2] 후속 서류 업데이트 (2~4단계 사진/텍스트 제출)
    # ----------------------------------------
    elif sub_menu == "📎 후속 서류 업데이트":
        st.header("📎 후속 서류 및 사진 제출")
        if df.empty:
            st.warning("등록된 사고 기록이 없습니다.")
        else:
            # 상태 변경 로직 함수 (자동 종결 체크 포함)
            def update_status(idx, col_name, val):
                df.loc[idx, col_name] = val
                # 종결 조건 체크
                c1 = df.loc[idx, "사고보고서_제출"] == "O"
                c2 = df.loc[idx, "재발방지대책_제출"] == "O"
                c3 = df.loc[idx, "산재표_제출"] == "O"
                c4 = df.loc[idx, "합의서_작성"] in ["O", "N/A"]
                df.loc[idx, "진행상태"] = "종결" if (c1 and c2 and c3 and c4) else "진행중"
                conn.update(data=df)
                st.toast(f"✅ {col_name} 업데이트 완료!")

            # 업데이트할 건 선택
            select_idx = st.selectbox("업데이트할 사고 건을 선택하세요", df.index, format_func=lambda x: f"[{df.loc[x, 'ID']}] {df.loc[x, '현장명']} - {df.loc[x, '피재자']} ({df.loc[x, '진행상태']})")
            row = df.loc[select_idx]

            st.markdown("---")
            st.subheader(f"📊 현재 제출 현황 (상태: **{row['진행상태']}**)")
            
            # 현황표 표시
            status_df = pd.DataFrame([{
                "사고보고서": row['사고보고서_제출'], "재발방지대책": row['재발방지대책_제출'], 
                "산재표 제출": row['산재표_제출'], "합의서 작성": row['합의서_작성']
            }])
            st.table(status_df)

            # 3개의 서류별 개별 업로드 탭 구성
            tab1, tab2, tab3 = st.tabs(["🛡️ 재발방지대책", "🏥 산재표 제출", "🤝 합의서 작성"])
            
            with tab1:
                st.markdown("**재발방지대책 (입력 + 사진업로드)**")
                tech = st.text_input("기술적 대책", value=row.get('기술적대책', ''))
                admin = st.text_input("관리적 대책", value=row.get('관리적대책', ''))
                edu = st.text_input("교육적 대책", value=row.get('교육적대책', ''))
                file1 = st.file_uploader("재발방지대책 관련 사진 업로드", type=["jpg", "png", "pdf"])
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

    # ----------------------------------------
    # [메뉴 3] 통합 DB 뷰어 (웹에서 구글시트 바로보기)
    # ----------------------------------------
    elif sub_menu == "📊 통합 DB (구글시트 뷰어)":
        st.header("📊 전사 사고 대장 통합 뷰어")
        st.caption("구글 스프레드시트에 접속할 필요 없이, 웹에서 전체 데이터를 확인하고 직접 수정(결재)할 수 있습니다.")
        
        # 전체 데이터프레임을 화면에 넓게 띄워 구글시트 환경을 대체
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=500, hide_index=True)
        
        if st.button("💾 데이터베이스 직접 저장 (결재 정보 업데이트)", type="primary"):
            # 수동으로 상태를 바꿨을 수도 있으므로 종결 로직 한 번 더 검사
            for idx in edited_df.index:
                d1, d2, d3, d4 = [str(edited_df.loc[idx, c]).strip().upper() for c in ["사고보고서_제출", "재발방지대책_제출", "산재표_제출", "합의서_작성"]]
                edited_df.loc[idx, "진행상태"] = "종결" if (d1=="O" and d2=="O" and d3=="O" and d4 in ["O", "N/A"]) else "진행중"
            
            conn.update(data=edited_df)
            st.success("✅ 구글 스프레드시트에 동기화 완료!")
            st.rerun()

    # ----------------------------------------
    # [메뉴 4] 상황도 및 최종 출력 (서류 현황 포함)
    # ----------------------------------------
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

            def process_images(uploaded_files):
                tags = []
                for f in uploaded_files:
                    encoded = base64.b64encode(f.getvalue()).decode()
                    tags.append(f'<img src="data:image/png;base64,{encoded}" class="grid-photo">')
                return tags

            def build_grid(tags, label):
                if not tags: return f'<tr><td class="gapji-header">{label}</td><td style="padding:6px;"><div class="photo-blank">사진 미등록</div></td></tr>'
                inner = '<table width="100%" border="0" cellpadding="0" cellspacing="0" style="table-layout:fixed; height:100%;">'
                for i in range((len(tags) + 1) // 2):
                    c1 = tags[i*2]
                    c2 = tags[i*2+1] if (i*2+1) < len(tags) else '<div class="photo-blank">대기</div>'
                    bb = 'border-bottom: 1px solid #000;' if i < ((len(tags)+1)//2 - 1) else ''
                    inner += f'<tr><td style="width:50%; border-right:1px solid #000; {bb} padding:6px;">{c1}</td><td style="width:50%; {bb} padding:6px;">{c2}</td></tr>'
                inner += '</table>'
                return f'<tr><td class="gapji-header">{label}</td><td style="padding:0;">{inner}</td></tr>'

            if st.button("🖨️ A4 보고서 생성 및 인쇄 다운로드", type="primary", use_container_width=True):
                def get_sign(val):
                    if str(val).strip() in ["승인", "확인"]: return "<b>[확인]<br><span style='font-size:9px; color:gray;'>signed</span></b>"
                    return ""
                
                s_color = "blue" if row.get('진행상태', '') == "종결" else "red"

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
                    f'<tr><td class="gapji-header" style="height:60px;">사고경위</td><td colspan="7" style="text-align:left; padding:8px;">{row.get("사고경위", "")}</td></tr>',
                    f'<tr><td class="gapji-header">사고원인</td><td colspan="7" style="text-align:left; padding:8px;">{row.get("사고원인", "")}</td></tr>',
                    f'<tr><td rowspan="3" class="gapji-header">피재자</td><td class="gapji-header">성명</td><td>{row.get("피재자", "")}</td><td class="gapji-header">주민번호</td><td>{row.get("주민번호_앞자리", "")}</td><td class="gapji-header">채용일자</td><td colspan="2">{row.get("채용일자", "")}</td></tr>',
                    f'<tr><td class="gapji-header">소속/직급</td><td>{row.get("소속_직급", "")}</td><td class="gapji-header">직종</td><td>{row.get("직종", "")}</td><td class="gapji-header">채용기간</td><td colspan="2">상세관리</td></tr>',
                    f'<tr><td class="gapji-header">주소</td><td colspan="3">사내 대장 전산 확인</td><td class="gapji-header">국적</td><td colspan="2">{row.get("국적_체류코드", "")}</td></tr>',
                    f'<tr><td rowspan="3" class="gapji-header">재발방지</td><td class="gapji-header">기술적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("기술적대책", "")}</td></tr>',
                    f'<tr><td class="gapji-header">관리적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("관리적대책", "")}</td></tr>',
                    f'<tr><td class="gapji-header">교육적</td><td colspan="6" style="text-align:left; padding-left:5px;">{row.get("교육적대책", "")}</td></tr>',
                    
                    '<tr><td colspan="8" style="padding:0; border:none;">',
                    '<table style="width:100%; border-collapse:collapse; text-align:center; margin-top:10px; margin-bottom:10px;">',
                    '<tr><td colspan="5" class="gapji-header">사고 서류 제출 현황</td></tr>',
                    '<tr><td class="gapji-header">사고보고서 제출</td><td class="gapji-header">재발방지대책</td><td class="gapji-header">산재표 제출</td><td class="gapji-header">합의서 작성</td><td class="gapji-header">진행상태</td></tr>',
                    f'<tr><td>{row.get("사고보고서_제출", "O")}</td><td>{row.get("재발방지대책_제출", "X")}</td><td>{row.get("산재표_제출", "X")}</td><td>{row.get("합의서_작성", "X")}</td><td style="font-weight:bold; color:{s_color};">{row.get("진행상태", "진행중")}</td></tr>',
                    '</table></td></tr></table>'
                ])

                html_2 = ''.join([
                    '<table class="gapji-table" style="table-layout:fixed; width:100%;">',
                    '<tr><td colspan="2" style="font-size:26px; font-weight:bold; border:none; padding-bottom:20px;">사고현장 상황도</td></tr>',
                    build_grid(process_images(files_situ), "사진 1<br>사고상황도"),
                    build_grid(process_images(files_injury), "사진 2<br>재해정도"),
                    '</table>'
                ])

                st.markdown(html_1 + "<br><br>" + html_2, unsafe_allow_html=True)

                standalone_html = f"""
                <!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>보고서 인쇄</title>
                <style>@page {{ size: A4; margin: 10mm 15mm; }} body {{ background: #fff; }} .gapji-table {{ width: 100%; border-collapse: collapse; font-family: 'Malgun Gothic', sans-serif; font-size: 14px; border: 2px solid #000; margin-bottom: 20px; }} .gapji-table th, .gapji-table td {{ border: 1px solid #000; padding: 7px; text-align: center; vertical-align: middle; }} .gapji-header {{ background-color: #f0f0f0; font-weight: bold; }} .grid-photo {{ width: 100%; height: 280px; object-fit: contain; display: block; margin: 0 auto; }} .page-break {{ page-break-before: always; }}</style>
                </head><body onload="window.print()">{html_1}<div class="page-break"></div>{html_2}</body></html>
                """
                b64_html = base64.b64encode(standalone_html.encode('utf-8')).decode('utf-8')
                st.markdown(f'<div style="text-align:center;"><a href="data:text/html;base64,{b64_html}" download="보고서.html" style="padding:15px; background-color:#4CAF50; color:white; text-decoration:none; border-radius:8px; font-weight:bold;">🖨️ 인쇄용 파일 다운로드</a></div>', unsafe_allow_html=True)

else:
    st.header(f"🚧 {main_menu} 모듈")
    st.info("현재 기획 및 개발 진행 중입니다.")