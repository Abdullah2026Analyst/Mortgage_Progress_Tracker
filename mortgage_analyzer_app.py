import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Mortgage Progress Analyzer", page_icon="🏠", layout="wide")

st.title("🏠 Mortgage Progress Analyzer")
st.caption("See principal paid, interest paid, remaining balance, and full mortgage breakdown.")

loan_amount = st.number_input("Original Loan Amount ($)", min_value=0.0, value=300000.0, step=1000.0)
annual_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=6.5, step=0.1)
loan_term_years = st.number_input("Loan Term (Years)", min_value=1, value=30, step=1)
start_date = st.date_input("Mortgage Start Date", value=date(2023, 1, 1))
extra_payment = st.number_input("Extra Monthly Payment ($) - optional", min_value=0.0, value=0.0, step=50.0)

monthly_rate = annual_rate / 100 / 12
total_months = int(loan_term_years * 12)

if monthly_rate == 0:
    monthly_payment = loan_amount / total_months
else:
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** total_months) / ((1 + monthly_rate) ** total_months - 1)

today = pd.Timestamp.today().normalize()
start = pd.Timestamp(start_date)
months_paid = max(0, min(total_months, (today.year - start.year) * 12 + (today.month - start.month)))

balance = loan_amount
rows = []

for month in range(1, total_months + 1):
    interest = balance * monthly_rate
    principal = monthly_payment - interest
    payment = monthly_payment

    if extra_payment > 0:
        principal += extra_payment
        payment += extra_payment

    if principal > balance:
        principal = balance
        payment = interest + principal

    balance -= principal

    payment_date = start + pd.DateOffset(months=month)
    rows.append({
        "Month": month,
        "Date": payment_date.date(),
        "Payment": payment,
        "Principal": principal,
        "Interest": interest,
        "Balance": max(balance, 0)
    })

    if balance <= 0:
        break

df = pd.DataFrame(rows)

paid_df = df[df["Month"] <= months_paid]
remaining_df = df[df["Month"] > months_paid]

principal_paid = paid_df["Principal"].sum()
interest_paid = paid_df["Interest"].sum()

if len(df) > 0:
    row_index = min(months_paid, len(df) - 1)
    remaining_balance = df.loc[row_index, "Balance"]
else:
    remaining_balance = loan_amount

remaining_interest = remaining_df["Interest"].sum()
total_interest = df["Interest"].sum()
total_cost = loan_amount + total_interest

c1, c2, c3, c4 = st.columns(4)
c1.metric("Monthly Payment", f"${monthly_payment:,.2f}")
c2.metric("Principal Paid So Far", f"${principal_paid:,.2f}")
c3.metric("Interest Paid So Far", f"${interest_paid:,.2f}")
c4.metric("Remaining Balance", f"${remaining_balance:,.2f}")

c5, c6, c7 = st.columns(3)
c5.metric("Remaining Interest", f"${remaining_interest:,.2f}")
c6.metric("Total Interest Lifetime", f"${total_interest:,.2f}")
c7.metric("Total Loan Cost", f"${total_cost:,.2f}")

st.subheader("📊 Balance Over Time")
st.line_chart(df.set_index("Month")["Balance"])

st.subheader("📊 Principal vs Interest Per Payment")
st.line_chart(df.set_index("Month")[["Principal", "Interest"]])

st.subheader("📋 Amortization Schedule")
st.dataframe(df, use_container_width=True)

st.download_button(
    "Download Amortization CSV",
    df.to_csv(index=False).encode("utf-8"),
    "mortgage_amortization_schedule.csv",
    "text/csv"
)
