import os
import datetime
from datetime import date, datetime as dt
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(page_title="신건설 통합관리 프로그램 - 사고보고서 입력", layout="centered")

# 🖨️ 인쇄 전용 CSS (1페이지 갑지 전용)
st.markdown("""
<style>
.nav-tip { color: #555; font-size: 0.85rem; margin-bottom: 20px; }

@media print {
    /* 웹 전용 UI (헤더, 사이드바, 버튼 등) 완벽 숨김 */
    header, footer, nav, [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stViewerBadge"] { 
        display: none !important; 
    }
    
    /* 인쇄 스크롤 및 여백 제한 해제 */
    html, body, #root, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
        display: block !important;
        width: 100% !important;
        height: auto !important;
        overflow: visible !important;
        position: static !important;
        padding: 0 !important; 
        margin: 0 !important; 
    }
    
    /* 화면에 입력창 숨기고 '갑지 표'만 남기기 */
    .element-container:not(:has(.print-area)) {
        display: none !important;
    }
    
    /* 1장짜리 표가 찢어지지 않도록 보호 */
    .gapji-table { page-break-inside: avoid; }
    
    /* 엑셀처럼 흑백 선/배경색 강제 유지 */
    * { 
        -webkit-print-color-adjust: exact !important; 
        print-color-adjust: exact !important; 
    }
    body { background-color: white !important; }
    
    /* A4 용지 여백 설정 */
    @page { size: A4; margin: 15mm; }
}

/* 표 기본 디자인 (웹 & 인쇄 공통) */
.gapji-table { width: 100% !important; border-collapse: collapse !important; margin-top: 0px !important; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; color: #000; border: 2px solid #000 !important; }
.gapji-table th, .gapji-table td { border: 1px solid #000 !important; padding: 6px !important; text-align: center; vertical-align: middle; word-wrap: break-word; }
.gapji-header { background-color: #f0f0f0 !important; font-weight: bold; border: 1px solid #000 !important; }
</style>
""", unsafe_allow_html=True)

st.title("🚨 신건설 통합관리 프로그램")
st.subheader("사고보고서 입력 시스템 (Ver.11 - 사진 제거 및 단일 갑지 최적화)")

st.markdown("### 📋 전자결재 사전 확인 (화면 검토용)")
con_col1, con_col2 = st.columns(2)
with con_col1:
    st.write("**현장 확인**")
    site_cols = st.columns(3)
    chk_s1 = site_cols[0].checkbox("안전담당")
    chk_s2 = site_cols[1].checkbox("공사/공무")
    chk_s3 = site_cols[2].checkbox("현장소장")
with con_col2:
    st.write("**본사 확인**")
    hq_cols = st.columns(4)
    chk_h1 = hq_cols[0].checkbox("안전팀")
    chk_h2 = hq_cols[1].checkbox("공사팀")
    chk_h3 = hq_cols[2].checkbox("PM")
    chk_h4 = hq_cols[3].checkbox("대표이사")

st.markdown("---")

st.header("1. 사고 기본 정보 및 원인")
col1, col2 = st.columns(2)
with col1:
    site_name = st.text_input("현장명", value="이천부발현장")
    accident_date = st.date_input("사고일자", value=date.today())
with col2:
    current_time = dt.now().time()
    accident_time = st.time_input("사고시간", value=datetime.time(current_time.hour, current_time.minute))
    accident_place = st.text_input("사고장소", value="A1구간 지하1층")

work_detail = st.text_input("작업환경", value="거푸집 설치 작업 중")
accident_cause = st.text_input("사고원인", value="박리제 도포된 알폼 슬라브, 벽체 철근 미보양 상태")
accident_type = st.selectbox("사고발생형태", ["떨어짐", "낙하·비래(맞음)", "넘어짐", "부딪힘/찔림", "절단·베임", "기타"], index=3)
injury_degree = st.text_input("상해피해정도 진단서", value="주상병 : 좌측 제12 늑골 골절, 폐쇄성 / 질병분류기호 : S22.390")

st.markdown("---")
st.header("2. 피재자 정보")
p_col1, p_col2 = st.columns(2)
with p_col1:
    p_name_ko = st.text_input("피재자 성명", value="김개똥")
    p_birth_code = st.text_input("주민번호 앞자리", value="630310-1")
    p_team = st.text_input("소속/직급", value="수도인력")
with p_col2:
    p_gongjong = st.text_input("직종", value="보통인부")
    p_hire_date = st.date_input("채용일자", value=date(2024, 11, 5))
    p_nation = st.text_input("국적/체류코드", value="베트남 / F-6")

prevent_tech = st.text_input("재발방지대책 (기술적)", value="1. 철근 근로자 찔림방지 방호조치 철저")

st.markdown("---")

formatted_time = accident_time.strftime('%H:%M')
auto_accident_detail = (
    f"{accident_date.strftime('%y.%m.%d')} {formatted_time}분경 / {accident_place}에서 / "
    f"용역 {p_name_ko}({p_birth_code})이 폭설 대비 알폼 슬라브 판개구간에서 천막보양 작업을 하던 중 / "
    f"보양 천막으로 인한 벽체 철근 구간을 인지하지 못하고 오른쪽 발이 미끄러지면서 벽체 단부에 발이 빠져 / 철근에 엉덩이를 찔림"
)
final_detail = st.text_area("사고경위 (수정 가능)", value=auto_accident_detail, height=100)

if st.button("📝 사고보고서 1장(갑지) 서식 완성", type="primary", use_container_width=True):
    
    html_content = f"""<div class="print-area">
<table class="gapji-table" border="1" cellpadding="5" cellspacing="0">
<tr>
<td colspan="8" style="border: none !important; font-size: 28px; font-weight: bold; text-align: center; padding-bottom: 20px;">재해발생보고서</td>
</tr>
<tr>
<td colspan="4" style="border: none !important; text-align: left; padding-left: 20px; font-size: 36px; font-weight: bold; vertical-align: bottom;">신건설(주)</td>
<td colspan="4" style="border: none !important; text-align: right; vertical-align: bottom;">
<table border="1" cellpadding="0" cellspacing="0" style="display: inline-table; margin: 0; text-align: center; border-collapse: collapse;">
<tr>
<td rowspan="2" style="background-color: #f0f0f0; font-weight: bold; width: 30px;">결<br><br>재</td>
<td style="width: 70px; background-color: #f0f0f0;">안전담당</td>
<td style="width: 70px; background-color: #f0f0f0;">공사/공무</td>
<td style="width: 70px; background-color: #f0f0f0;">현장소장</td>
</tr>
<tr><td style="height: 50px;"></td><td></td><td></td></tr>
</table>
</td>
</tr>
<tr>
<td class="gapji-header" style="width: 12%;">현장명</td>
<td colspan="3" style="width: 38%; font-weight: bold; font-size: 15px;">{site_name}</td>
<td class="gapji-header" style="width: 12%;">사고장소</td>
<td colspan="3" style="width: 38%;">{accident_place}</td>
</tr>
<tr>
<td class="gapji-header">사고일시</td>
<td colspan="2">{accident_date.strftime('%y.%m.%d')}</td>
<td>{formatted_time}분경</td>
<td class="gapji-header">작업환경</td>
<td colspan="3">{work_detail}</td>
</tr>
<tr>
<td class="gapji-header" style="height: 90px;">사고경위<br>(6하원칙에<br>의거작성)</td>
<td colspan="7" style="text-align: left; line-height: 1.6; padding: 10px;">{final_detail}</td>
</tr>
<tr>
<td class="gapji-header" style="height: 50px;">사고원인</td>
<td colspan="7" style="text-align: left; padding: 10px;">{accident_cause}</td>
</tr>
<tr>
<td class="gapji-header">원청보고</td>
<td>사후구두보고</td>
<td class="gapji-header">보고일시</td>
<td colspan="2">24.12.20 18시 20분경</td>
<td class="gapji-header">보고방법</td>
<td colspan="2">전화보고</td>
</tr>
<tr>
<td class="gapji-header" style="height: 50px;">상해<br>피해정도<br>진단서</td>
<td colspan="7" style="text-align: left; padding: 10px;">{injury_degree}</td>
</tr>
<tr>
<td class="gapji-header">교육사항</td>
<td class="gapji-header">정기교육</td>
<td>실시</td>
<td class="gapji-header">특별교육</td>
<td>실시</td>
<td class="gapji-header">사고발생형태</td>
<td colspan="2">{accident_type}</td>
</tr>
<tr>
<td rowspan="3" class="gapji-header">피재자<br>인적사항</td>
<td class="gapji-header">성명</td>
<td>{p_name_ko}</td>
<td class="gapji-header">주민등록번호</td>
<td>{p_birth_code}</td>
<td class="gapji-header">채용일자</td>
<td colspan="2">{p_hire_date.strftime('%y.%m.%d')}</td>
</tr>
<tr>
<td class="gapji-header">소속/직급</td>
<td>{p_team}</td>
<td class="gapji-header">직종</td>
<td>{p_gongjong}</td>
<td class="gapji-header">채용기간</td>
<td colspan="2">587</td>
</tr>
<tr>
<td class="gapji-header">주소</td>
<td colspan="3">인천시 부평구 갈산로 123번길 45</td>
<td class="gapji-header">국적/체류코드</td>
<td colspan="2">{p_nation}</td>
</tr>
<tr>
<td rowspan="2" class="gapji-header">목격자<br>인적사항<br>(주변근로자)</td>
<td class="gapji-header">성명</td>
<td colspan="2">홍길동</td>
<td class="gapji-header">주민등록번호</td>
<td colspan="3">630310-1</td>
</tr>
<tr>
<td class="gapji-header">직종</td>
<td colspan="2"></td>
<td class="gapji-header">주소</td>
<td colspan="3"></td>
</tr>
<tr>
<td rowspan="3" class="gapji-header">재발방지<br>대책</td>
<td class="gapji-header">기술적</td>
<td colspan="6" style="text-align: left; padding-left: 10px;">{prevent_tech}</td>
</tr>
<tr>
<td class="gapji-header" style="height: 35px;">관리적</td>
<td colspan="6"></td>
</tr>
<tr>
<td class="gapji-header" style="height: 35px;">교육적</td>
<td colspan="6"></td>
</tr>
<tr>
<td class="gapji-header" style="height: 40px;">첨부서류</td>
<td colspan="7" style="text-align: left; padding-left: 10px;">추후 진단서 첨부 예정</td>
</tr>
</table>
</div>"""
    
    st.markdown(html_content, unsafe_allow_html=True)