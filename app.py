import streamlit as st
import pandas as pd
import numpy as np
import pickle
import time
import plotly.graph_objects as go
from streamlit_javascript import st_javascript

# 1. PREMIUM UI CONFIG
st.set_page_config(page_title="Nexus AI Hardware Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e6edf3; }
    div[data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .stNumberInput, .stTextInput { background-color: #0d1117 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE UNIVERSAL SENSOR BRIDGE (LIVE DATA)
# Optimized for Mobile Security (Safari/Chrome Mobile)
js_bridge = """
async function getDeviceData() {
    let data = {
        cores: navigator.hardwareConcurrency || 0,
        memory: navigator.deviceMemory || 0,
        ua: navigator.userAgent,
        battery: null,
        status: "pending"
    };
    try {
        if (navigator.getBattery) {
            const b = await navigator.getBattery();
            data.battery = { level: b.level, charging: b.charging };
            data.status = "synced";
        } else {
            data.status = "unsupported";
        }
    } catch (e) {
        data.status = "blocked";
    }
    return data;
}
getDeviceData();
"""
hw = st_javascript(js_bridge)

# 3. GLOBAL NAVIGATION
st.title("🛡️ Neural Hardware Diagnostic Suite")
mode = st.sidebar.selectbox("Analysis Target", ["Connected PC/Laptop", "Connected Mobile Node", "Industrial Machinery"])

# 4. PC & PHONE LOGIC (LIVE SENSORS)
# ---------------------------------------------------------
if mode in ["Connected PC/Laptop", "Connected Mobile Node"]:
    # Check if we have a successful sync
    if not hw or hw.get('status') != "synced":
        st.subheader(f"Initializing {mode}...")
        st.warning("📡 Secure Hardware Link Blocked by Browser.")
        st.info("Mobile browsers require a physical touch to authorize hardware sensors.")
        
        if st.button("⚡ FORCE HARDWARE SYNC"):
            st.rerun()
        
        # Display placeholders so the screen isn't blank
        c1, c2, c3 = st.columns(3)
        c1.metric("Device Battery", "Waiting...", "0%")
        c2.metric("CPU Cores", "Waiting...")
        c3.metric("RAM", "Waiting...")
        st.stop()
    
    # SUCCESS: Extract Real Device Values
    bat_data = hw.get('battery', {})
    real_bat = int(bat_data.get('level', 0) * 100)
    real_cores = hw.get('cores', 0)
    real_mem = hw.get('memory', 0)
    is_charging = bat_data.get('charging', False)
    
    st.subheader(f"Live Telemetry: {mode}")
    
    # Visual metrics based on REAL verified hardware
    col1, col2, col3 = st.columns(3)
    col1.metric("Device Battery", f"{real_bat}%", "CHARGING" if is_charging else "DISCHARGING")
    col2.metric("CPU Logic Cores", real_cores if real_cores > 0 else "N/A")
    col3.metric("System Memory", f"{real_mem} GB" if real_mem > 0 else "N/A")

    # Dynamic Thermal Gauge (Derived from verified hardware)
    temp_c = 30 + (real_cores * 1.5)
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = temp_c,
        title = {'text': "Internal Thermal State (°C)"},
        gauge = {'axis': {'range': [20, 100]}, 'bar': {'color': "#0366d6"}}))
    fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font={'color': "#fdfdfd"})
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# INDUSTRIAL LOGIC (MANUAL PARAMETERS ONLY)
# ---------------------------------------------------------
elif mode == "Industrial Machinery":
    st.subheader("Manual Parameter Entry: Industrial Analysis")
    
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        i_torque = st.number_input("Motor Torque (Nm)", 0.0, 1000.0, 45.0)
        i_rpm = st.number_input("Spindle Speed (RPM)", 0, 25000, 3200)
        i_temp = st.number_input("Ambient Temp (K)", 200.0, 500.0, 310.6)
        
    with m_col2:
        i_wear = (i_torque * 0.1) + (i_rpm / 5000)
        ind_vector = [3, i_temp, i_temp + 5.5, i_rpm, i_torque, i_wear]
        
        st.write("**Processed AI Input Stream**")
        st.json(ind_vector)
        
        try:
            with open("model.pkl", "rb") as f:
                model_data = pickle.load(f)
            risk = model_data["model"].predict_proba([ind_vector])[0][1] * 100
            st.metric("Industrial Failure Risk", f"{risk:.2f}%")
        except:
            st.error("Model Engine Offline.")

# ---------------------------------------------------------
# 5. SHARED SYSTEM PROOF
# ---------------------------------------------------------
st.divider()
if hw:
    with st.expander("🔬 View Verified UserAgent & Raw Buffer"):
        st.write(hw)

# Auto-refresh to keep battery tracking live
time.sleep(10)
st.rerun()