import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.graph_objects as go
import psutil
import time
from streamlit_javascript import st_javascript # <--- New bridge

# -----------------------------
# 1. UI & DEVICE DETECTION
# -----------------------------
st.set_page_config(page_title="Nexus AI - Mobile Predict", layout="wide")

# This script asks the phone: "Who are you?"
user_info = st_javascript("navigator.userAgent")

st.sidebar.title("🌐 Nexus Control")

# -----------------------------
# 2. DYNAMIC DEVICE RECOGNITION
# -----------------------------
detected_device = "Generic Device"
if user_info:
    if "iPhone" in user_info:
        detected_device = "Apple iPhone"
    elif "Android" in user_info:
        detected_device = "Android Smartphone"
    elif "Windows" in user_info:
        detected_device = "Windows Workstation"

st.sidebar.success(f"Connected: {detected_device}")

system_mode = st.sidebar.selectbox("Analysis Mode", 
    ["📱 Mobile Diagnostics", "🏭 Industrial CNC", "💻 Cloud Server"])

# -----------------------------
# 3. THE "6-COLUMN" DATA PREP
# -----------------------------
# We must always pass exactly 6 values to the model
# [Type, AirTemp, ProcTemp, Speed, Torque, Wear]

if system_mode == "📱 Mobile Diagnostics":
    st.sidebar.subheader(f"{detected_device} Sensors")
    
    # Simulating 'Live' behavior with a small random wiggle
    # In a real IoT project, this is where your ESP32 data would go
    temp_base = st.sidebar.slider("Battery Temp (°C)", 20, 60, 35)
    live_temp = temp_base + np.random.normal(0, 0.2)
    
    # Mapping to 6 columns
    vals = [0, live_temp + 273, live_temp + 278, 0, 15.5, 120]
    labels = ["Tier", "Internal Temp", "Chipset Temp", "Fan", "Voltage Load", "Cycle Wear"]

elif system_mode == "🏭 Industrial CNC":
    # ... (Keep your existing CNC sliders here) ...
    vals = [1, 300, 312, 1800, 45, 60]
    labels = ["Class", "Ambient", "Spindle", "RPM", "Torque", "Wear"]

else: # Cloud Server
    cpu = psutil.cpu_percent()
    vals = [2, 298, 310 + (cpu*0.5), 2400, cpu, 15]
    labels = ["Grade", "Inlet", "CPU Core", "Fan", "Load", "Uptime"]

# -----------------------------
# 4. PREDICTION & UI
# -----------------------------
# Load model (make sure model.pkl is on GitHub!)
try:
    with open("model.pkl", "rb") as f:
        engine = pickle.load(f)
    model = engine["model"]
    feature_names = engine["features"]
    
    input_df = pd.DataFrame([vals], columns=feature_names)
    prob = model.predict_proba(input_df)[0][1] * 100
    
    st.title(f"🚀 {detected_device} Integrity Report")
    
    col1, col2 = st.columns(2)
    col1.metric("Failure Risk", f"{prob:.1f}%")
    col2.metric("Device State", "STABLE" if prob < 40 else "CRITICAL")
    
    # Gauge Chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=prob,
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#00d4ff"}}))
    st.plotly_chart(fig)

except Exception as e:
    st.error(f"Sync Error: {e}")

# Refresh to make the "Live" feeling work
time.sleep(2)
st.rerun()