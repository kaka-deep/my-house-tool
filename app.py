import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="내 집 마련 시뮬레이터", layout="centered", page_icon="🏢")

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
    if n <= 0: return pd.DataFrame()
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
            schedule.append({
                "월": i, "상환액": int(monthly_payment), "원금": int(principal_pay), "이자": int(interest_pay), "잔금": int(max(0, remaining_principal))
            })
            
    else: # 원금균등
        principal_pay = principal_won / n
        for i in range(1, n + 1):
            interest_pay = remaining_principal * r
            monthly_payment = principal_pay + interest_pay
            remaining_principal -= principal_pay
            schedule.append({
                "월": i, "상환액": int(monthly_payment), "원금": int(principal_pay), "이자": int(interest_pay), "잔금": int(max(0, remaining_principal))
            })
    return pd.DataFrame(schedule)

# --- 메인 UI 시작 ---
st.title("🏠 내 집 마련 종합 시뮬레이터 v5.0")
st.markdown("자금 구성부터 상환 계획까지 한 페이지에서 확인하세요.")

# --- STEP 1: 주택 정보 및 LTV ---
st.subheader("1️⃣ 주택 정보 및 한도")
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

# --- STEP 3: 은행 대출 조건 ---
st.divider()
st.subheader("3️⃣ 은행 대출 조건 (자동 계산)")
cb1, cb2, cb3 = st.columns(3)
with cb1: bank_rate = st.number_input("은행 금리 (%)", value=4.2, step=0.1)
with cb2: bank_term = st.number_input("은행 기간 (년)", value=30, step=1)
with cb3: bank_method = st.selectbox("은행 상환 방식", ["원리금균등", "원금균등"], key="bank")

# --- 계산 로직 ---
# 취득세 (85㎡ 이하 기준 단순화)
tax_rate = 0.011 if house_price <= 60000 else (0.022 if house_price <= 90000 else 0.033)
acquisition_tax = house_price * tax_rate
total_cost = house_price + acquisition_tax

# 은행 대출 자동 계산 (필요금액 = 총비용 - 내돈 - 회사대출)
needed_bank = max(0, total_cost - my_cash - co_loan_amount)
# LTV 제한 적용 (회사대출 + 은행대출 합계가 LTV 한도 내여야 함이 일반적)
available_bank_limit = max(0, max_ltv_won - co_loan_amount)
final_bank_loan = min(needed_bank, available_bank_limit)

# 상환 스케줄
bank_sched = get_repayment_schedule(final_bank_loan, bank_rate, bank_term, bank_method)
co_sched = get_repayment_schedule(co_loan_amount, co_loan_rate, co_loan_term, co_method)

# 첫 달 상환액 및 DSR
monthly_bank = bank_sched["상환액"].iloc[0] if not bank_sched.empty else 0
monthly_co = co_sched["상환액"].iloc[0] if not co_sched.empty else 0
total_monthly = monthly_bank + monthly_co

annual_debt_pay = (monthly_bank + monthly_co) * 12 / 10000
dsr_value = (annual_debt_pay / annual_income) * 100

# --- 결과 발표 ---
st.divider()
st.subheader("💰 시뮬레이션 결과 리포트")

# 1. 자금 구성 차트 (누적 막대 그래프)
st.write("### 🏦 전체 자금 구성")
fund_data = pd.DataFrame({
    "항목": ["내 돈", "회사 대출", "은행 대출"],
    "금액(만원)": [my_cash, co_loan_amount, final_bank_loan]
})
fig = px.bar(fund_data, x="항목", y="금액(만원)", color="항목", 
             text=fund_data["금액(만원)"].apply(format_won),
             color_discrete_sequence=px.colors.qualitative.Pastel)
fig.update_layout(showlegend=False, height=400)
st.plotly_chart(fig, use_container_width=True)

# 2. 주요 지표 요약
shortage = max(0, total_cost - my_cash - co_loan_amount - final_bank_loan)

col_res1, col_res2 = st.columns(2)
with col_res1:
    st.write(f"📍 **총 소요 비용:** {format_won(total_cost)}")
    st.write(f"- 매매가: {format_won(house_price)}")
    st.write(f"- 취득세(예상): {format_won(acquisition_tax)}")
with col_res2:
    if shortage > 0:
        st.error(f"❌ **자금 부족:** {format_won(shortage)}")
        st.caption("현금이 더 필요하거나 LTV 한도를 확인하세요.")
    else:
        st.success("✅ **자금 계획 성공!** 모든 비용이 충당되었습니다.")

st.divider()

# 3. 상환액 및 DSR
st.write("### 💳 월 상환 계획")
c_m1, c_m2, c_m3 = st.columns(3)
c_m1.metric("총 월 상환액", f"{int(total_monthly):,}원")
c_m2.metric("DSR 지수", f"{dsr_value:.1f}%")
c_m3.metric("은행 대출금", format_won(final_bank_loan))

with st.expander("상세 상환 내역"):
    st.write(f"- 은행 ({bank_method}): 월 약 {int(monthly_bank):,}원")
    st.write(f"- 회사 ({co_method}): 월 약 {int(monthly_co):,}원")

# DSR 판정
if dsr_value <= 40:
    st.balloons()
    st.success("안정적인 수준입니다.")
elif dsr_value <= 50:
    st.warning("주의가 필요한 수준입니다.")
else:
    st.error("위험한 수준입니다. 대출 규모를 줄이는 것을 권장합니다.")

st.caption("※ 본 시뮬레이션은 입력된 수치를 기반으로 하며, 실제 대출 승인 및 금리는 금융기관에 따라 다를 수 있습니다.")
