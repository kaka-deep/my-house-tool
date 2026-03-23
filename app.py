import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="내 집 마련 종합 시뮬레이터", layout="wide", page_icon="🏢")

# --- 유틸리티 함수: 숫자를 한글 단위(억, 만)로 변환 ---
def format_korean_currency(value_manwon):
    if value_manwon < 10000:
        return f"{int(value_manwon):,}만원"
    uk = value_manwon // 10000
    man = value_manwon % 10000
    if man == 0:
        return f"{int(uk):,}억 원"
    return f"{int(uk):,}억 {int(man):,}만원"

# --- [데이터 정의: 지역별 규제] ---
REGION_DATA = {
    "비규제지역": {"LTV": 0.70, "DSR": 0.40},
    "과밀억제권역": {"LTV": 0.60, "DSR": 0.40},
    "투기과열지구(강남3구/용산)": {"LTV": 0.50, "DSR": 0.40}
}

st.title("🏦 내 집 마련 종합 시뮬레이터 v2.0")
st.markdown("정확한 대출 한도(LTV/DSR)와 세금, 금리 시나리오를 확인하세요.")

# --- [사이드바: 사용자 입력] ---
with st.sidebar:
    st.header("1️⃣ 매수 대상 정보")
    region = st.selectbox("지역 선택", list(REGION_DATA.keys()))
    house_price = st.number_input("주택 매매가 (만원)", value=80000, step=1000)
    is_large = st.checkbox("전용면적 85㎡ 초과인가요?")
    
    st.divider()
    st.header("2️⃣ 자금 및 소득 정보")
    my_cash = st.number_input("보유 현금 (만원)", value=30000, step=1000)
    annual_income = st.number_input("연봉 (만원)", value=6000, step=500)
    other_loan_pay = st.number_input("기타 대출 연간 원리금 상환액 (만원)", value=0, step=100)

    st.divider()
    st.header("3️⃣ 대출 조건 설정")
    current_rate = st.number_input("적용 금리 (%)", value=4.2, step=0.1)
    loan_term = st.slider("대출 기간 (년)", 10, 40, 30)

# --- [로직 계산 영역] ---
# 1. 취득세 계산 (단순화: 생애최초 등 제외 기본이율)
base_tax_rate = 0.01 if house_price <= 60000 else (0.02 if house_price <= 90000 else 0.03)
edu_tax = 0.001 # 지방교육세
rural_tax = 0.002 if is_large else 0 # 농어촌특별세
total_tax_rate = base_tax_rate + edu_tax + rural_tax
acquisition_tax = house_price * total_tax_rate

# 2. 대출 한도 계산 (LTV vs DSR)
ltv_limit = house_price * REGION_DATA[region]["LTV"]

# DSR 기반 대출 한도 역산 (원리금균등 기준)
r = (current_rate / 100) / 12
n = loan_term * 12
dsr_ratio = REGION_DATA[region]["DSR"]
max_annual_pay = (annual_income * dsr_ratio) - other_loan_pay
# 원리금균등상환 공식 역산: Principal = PMT * ((1+r)^n - 1) / (r * (1+r)^n)
if r > 0:
    dsr_limit = (max_annual_pay / 12) * ((1+r)**n - 1) / (r * (1+r)**n)
else:
    dsr_limit = max_annual_pay * loan_term

final_loan_limit = min(ltv_limit, dsr_limit)
actual_needed_loan = max(0, house_price - my_cash)
final_loan = min(final_loan_limit, actual_needed_loan)

# 3. 월 상환액 계산
def calc_monthly(principal_manwon, rate, years):
    if rate <= 0: return int(principal_manwon * 10000 / (years * 12))
    r_val = (rate / 100) / 12
    n_val = years * 12
    return int((principal_manwon * 10000) * (r_val * (1+r_val)**n_val) / ((1+r_val)**n_val - 1))

monthly_now = calc_monthly(final_loan, current_rate, loan_term)
monthly_future = calc_monthly(final_loan, current_rate + 1.0, loan_term)

# --- [결과 출력 영역] ---
st.subheader("📊 시뮬레이션 결과 리포트")

# 주요 지표 (3컬럼)
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("총 필요 자금 (매매가+세금)", format_korean_currency(house_price + acquisition_tax))
    st.write(f"취득세(예상): {format_korean_currency(acquisition_tax)}")

with c2:
    st.metric("최종 대출 가능액", format_korean_currency(final_loan))
    if dsr_limit < ltv_limit:
        st.caption("⚠️ 소득 제한(DSR)으로 인해 한도가 줄어들었습니다.")
    else:
        st.caption(f"LTV {int(REGION_DATA[region]['LTV']*100)}% 한도 적용됨")

with c3:
    shortage = max(0, house_price + acquisition_tax - final_loan - my_cash)
    if shortage > 0:
        st.metric("부족한 금액", format_korean_currency(shortage), delta_color="inverse")
        st.error("현금이 부족하여 매수가 어렵습니다.")
    else:
        st.metric("추가 자금 여유", format_korean_currency(abs(shortage)))
        st.success("매수 가능권입니다! ✅")

st.divider()

# 금리 시나리오 비교 (2컬럼)
st.subheader("📈 금리 변동 시나리오 (현재 vs +1% 상승)")
sc1, sc2 = st.columns(2)

with sc1:
    st.info(f"**현재 금리 ({current_rate}%)**")
    st.markdown(f"### 월 {monthly_now:,} 원")
    st.write(f"연간 상환액: {format_korean_currency((monthly_now * 12)//10000)}")

with sc2:
    st.warning(f"**금리 상승 시 ({current_rate+1.0}%)**")
    st.markdown(f"### 월 {monthly_future:,} 원")
    st.write(f"추가 부담: 월 {monthly_future - monthly_now:,} 원")

# 차트
chart_data = pd.DataFrame({
    "금리 조건": ["현재 금리", "1% 인상"],
    "월 상환액(원)": [monthly_now, monthly_future]
})
st.bar_chart(data=chart_data, x="금리 조건", y="월 상환액(원)")

st.caption("※ 본 계산은 참고용이며, 실제 대출 금리와 한도는 금융기관의 심사 결과에 따라 달라집니다.")
