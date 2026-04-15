import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Page Configuration & Branding
st.set_page_config(page_title="Elektro Maribor | Outage Analytics", layout="wide")

# Custom CSS for corporate look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #CCE12A; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Low-Voltage Network Outage Tracker")
st.sidebar.header("Settings & Filters")


# 2. Data Loading Logic
def load_data(file):
    # Based on your CSV: 0,01.03 00:00, 27.713, 1
    df = pd.read_csv(file, names=['ID', 'Timestamp', 'Voltage', 'Status'])

    # Cleaning the timestamp (handling that "0," prefix and missing year)
    df['Timestamp'] = df['Timestamp'].str.replace('0,', '2026-')  # Assuming 2026
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y-%d.%m %H:%M')
    return df


uploaded_file = st.sidebar.file_uploader("Upload Meter Data (.csv)", type="csv")

if uploaded_file:
    df = load_data(uploaded_file)

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
    col3.metric("Estimated SAIDI", "4.2 min")  # Replace with your formula

    # 4. Visualization
    st.write("### Voltage Profiles")
    fig = px.line(df, x='Timestamp', y='Voltage', color='ID',
                  color_discrete_sequence=['#004A99', '#CCE12A'])
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload the 'm0.csv' file to begin analysis.")
    # Show an example of the expected format
    st.image("https://via.placeholder.com/800x400.png?text=Waiting+for+Data+Upload")