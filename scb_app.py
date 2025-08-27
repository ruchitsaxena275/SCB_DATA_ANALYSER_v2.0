import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, time

st.set_page_config(page_title="SCB Data Analyzer", layout="wide")

# ---------------------- File Upload ----------------------
st.title("📊 SCB String Current Analyzer")

uploaded_file = st.file_uploader("Upload your SCB Excel file", type=["xlsx"])

if uploaded_file:
    # Read Excel file
    df = pd.read_excel(uploaded_file)

    # Assume timestamp column exists (adjust if needed)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df = df.set_index("Timestamp")

    st.write("✅ File Uploaded Successfully")

    # ---------------------- Date & Time Range Selection ----------------------
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date", value=df.index.min().date())
        start_time = st.time_input("Start Time", value=time(7, 0))  # default 07:00

    with col2:
        end_date = st.date_input("End Date", value=df.index.max().date())
        end_time = st.time_input("End Time", value=time(19, 0))  # default 19:00

    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)

    df_filtered = df.loc[(df.index >= start_dt) & (df.index <= end_dt)]

    st.write(f"📌 Data filtered from **{start_dt}** to **{end_dt}**")

    # ---------------------- Compute Ratios ----------------------
    def compute_ratio(dataframe):
        string_cols = dataframe.columns[1:19]  # Assuming B–S are string currents
        irr_col = "Irradiation"  # Adjust if needed

        expected_current = dataframe[irr_col] / 100  # simple assumption
        ratio = dataframe[string_cols].div(expected_current, axis=0)

        # Replace infinities & NaNs with 0
        ratio = ratio.replace([np.inf, -np.inf], np.nan).fillna(0)
        return ratio

    ratio = compute_ratio(df_filtered)

    # ---------------------- Heatmap ----------------------
    def plot_heatmap(data):
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.heatmap(data.T, cmap="coolwarm", cbar=True, ax=ax)
        ax.set_title("String Current Ratio Heatmap", fontsize=14)
        ax.set_xlabel("Time")
        ax.set_ylabel("String Number")
        st.pyplot(fig)

    if not ratio.empty:
        plot_heatmap(ratio)
    else:
        st.warning("⚠️ No data available in selected range")
