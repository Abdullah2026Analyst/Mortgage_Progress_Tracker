import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Mortgage Progress Analyzer", page_icon="🏠", layout="wide")

st.title("🏠 Mortgage Progress Analyzer")
st.caption("Analyze your mortgage, down payment, PMI, HOA, interest, principal, and remaining balance.")

# ---------------- INPUTS ----------------
st.subheader("Loan Information")

home_price = st.number_input("Home Price ($)", min_value=0.0, value=400000.0, step=1000.0)
down_payment = st.number_input("Down Payment ($)", min_value=0.0, value=80000.0, step=1000.0)

loan_amount = home_price - down_payment
down_payment_percent = (down_payment / home_price) * 100 if home_price > 0 else 0
loan_to_value = (loan_amount / home_price) * 100 if home_price > 0 else 0

annual_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=6.5, step=0.1)
loan_term_years = st.number_input("Loan Term (Years)", min_value=1, value=30, step=1)
start_date = st.date_input("Mortgage Start Date", value=date(2023, 1, 1))
extra_payment = st.number_input("Extra Monthly Payment ($) - optional", min_value=0.0, value=0.0, step=50.0)
monthly_hoa = st.number_input("Monthly HOA Fee ($) - optional", min_value=0.0, value=0.0, step=10.0)

st.subheader("PMI Settings")
pmi_monthly = st.number_input("Monthly PMI Amount ($)", min_value=0.0, value=0.0, step=10.0)
pmi_cutoff_percent = st.number_input(
    "Stop PMI When Loan Balance Reaches This % of Home Value",
    min_value=0.0,
    max_value=100.0,
    value=80.0,
    step=1.0,
)

# ---------------- DOWN PAYMENT SUMMARY ----------------
st.subheader("Down Payment Summary")

d1, d2, d3, d4 = st.columns(4)
d1.metric("Home Price", f"${home_price:,.2f}")
d2.metric("Down Payment", f"${down_payment:,.2f}")
d3.metric("Loan Amount", f"${loan_amount:,.2f}")
d4.metric("Down Payment %", f"{down_payment_percent:.1f}%")

if loan_to_value > 80:
    st.warning(f"PMI is likely needed because loan-to-value is {loan_to_value:.1f}%.")
else:
    st.success(f"PMI is likely not needed because loan-to-value is {loan_to_value:.1f}%.")

# ---------------- CALCULATIONS ----------------
monthly_rate = annual_rate / 100 / 12
total_months = int(loan_term_years * 12)
pmi_cutoff_balance = home_price * (pmi_cutoff_percent / 100)

if loan_amount <= 0:
    st.error("Loan amount must be greater than $0. Check home price and down payment.")
    st.stop()

if monthly_rate == 0:
    monthly_payment = loan_amount / total_months
else:
    monthly_payment = loan_amount * (
        monthly_rate * (1 + monthly_rate) ** total_months
    ) / ((1 + monthly_rate) ** total_months - 1)

today = pd.Timestamp.today().normalize()
start = pd.Timestamp(start_date)
months_paid = max(0, min(total_months, (today.year - start.year) * 12 + (today.month - start.month)))

balance = loan_amount
rows = []

for month in range(1, total_months + 1):
    interest = balance * monthly_rate
    principal = monthly_payment - interest
    pmi = pmi_monthly if balance > pmi_cutoff_balance else 0
    hoa = monthly_hoa

    payment_without_pmi_hoa = monthly_payment + extra_payment
    total_monthly_cost = payment_without_pmi_hoa + pmi + hoa

    if extra_payment > 0:
        principal += extra_payment

    if principal > balance:
        principal = balance
        payment_without_pmi_hoa = interest + principal
        total_monthly_cost = payment_without_pmi_hoa + pmi + hoa

    balance -= principal
    payment_date = start + pd.DateOffset(months=month)

    rows.append({
        "Month": month,
        "Date": payment_date.date(),
        "Mortgage Payment": monthly_payment,
        "Extra Payment": extra_payment,
        "PMI": pmi,
        "HOA": hoa,
        "Total Monthly Cost": total_monthly_cost,
        "Principal": principal,
        "Interest": interest,
        "Balance": max(balance, 0),
    })

    if balance <= 0:
        break

df = pd.DataFrame(rows)
paid_df = df[df["Month"] <= months_paid]
remaining_df = df[df["Month"] > months_paid]

principal_paid = paid_df["Principal"].sum()
interest_paid = paid_df["Interest"].sum()
pmi_paid = paid_df["PMI"].sum()
hoa_paid = paid_df["HOA"].sum()
remaining_pmi = remaining_df["PMI"].sum()
remaining_hoa = remaining_df["HOA"].sum()
remaining_interest = remaining_df["Interest"].sum()
total_interest = df["Interest"].sum()
total_pmi = df["PMI"].sum()
total_hoa = df["HOA"].sum()
total_cost = loan_amount + total_interest + total_pmi + total_hoa

if len(df) > 0:
    row_index = min(months_paid, len(df) - 1)
    remaining_balance = df.loc[row_index, "Balance"]
    current_pmi = df.loc[row_index, "PMI"]
    current_total_monthly_cost = monthly_payment + extra_payment + current_pmi + monthly_hoa
else:
    remaining_balance = loan_amount
    current_pmi = 0
    current_total_monthly_cost = monthly_payment + extra_payment + monthly_hoa

# ---------------- RESULTS ----------------
st.subheader("Monthly Cost Summary")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Mortgage Payment", f"${monthly_payment:,.2f}")
m2.metric("Current PMI", f"${current_pmi:,.2f}")
m3.metric("Monthly HOA", f"${monthly_hoa:,.2f}")
m4.metric("Total Monthly Cost", f"${current_total_monthly_cost:,.2f}")

st.subheader("Mortgage Summary")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Principal Paid So Far", f"${principal_paid:,.2f}")
c2.metric("Interest Paid So Far", f"${interest_paid:,.2f}")
c3.metric("HOA Paid So Far", f"${hoa_paid:,.2f}")
c4.metric("Remaining Balance", f"${remaining_balance:,.2f}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("PMI Paid So Far", f"${pmi_paid:,.2f}")
c6.metric("Remaining PMI", f"${remaining_pmi:,.2f}")
c7.metric("Remaining HOA", f"${remaining_hoa:,.2f}")
c8.metric("Total Loan + Fees Cost", f"${total_cost:,.2f}")

# ---------------- CHARTS ----------------
st.subheader("📊 Balance Over Time")
st.line_chart(df.set_index("Month")["Balance"])

st.subheader("📊 Principal vs Interest vs PMI vs HOA")
st.line_chart(df.set_index("Month")[["Principal", "Interest", "PMI", "HOA"]])

# ---------------- TABLE ----------------
st.subheader("📋 Amortization Schedule")
st.dataframe(df, use_container_width=True)

st.download_button(
    "Download Amortization CSV",
    df.to_csv(index=False).encode("utf-8"),
    "mortgage_amortization_schedule.csv",
    "text/csv",
)
