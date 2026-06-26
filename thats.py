import os
import json
import base64
import datetime
from datetime import date, datetime as dt
import streamlit as st

st.set_page_config(page_title="신건설 통합관리 프로그램 - 사고보고서 입력", layout="centered")

def img_to_base64(uploaded_file):
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)
        return f"data:image/jpeg;base64,{base64.b64encode(file_bytes).decode()}"
    return ""

st.markdown("""
<style>
.nav-tip { color: #555; font-size: 0.85rem; margin-bottom: 20px; }

/* [완벽 해결] 인쇄 시 모든 요소를 숨기고 표만 강제로 띄우는 절대 규칙 */
@media print {
    /* 1. 화면의 모든 것을 일단 안 보이게 숨깁니다 */
    body * {
        visibility: hidden !important;
    }
    
    /* 2. 오직 print-area(갑지 표)와 그 안의 내용물만 강제로 보이게 살려냅니다 */
    .print-area, .print-area * {
        visibility: visible !important;
    }
    
    /* 3. 살려낸 표를 A4 용지 맨 왼쪽 위(0,0) 좌표로 멱살 잡고 끌어다 놓습니다 */
    .print-area {
        position: absolute !important;
        left: 0 !important;
        top: 0 !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 4. 배경색과 선 강제 유지 */
    * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }
    
    .page-break { page-break-before: always !important; } 
    body { background-color: #fff !important; }
}

/* 표 기본 디자인 */
.gapji-table { width: 100% !important; border-collapse: collapse !important; margin-top: 10px; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; color: #000; border: 2px solid #000 !important; }
.gapji-table th, .gapji-table td { border: 1px solid #000 !important; padding: 8px !important; text-align: center; vertical-align: middle; word-wrap: break-word; }
.gapji-header { background-color: #f0f0f0 !important; font-weight: bold; border: 1px solid #000 !important; }
.main-title { font-size: 24px; font-weight: bold; text-align: left; padding-bottom: 10px; border: none !important; }
.sign-table { border-collapse: collapse !important; float: right; height: 70px; margin-right: 5px; margin-top: 5px; border: 2px solid #000 !important; }
.sign-table td { border: 1px solid #000 !important; font-size: 11px; text-align: center; padding: 2px; width: 52px; }
.sign-title { background-color: #f0f0f0 !important; font-weight: bold; width: 25px; }
.text-left { text-align: left !important; padding-left: 10px !important; }
.photo-title { font-size: 22px; font-weight: bold; padding: 15px !important; border-bottom: 2px solid #000 !important; background-color: white !important; }
.photo-row { height: 260px; } 
.photo-img { max-width: 95%; max-height: 220px; object-fit: contain; }
</style>
""", unsafe_allow_html=True)

st.title("🚨 신건설 통합관리 프로그램")
st.subheader("사고보고서 입력 시스템 (Ver.5 - 인쇄 버그 완벽 수정)")

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

st.header("1. 사고 기본 정보 및 원인 (챕터1)")
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
st.subheader("👤 피재자 정보")
p_col1, p_col2 = st.columns(2)
with p_col1:
    p_name_ko = st.text_input("피재자 성명", value="김개똥")
    p_birth_code = st.text_input("주민번호 앞자리(또는 생년월일)", value="630310-1")
    p_team = st.text_input("소속/직급", value="수도인력")
with p_col2:
    p_gongjong = st.text_input("직종", value="보통인부")
    p_hire_date = st.date_input("채용일자", value=date(2024, 11, 5))
    p_nation = st.text_input("국적/체류코드", value="베트남 / F-6")

prevent_tech = st.text_input("재발방지대책 (기술적)", value="1. 철근 근로자 찔림방지 방호조치 철저")

st.markdown("---")

st.header("📸 2. 현장 상황도 사진 등록")
col_img1, col_img2 = st.columns(2)
with col_img1:
    uploaded_accident = st.file_uploader("🖼️ [사고상황도] 사진", type=["jpg","png","jpeg"], accept_multiple_files=True)
with col_img2:
    uploaded_injury = st.file_uploader("🩺 [재해정도] 사진", type=["jpg","png","jpeg"], accept_multiple_files=True)

formatted_time = accident_time.strftime('%H:%M')
auto_accident_detail = (
    f"{accident_date.strftime('%y.%m.%d')} {formatted_time}분경 / {accident_place}에서 / "
    f"용역 {p_name_ko}({p_birth_code})이 폭설 대비 알폼 슬라브 판개구간에서 천막보양 작업을 하던 중 / "
    f"보양 천막으로 인한 벽체 철근 구간을 인지하지 못하고 오른쪽 발이 미끄러지면서 벽체 단부에 발이 빠져 / 철근에 엉덩이를 찔림"
)
final_detail = st.text_area("사고경위 (수정 가능)", value=auto_accident_detail, height=100)

if st.button("📝 사고보고서 등록 및 갑지 서식 완성", type="primary", use_container_width=True):
    
    photo_rows_html = ""
    photo_count = 1
    
    if uploaded_accident:
        for i in range(0, len(uploaded_accident), 2):
            img1_b64 = img_to_base64(uploaded_accident[i])
            img2_b64 = img_to_base64(uploaded_accident[i+1]) if i+1 < len(uploaded_accident) else ""
            img1_tag = f'<img src="{img1_b64}" class="photo-img">' if img1_b64 else ''
            img2_tag = f'<img src="{img2_b64}" class="photo-img">' if img2_b64 else ''
            photo_rows_html += f"""<tr class="photo-row">
<td class="gapji-header">사진{photo_count}<br>사고상황도</td>
<td>{img1_tag}<br><br>전체사진</td>
<td>{img2_tag}<br><br>확대사진</td>
</tr>"""
            photo_count += 1

    if uploaded_injury:
        for i in range(0, len(uploaded_injury), 2):
            img1_b64 = img_to_base64(uploaded_injury[i])
            img2_b64 = img_to_base64(uploaded_injury[i+1]) if i+1 < len(uploaded_injury) else ""
            img1_tag = f'<img src="{img1_b64}" class="photo-img">' if img1_b64 else ''
            img2_tag = f'<img src="{img2_b64}" class="photo-img">' if img2_b64 else ''
            photo_rows_html += f"""<tr class="photo-row">
<td class="gapji-header">사진{photo_count}<br>재해정도</td>
<td>{img1_tag}<br><br>전체사진</td>
<td>{img2_tag}<br><br>확대사진</td>
</tr>"""
            photo_count += 1
            
    if not uploaded_accident and not uploaded_injury:
        photo_rows_html = """<tr class="photo-row">
<td class="gapji-header">사진1<br>사고상황도</td><td>사진 없음</td><td>사진 없음</td>
</tr>
<tr class="photo-row">
<td class="gapji-header">사진2<br>재해정도</td><td>사진 없음</td><td>사진 없음</td>
</tr>"""
    
    html_content = f"""<div class="print-area">
<table class="gapji-table" border="1" cellpadding="5" cellspacing="0">
<tr>
<td colspan="7" style="border: none !important; padding: 0 !important; background-color: white !important;">
<div style="display: flex; justify-content: space-between; align-items: flex-end;">
<div class="main-title">재해발생보고서<br><br><span style="font-size:32px;">신건설(주)</span></div>
<table class="sign-table" border="1">
<tr>
<td rowspan="2" class="sign-title">결<br><br>재</td>
<td>안전담당</td><td>공사/공무</td><td>현장소장</td>
</tr>
<tr>
<td style="height:45px;"></td><td></td><td></td>
</tr>
</table>
</div>
</td>
</tr>
<tr>
<td class="gapji-header" style="width: 12%;">현 장 명</td>
<td colspan="3" style="font-size: 15px; font-weight: bold;">{site_name}</td>
<td class="gapji-header" style="width: 12%;">사고장소</td>
<td colspan="2">{accident_place}</td>
</tr>
<tr>
<td class="gapji-header">사고일시</td>
<td colspan="2">{accident_date.strftime('%y.%m.%d')}</td>
<td>{formatted_time}분경</td>
<td class="gapji-header">작업환경</td>
<td colspan="2">{work_detail}</td>
</tr>
<tr>
<td class="gapji-header" style="height: 120px;">사고경위<br>(6하원칙에<br>의거작성)</td>
<td colspan="6" class="text-left" style="line-height: 1.6;">{final_detail}</td>
</tr>
<tr>
<td class="gapji-header" style="height: 60px;">사고원인</td>
<td colspan="6" class="text-left">{accident_cause}</td>
</tr>
<tr>
<td class="gapji-header">원청보고</td>
<td>사후구두보고</td>
<td class="gapji-header">보고일시</td>
<td colspan="2">24.12.20 18시 20분경</td>
<td class="gapji-header">보고방법</td>
<td>전화보고</td>
</tr>
<tr>
<td class="gapji-header" style="height: 60px;">상해<br>피해정도<br>진단서</td>
<td colspan="6" class="text-left">{injury_degree}</td>
</tr>
<tr>
<td rowspan="3" class="gapji-header">피재자<br>인적사항</td>
<td class="gapji-header">성명</td>
<td>{p_name_ko}</td>
<td class="gapji-header">주민등록번호</td>
<td>{p_birth_code}</td>
<td class="gapji-header">사고발생형태</td>
<td>{accident_type}</td>
</tr>
<tr>
<td class="gapji-header">소속/직급</td>
<td>{p_team}</td>
<td class="gapji-header">직종</td>
<td>{p_gongjong}</td>
<td class="gapji-header">채용일자</td>
<td>{p_hire_date.strftime('%y.%m.%d')}</td>
</tr>
<tr>
<td class="gapji-header">주소</td>
<td colspan="3">인천시 부평구 갈산로 123번길 45</td>
<td class="gapji-header">국적/체류코드</td>
<td>{p_nation}</td>
</tr>
<tr>
<td class="gapji-header">목격자</td>
<td class="gapji-header">성명</td>
<td colspan="2">홍길동</td>
<td class="gapji-header">주민등록번호</td>
<td colspan="2">630310-1</td>
</tr>
<tr>
<td rowspan="3" class="gapji-header">재발방지<br>대책</td>
<td class="gapji-header">기술적</td>
<td colspan="5" class="text-left">{prevent_tech}</td>
</tr>
<tr>
<td class="gapji-header" style="height: 40px;">관리적</td>
<td colspan="5"></td>
</tr>
<tr>
<td class="gapji-header" style="height: 40px;">교육적</td>
<td colspan="5"></td>
</tr>
</table>
<div class="page-break"></div>
<table class="gapji-table" border="1" cellpadding="5" cellspacing="0">
<tr>
<td colspan="3" class="photo-title" style="background-color: white !important;">사고현장 상황도</td>
</tr>
<tr>
<td class="gapji-header" style="width: 15%;">일 시</td>
<td style="width: 42%;">{accident_date.strftime('%Y-%m-%d')} ({formatted_time}경)</td>
<td class="gapji-header" style="width: 43%;">사 고 장 소 : {accident_place}</td>
</tr>
<tr>
<td class="gapji-header" style="height: 50px;">상황도</td>
<td colspan="2" class="text-left">{accident_cause}</td>
</tr>
{photo_rows_html}
</table>
</div>"""
    
    st.markdown(html_content, unsafe_allow_html=True)