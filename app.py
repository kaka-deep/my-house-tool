import streamlit as st
import pandas as pd

# 웹페이지 설정
st.set_page_config(page_title="내 집 마련 시뮬레이터", layout="wide", page_icon="🏠")

# --- [데이터 정의: 지역별 규제] ---
# 실제 정책에 따라 이 수치만 바꾸면 전체 시스템에 반영됩니다.
REGION_DATA = {
    "비규제지역": {"LTV": 0.70, "취득세율": 0.011}, # 1~3% 지만 단순화
    "밀집지역(과밀억제)": {"LTV": 0.60, "취득세율": 0.011},
    "투기과열지구(강남3구/용산)": {"LTV": 0.50, "취득세율": 0.011}
}

# --- [메인 화면 UI] ---
st.title("🚀 주택 구매 종합 시뮬레이터")
st.markdown("금리 변화와 지역 규제를 반영하여 나의 대출 상환 능력을 확인하세요.")

# 사이드바 입력창
with st.sidebar:
    st.header("1. 기본 정보 입력")
    region = st.selectbox("매수 예정 지역", list(REGION_DATA.keys()))
    house_price = st.number_input("주택 매매가 (만원)", value=80000, step=1000)
    my_cash = st.number_input("보유 현금 (만원)", value=30000, step=1000)
    
    st.divider()
    st.header("2. 대출 조건")
    # 실시간 금리 API 대신 현재 평균 금리를 기본값으로 설정 (사용자 수정 가능)
    current_rate = st.number_input("현재 대출 금리 (%)", value=4.2, step=0.1)
    loan_term = st.slider("대출 기간 (년)", 10, 40, 30)

# --- [계산 로직] ---
ltv_ratio = REGION_DATA[region]["LTV"]
max_loan_by_ltv = house_price * ltv_ratio
needed_loan = max(0, house_price - my_cash)
final_loan = min(max_loan_by_ltv, needed_loan)

def calc_monthly(principal_manwon, rate, years):
    if rate == 0: return principal_manwon * 10000 / (years * 12)
    r = (rate / 100) / 12
    n = years * 12
    monthly = (principal_manwon * 10000) * (r * (1+r)**n) / ((1+r)**n - 1)
    return int(monthly)

# 시나리오 계산
current_monthly = calc_monthly(final_loan, current_rate, loan_term)
future_rate = current_rate + 1.0
future_monthly = calc_monthly(final_loan, future_rate, loan_term)

# --- [결과 출력] ---
st.subheader(f"📍 {region} 분석 결과")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("최대 대출 가능액", f"{int(max_loan_by_ltv):,} 만원")
    st.caption(f"해당 지역 LTV {int(ltv_ratio*100)}% 적용")

with col2:
    st.metric("실제 필요한 대출", f"{int(final_loan):,} 만원")
    st.caption("매매가 - 보유현금 (한도 내)")

with col3:
    extra_cash = max(0, house_price - final_loan - my_cash)
    if extra_cash > 0:
        st.metric("추가 필요 자금", f"{int(extra_cash):,} 만원", delta_color="inverse")
        st.error("보유 현금이 부족합니다!")
    else:
        st.metric("자금 준비", "완료 ✅")

st.divider()

# 시나리오 비교
st.subheader("📊 금리 인상 시나리오 비교 (+1.0%)")
c1, c2 = st.columns(2)

with c1:
    st.info(f"**현재 금리 ({current_rate}%)**")
    st.write(f"월 원리금: **{current_monthly:,} 원**")
    st.write(f"총 이자: **{int(current_monthly * loan_term * 12 - final_loan*10000):,} 원**")

with c2:
    st.warning(f"**금리 인상 시 ({future_rate}%)**")
    st.write(f"월 원리금: **{future_monthly:,} 원**")
    st.write(f"추가 부담금: **월 {future_monthly - current_monthly:,} 원**")

# 차트 시각화
st.bar_chart(pd.DataFrame({
    "구분": ["현재", "1% 인상"],
    "월 납입금": [current_monthly, future_monthly]
}).set_index("구분"))

st.caption("※ 본 계산은 원리금균등상환 방식 기준이며, 실제 대출 심사 시 DSR 등에 따라 달라질 수 있습니다.")
