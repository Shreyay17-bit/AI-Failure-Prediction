import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.graph_objects as go
import psutil
import time
from datetime import datetime

# -----------------------------
# 1. GLOBAL APP CONFIG
# -----------------------------
st.set_page_config(page_title="Nexus AI - Asset Integrity", layout="wide", page_icon="🌐")

# Enterprise Dark Theme CSS
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    [data-testid="stMetricValue"] { font-size: 1.6rem; color: #00d4ff; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 600; }
    .css-1r6slb0 { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# 2. MODEL & ASSET LOADER
# -----------------------------
@st.cache_resource
def load_engine():
    try:
        with open("model.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        st.error("Model 'model.pkl' not found. Please run your training script first.")
        st.stop()

engine_data = load_engine()
model = engine_data["model"]
feature_order = engine_data["features"] 

# -----------------------------
# 3. SIDEBAR: MULTI-SYSTEM SELECTOR
# -----------------------------
st.sidebar.title("🌐 Mission Control")
system_mode = st.sidebar.selectbox("Active Telemetry Source", 
    ["💻 Live Workstation (Local)", "🏭 Industrial CNC Asset", "📱 Smartphone Diagnostics"])

st.sidebar.divider()
grade = st.sidebar.select_slider("Hardware Reliability Grade", options=["Low", "Medium", "High"], value="Medium")
type_val = {"High": 0, "Low": 1, "Medium": 2}[grade]

# Utility function for "Sensor Noise" to make the UI feel live
def get_noise(scale=0.5):
    return np.random.normal(0, scale)

# -----------------------------
# 4. SYSTEM-SPECIFIC LOGIC
# -----------------------------
if system_mode == "💻 Live Workstation (Local)":
    st.sidebar.info("Streaming live OS telemetry...")
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    # Map to: [Type, AirTemp, ProcTemp, Speed, Torque, Wear]
    vals = [type_val, 300 + get_noise(0.1), 310 + (cpu * 0.4), 2200 + (cpu * 5), cpu, ram]
    labels = ["Architecture Grade", "Inlet Temp (K)", "Core Junction (K)", "Fan Speed (RPM)", "CPU Utilization %", "Memory Commit %"]

elif system_mode == "🏭 Industrial CNC Asset":
    st.sidebar.subheader("Manual Control Deck")
    air = st.sidebar.slider("Ambient Temp (K)", 285, 315, 300)
    proc = st.sidebar.slider("Spindle Temp (K)", 295, 350, 312)
    rpm = st.sidebar.slider("Rotational Speed (RPM)", 500, 4000, 1800)
    trq = st.sidebar.slider("Torque Load (Nm)", 0, 100, 45)
    wr = st.sidebar.slider("Tool Path Wear (min)", 0, 250, 80)
    vals = [type_val, air + get_noise(), proc + get_noise(), rpm, trq, wr]
    labels = ["Machine Class", "Air Temperature", "Process Temperature", "Rotational Speed", "Torque", "Tool Wear"]

else: # Smartphone
    st.sidebar.subheader("Mobile Sensor Simulation")
    bt = st.sidebar.slider("Battery Thermal (°C)", 20, 65, 35)
    volt = st.sidebar.slider("Charging Voltage (mV)", 3200, 4400, 3800)
    cyc = st.sidebar.slider("Cycle Degradation", 0, 1000, 300)
    # Map to: [Type, Air, Proc, RPM(0), Torque(Volt), Wear(Cycles)]
    vals = [type_val, bt + 273, bt + 278, 0, (volt-3000)/15, cyc/4]
    labels = ["Device Tier", "Battery Temp (K)", "Logic Board (K)", "Active Cooling", "Voltage Stress", "Cell Wear Index"]

# -----------------------------
# 5. INFERENCE & HISTORY
# -----------------------------
input_df = pd.DataFrame([vals], columns=feature_order)
risk_score = model.predict_proba(input_df)[0][1] * 100

if "risk_history" not in st.session_state:
    st.session_state.risk_history = [risk_score] * 20
st.session_state.risk_history.append(risk_score)
st.session_state.risk_history = st.session_state.risk_history[-30:] # Keep last 30 readings

# -----------------------------
# 6. MAIN DASHBOARD UI
# -----------------------------
st.title(f"🚀 System Analysis: {system_mode}")
st.caption(f"Predictive Engine Version 4.2 | Logic: Random Forest Classifier | Grade: {grade}")

# TABBED INTERFACE
tab_main, tab_sensors, tab_logs = st.tabs(["📊 KPI Dashboard", "🧬 Technical Matrix", "🛡️ Maintenance Protocol"])

with tab_main:
    # TOP ROW: METRICS
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Risk", f"{risk_score:.1f}%", delta=f"{risk_score - st.session_state.risk_history[-2]:.1f}%", delta_color="inverse")
    
    health_status = "CRITICAL" if risk_score > 75 else ("WARNING" if risk_score > 35 else "HEALTHY")
    m2.metric("System Health", health_status)
    
    # Show the primary driver (usually Process Temp)
    m3.metric(labels[2], f"{vals[2]:.1f}")
    
    m4.metric("Est. Useful Life", f"{max(0, int(100 - risk_score) * 4)}h")

    st.divider()

    # MIDDLE ROW: CHARTS
    col_chart, col_gauge = st.columns([2, 1])
    
    with col_chart:
        st.subheader("Live Risk Trajectory")
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(y=st.session_state.risk_history, fill='tozeroy', line=dict(color='#00d4ff', width=3)))
        fig_line.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,t=0,b=0), xaxis_showgrid=False)
        st.plotly_chart(fig_line, use_container_width=True)
    
    with col_gauge:
        st.subheader("Threat Gauge")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=risk_score,
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#00d4ff"},
                   'steps': [{'range': [0, 35], 'color': "#1e4620"}, {'range': [35, 75], 'color': "#856404"}, {'range': [75, 100], 'color': "#721c24"}]}))
        fig_gauge.update_layout(template="plotly_dark", height=300, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

with tab_sensors:
    st.subheader("Deep-Dive Sensor Matrix")
    # Display 5 individual sensor values (excluding the 'Type' grade)
    s_cols = st.columns(5)
    for i in range(1, 6):
        with s_cols[i-1]:
            st.metric(labels[i], f"{vals[i]:.2f}")
    
    st.divider()
    
    # Feature Importance Logic
    st.subheader("AI Decision Analysis")
    importances = model.feature_importances_
    # Align importance with the dynamic labels
    fig_imp = go.Figure(go.Bar(x=importances[1:], y=labels[1:], orientation='h', marker_color='#1f6feb'))
    fig_imp.update_layout(template="plotly_dark", height=300, yaxis={'categoryorder':'total ascending'}, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig_imp, use_container_width=True)

with tab_logs:
    st.subheader("Recommended Maintenance Actions")
    l_col1, l_col2 = st.columns(2)
    
    with l_col1:
        if risk_score > 75:
            st.error(f"### 🚩 CRITICAL INTERVENTION\nHigh stress detected on {labels[2]}. Immediate shutdown of {system_mode} required to prevent catastrophic failure.")
        elif risk_score > 35:
            st.warning(f"### ⚠️ PREVENTATIVE MAINTENANCE\nAbnormal wear patterns on {labels[5]}. Schedule technical inspection within 24 operational hours.")
        else:
            st.success("### ✅ NOMINAL STATUS\nAll hardware parameters within safety bounds. No maintenance required.")
    
    with l_col2:
        st.info("**Technician Note:**")
        st.write(f"The analysis for **{system_mode}** is based on the current **{grade}** reliability profile. If the hardware has been modified, update the grade in the sidebar for more accurate results.")

# 7. AUTOMATED REFRESH (Simulates a live system)
if system_mode == "💻 Live Workstation (Local)":
    time.sleep(1)
    st.rerun()