import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.graph_objects as go
import time
from streamlit_javascript import st_javascript

# -----------------------------
# 1. ADVANCED DEVICE DETECTION
# -----------------------------
st.set_page_config(page_title="Nexus AI - Multi-Platform", layout="wide")

# This script pulls the full hardware identity from the browser
ui_string = st_javascript("navigator.userAgent")

# Logic to sort the device type
if ui_string:
    if "iPhone" in ui_string or "iPad" in ui_string:
        device_category = "📱 Apple iOS Device"
        model_type = 0  # High Tier
    elif "Android" in ui_string:
        device_category = "🤖 Android Mobile"
        model_type = 2  # Medium Tier
    elif "Windows" in ui_string or "Macintosh" in ui_string or "Linux" in ui_string:
        device_category = "💻 Desktop PC / Workstation"
        model_type = 1  # Standard Tier
    else:
        device_category = "🌐 Unknown Terminal"
        model_type = 2
else:
    device_category = "⌛ Synchronizing..."
    model_type = 2

# -----------------------------
# 2. SIDEBAR & UI STYLING
# -----------------------------
st.sidebar.title("📡 System Identification")
st.sidebar.info(f"Identity: {device_category}")

# Custom Cyberpunk Theme
st.markdown("""
    <style>
    .main { background-color: #05070a; }
    [data-testid="stMetricValue"] { color: #00e5ff; font-family: 'Share Tech Mono', monospace; }
    .stAlert { background-color: #111; border: 1px solid #00e5ff; }
    </style>
    """, unsafe_allow_html=True)

# Toggle between the Live Device and Industrial Assets
mode = st.sidebar.radio("Analysis Target", ["Live Connected Device", "Industrial CNC Mill"])

# -----------------------------
# 3. DYNAMIC PARAMETER MAPPING
# -----------------------------
if mode == "Live Connected Device":
    st.sidebar.subheader(f"{device_category} Telemetry")
    
    # Sensors adjust based on whether it's a PC or Phone
    if "PC" in device_category:
        t_label = "CPU Package Temp (°C)"
        p_label = "GPU Junction Temp (°C)"
        v_label = "PSU Rail Voltage (V)"
    else:
        t_label = "Battery Thermal (°C)"
        p_label = "Logic Board Temp (°C)"
        v_label = "Lithium Voltage (mV)"

    t1 = st.sidebar.slider(t_label, 15, 80, 38)
    t2 = st.sidebar.slider(p_label, 20, 90, 42)
    volts = st.sidebar.slider(v_label, 3000, 4500, 3800)
    wear = st.sidebar.slider("Component Wear Index", 0, 1000, 150)
    
    # Standardizing for the 6-column model
    vals = [model_type, t1 + 273, t2 + 273, 2500, (volts-3000)/10, wear/4]
    sensor_names = ["Category", t_label, p_label, "Fan/Cooling", "Load Stress", "Life Cycles"]

else:
    # CNC Mode (Manual Inputs)
    vals = [1, 298, 310, 1800, 45, 20]
    sensor_names = ["Class", "Air Temp", "Proc Temp", "RPM", "Torque", "Tool Wear"]

# -----------------------------
# 4. AI INFERENCE ENGINE
# -----------------------------
try:
    with open("model.pkl", "rb") as f:
        nexus = pickle.load(f)
    
    model = nexus["model"]
    features = nexus["features"]
    
    input_df = pd.DataFrame([vals], columns=features)
    risk = model.predict_proba(input_df)[0][1] * 100

    # -----------------------------
    # 5. DASHBOARD VISUALS
    # -----------------------------
    st.title(f"🔍 Diagnostic: {device_category}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Failure Risk", f"{risk:.2f}%")
    col2.metric("Detection Sync", "ACTIVE" if ui_string else "PENDING")
    
    health = "OPTIMAL" if risk < 30 else ("WARNING" if risk < 70 else "CRITICAL")
    col3.metric("Health Status", health)

    st.divider()

    # Gauge and Trend
    c_left, c_right = st.columns([1, 1])
    with c_left:
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number", value=risk,
            title={'text': "Risk Index"},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#00e5ff"}}))
        fig_g.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig_g, use_container_width=True)
        
    with c_right:
        st.subheader("Sensor Detail")
        for i in range(1, 6):
            st.write(f"**{sensor_names[i]}:** {vals[i]:.1f}")

except Exception as e:
    st.warning("Hardware link initializing... Please wait 2 seconds.")

# Real-time refresh
time.sleep(1)
st.rerun()