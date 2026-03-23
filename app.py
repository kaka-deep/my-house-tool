import streamlit as st
import pandas as pd

# 1. 페이지 설정 (최대 너비를 제한하여 PC에서도 모바일처럼 깔끔하게 보이도록 함)
st.set_page_config(page_title="주택 구매 시뮬레이터", layout="centered", page_icon="🏠")

# 스타일 커스텀 (글자 크기 및 간격 조정)
st.markdown("""
    <style>
    .main .block-container { max-width: 600px; padding-top: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007BFF; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 한국어 화폐 단위 변환 함수
def format_won(val_man):
    if val_man < 10000: return f"{int(val_man):,}만원"
    uk = val_man // 10000
    man = val_man % 10000
    return f"{int(uk):,}억 {int(man):,}만원" if man > 0 else f"{int(uk):,}억원"

# 원리금 균등상환 계산기
def calc_monthly(principal_man, rate, years):
    if rate <= 0 or years <= 0: return int((principal_man * 10000) / (years * 12)) if years > 0 else 0
    r = (rate / 100) / 12
    n = years * 12
    return int((principal_man * 10000) * (r * (1+r)**n) / ((1+r)**n - 1))

# --- 데이터 정의 ---
REGION_DATA = {
    "비규제지역 (LTV 70%)": {"LTV": 0.70, "DSR": 0.40},
    "과밀억제권역 (LTV 60%)": {"LTV": 0.60, "DSR": 0.40},
    "투기과열지구 (LTV 50%)": {"LTV": 0.50, "DSR": 0.40}
}

st.title("🏠 내 집 마련 시뮬레이터")
st.info("항목별로 정보를 입력하면 실시간으로 분석 결과가 업데이트됩니다.")

# --- STEP 1: 주택 정보 ---
st.subheader("1️⃣ 주택 및 세금 정보")
region_name = st.selectbox("매수 예정 지역", list(REGION_DATA.keys()))
house_price = st.number_input("주택 매매가 (만원)", value=80000, step=1000)
is_large = st.radio("전용면적 85㎡ 초과여부", ["이하", "초과"], horizontal=True)

# 취득세 계산 (간략화)
tax_rate = 0.011 if house_price <= 60000 else (0.022 if house_price <= 90000 else 0.033)
if is_large == "초과": tax_rate += 0.002
acquisition_tax = house_price * tax_rate

# --- STEP 2: 자금 및 소득 (회사 대출 포함) ---
st.divider()
st.subheader("2️⃣ 내 자금 및 소득")
my_cash = st.number_input("현재 보유 현금 (만원)", value=30000, step=1000)
annual_income = st.number_input("본인 연봉 (만원)", value=6000, step=500)

with st.expander("🏢 회사 대출(복지기금)이 있다면 입력하세요"):
    co_loan_amount = st.number_input("회사 대출 금액 (만원)", value=0, step=500)
    co_loan_rate = st.number_input("회사 대출 금리 (%)", value=2.0, step=0.1)
    co_loan_term = st.number_input("회사 대출 기간 (년)", value=10, step=1)

# --- STEP 3: 은행 대출 설정 ---
st.divider()
st.subheader("3️⃣ 은행 대출 조건")
bank_rate = st.number_input("은행 대출 금리 (%)", value=4.2, step=0.1)
bank_term = st.slider("은행 대출 기간 (년)", 10, 40, 30)

# --- 로직 계산 ---
# 1. 은행 대출 한도 계산 (LTV)
ltv_limit = (house_price * REGION_DATA[region_name]["LTV"]) - co_loan_amount # 회사대출만큼 LTV 한도 차감 가정
needed_from_bank = max(0, house_price + acquisition_tax - my_cash - co_loan_amount)
final_bank_loan = min(ltv_limit, needed_from_bank)

# 2. 월 상환액 계산
monthly_bank = calc_monthly(final_bank_loan, bank_rate, bank_term)
monthly_co = calc_monthly(co_loan_amount, co_loan_rate, co_loan_term)
total_monthly = monthly_bank + monthly_co

# 3. 금리 시나리오 (+1%)
monthly_bank_up = calc_monthly(final_bank_loan, bank_rate + 1.0, bank_term)
total_monthly_up = monthly_bank_up + monthly_co

# --- 결과 발표 ---
st.divider()
st.subheader("💰 최종 시뮬레이션 리포트")

# 결과 요약 카드
res_col1, res_col2 = st.columns(2)
with res_col1:
    st.metric("총 필요 자금", format_won(house_price + acquisition_tax))
    st.caption(f"매매가 + 취득세({format_won(acquisition_tax)})")
with res_col2:
    shortage = max(0, house_price + acquisition_tax - my_cash - co_loan_amount - final_bank_loan)
    if shortage > 0:
        st.metric("부족한 자금", format_won(shortage), delta="-부족", delta_color="inverse")
    else:
        st.metric("자금 계획", "완료", delta="정상")

# 대출 구성 상세
with st.container():
    st.write(f"✅ **은행 대출:** {format_won(final_bank_loan)} (금리 {bank_rate}%)")
    st.write(f"✅ **회사 대출:** {format_won(co_loan_amount)} (금리 {co_loan_rate}%)")
    st.markdown(f"### 💳 총 월 상환액: {total_monthly:,}원")

# --- 그래프 (너비 최적화) ---
st.divider()
st.subheader("📈 금리 1% 상승 시 변화")

# 그래프 데이터
compare_data = pd.DataFrame({
    "구분": ["현재", "1% 상승"],
    "월 상환액": [total_monthly, total_monthly_up]
})

# 컬럼을 사용하여 그래프 너비를 중앙으로 제한
empty1, chart_col, empty2 = st.columns([0.1, 0.8, 0.1])
with chart_col:
    st.bar_chart(compare_data.set_index("구분"), use_container_width=True)

st.warning(f"금리가 1% 오르면 매월 **{total_monthly_up - total_monthly:,}원**을 더 내야 합니다.")

# 하단 정보
st.caption("※ 본 계산은 원리금균등상환 기준이며 실제 대출 시 DSR, 부대비용 등에 따라 차이가 발생할 수 있습니다.")
