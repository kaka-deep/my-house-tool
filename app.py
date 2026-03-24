import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="내 집 마련 시뮬레이터 v6.0", layout="centered", page_icon="🏢")

# --- 유틸리티 함수: 한글 화폐 단위 표시 ---
def format_won(val_man):
    if val_man <= 0: return "0원"
    uk = int(val_man // 10000)
    man = int(val_man % 10000)
    if uk > 0 and man > 0:
        return f"{uk:,}억 {man:,}만원"
    elif uk > 0:
        return f"{uk:,}억원"
    else:
        return f"{man:,}만원"

# --- 상환 방식별 계산 함수 ---
def get_repayment_schedule(principal_man, annual_rate, years, method):
    n = int(years * 12)
    if n <= 0 or principal_man <= 0: return pd.DataFrame()
    r = (annual_rate / 100) / 12
    principal_won = principal_man * 10000
    schedule = []
    remaining_principal = principal_won
    
    if method == "원리금균등":
        if r > 0:
            monthly_payment = principal_won * (r * (1+r)**n) / ((1+r)**n - 1)
        else:
            monthly_payment = principal_won / n
        for i in range(1, n + 1):
            interest_pay = remaining_principal * r
            principal_pay = monthly_payment - interest_pay
            remaining_principal -= principal_pay
            schedule.append({"월": i, "상환액": int(monthly_payment), "원금": int(principal_pay), "이자": int(interest_pay)})
    else: # 원금균등
        principal_pay = principal_won / n
        for i in range(1, n + 1):
            interest_pay = remaining_principal * r
            monthly_payment = principal_pay + interest_pay
            remaining_principal -= principal_pay
            schedule.append({"월": i, "상환액": int(monthly_payment), "원금": int(principal_pay), "이자": int(interest_pay)})
    return pd.DataFrame(schedule)

# --- 메인 UI 시작 ---
st.title("🏠 내 집 마련 시뮬레이터 v6.0")

# --- STEP 1: 주택 정보 및 LTV 한도 확인 ---
st.subheader("1️⃣ 주택 정보 및 LTV 한도")
col1, col2 = st.columns(2)
with col1:
    house_price = st.number_input("주택 매매가 (만원)", value=80000, step=1000)
    st.info(f"💰 매매가: **{format_won(house_price)}**")
with col2:
    ltv_input = st.number_input("적용 LTV (%)", value=70, min_value=0, max_value=100)
    max_ltv_won = house_price * ltv_input / 100
    st.info(f"📏 LTV 한도액: **{format_won(max_ltv_won)}**")

# --- STEP 2: 자금 및 소득 정보 ---
st.divider()
st.subheader("2️⃣ 나의 자금 및 소득")
c2_1, c2_2 = st.columns(2)
with c2_1:
    my_cash = st.number_input("보유 현금 (만원)", value=30000, step=1000)
    st.write(f"👉 {format_won(my_cash)}")
with c2_2:
    income_type = st.radio("소득 구분", ["개인", "부부합산"], horizontal=True)
    annual_income = st.number_input(f"{income_type} 연봉 (만원)", value=6000, step=500)
    st.write(f"👉 {format_won(annual_income)}")

with st.expander("🏢 회사 대출(복지기금) 설정"):
    co_loan_amount = st.number_input("회사 대출액 (만원)", value=0, step=500)
    st.write(f"👉 **{format_won(co_loan_amount)}**")
    cc1, cc2, cc3 = st.columns(3)
    with cc1: co_loan_rate = st.number_input("회사 금리 (%)", value=2.0, step=0.1)
    with cc2: co_loan_term = st.number_input("회사 기간 (년)", value=10, step=1)
    with cc3: co_method = st.selectbox("회사 상환 방식", ["원리금균등", "원금균등"], key="co")

# --- STEP 3: 은행 대출 신청 ---
st.divider()
st.subheader("3️⃣ 은행 주택담보대출 설정")
col_b1, col_b2 = st.columns(2)
with col_b1:
    bank_loan_amount = st.number_input("은행 대출 신청액 (만원)", value=30000, step=1000)
    st.write(f"👉 **{format_won(bank_loan_amount)}**")
with col_b2:
    bank_method = st.selectbox("은행 상환 방식", ["원리금균등", "원금균등"], key="bank")

cb1, cb2 = st.columns(2)
with cb1: bank_rate = st.number_input("은행 금리 (%)", value=4.2, step=0.1)
with cb2: bank_term = st.number_input("은행 기간 (년)", value=30, step=1)

# --- 계산 로직 ---
tax_rate = 0.011 if house_price <= 60000 else (0.022 if house_price <= 90000 else 0.033)
acquisition_tax = house_price * tax_rate
total_cost = house_price + acquisition_tax

# 자금 분석
total_funding = my_cash + co_loan_amount + bank_loan_amount
shortage = total_cost - total_funding

# 상환액 및 DSR (은행 + 회사)
bank_sched = get_repayment_schedule(bank_loan_amount, bank_rate, bank_term, bank_method)
co_sched = get_repayment_schedule(co_loan_amount, co_loan_rate, co_loan_term, co_method)

monthly_bank = bank_sched["상환액"].iloc[0] if not bank_sched.empty else 0
monthly_co = co_sched["상환액"].iloc[0] if not co_sched.empty else 0
total_monthly = monthly_bank + monthly_co
annual_debt_pay = total_monthly * 12 / 10000
dsr_value = (annual_debt_pay / annual_income) * 100

# --- 결과 발표 ---
st.divider()
st.subheader("💰 시뮬레이션 결과 리포트")

# 1. 자금 구성 차트
fund_data = pd.DataFrame({
    "항목": ["내 돈", "회사 대출", "은행 대출"],
    "금액(만원)": [my_cash, co_loan_amount, bank_loan_amount]
})
fig = px.bar(fund_data, x="항목", y="금액(만원)", color="항목", 
             text=fund_data["금액(만원)"].apply(format_won),
             color_discrete_sequence=px.colors.qualitative.Pastel)
fig.update_layout(showlegend=False, height=350, margin=dict(t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

# 2. 핵심 요약 (간결한 안내 문구)
c_res1, c_res2 = st.columns(2)
with c_res1:
    st.write(f"📍 **총 비용:** {format_won(total_cost)}")
    if shortage > 0:
        st.error(f"⚠️ **자금 부족:** {format_won(shortage)}")
    else:
        st.success(f"✅ **자금 충당 완료** (여유: {format_won(abs(shortage))})")

with c_res2:
    total_loan = bank_loan_amount + co_loan_amount
    if total_loan > max_ltv_won:
        st.error(f"🚨 **LTV 한도 초과:** {format_won(total_loan - max_ltv_won)} 초과")
    else:
        st.success("✅ **대출 한도 이내**")

st.divider()

# 3. 월 상환 및 DSR
st.write("### 💳 월 상환 계획")
m1, m2, m3 = st.columns(3)
m1.metric("월 상환액", f"{int(total_monthly):,}원")
m2.metric("DSR 지수", f"{dsr_value:.1f}%")
m3.metric("최종 대출합계", format_won(bank_loan_amount + co_loan_amount))

# DSR 한줄 평
if dsr_value <= 40: st.info("상환 능력이 충분합니다.")
elif dsr_value <= 50: st.warning("상환 부담이 다소 있습니다.")
else: st.error("상환이 매우 위험한 수준입니다.")

st.caption("※ 본 시뮬레이션은 입력값을 바탕으로 계산되었으며, 실제 대출 승인 결과와 차이가 있을 수 있습니다.")
