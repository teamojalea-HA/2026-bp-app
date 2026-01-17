import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="2026 새혈압운동", layout="wide", page_icon="🩺")

# --- 2. 구글 시트 연결 (보안 및 에러 방지) ---
try:
    conf = st.secrets["connections"]["gsheets"].to_dict()
    if "private_key" in conf:
        pk = conf["private_key"].strip()
        header = "-----BEGIN PRIVATE KEY-----"
        footer = "-----END PRIVATE KEY-----"
        if header in pk and footer in pk:
            core = "".join(pk.split(header)[1].split(footer)[0].split())
            conf["private_key"] = f"{header}\n{core}\n{footer}\n"

    SHEET_URL = conf.get("spreadsheet")
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"⚠️ 연결 설정 중 오류 발생: {e}")
    st.stop()

def load_data(worksheet_name):
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        return df.dropna(how="all")
    except:
        return pd.DataFrame()

def save_data(new_df, worksheet_name):
    try:
        conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=new_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"시트 저장 실패: {e}")
        return False

# --- 3. 데이터 로드 ---
df_apply = load_data("신청서")
if df_apply.empty:
    df_apply = pd.DataFrame(columns=["ID", "사무소명", "신청자", "행사일시", "희망장소", "인원수", "참석자상세", "상태"])

# --- 4. 사무소 리스트 정리 ---
OFFICE_LIST = [
    "서울3 남부1", "서울3 남부2", "서울3 남부3", "서울3 동부1", "서울3 동부2",
    "서울3 북부1", "서울3 북부2", "서울3 북부3", "서울3 서부1", "서울3 서부2", "서울3 MS",
    "서울4 강원", "서울4 경기1", "서울4 경기2", "서울4 경기3", "서울4 경인1", "서울4 경인2", "서울4 경인3", "서울4 경인4",
    "지방3 경남1", "지방3 경남2", "지방3 대구1", "지방3 대구2", "지방3 대구3", "지방3 부산1", "지방3 부산2", "지방3 부산3", "지방3 울산",
    "지방4 광주1", "지방4 광주2", "지방4 대전1", "지방4 대전2", "지방4 전주1", "지방4 전주2", "지방4 청주1", "지방4 청주2"
]

# --- 5. 사이드바 메뉴 ---
with st.sidebar:
    try:
        st.image("new_bp_logo.png", use_container_width=True)
    except:
        st.info("💡 new_bp_logo.png 파일을 폴더에 넣어주세요.")
    
    st.divider()
    menu = st.radio("메뉴 선택", ["📋 신청서 작성", "🔎 현황 조회 및 승인", "💬 소통 게시판"])

# --- 6. 신청서 작성 화면 ---
if menu == "📋 신청서 작성":
    st.markdown("### 📝 2026 새혈압운동 신규 신청")
    
    # [💡 개선] 인원수 설정을 폼 밖으로 배치하여 즉시 반응 유도
    num = st.number_input("1. 참석 인원을 설정해주세요", 1, 20, 1)
    
    st.divider()
    
    with st.form("apply_form_final"):
        st.markdown("##### 2. 기본 정보 입력")
        col1, col2 = st.columns(2)
        with col1:
            office = st.selectbox("사무소 선택", OFFICE_LIST)
            applicant = st.text_input("신청자 성함")
        with col2:
            date = st.date_input("행사 예정일", datetime.now())
            wish_loc = st.text_input("희망장소")
        
        st.divider()
        st.markdown("##### 3. 참석자 상세 및 CART 도입 여부")
        
        # [💡 개선] 참석자 리스트 열 맞춰 배치
        details_inputs = []
        for i in range(int(num)):
            c1, c2 = st.columns([3, 1])
            with c1:
                p_name = st.text_input(f"참석자 {i+1} 성함/병원명", key=f"p_name_{i}")
            with c2:
                # [💡 개선] 라디오 버튼으로 미도입/도입처 선택
                p_cart = st.radio(f"도입여부 {i+1}", ["미도입", "도입처"], key=f"p_cart_{i}", horizontal=True)
            details_inputs.append((p_name, p_cart))
        
        st.divider()
        submit = st.form_submit_button("🚀 신청서 최종 제출")
        
        if submit:
            if applicant and wish_loc:
                # 상세 정보 문자열 결합
                combined_details = " | ".join([f"{n}({s})" for n, s in details_inputs if n])
                
                new_row = pd.DataFrame([{
                    "ID": len(df_apply) + 1,
                    "사무소명": office,
                    "신청자": applicant,
                    "행사일시": str(date),
                    "희망장소": wish_loc,
                    "인원수": int(num),
                    "참석자상세": combined_details,
                    "상태": "대기"
                }])
                
                # 시트 저장 로직 실행
                if save_data(pd.concat([df_apply, new_row], ignore_index=True), "신청서"):
                    st.success("✅ 신청서가 구글 시트에 정상적으로 전송되었습니다!")
                    st.balloons()
                    st.rerun()
            else:
                st.error("⚠️ 신청자 성함과 희망장소는 필수 입력 사항입니다.")

# --- 7. 조회 화면 ---
elif menu == "🔎 현황 조회 및 승인":
    st.subheader("📊 전체 신청 현황")
    df_current = load_data("신청서")
    if not df_current.empty:
        st.dataframe(df_current, use_container_width=True)
    else:
        st.info("현재 등록된 데이터가 없습니다.")