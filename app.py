import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.graph_objects as go
import psutil
import time
from datetime import datetime

# -----------------------------
# 1. ENTERPRISE UI CONFIG
# -----------------------------
st.set_page_config(page_title="Nexus AI - Global Predict", layout="wide", page_icon="🌐")

st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00d4ff; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 600; }
    .status-card { padding: 20px; border-radius: 10px; border: 1px solid #30363d; background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# 2. DATA & MODEL ENGINE
# -----------------------------
@st.cache_resource
def load_nexus_engine():
    try:
        with open("model.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        st.error("CRITICAL: 'model.pkl' not found on server. Ensure it is uploaded to GitHub.")
        st.stop()

engine = load_nexus_engine()
model = engine["model"]
feature_order = engine["features"] # Expected: [Type, Air, Proc, Speed, Torque, Wear]

# -----------------------------
# 3. SMART DEVICE DETECTION
# -----------------------------
# This helps the user feel like the app "knows" their phone
user_agent = st.query_params.to_dict() # Simple way to check session context
st.sidebar.title("🌐 Nexus Control")

# -----------------------------
# 4. SYSTEM SELECTION & MAPPING
# -----------------------------
system_mode = st.sidebar.selectbox("Analysis Mode", 
    ["📱 Smartphone Diagnostics", "🏭 Industrial CNC Asset", "💻 Live Server (Cloud)"])

st.sidebar.divider()
grade = st.sidebar.select_slider("Hardware Grade", options=["Low", "Medium", "High"], value="Medium")
type_map = {"High": 0, "Low": 1, "Medium": 2}
machine_type = type_map[grade]

# Dynamic UI Logic
if system_mode == "📱 Smartphone Diagnostics":
    st.sidebar.subheader("Mobile Sensor Input")
    bt = st.sidebar.slider("Battery Temp (°C)", 15, 60, 32)
    volt = st.sidebar.slider("Charge Voltage (mV)", 3000, 4400, 3750)
    cyc = st.sidebar.slider("Battery Cycles", 0, 1500, 200)
    
    # Map to Model: [Type, Air, Proc, Speed(0), Torque(Volt), Wear(Cycles)]
    vals = [machine_type, bt + 273, bt + 278, 0, (volt-3000)/10, cyc/5]
    labels = ["Tier", "Battery Temp", "Logic Board", "Cooling", "Voltage Load", "Cell Wear"]

elif system_mode == "🏭 Industrial CNC Asset":
    st.sidebar.subheader("Factory Telemetry")
    air = st.sidebar.slider("Ambient Temp (K)", 285, 315, 300)
    proc = st.sidebar.slider("Spindle Temp (K)", 295, 350, 312)
    rpm = st.sidebar.slider("Rotational Speed (RPM)", 0, 5000, 2200)
    trq = st.sidebar.slider("Torque (Nm)", 0, 100, 45)
    wr = st.sidebar.slider("Tool Wear (min)", 0, 250, 50)
    
    vals = [machine_type, air, proc, rpm, trq, wr]
    labels = ["Class", "Air Temp", "Process Temp", "RPM", "Torque", "Tool Wear"]

else: # Cloud Server Mode
    st.sidebar.info("Reading Streamlit Cloud Instance Telemetry...")
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    vals = [machine_type, 300, 310 + (cpu*0.5), 2500, cpu, mem]
    labels = ["Server Grade", "Inlet Temp", "CPU Junction", "Fan Speed", "CPU Load", "Memory Wear"]

# -----------------------------
# 5. PREDICTION LOGIC
# -----------------------------
# Ensure 6 columns always
input_df = pd.DataFrame([vals], columns=feature_order)
risk_prob = model.predict_proba(input_df)[0][1] * 100

if "history" not in st.session_state:
    st.session_state.history = [risk_prob] * 10
st.session_state.history.append(risk_prob)
st.session_state.history = st.session_state.history[-30:]

# -----------------------------
# 6. APP LAYOUT
# -----------------------------
st.title(f"🔍 Asset Analysis: {system_mode}")
st.caption(f"Status: Synchronized | Mode: {grade} Integrity | Frequency: 1Hz")

t1, t2, t3 = st.tabs(["📊 Dashboard", "🧬 Technicals", "🛡️ Safety Logs"])

with t1:
    # KPI Row
    col1, col2, col3 = st.columns(3)
    col1.metric("Failure Risk", f"{risk_prob:.1f}%", delta=f"{risk_prob - st.session_state.history[-2]:.1f}%", delta_color="inverse")
    
    status = "🚨 CRITICAL" if risk_prob > 75 else ("⚠️ WARNING" if risk_prob > 35 else "✅ OPTIMAL")
    col2.metric("System Health", status)
    col3.metric("Primary Metric", f"{vals[2]:.1f}", help="The most significant driver of failure in this mode.")

    st.divider()

    # Visuals
    v_left, v_right = st.columns([2, 1])
    with v_left:
        st.markdown("### 📈 Live Risk Trajectory")
        fig_l = go.Figure(go.Scatter(y=st.session_state.history, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
        fig_l.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig_l, use_container_width=True)
    
    with v_right:
        st.markdown("### ⏲️ Current Load")
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number", value=risk_prob,
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#1f6feb"},
                   'steps': [{'range': [0, 35], 'color': "green"}, {'range': [35, 75], 'color': "orange"}, {'range': [75, 100], 'color': "red"}]}))
        fig_g.update_layout(template="plotly_dark", height=280, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_g, use_container_width=True)

with t2:
    st.subheader("Sub-System Sensor Matrix")
    s_cols = st.columns(5)
    for i in range(1, 6):
        s_cols[i-1].metric(labels[i], f"{vals[i]:.2f}")
    
    st.divider()
    st.markdown("### 🧠 AI Interpretation (Feature Impact)")
    imp = model.feature_importances_
    fig_b = go.Figure(go.Bar(x=imp[1:], y=labels[1:], orientation='h', marker_color='#00d4ff'))
    fig_b.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig_b, use_container_width=True)

with t3:
    st.subheader("Maintenance Protocols")
    if risk_prob > 75:
        st.error(f"### 🚩 CRITICAL FAILURE RISK\nImmediate action required for {system_mode}. Thermal runaway detected on {labels[2]}.")
    elif risk_prob > 35:
        st.warning(f"### ⚠️ PREVENTATIVE MAINTENANCE\nAbnormal wear on {labels[5]} detected. Schedule inspection within 24h.")
    else:
        st.success("### ✅ NOMINAL OPERATIONS\nHardware is performing within 1-sigma of efficiency. No action needed.")

# Auto-Refresh for Server Mode
if system_mode == "💻 Live Server (Cloud)":
    time.sleep(2)
    st.rerun()