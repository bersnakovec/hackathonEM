import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import joblib

# 1. Page Configuration & Branding
st.set_page_config(page_title="Elektro Maribor | Outage Analytics", layout="wide")

# Custom CSS for corporate look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #CCE12A;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricDelta"],
    div[data-testid="stMetric"] p,
    div[data-testid="stMetric"] span {
        color: #000000 !important;
        opacity: 1 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Low-Voltage Network Outage Tracker")
st.sidebar.header("Settings & Filters")

APP_DIR = Path(__file__).resolve().parent
OUTAGE_DURATION_HOURS = 3.0

# 2. Data Loading Logic
def load_data(file, source_name):
    # Based on your CSV: 0,01.03 00:00, 27.713, 1
    df = pd.read_csv(file, decimal=".", sep=",", names=['ID', 'Timestamp', 'Voltage', 'Status'])

    # Cleaning and normalization for analysis across multiple files
    df['ID'] = pd.to_numeric(df['ID'], errors='coerce').astype('Int64')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d.%m %H:%M', errors='coerce')
    df['Voltage'] = pd.to_numeric(df['Voltage'], errors='coerce')
    df = df.dropna(subset=['ID', 'Timestamp', 'Voltage'])
    df['Source File'] = source_name
    return df


def format_time_axis_without_year(fig):
    # Keep internal datetime values, but display only day-month and time.
    fig.update_xaxes(tickformat="%d.%m %H:%M")
    fig.update_traces(xhoverformat="%d.%m %H:%M")


def merge_windows(windows):
    if not windows:
        return []

    sorted_windows = sorted(windows)
    merged = [sorted_windows[0]]

    for start, end in sorted_windows[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


def classify_windows(windows, outage_threshold_hours=OUTAGE_DURATION_HOURS):
    outage_windows = []
    anomaly_windows = []

    for start, end in windows:
        duration_hours = (end - start).total_seconds() / 3600.0
        if duration_hours >= outage_threshold_hours:
            outage_windows.append((start, end))
        else:
            anomaly_windows.append((start, end))

    return outage_windows, anomaly_windows


@st.cache_resource
def load_ml_model():
    model_path = APP_DIR / "xgboost_anomaly_model.pkl"
    features_path = APP_DIR / "model_features.pkl"
    if not model_path.exists() or not features_path.exists():
        return None, None
    model = joblib.load(model_path)
    features = joblib.load(features_path)
    return model, features


@st.cache_data
def predict_anomalies_for_df(df):
    model, features = load_ml_model()
    if model is None:
        return {}

    # Sort and reset index to guarantee index alignment for rolling operations
    df_sorted = df.copy().sort_values(['ID', 'Timestamp']).reset_index(drop=True)

    # Cache the groupby object for massive speedups
    grouped = df_sorted.groupby('ID')['Voltage']

    # Fully vectorized ML Feature Engineering (avoids extremely slow lambda transforms)
    for i in range(1, 4):
        df_sorted[f'lag_{i}'] = grouped.shift(i)
        
    df_sorted['rolling_mean'] = grouped.rolling(window=5).mean().reset_index(level=0, drop=True)
    df_sorted['rolling_std'] = grouped.rolling(window=5).std().reset_index(level=0, drop=True)
    df_sorted['velocity'] = grouped.diff()
    
    # Drop rows that don't have full features
    df_clean = df_sorted.dropna(subset=['Voltage', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean', 'rolling_std', 'velocity']).copy()
    
    if df_clean.empty:
        return {}

    # Setup the feature matrix mimicking Notebook column names
    X = df_clean[['Voltage', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean', 'rolling_std', 'velocity']]
    X.columns = ['meritev', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean', 'rolling_std', 'velocity']
    
    # Re-order to exactly match what the model expects
    X = X[features]
    
    probs = model.predict_proba(X)[:, 1]
    df_clean['pred_anom'] = (probs > 0.35).astype(int)
    
    # Identify transitions (1 = start, -1 = end)
    df_clean['transition'] = df_clean.groupby('ID')['pred_anom'].diff()
    
    windows = {}
    for meter_id, group in df_clean.groupby('ID'):
        starts = group[group['transition'] == 1]['Timestamp'].tolist()
        ends = group[group['transition'] == -1]['Timestamp'].tolist()
        
        # Handle boundaries: if the first point is abnormal, the start was at the beginning.
        if group['pred_anom'].iloc[0] == 1:
            starts.insert(0, group['Timestamp'].iloc[0])
            
        # Handle boundaries: if the last point is abnormal, it lasted until the end.
        if group['pred_anom'].iloc[-1] == 1:
            ends.append(group['Timestamp'].iloc[-1])
        
        meter_windows = []
        for start, end in zip(starts, ends):
            meter_windows.append((start, end))
        
        if meter_windows:
            windows[int(meter_id)] = meter_windows
            
    return windows


def apply_anomaly_highlights(fig, anomaly_windows):
    for start_time, end_time in anomaly_windows:
        fig.add_vrect(
            x0=start_time,
            x1=end_time,
            fillcolor="red",
            opacity=0.25,
            line_width=0,
            layer="below"
        )


def apply_event_highlights(fig, outage_windows, anomaly_windows):
    if outage_windows:
        fig.add_scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color="#d62728", symbol="square"),
            name="Power outage"
        )
        for start_time, end_time in outage_windows:
            fig.add_vrect(
                x0=start_time,
                x1=end_time,
                fillcolor="#d62728",
                opacity=0.30,
                line_width=0,
                layer="below"
            )

    if anomaly_windows:
        fig.add_scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color="#ff00ff", symbol="square"),
            name="Short anomaly"
        )
        for start_time, end_time in anomaly_windows:
            fig.add_vrect(
                x0=start_time,
                x1=end_time,
                fillcolor="#ff00ff",
                opacity=0.30,
                line_width=0,
                layer="below"
            )


uploaded_files = st.sidebar.file_uploader("Upload Meter Data (.csv)", type="csv", accept_multiple_files=True)
view_mode = st.sidebar.radio("Graph View", ["Separate graph per file", "Combined graph"])

if uploaded_files:
    frames = []
    failed_files = []

    for file in uploaded_files:
        try:
            frames.append(load_data(file, file.name))
        except Exception:
            failed_files.append(file.name)

    if failed_files:
        st.warning(f"Skipped invalid files: {', '.join(failed_files)}")

    if frames:
        df = pd.concat(frames, ignore_index=True)
        df['ID'] = pd.to_numeric(df['ID'], errors='coerce').astype('Int64')
        
        # Dynamically predict anomalies for the loaded data!
        predictions_by_meter = predict_anomalies_for_df(df)

        # 3. The Analytical Engine (Placeholder for your ML)
        # Goal: Distinguish Outage (Voltage -> 0) vs Comms Error (Missing Row)
        st.subheader("Network Overview")

        col1, col2, col3 = st.columns(3)

        # Calculations for SAIDI / SAIFI
        total_customers = df['ID'].nunique()
        
        total_interruptions = 0
        total_duration_hours = 0.0
        
        for windows in predictions_by_meter.values():
            if not windows:
                continue

            merged_meter_windows = merge_windows(windows)
            outage_windows, _ = classify_windows(merged_meter_windows)

            # Only longer outages count toward SAIDI/SAIFI
            total_interruptions += len(outage_windows)
            for start, end in outage_windows:
                total_duration_hours += (end - start).total_seconds() / 3600.0
                
        # SAIFI = Total number of interruptions / Total number of customers
        saifi = total_interruptions / total_customers if total_customers > 0 else 0
        
        # SAIDI = Total duration of all interruptions / Total number of customers
        saidi = total_duration_hours / total_customers if total_customers > 0 else 0

        # Metrics
        col1.metric("Total Measuring Points", total_customers)
        col2.metric("SAIDI (Avg Duration)", f"{saidi:.1f} h/user")
        col3.metric("SAIFI (Avg Frequency)", f"{saifi:.2f} int/user")

        # 4. Visualization
        st.write("### Voltage Profiles")

        def get_classified_windows_for_ids(ids):
            windows = []
            for meter_id in ids:
                if pd.isna(meter_id):
                    continue
                windows.extend(predictions_by_meter.get(int(meter_id), []))

            merged = merge_windows(windows)
            return classify_windows(merged)

        if view_mode == "Combined graph":
            fig = px.line(
                df.sort_values('Timestamp'),
                x='Timestamp',
                y='Voltage',
                color='Source File',
                line_group='ID',
                hover_data=['ID']
            )
            outage_windows, anomaly_windows = get_classified_windows_for_ids(df['ID'].dropna().unique())
            if outage_windows or anomaly_windows:
                apply_event_highlights(fig, outage_windows, anomaly_windows)
            format_time_axis_without_year(fig)
            st.plotly_chart(fig, use_container_width=True)
            if not outage_windows and not anomaly_windows:
                st.markdown("No anomalies detected")
            elif anomaly_windows and not outage_windows:
                st.markdown("Only short anomalous readings detected")
        else:
            source_files = sorted(df['Source File'].unique())
            selected_file = st.selectbox("Select File to View", source_files)

            file_df = df[df['Source File'] == selected_file].sort_values('Timestamp')
            outage_windows, anomaly_windows = get_classified_windows_for_ids(file_df['ID'].dropna().unique())
            fig = px.line(
                file_df,
                x='Timestamp',
                y='Voltage',
                color='ID',
                color_discrete_sequence=['#004A99', '#CCE12A']
            )
            if outage_windows or anomaly_windows:
                apply_event_highlights(fig, outage_windows, anomaly_windows)
            format_time_axis_without_year(fig)
            st.plotly_chart(fig, use_container_width=True)
            if not outage_windows and not anomaly_windows:
                st.markdown("No anomalies detected")
            elif anomaly_windows and not outage_windows:
                st.markdown("Only short anomalous readings detected")
    else:
        st.error("No valid data found in uploaded files.")

else:
    st.info("Please upload one or more .csv files (for example 'm0.csv') to begin analysis.")
    # Show an example of the expected format
    st.image("https://via.placeholder.com/800x400.png?text=Waiting+for+Data+Upload")