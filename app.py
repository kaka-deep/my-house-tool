import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="내 집 마련 시뮬레이터 v7.0", layout="centered", page_icon="🏢")

# --- 유틸리티 함수: 한글 화폐 단위 표시 ---
def format_won(val_man):
    if val_man == 0: return "0원"
    abs_val = abs(val_man)
    uk = int(abs_val // 10000)
    man = int(abs_val % 10000)
    res = ""
    if uk > 0: res += f"{uk:,}억 "
    if man > 0 or uk == 0: res += f"{man:,}만원"
    return f"-{res.strip()}" if val_man < 0 else res.strip()

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
            schedule.append({"상환액": int(monthly_payment)})
    else: # 원금균등
        principal_pay = principal_won / n
        for i in range(1, n + 1):
            interest_pay = remaining_principal * r
            monthly_payment = principal_pay + interest_pay
            remaining_principal -= principal_pay
            schedule.append({"상환액": int(monthly_payment)})
    return pd.DataFrame(schedule)

# --- 메인 UI ---
st.title("🏠 내 집 마련 시뮬레이터 v7.0")

# STEP 1, 2, 3 입력부 (기존과 동일하되 레이아웃 정리)
with st.container():
    st.subheader("1️⃣ 주택 및 한도 설정")
    c1, c2 = st.columns(2)
    house_price = c1.number_input("주택 매매가 (만원)", value=80000, step=1000)
    ltv_input = c2.number_input("적용 LTV (%)", value=70, min_value=0, max_value=100)
    tax_rate = 0.011 if house_price <= 60000 else (0.022 if house_price <= 90000 else 0.033)
    total_cost = house_price + (house_price * tax_rate)
    max_ltv_won = house_price * ltv_input / 100
    st.caption(f"📍 총 소요 비용(세금포함): {format_won(total_cost)} | LTV 한도: {format_won(max_ltv_won)}")

st.divider()

with st.container():
    st.subheader("2️⃣ 자금 및 소득")
    c3, c4 = st.columns(2)
    my_cash = c3.number_input("보유 현금 (만원)", value=30000, step=1000)
    annual_income = c4.number_input("연봉 (만원)", value=6000, step=500)
    
    with st.expander("🏢 회사 대출 설정"):
        co_loan_amount = st.number_input("회사 대출액 (만원)", value=0, step=500)
        cc1, cc2 = st.columns(2)
        co_loan_rate = cc1.number_input("회사 금리 (%)", value=2.0)
        co_loan_term = cc2.number_input("회사 기간 (년)", value=10)

st.divider()

with st.container():
    st.subheader("3️⃣ 은행 대출 설정")
    c5, c6 = st.columns(2)
    bank_loan_amount = c5.number_input("은행 대출 신청액 (만원)", value=30000, step=1000)
    bank_rate = c6.number_input("은행 금리 (%)", value=4.2)
    c7, c8 = st.columns(2)
    bank_term = c7.number_input("은행 기간 (년)", value=30)
    bank_method = c8.selectbox("상환 방식", ["원리금균등", "원금균등"])

# --- 계산 ---
total_funding = my_cash + co_loan_amount + bank_loan_amount
diff = total_funding - total_cost # (+)면 초과/충당, (-)면 부족

# --- 결과 발표 ---
st.divider()
st.subheader("💰 시뮬레이션 결과 리포트")

# 1. 자금 비중 도넛 차트
if total_funding > 0:
    fund_df = pd.DataFrame({
        "항목": ["내 돈", "회사 대출", "은행 대출"],
        "금액": [my_cash, co_loan_amount, bank_loan_amount]
    })
    # 금액이 0인 항목은 차트에서 제외
    fund_df = fund_df[fund_df["금액"] > 0]
    
    fig = px.pie(fund_df, values='금액', names='항목', hole=0.5,
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False, height=300, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

# 2. 자금 상태 요약 문구
st.markdown(f"### 자금 구성 요약")
if diff > 0:
    st.info(f"✅ 총 비용 대비 **{format_won(diff)}**만큼 자금이 **초과(여유)** 상태입니다.")
elif diff == 0:
    st.success(f"✅ 총 비용과 준비된 자금이 **정확히 일치**합니다.")
else:
    st.error(f"⚠️ 총 비용 대비 **{format_won(abs(diff))}**만큼 자금이 **부족**합니다.")

# 3. 경고 및 안내 (한 줄씩 깔끔하게 배치)
total_loan = bank_loan_amount + co_loan_amount
if total_loan > max_ltv_won:
    st.warning(f"🚨 **LTV 한도 초과:** 신청하신 대출 합계({format_won(total_loan)})가 한도({format_won(max_ltv_won)})를 **{format_won(total_loan - max_ltv_won)}** 초과했습니다.")
else:
    st.write(f"🆗 **LTV 한도 준수:** 현재 대출 비중은 매수가 대비 **{(total_loan/house_price)*100:.1f}%**입니다.")

# 4. 상환 및 DSR
bank_sched = get_repayment_schedule(bank_loan_amount, bank_rate, bank_term, bank_method)
co_sched = get_repayment_schedule(co_loan_amount, co_loan_rate, co_loan_term, "원리금균등")
monthly_total = (bank_sched["상환액"].iloc[0] if not bank_sched.empty else 0) + \
                (co_sched["상환액"].iloc[0] if not co_sched.empty else 0)
dsr = (monthly_total * 12 / 10000) / annual_income * 100

st.divider()
col_f1, col_f2 = st.columns(2)
col_f1.metric("월 상환액 (합계)", f"{int(monthly_total):,}원")
col_f2.metric("DSR 지수", f"{dsr:.1f}%")

if dsr > 40:
    st.error(f"❗ DSR이 {dsr:.1f}%로 높습니다. 대출 승인이 어려울 수 있으니 주의하세요.")

st.caption("※ 본 리포트는 입력한 매매가와 취득세(기본세율)를 기준으로 작성되었습니다.")
