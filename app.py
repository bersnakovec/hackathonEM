import streamlit as st
import pandas as pd
import plotly.express as px

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


# 2. Data Loading Logic
def load_data(file, source_name):
    # Based on your CSV: 0,01.03 00:00, 27.713, 1
    df = pd.read_csv(file, decimal=".", sep=",", names=['ID', 'Timestamp', 'Voltage', 'Status'])

    # Cleaning and normalization for analysis across multiple files
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d.%m %H:%M', errors='coerce')
    df['Voltage'] = pd.to_numeric(df['Voltage'], errors='coerce')
    df = df.dropna(subset=['Timestamp', 'Voltage'])
    df['Source File'] = source_name
    return df


def format_time_axis_without_year(fig):
    # Keep internal datetime values, but display only day-month and time.
    fig.update_xaxes(tickformat="%d.%m %H:%M")
    fig.update_traces(xhoverformat="%d.%m %H:%M")


uploaded_files = st.sidebar.file_uploader("Upload Meter Data (.csv)", type="csv", accept_multiple_files=True)
view_mode = st.sidebar.radio("Graph View", ["Combined graph", "Separate graph per file"])

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

        # 3. The Analytical Engine (Placeholder for your ML)
        # Goal: Distinguish Outage (Voltage -> 0) vs Comms Error (Missing Row)
        st.subheader("Network Overview")

        col1, col2, col3 = st.columns(3)

        # Placeholder calculations
        total_customers = df['ID'].nunique()
        outages = df[df['Voltage'] < 10]  # Example threshold

        # Metrics
        col1.metric("Total Measuring Points", total_customers)
        col2.metric("Detected Interruptions", len(outages))
        col3.metric("Uploaded Files", df['Source File'].nunique())

        # 4. Visualization
        st.write("### Voltage Profiles")

        if view_mode == "Combined graph":
            fig = px.line(
                df.sort_values('Timestamp'),
                x='Timestamp',
                y='Voltage',
                color='Source File',
                line_group='ID',
                hover_data=['ID']
            )
            format_time_axis_without_year(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            source_files = sorted(df['Source File'].unique())
            tabs = st.tabs(source_files)

            for tab, source_file in zip(tabs, source_files):
                with tab:
                    file_df = df[df['Source File'] == source_file].sort_values('Timestamp')
                    fig = px.line(
                        file_df,
                        x='Timestamp',
                        y='Voltage',
                        color='ID',
                        color_discrete_sequence=['#004A99', '#CCE12A']
                    )
                    format_time_axis_without_year(fig)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No valid data found in uploaded files.")

else:
    st.info("Please upload one or more .csv files (for example 'm0.csv') to begin analysis.")
    # Show an example of the expected format
    st.image("https://via.placeholder.com/800x400.png?text=Waiting+for+Data+Upload")