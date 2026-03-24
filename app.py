import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정 (브라우저 탭 제목)
st.set_page_config(page_title="내 집 마련 시뮬레이터", layout="centered", page_icon="🏢")

# 스타일 커스텀: 텍스트 색상 및 레이아웃 최적화
st.markdown("""
    <style>
    .small-font { font-size: 1.1rem !important; font-weight: 600; color: #E0E0E0 !important; }
    .main-val { font-size: 2.2rem !important; font-weight: 800; color: #FFFFFF !important; margin-bottom: 5px; }
    .sub-val { font-size: 0.95rem; color: #BDBDBD !important; line-height: 1.6; }
    /* 인풋창 라벨 높이 조절 */
    div[data-testid="stWidgetLabel"] p { font-size: 1rem !important; margin-bottom: 5px !important; }
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
        schedule.append({"month": i, "year": (i-1)//12 + 1, "total": int(m_pay), "principal": int(pri_pay), "interest": int(int_pay)})
    return pd.DataFrame(schedule)

# --- UI 입력부 ---
# 이 부분(46번 줄)에서 v11.0 문구를 삭제했습니다.
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

# 2️⃣ 자금 및 소득 (UI 개선: 드롭다운 + 인풋 한 줄 배치)
st.subheader("2️⃣ 나의 자금 및 소득")
c3, c4 = st.columns(2)
with c3:
    my_cash = st.number_input("보유 현금 (만원)", value=30000, step=1000)
    st.caption(f"👉 **{format_won(my_cash)}**")

with c4:
    # 소득 구분과 연봉 입력을 내부 컬럼으로 쪼개서 한 줄로 배치
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

# 3️⃣ 은행 대출
st.subheader("3️⃣ 은행 대출 설정")
c5, c6 = st.columns(2)
bank_loan_amount = c5.number_input("은행 대출 신청액 (만원)", value=30000, step=1000)
c5.caption(f"👉 **{format_won(bank_loan_amount)}**")
bank_rate = c6.number_input("은행 금리 (%)", value=4.2)
c7, c8 = st.columns(2)
bank_term = c7.number_input("은행 기간 (년)", value=30)
bank_method = c8.selectbox("은행 상환", ["원리금균등", "원금균등"])

# --- 계산 로직 ---
total_funding = my_cash + co_loan_amount + bank_loan_amount
diff = total_funding - total_cost
total_loan = bank_loan_amount + co_loan_amount
bank_sched = get_full_schedule(bank_loan_amount, bank_rate, bank_term, bank_method)
co_sched = get_full_schedule(co_loan_amount, co_loan_rate, co_loan_term, co_method)

# --- 결과 리포트 ---
st.divider()
st.subheader("💰 시뮬레이션 결과 리포트")

# 자금 상태 요약
if diff > 0: st.info(f"✅ 자금 계획: **{format_won(diff)}** 초과 (여유)")
elif diff == 0: st.success(f"✅ 자금 계획: 총 비용과 정확히 일치합니다.")
else: st.error(f"⚠️ 자금 계획: **{format_won(abs(diff))}** 부족합니다.")

# 연도별 상환 추이 그래프
max_years = int(max(bank_term, co_loan_term))
annual_data = []
for y in range(1, max_years + 1):
    b_y = bank_sched[bank_sched['year'] == y] if not bank_sched.empty else pd.DataFrame()
    c_y = co_sched[co_sched['year'] == y] if not co_sched.empty else pd.DataFrame()
    annual_data.append({
        "연도": f"{y}년",
        "은행 원금": b_y['principal'].sum() if not b_y.empty else 0,
        "은행 이자": b_y['interest'].sum() if not b_y.empty else 0,
        "회사 상환액": (c_y['total'].sum()) if not c_y.empty else 0
    })
df_annual = pd.DataFrame(annual_data)

st.write("### 📉 통합 상환 추이 (연도별)")
fig_trend = go.Figure()
fig_trend.add_trace(go.Bar(x=df_annual["연도"], y=df_annual["은행 원금"], name="은행 원금", marker_color="#5DADE2"))
fig_trend.add_trace(go.Bar(x=df_annual["연도"], y=df_annual["은행 이자"], name="은행 이자", marker_color="#2E86C1"))
fig_trend.add_trace(go.Bar(x=df_annual["연도"], y=df_annual["회사 상환액"], name="회사 상환액", marker_color="#EB984E"))

fig_trend.update_layout(
    barmode='stack', height=400,
    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, font=dict(color="white")),
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color="white"),
    margin=dict(t=20, b=100)
)
st.plotly_chart(fig_trend, use_container_width=True)

# 주요 지표 (DSR % 표시 보완)
monthly_bank = bank_sched["total"].iloc[0] if not bank_sched.empty else 0
monthly_co = co_sched["total"].iloc[0] if not co_sched.empty else 0
total_m = monthly_bank + monthly_co
dsr = (total_m * 12 / 10000) / annual_income * 100

st.divider()
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.markdown(f'<p class="small-font">첫 달 상환액</p><p class="main-val">{total_m:,}원</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-val">🏦 은행: {int(monthly_bank):,}원<br>🏢 회사: {int(monthly_co):,}원</p>', unsafe_allow_html=True)

with col_m2:
    st.markdown(f'<p class="small-font">DSR 지수</p><p class="main-val">{dsr:.1f}%</p>', unsafe_allow_html=True)
    # 연 소득 대비 비중에 실제 수치(dsr) 추가
    st.markdown(f'<p class="sub-val">연간 상환액: {format_won(total_m*12/10000)}<br>연 소득 대비 비중: {dsr:.1f}%</p>', unsafe_allow_html=True)

if dsr > 40:
    st.warning(f"⚠️ DSR {dsr:.1f}%: 상환 부담이 크며 대출 거절 가능성이 있습니다.")

# 연도별 상세 내역 표
st.write("")
with st.expander("📊 연도별 상세 상환 내역 표 보기"):
    table_df = df_annual.copy()
    table_df["연간 총액"] = table_df["은행 원금"] + table_df["은행 이자"] + table_df["회사 상환액"]
    for col in ["은행 원금", "은행 이자", "회사 상환액", "연간 총액"]:
        table_df[col] = table_df[col].apply(lambda x: f"{int(x/10000):,}만원" if x > 0 else "0원")
    st.dataframe(table_df, use_container_width=True)

st.caption(f"※ 총 지불 이자 예상액: **{format_won((bank_sched['interest'].sum() + co_sched['interest'].sum())/10000)}**")
