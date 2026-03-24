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

def get_full_schedule(principal_man, annual_rate, years, method):
    n = int(years * 12)
    cols = ["month", "year", "total", "principal", "interest", "balance"]
    if n <= 0 or principal_man <= 0:
        return pd.DataFrame(columns=cols)
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
            "month": i, "year": (i-1)//12 + 1, 
            "total": int(m_pay), "principal": int(pri_pay), 
            "interest": int(int_pay), "balance": int(max(0, rem_p))
        })
    return pd.DataFrame(schedule)

# --- UI 입력부 (기존과 동일) ---
st.title("🏠 내 집 마련 시뮬레이터")

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

st.divider()

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
bank_sched = get_full_schedule(bank_loan_amount, bank_rate, bank_term, bank_method)
co_sched = get_full_schedule(co_loan_amount, co_loan_rate, co_loan_term, co_method)

# 월별 통합 데이터 프레임 생성
max_m = int(max(bank_term * 12, co_loan_term * 12)) if max(bank_term, co_loan_term) > 0 else 1
monthly_rows = []
for m in range(1, max_m + 1):
    b_m = bank_sched[bank_sched['month'] == m].iloc[0] if m <= len(bank_sched) else None
    c_m = co_sched[co_sched['month'] == m].iloc[0] if m <= len(co_sched) else None
    
    b_total = b_m['total'] if b_m is not None else 0
    c_total = c_m['total'] if c_m is not None else 0
    b_bal = b_m['balance'] if b_m is not None else 0
    c_bal = c_m['balance'] if c_m is not None else 0
    
    monthly_rows.append({
        "month": m, "year": (m-1)//12 + 1,
        "은행 상환": b_total, "회사 상환": c_total,
        "합계 상환": b_total + c_total,
        "남은 부채": (b_bal + c_bal) / 10000
    })
df_monthly = pd.DataFrame(monthly_rows)

# --- 결과 리포트 ---
st.divider()
st.subheader("💰 시뮬레이션 결과 리포트")

if diff > 0: st.info(f"✅ 자금 계획: **{format_won(diff)}** 초과 (여유)")
elif diff == 0: st.success(f"✅ 자금 계획: 총 비용과 정확히 일치합니다.")
else: st.error(f"⚠️ 자금 계획: **{format_won(abs(diff))}** 부족합니다.")

# 📉 [업데이트] 월별 상환액 영역 차트
st.write("### 📉 월별 상환 부담 추이")
fig_monthly = go.Figure()
fig_monthly.add_trace(go.Scatter(x=df_monthly["month"], y=df_monthly["은행 상환"], name="은행 상환", fill='tozeroy', line_color='#2E86C1'))
fig_trend_total = go.Scatter(x=df_monthly["month"], y=df_monthly["합계 상환"], name="총 상환액", fill='tonexty', line_color='#EB984E')
fig_monthly.add_trace(fig_trend_total)

fig_monthly.update_layout(
    height=350, hovermode="x unified",
    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, font=dict(color="white")),
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"),
    margin=dict(t=20, b=80), xaxis_title="개월수", yaxis_title="월 상환액 (원)"
)
st.plotly_chart(fig_monthly, use_container_width=True)

# 💡 상환 마일스톤 안내
if co_loan_amount > 0 and co_loan_term < bank_term:
    reduction_val = df_monthly.iloc[int(co_loan_term*12-1)]["회사 상환"]
    st.markdown(f"""
    <div class="milestone-box">
        <b>💡 상환 마일스톤:</b><br>
        매수 후 <b>{int(co_loan_term)}년({int(co_loan_term*12)}개월)</b>이 지나면 회사 대출 상환이 완료되어,<br>
        월 상환 부담이 약 <b>{int(reduction_val/10000):,}만원</b>만큼 툭 떨어집니다!
    </div>
    """, unsafe_allow_html=True)

# 주요 지표
total_m = df_monthly["합계 상환"].iloc[0] if not df_monthly.empty else 0
dsr = (total_m * 12 / 10000) / annual_income * 100 if annual_income > 0 else 0

col_m1, col_m2 = st.columns(2)
with col_m1:
    st.markdown(f'<p class="small-font">첫 달 상환액</p><p class="main-val">{int(total_m):,}원</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-val">🏦 은행: {int(df_monthly["은행 상환"].iloc[0]):,}원<br>🏢 회사: {int(df_monthly["회사 상환"].iloc[0]):,}원</p>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<p class="small-font">DSR 지수</p><p class="main-val">{dsr:.1f}%</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-val">연간 상환액: {format_won(total_m*12/10000)}<br>연 소득 대비 비중: {dsr:.1f}%</p>', unsafe_allow_html=True)

# 부채 잔액 감소 추이
with st.expander("📉 내 집이 되는 과정 (부채 잔액 감소 추이)"):
    fig_bal = px.line(df_monthly, x="month", y="남은 부채", title="부채 잔액 변화 (단위: 만원)", line_shape="spline")
    fig_bal.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
    st.plotly_chart(fig_bal, use_container_width=True)

# 상세 표
with st.expander("📊 연도별 상세 상환 내역 표 보기"):
    df_annual_summary = df_monthly.groupby('year').agg({'은행 상환':'sum', '회사 상환':'sum', '합계 상환':'sum'}).reset_index()
    for col in ['은행 상환', '회사 상환', '합계 상환']:
        df_annual_summary[col] = df_annual_summary[col].apply(lambda x: f"{int(x/10000):,}만원")
    st.dataframe(df_annual_summary, use_container_width=True)

b_int_sum = bank_sched['interest'].sum() if 'interest' in bank_sched.columns else 0
c_int_sum = co_sched['interest'].sum() if 'interest' in co_sched.columns else 0
st.caption(f"※ 총 지불 이자 예상액: **{format_won((b_int_sum + c_int_sum)/10000)}**")
