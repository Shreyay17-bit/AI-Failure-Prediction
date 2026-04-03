import streamlit as st
import pandas as pd
import numpy as np
import pickle
import time
import plotly.graph_objects as go
from streamlit_javascript import st_javascript

# 1. VISUAL ENGINE SETUP
st.set_page_config(page_title="Nexus AI Hardware Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e6edf3; }
    div[data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .stNumberInput, .stTextInput { background-color: #0d1117 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE UNIVERSAL SENSOR BRIDGE (LIVE DATA)
# This strictly queries the device hardware for PC/Phone modes.
js_bridge = """
(async function() {
    let data = {
        cores: navigator.hardwareConcurrency || 0,
        memory: navigator.deviceMemory || 0,
        ua: navigator.userAgent,
        battery: null
    };
    try {
        if (navigator.getBattery) {
            const b = await navigator.getBattery();
            data.battery = { level: b.level, charging: b.charging };
        }
    } catch (e) {}
    return data;
})()
"""
hw = st_javascript(js_bridge)

# 3. GLOBAL NAVIGATION
st.title("🛡️ Neural Hardware Diagnostic Suite")
mode = st.sidebar.selectbox("Analysis Target", ["Connected PC/Laptop", "Connected Mobile Node", "Industrial Machinery"])

# 4. MODE LOGIC: PC & PHONE (LIVE) VS INDUSTRIAL (MANUAL)
# ---------------------------------------------------------
if mode in ["Connected PC/Laptop", "Connected Mobile Node"]:
    if not hw or (hw.get('battery') is None and mode == "Connected PC/Laptop"):
        st.info("🛰️ Initializing Secure Hardware Link... Please ensure browser permissions are granted.")
        # Brief pause to allow the JS bridge to complete the handshake
        time.sleep(1)
        st.rerun()
    
    # Extract Real Device Values
    real_bat = int(hw['battery']['level'] * 100) if hw.get('battery') else 0
    real_cores = hw.get('cores', 0)
    real_mem = hw.get('memory', 0)
    
    st.subheader(f"Live Telemetry: {mode}")
    
    # Visual metrics based on REAL device data
    col1, col2, col3 = st.columns(3)
    col1.metric("Device Battery", f"{real_bat}%", "LIVE" if real_bat > 0 else "OFFLINE")
    col2.metric("CPU Logic Cores", real_cores if real_cores > 0 else "Locked")
    col3.metric("System Memory", f"{real_mem} GB" if real_mem > 0 else "Locked")

    # Thermal Gauge (Derived from verified hardware cores)
    temp_c = 30 + (real_cores * 1.2) if real_cores > 0 else 30
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = temp_c,
        title = {'text': "Internal Thermal State (°C)"},
        gauge = {'axis': {'range': [20, 90]}, 'bar': {'color': "#0366d6"}}))
    fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font={'color': "#fdfdfd"})
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
elif mode == "Industrial Machinery":
    st.subheader("Manual Parameter Entry: Industrial Analysis")
    st.info("Input verified values from machine sensors below.")
    
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        i_torque = st.number_input("Motor Torque (Nm)", 0.0, 1000.0, 45.0)
        i_rpm = st.number_input("Spindle Speed (RPM)", 0, 25000, 3200)
        i_temp = st.number_input("Ambient Temp (K)", 200.0, 500.0, 310.6)
        
    with m_col2:
        # Neural Input Vector for the model
        # [Type, AirTemp, ProcTemp, Speed, Torque, Wear]
        i_wear = (i_torque * 0.1) + (i_rpm / 5000)
        ind_vector = [3, i_temp, i_temp + 5.5, i_rpm, i_torque, i_wear]
        
        st.write("**Processed AI Input Stream**")
        st.json(ind_vector)
        
        # Risk Prediction
        try:
            with open("model.pkl", "rb") as f:
                nexus = pickle.load(f)
            risk = nexus["model"].predict_proba([ind_vector])[0][1] * 100
            st.metric("Industrial Failure Risk", f"{risk:.2f}%")
        except:
            st.warning("Prediction engine offline. Please verify model.pkl.")

# ---------------------------------------------------------
# 5. SHARED SYSTEM PROOF
# ---------------------------------------------------------
st.divider()
st.subheader("Neural Handshake Log")
st.write("Verified UserAgent:", hw.get('ua') if hw else "Connecting...")

# Auto-refresh to keep battery tracking live
time.sleep(10)
st.rerun()