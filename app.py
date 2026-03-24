import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="내 집 마련 시뮬레이터", layout="centered", page_icon="🏢")

# 스타일 커스텀
st.markdown("""
    <style>
    .small-font { font-size: 1.1rem !important; font-weight: 600; color: #E0E0E0 !important; }
    .main-val { font-size: 2.2rem !important; font-weight: 800; color: #FFFFFF !important; margin-bottom: 5px; }
    .sub-val { font-size: 0.95rem; color: #BDBDBD !important; line-height: 1.6; }
    .milestone-box { background-color: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border-left: 5px solid #EB984E; margin-bottom: 20px; }
    .notice-box { background-color: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-top: 30px; }
    .notice-title { font-weight: 700; color: #F1C40F; margin-bottom: 10px; }
    .notice-item { font-size: 0.85rem; color: #CCCCCC; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 유틸리티 함수 ---
def format_won(val_man):
    if val_man == 0: return "0원"
    abs_val = abs(val_man)
    uk = int(abs_val // 10000)
    man = int(abs_val % 10000)
    res = ""
    if uk > 0: res += f"{uk:,}억 "
    if man > 0 or uk == 0: res += f"{man:,}만원"
    return f"-{res.strip()}" if val_man < 0 else res.strip()

# 거치 기간 로직이 포함된 스케줄 함수
def get_full_schedule(principal_man, annual_rate, total_years, method, grace_years=0):
    n = int(total_years * 12)
    g = int(grace_years * 12)
    cols = ["month", "year", "total", "principal", "interest", "balance"]
    if n <= 0 or principal_man <= 0:
        return pd.DataFrame(columns=cols)
        
    r = (annual_rate / 100) / 12
    p_won = principal_man * 10000
    schedule = []
    rem_p = p_won
    
    amort_months = max(1, n - g) # 원금 상환이 일어나는 실제 개월 수

    for i in range(1, n + 1):
        if i <= g: # 거치 기간 (이자만 납부)
            int_pay = rem_p * r
            pri_pay = 0
            m_pay = int_pay
        else: # 상환 기간
            curr_idx = i - g
            if method == "원리금균등":
                m_pay = p_won * (r * (1+r)**amort_months) / ((1+r)**amort_months - 1) if r > 0 else p_won / amort_months
                int_pay = rem_p * r
                pri_pay = m_pay - int_pay
            else: # 원금균등
                pri_pay = p_won / amort_months
                int_pay = rem_p * r
                m_pay = pri_pay + int_pay
            rem_p -= pri_pay
            
        schedule.append({
            "month": i, "year": (i-1)//12 + 1, 
            "total": int(m_pay), "principal": int(pri_pay), 
            "interest": int(int_pay), "balance": int(max(0, rem_p))
        })
    return pd.DataFrame(schedule)

# --- UI 입력부 ---
st.title("🏠 내 집 마련 시뮬레이터")

# 1️⃣ 주택 정보
st.subheader("1️⃣ 주택 정보 및 한도")
c1, c2 = st.columns(2)
house_price = c1.number_input("주택 매매가 (만원)", value=80000, step=1000)
c1.caption(f"👉 **{format_won(house_price)}**")
ltv_input = c2.number_input("적용 LTV (%)", value=70, min_value=0, max_value=100)
max_ltv_won = house_price * ltv_input / 100
c2.caption(f"최대 한도: {format_won(max_ltv_won)}")
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
    c_sub1, c_sub2 = st.columns([1, 2]) 
    income_type = c_sub1.selectbox("소득 구분", ["개인", "부부합산"])
    annual_income = c_sub2.number_input(f"{income_type} 연봉 (만원)", value=6000, step=500)
    st.caption(f"👉 **{format_won(annual_income)}**")

with st.expander("🏢 회사 대출(복지기금) 설정"):
    co_loan_amount = st.number_input("회사 대출액 (만원)", value=0, step=500)
    st.caption(f"👉 **{format_won(co_loan_amount)}**")
    cc1, cc2, cc3 = st.columns(3)
    co_loan_rate = cc1.number_input("회사 금리 (%)", value=2.0)
    co_loan_term = cc2.number_input("회사 기간 (년)", value=10)
    co_method = cc3.selectbox("회사 상환", ["원리금균등", "원금균등"])
    # 거치 기간 추가
    co_grace_period = st.selectbox("회사 대출 거치 기간 (년)", range(11), index=0, help="원금 상환 없이 이자만 내는 유예 기간입니다.")

st.divider()

# 3️⃣ 은행 대출
st.subheader("3️⃣ 은행 대출 설정")
c5, c6 = st.columns(2)
bank_loan_amount = c5.number_input("은행 대출 신청액 (만원)", value=30000, step=1000)
c5.caption(f"👉 **{format_won(bank_loan_amount)}**")
bank_rate = c6.number_input("은행 금리 (%)", value=4.2)
c7, c8 = st.columns(2)
bank_term = c7.number_input("은행 기간 (년)", value=30)
bank_method = c8.selectbox("은행 상환", ["원리금균등", "원금균등"])

# --- 계산 및 데이터 통합 ---
total_funding = my_cash + co_loan_amount + bank_loan_amount
diff = total_funding - total_cost
bank_sched = get_full_schedule(bank_loan_amount, bank_rate, bank_term, bank_method, grace_years=0)
co_sched = get_full_schedule(co_loan_amount, co_loan_rate, co_loan_term, co_method, grace_years=co_grace_period)

# 통합 데이터
max_m = int(max(bank_term * 12, co_loan_term * 12)) if max(bank_term, co_loan_term) > 0 else 1
monthly_rows = []
for m in range(1, max_m + 1):
    b_m = bank_sched[bank_sched['month'] == m].iloc[0] if m <= len(bank_sched) else None
    c_m = co_sched[co_sched['month'] == m].iloc[0] if m <= len(co_sched) else None
    b_total = b_m['total'] if b_m is not None else 0
    c_total = c_m['total'] if c_m is not None else 0
    monthly_rows.append({"month": m, "은행": b_total, "회사": c_total, "합계": b_total + c_total})
df_monthly = pd.DataFrame(monthly_rows)

# --- 결과 리포트 ---
st.divider()
st.subheader("💰 시뮬레이션 결과 리포트")

if diff > 0: st.info(f"✅ 자금 계획: **{format_won(diff)}** 초과 (여유)")
elif diff == 0: st.success(f"✅ 자금 계획: 총 비용과 정확히 일치합니다.")
else: st.error(f"⚠️ 자금 계획: **{format_won(abs(diff))}** 부족합니다.")

# 📉 상환 추이 그래프
st.write("### 📉 월별 상환 부담 추이")
fig_monthly = go.Figure()
fig_monthly.add_trace(go.Scatter(x=df_monthly["month"], y=df_monthly["은행"], name="은행 상환", fill='tozeroy', line_color='#2E86C1'))
fig_monthly.add_trace(go.Scatter(x=df_monthly["month"], y=df_monthly["합계"], name="총 상환액", fill='tonexty', line_color='#EB984E'))
fig_monthly.update_layout(height=350, hovermode="x unified", legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, font=dict(color="white")),
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), margin=dict(t=20, b=80))
st.plotly_chart(fig_monthly, use_container_width=True)

# 주요 시점 알림
if co_grace_period > 0 and co_loan_amount > 0:
    jump_val = df_monthly.iloc[int(co_grace_period*12+1)]["합계"] - df_monthly.iloc[0]["합계"]
    st.markdown(f'<div class="milestone-box"><b>⚠️ 유의 시점:</b> {co_grace_period}년 뒤 회사 대출 거치가 종료되면 월 상환액이 약 <b>{int(jump_val/10000):,}만원</b> 증가합니다.</div>', unsafe_allow_html=True)

# 지표 표시
total_m = df_monthly["합계"].iloc[0] if not df_monthly.empty else 0
dsr = (total_m * 12 / 10000) / annual_income * 100 if annual_income > 0 else 0
c_m1, c_m2 = st.columns(2)
with c_m1:
    st.markdown(f'<p class="small-font">첫 달 상환액</p><p class="main-val">{int(total_m):,}원</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-val">🏦 은행: {int(df_monthly["은행"].iloc[0]):,}원<br>🏢 회사: {int(df_monthly["회사"].iloc[0]):,}원</p>', unsafe_allow_html=True)
with c_m2:
    st.markdown(f'<p class="small-font">DSR 지수</p><p class="main-val">{dsr:.1f}%</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-val">연간 상환액: {format_won(total_m*12/10000)}<br>연 소득 대비 비중: {dsr:.1f}%</p>', unsafe_allow_html=True)

# ⚠️ 유의사항 섹션
st.markdown(f"""
<div class="notice-box">
    <div class="notice-title">📢 사용 전 반드시 읽어주세요</div>
    <div class="notice-item">1. <b>전문 상담 필수:</b> 본 결과는 입력값을 바탕으로 한 단순 시뮬레이션입니다. 정확한 한도와 금리는 반드시 대출 예정 은행을 방문하여 상담받으시기 바랍니다.</div>
    <div class="notice-item">2. <b>이자 방식 확인:</b> 금융기관마다 상환 방식(원리금/원금)에 따른 우대 금리 조건이 다를 수 있습니다.</div>
    <div class="notice-item">3. <b>규제 변동성:</b> 정부 정책(LTV, DSR 규제)은 수시로 변경될 수 있으며, 개인 신용 점수에 따라 결과가 상이할 수 있습니다.</div>
    <div class="notice-item">4. <b>부대 비용 고려:</b> 실제 매수 시에는 인지세, 채권 할인, 법무 대행비, 중개 수수료 등 약 1~2%의 추가 자금이 더 필요할 수 있습니다.</div>
</div>
""", unsafe_allow_html=True)

st.caption(f"※ 예상 총 이자 지불액: {format_won((bank_sched['interest'].sum() + co_sched['interest'].sum())/10000)}")
