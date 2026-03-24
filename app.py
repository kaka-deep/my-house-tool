import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 설정
st.set_page_config(page_title="내 집 마련 시뮬레이터 v4.0", layout="centered", page_icon="🏢")

# --- 유틸리티 함수: 한글 화폐 단위 표시 ---
def format_won(val_man):
    if val_man <= 0: return "0원"
    uk = val_man // 10000
    man = val_man % 10000
    if uk > 0 and man > 0:
        return f"{int(uk):,}억 {int(man):,}만원"
    elif uk > 0:
        return f"{int(uk):,}억원"
    else:
        return f"{int(man):,}만원"

# --- 상환 방식별 계산 함수 ---
def get_repayment_schedule(principal_man, annual_rate, years, method):
    n = int(years * 12)
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
                "월": i,
                "상환액": int(monthly_payment),
                "원금": int(principal_pay),
                "이자": int(interest_pay),
                "잔금": int(max(0, remaining_principal))
            })
            
    else: # 원금균등
        principal_pay = principal_won / n
        for i in range(1, n + 1):
            interest_pay = remaining_principal * r
            monthly_payment = principal_pay + interest_pay
            remaining_principal -= principal_pay
            schedule.append({
                "월": i,
                "상환액": int(monthly_payment),
                "원금": int(principal_pay),
                "이자": int(interest_pay),
                "잔금": int(max(0, remaining_principal))
            })
    return pd.DataFrame(schedule)

# --- 메인 UI 시작 ---
st.title("🏠 내 집 마련 시뮬레이터 v4.0")

# --- STEP 1: 주택 정보 및 LTV ---
st.subheader("1️⃣ 주택 정보 및 대출 한도 설정")
col1_1, col1_2 = st.columns(2)
with col1_1:
    house_price = st.number_input("주택 매매가 (만원)", value=80000, step=1000)
    st.caption(f"👉 {format_won(house_price)}")
with col1_2:
    ltv_input = st.number_input("적용 LTV (%)", value=70, min_value=0, max_value=100)
    st.caption(f"최대 대출 가능액: {format_won(house_price * ltv_input / 100)}")

# --- STEP 2: 자금 및 소득 정보 ---
st.divider()
st.subheader("2️⃣ 나의 자금 및 소득")
col2_1, col2_2 = st.columns(2)
with col2_1:
    my_cash = st.number_input("보유 현금 (만원)", value=30000, step=1000)
    st.caption(f"👉 {format_won(my_cash)}")
with col2_2:
    annual_income = st.number_input("연봉 (만원)", value=6000, step=500)
    st.caption(f"👉 {format_won(annual_income)}")

with st.expander("🏢 회사 대출 / 기타 대출 정보 (선택)"):
    co_loan_amount = st.number_input("회사 대출액 (만원)", value=0, step=500)
    co_loan_rate = st.number_input("회사 대출 금리 (%)", value=2.0, step=0.1)
    co_loan_term = st.number_input("회사 대출 기간 (년)", value=10, step=1)
    co_method = st.selectbox("회사 대출 상환 방식", ["원리금균등", "원금균등"], key="co")
    other_annual_pay = st.number_input("기타 대출 연간 상환액 (만원)", value=0, step=100, help="신용대출, 자동차 할부 등")

# --- STEP 3: 은행 대출 및 상환 방식 ---
st.divider()
st.subheader("3️⃣ 은행 대출 조건 설정")
col3_1, col3_2, col3_3 = st.columns(3)
with col3_1:
    bank_rate = st.number_input("은행 금리 (%)", value=4.2, step=0.1)
with col3_2:
    bank_term = st.number_input("대출 기간 (년)", value=30, step=1)
with col3_3:
    bank_method = st.selectbox("은행 상환 방식", ["원리금균등", "원금균등"], key="bank")

# --- 계산 로직 ---
# 취득세 (85㎡ 이하 기준 단순화)
tax_rate = 0.011 if house_price <= 60000 else (0.022 if house_price <= 90000 else 0.033)
total_needed = house_price + (house_price * tax_rate)

# 은행 대출액 결정 (한도 내에서 부족한 만큼)
max_bank_by_ltv = (house_price * ltv_input / 100) - co_loan_amount
needed_bank = max(0, total_needed - my_cash - co_loan_amount)
final_bank_loan = min(max_bank_by_ltv, needed_bank)

# 스케줄 생성
bank_sched = get_repayment_schedule(final_bank_loan, bank_rate, bank_term, bank_method)
co_sched = get_repayment_schedule(co_loan_amount, co_loan_rate, co_loan_term, co_method)

# 첫 달 상환액 및 연간 상환액(DSR용)
first_month_pay = bank_sched["상환액"].iloc[0] + (co_sched["상환액"].iloc[0] if not co_sched.empty else 0)
annual_bank_pay = bank_sched["상환액"].sum() / bank_term if not bank_sched.empty else 0
annual_co_pay = co_sched["상환액"].sum() / co_loan_term if not co_sched.empty else 0
total_annual_debt_pay = (annual_bank_pay + annual_co_pay + (other_annual_pay * 10000)) / 10000

# DSR 계산
dsr_value = (total_annual_debt_pay / annual_income) * 100

# --- 결과 발표 ---
st.divider()
st.subheader("💰 시뮬레이션 결과 리포트")

# 결과 지표 표시
m1, m2, m3 = st.columns(3)
m1.metric("총 필요 자금", format_won(total_needed))
m2.metric("은행 대출액", format_won(final_bank_loan))
m3.metric("DSR 지수", f"{dsr_value:.1f}%")

# DSR 기반 판정
if dsr_value <= 40:
    st.success(f"✅ **[안전]** DSR {dsr_value:.1f}%로 대출 실행 및 상환이 안정적인 수준입니다.")
elif dsr_value <= 50:
    st.warning(f"⚠️ **[주의]** DSR {dsr_value:.1f}%로 소득의 절반 가까이가 원리금 상환에 쓰입니다.")
else:
    st.error(f"🚨 **[위험]** DSR {dsr_value:.1f}%입니다. 은행 대출이 거절되거나 생활에 무리가 올 수 있습니다.")

# 상세 요약
with st.container():
    st.write(f"📌 **첫 달 상환액:** {int(first_month_pay):,}원 ({bank_method} 기준)")
    shortage = max(0, total_needed - my_cash - co_loan_amount - final_bank_loan)
    if shortage > 0:
        st.error(f"❗ 자금이 {format_won(shortage)} 부족합니다. 현금을 더 확보하거나 대출을 늘려야 합니다.")

# --- 상환 추세 그래프 ---
st.divider()
st.subheader("📉 대출 상환 추세 비교")

# 데이터 정리 (연단위 요약)
bank_sched['year'] = (bank_sched['월'] - 1) // 12 + 1
annual_trend = bank_sched.groupby('year')[['원금', '이자']].sum() / 10000 # 만원 단위

st.write("은행 대출 연도별 원금/이자 구성 변화")
st.bar_chart(annual_trend)

# 금리 +1% 비교
bank_sched_up = get_repayment_schedule(final_bank_loan, bank_rate + 1.0, bank_term, bank_method)
monthly_up_diff = bank_sched_up["상환액"].iloc[0] - bank_sched["상환액"].iloc[0]
st.info(f"💡 만약 금리가 1% 상승한다면, 첫 달 상환액이 **{int(monthly_up_diff):,}원** 증가합니다.")

st.caption("※ 본 시뮬레이션은 입력값을 바탕으로 계산된 수치이며, 실제 대출 가능 여부와 금리는 금융기관을 통해 확인해야 합니다.")
