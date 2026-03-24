import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="내 집 마련 시뮬레이터", layout="centered", page_icon="🏢")

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

# --- 상환 방식별 스케줄 계산 함수 ---
def get_full_schedule(principal_man, annual_rate, years, method):
    n = int(years * 12)
    if n <= 0 or principal_man <= 0: return pd.DataFrame()
    r = (annual_rate / 100) / 12
    p_won = principal_man * 10000
    schedule = []
    rem_p = p_won
    
    for i in range(1, n + 1):
        if method == "원리금균등":
            m_pay = p_won * (r * (1+r)**n) / ((1+r)**n - 1) if r > 0 else p_won / n
            int_pay = rem_p * r
            pri_pay = m_pay - int_pay
        else: # 원금균등
            pri_pay = p_won / n
            int_pay = rem_p * r
            m_pay = pri_pay + int_pay
        
        rem_p -= pri_pay
        schedule.append({
            "month": i,
            "year": (i-1)//12 + 1,
            "total": int(m_pay),
            "principal": int(pri_pay),
            "interest": int(int_pay)
        })
    return pd.DataFrame(schedule)

# --- 메인 UI ---
st.title("🏠 내 집 마련 시뮬레이터 v8.0")

# 1️⃣ 주택 정보
st.subheader("1️⃣ 주택 정보 및 한도")
c1, c2 = st.columns(2)
with c1:
    house_price = st.number_input("주택 매매가 (만원)", value=80000, step=1000)
    st.caption(f"👉 **{format_won(house_price)}**")
with c2:
    ltv_input = st.number_input("적용 LTV (%)", value=70, min_value=0, max_value=100)
    max_ltv_won = house_price * ltv_input / 100
    st.caption(f"최대 한도: {format_won(max_ltv_won)}")

tax_rate = 0.011 if house_price <= 60000 else (0.022 if house_price <= 90000 else 0.033)
total_cost = house_price + (house_price * tax_rate)

st.divider()

# 2️⃣ 자금 및 소득
st.subheader("2️⃣ 나의 자금 및 소득")
c3, c4 = st.columns(2)
with c3:
    my_cash = st.number_input("보유 현금 (만원)", value=30000, step=1000)
    st.caption(f"👉 **{format_won(my_cash)}**")
with c4:
    annual_income = st.number_input("연봉 (만원)", value=6000, step=500)
    st.caption(f"👉 **{format_won(annual_income)}**")

with st.expander("🏢 회사 대출(복지기금) 설정"):
    co_loan_amount = st.number_input("회사 대출액 (만원)", value=0, step=500)
    st.caption(f"👉 **{format_won(co_loan_amount)}**")
    cc1, cc2, cc3 = st.columns(3)
    co_loan_rate = cc1.number_input("회사 금리 (%)", value=2.0)
    co_loan_term = cc2.number_input("회사 기간 (년)", value=10)
    co_method = cc3.selectbox("회사 상환", ["원리금균등", "원금균등"])

st.divider()

# 3️⃣ 은행 대출
st.subheader("3️⃣ 은행 대출 설정")
c5, c6 = st.columns(2)
with c5:
    bank_loan_amount = st.number_input("은행 대출 신청액 (만원)", value=30000, step=1000)
    st.caption(f"👉 **{format_won(bank_loan_amount)}**")
with c6:
    bank_rate = st.number_input("은행 금리 (%)", value=4.2)

c7, c8 = st.columns(2)
with c7:
    bank_term = st.number_input("은행 기간 (년)", value=30)
with c8:
    bank_method = st.selectbox("은행 상환", ["원리금균등", "원금균등"])

# --- 계산 ---
total_funding = my_cash + co_loan_amount + bank_loan_amount
diff = total_funding - total_cost

# --- 결과 발표 ---
st.divider()
st.subheader("💰 시뮬레이션 결과 리포트")

# 1. 자금 비중 차트
if total_funding > 0:
    fund_df = pd.DataFrame({
        "항목": ["내 돈", "회사 대출", "은행 대출"],
        "금액": [my_cash, co_loan_amount, bank_loan_amount]
    })
    fund_df = fund_df[fund_df["금액"] > 0]
    fig = px.pie(fund_df, values='금액', names='항목', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(showlegend=True, height=300, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

# 2. 자금 상태 요약 (한 줄씩 배치)
if diff > 0:
    st.info(f"✅ 자금 계획: **{format_won(diff)}** 초과 (여유)")
elif diff == 0:
    st.success(f"✅ 자금 계획: 총 비용과 **정확히 일치**합니다.")
else:
    st.error(f"⚠️ 자금 계획: **{format_won(abs(diff))}** 부족합니다.")

total_loan = bank_loan_amount + co_loan_amount
if total_loan > max_ltv_won:
    st.warning(f"🚨 LTV 한도: 신청액({format_won(total_loan)})이 한도({format_won(max_ltv_won)})를 **{format_won(total_loan - max_ltv_won)}** 초과")
else:
    st.write(f"🆗 LTV 한도: 규정 준수 (매수가 대비 **{(total_loan/house_price)*100:.1f}%**)")

# 3. 상환 추이 그래프 및 DSR
bank_sched = get_full_schedule(bank_loan_amount, bank_rate, bank_term, bank_method)
co_sched = get_full_schedule(co_loan_amount, co_loan_rate, co_loan_term, co_method)

# 상환액 합산 로직 (연도별)
max_years = int(max(bank_term, co_loan_term))
annual_data = []

for y in range(1, max_years + 1):
    b_year = bank_sched[bank_sched['year'] == y] if not bank_sched.empty else pd.DataFrame()
    c_year = co_sched[co_sched['year'] == y] if not co_sched.empty else pd.DataFrame()
    
    annual_data.append({
        "연도": f"{y}년차",
        "은행 원금": b_year['principal'].sum() / 10000 if not b_year.empty else 0,
        "은행 이자": b_year['interest'].sum() / 10000 if not b_year.empty else 0,
        "회사 원리금": (c_year['principal'].sum() + c_year['interest'].sum()) / 10000 if not c_year.empty else 0
    })

df_annual = pd.DataFrame(annual_data)

st.divider()
st.subheader("📉 통합 상환 추이 (연도별)")
fig_trend = go.Figure()
fig_trend.add_trace(go.Bar(x=df_annual["연도"], y=df_annual["은행 원금"], name="은행 원금"))
fig_trend.add_trace(go.Bar(x=df_annual["연도"], y=df_annual["은행 이자"], name="은행 이자"))
fig_trend.add_trace(go.Bar(x=df_annual["연도"], y=df_annual["회사 원리금"], name="회사 대출(원리금)"))
fig_trend.update_layout(barmode='stack', height=400, margin=dict(t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig_trend, use_container_width=True)

# 4. 상환 요약 지표
monthly_bank = bank_sched["total"].iloc[0] if not bank_sched.empty else 0
monthly_co = co_sched["total"].iloc[0] if not co_sched.empty else 0
total_m = monthly_bank + monthly_co
dsr = (total_m * 12 / 10000) / annual_income * 100

col_f1, col_f2 = st.columns(2)
col_f1.metric("첫 달 합계 상환액", f"{int(total_m):,}원")
col_f2.metric("DSR 지수", f"{dsr:.1f}%")

if dsr > 40:
    st.error(f"🚨 DSR {dsr:.1f}%: 상환 부담이 매우 높거나 대출이 거절될 수 있습니다.")

st.caption(f"※ 총 지불 이자 예상액: {format_won((bank_sched['interest'].sum() + co_sched['interest'].sum())/10000)}")
