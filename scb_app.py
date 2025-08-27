import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt

st.set_page_config(page_title="SCB Data Analyzer", layout="wide")
st.title("SCB Data Analyzer")

# ---------- Helpers ----------

def read_file(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> pd.DataFrame:
    """Read CSV or Excel into a DataFrame."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            # Requires 'openpyxl' in requirements.txt for .xlsx
            df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()
    return df

def ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """Ask user which column is timestamp, parse as datetime (day-first), set as index."""
    col_options = list(df.columns)
    if not col_options:
        st.error("No columns found in the uploaded file.")
        st.stop()

    ts_col = st.selectbox("Select timestamp column", col_options, index=0)
    # Parse common Indian format DD-MM-YYYY HH:MM
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce", dayfirst=True)
    bad = df[ts_col].isna().sum()
    if bad > 0:
        st.info(f"Dropping {bad} rows with invalid timestamps in '{ts_col}'.")
    df = df.dropna(subset=[ts_col]).copy()
    df = df.set_index(ts_col).sort_index()
    return df

def filter_by_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """User-selectable date and time range filter."""
    if df.index.empty:
        st.error("No timestamped rows after parsing.")
        st.stop()

    min_d = df.index.min().date()
    max_d = df.index.max().date()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        start_date = st.date_input("Start date", value=min_d, min_value=min_d, max_value=max_d, key="start_date")
    with c2:
        end_date = st.date_input("End date", value=max_d, min_value=min_d, max_value=max_d, key="end_date")
    with c3:
        start_time = st.time_input("Start time", value=dt.time(7, 0), key="start_time")
    with c4:
        end_time = st.time_input("End time", value=dt.time(19, 0), key="end_time")

    start_dt = dt.datetime.combine(start_date, start_time)
    end_dt = dt.datetime.combine(end_date, end_time)
    if end_dt < start_dt:
        st.warning("End datetime is before start datetime. Swapping them.")
        start_dt, end_dt = end_dt, start_dt

    df_f = df.loc[start_dt:end_dt]
    st.caption(f"Filtered range: {start_dt} → {end_dt} ({len(df_f):,} rows)")
    if df_f.empty:
        st.warning("No data in the selected date/time range.")
    return df_f

def pick_string_columns(df: pd.DataFrame) -> list:
    """Let user pick which numeric columns are string currents (B–S = 18 typical)."""
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        st.error("No numeric columns found for string currents. Check your file.")
        st.stop()
    preselect = numeric_cols[:18]  # preselect first 18 numeric cols if available
    chosen = st.multiselect("Select string current columns (typically 18: B–S)", numeric_cols, default=preselect)
    if len(chosen) == 0:
        st.error("Please select at least one string current column.")
        st.stop()
    return chosen

def compute_ratio(df: pd.DataFrame, string_cols: list) -> pd.DataFrame:
    """
    Compute ratio of each string to the expected current (row mean).
    Avoid divide-by-zero by treating zeros as missing for the average.
    """
    strings = df[string_cols].copy()
    expected = strings.replace(0, pd.NA).mean(axis=1)
    ratio = strings.div(expected, axis=0)
    return ratio

def plot_heatmap(ratio_df: pd.DataFrame) -> None:
    """Matplotlib heatmap: rows = strings, columns = time."""
    if ratio_df.empty:
        st.warning("No data to plot.")
        return

    data = ratio_df.T  # strings as rows, time as columns
    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.imshow(data.values, aspect="auto")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("String / Expected", rotation=90)

    # X ticks (time); limit to ~12 labels to avoid clutter
    n_cols = data.shape[1]
    if n_cols <= 12:
        xticks = list(range(n_cols))
    else:
        step = max(1, n_cols // 12)
        xticks = list(range(0, n_cols, step))
    ax.set_xticks(xticks)
    # format labels safely
    time_labels = []
    for i in xticks:
        try:
            time_labels.append(pd.to_datetime(data.columns[i]).strftime("%d-%m %H:%M"))
        except Exception:
            time_labels.append(str(data.columns[i]))
    ax.set_xticklabels(time_labels, rotation=45, ha="right")

    # Y ticks (strings)
    ax.set_yticks(range(data.shape[0]))
    ax.set_yticklabels(list(data.index))

    ax.set_xlabel("Time")
    ax.set_ylabel("String")
    ax.set_title("Low-Current Heatmap (ratio to expected)")
    st.pyplot(fig)

# ---------- App Flow ----------

uploaded_file = st.file_uploader("Upload SCB file (.csv or .xlsx)", type=["csv", "xlsx"])

if uploaded_file is None:
    st.info("Upload a file to begin. Tip: first column should be the timestamp (DD-MM-YYYY HH:MM).")
else:
    raw_df = read_file(uploaded_file)
    st.subheader("Step 1: Choose timestamp column")
    df = ensure_datetime_index(raw_df)

    st.subheader("Step 2: Pick date & time window")
    df = filter_by_datetime(df)

    st.subheader("Step 3: Select string current columns")
    string_cols = pick_string_columns(df)

    st.subheader("Step 4: Heatmap")
    ratio = compute_ratio(df, string_cols)
    plot_heatmap(ratio)

    st.subheader("Preview (first 10 rows of ratio)")
    st.dataframe(ratio.head(10))
