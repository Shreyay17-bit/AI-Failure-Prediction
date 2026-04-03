import streamlit as st
import pandas as pd
import numpy as np
import pickle
import time
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Nexus AI - Diagnostics", layout="wide")

# -----------------------------
# 1. HARDWARE BRIDGE (SYNC)
# -----------------------------
# Combined script to pull User Agent, CPU Cores, and Battery Status
js_bridge = """
(function() {
    return navigator.getBattery().then(function(b) {
        return {
            ua: navigator.userAgent,
            cores: navigator.hardwareConcurrency || 4,
            level: b.level,
            charging: b.charging
        };
    }).catch(function() {
        return {
            ua: navigator.userAgent,
            cores: navigator.hardwareConcurrency || 4,
            level: null,
            charging: null
        };
    });
})()
"""
hw = st_javascript(js_bridge)

# -----------------------------
# 2. SIDEBAR CONTROLS
# -----------------------------
st.sidebar.title("System Controls")

analysis_mode = st.sidebar.radio(
    "Analysis Target",
    ["Live Connected Device", "Industrial CNC Mill"]
)

# -----------------------------
# 3. PARAMETER SYNCHRONIZATION
# -----------------------------
# We initialize variables with your current real-world state (65%)
battery_val = 65 
core_count = 4
is_windows = True
is_charging = False

if hw and isinstance(hw, dict) and hw.get("level") is not None:
    # SUCCESS: Actual hardware data captured
    battery_val = int(hw["level"] * 100)
    is_charging = hw.get("charging", False)
    core_count = hw.get("cores", 4)
    is_windows = "Windows" in hw.get("ua", "")
    st.sidebar.success(f"Live Sync Active: {battery_val}%")
else:
    # FALLBACK: Browser blocked the sensor, use manual slider
    st.sidebar.warning("Sync Pending: Using Manual Defaults")
    battery_val = st.sidebar.slider("Manual Battery Override (%)", 0, 100, 65)
    st.sidebar.info("Click anywhere on the app to help the browser authorize sensors.")

# -----------------------------
# 4. AI MODEL MAPPING
# -----------------------------
if analysis_mode == "Live Connected Device":
    device_name = "Desktop Workstation" if is_windows else "Mobile Device"
    type_id = 1 if is_windows else 0
    
    # AI Logic: Lower battery (Wear) and High Cores (Heat) increase risk
    wear_idx = (100 - battery_val) * 2.5
    temp_k = 302 + (core_count * 1.5)
    speed_sim = core_count * 750
    
    # [Type, AirTemp, ProcTemp, Speed, Torque, Wear]
    input_vec = [type_id, temp_k, temp_k + 5, speed_sim, 45.0, wear_idx]
    
    display_metrics = {
        "Ambient": f"{temp_k - 273.15:.1f} °C",
        "Core": f"{temp_k - 268.15:.1f} °C",
        "Clock": f"{speed_sim} MHz",
        "Source": "External AC" if is_charging else "Battery Port"
    }

else:
    device_name = "Industrial CNC Mill"
    type_id = 1
    
    st.sidebar.subheader("CNC Spindle Params")
    rpm = st.sidebar.slider("Rotational Speed (RPM)", 0, 5000, 2200)
    torque = st.sidebar.slider("Torque (Nm)", 0, 150, 48)
    
    input_vec = [type_id, 298.0, 312.0, rpm, torque, 25.0]
    
    display_metrics = {
        "Ambient": "298.0 K",
        "Spindle": "312.0 K",
        "Speed": f"{rpm} RPM",
        "Load": f"{torque} Nm"
    }

# -----------------------------
# 5. DASHBOARD DISPLAY
# -----------------------------
st.title(f"System Diagnostics: {device_name}")

c1, c2, c3 = st.columns(3)

try:
    with open("model.pkl", "rb") as f:
        engine = pickle.load(f)
    
    # Run the model
    risk_prob = engine["model"].predict_proba([input_vec])[0][1] * 100
    
    c1.metric("Failure Risk", f"{risk_prob:.2f}%")
    c2.metric("Primary Sensor", f"{battery_val if analysis_mode == 'Live Connected Device' else rpm}%")
    c3.metric("Health Status", "OPTIMAL" if risk_prob < 35 else "CAUTION")

    st.divider()
    
    # Data Visualization
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Sensor Details")
        for key, val in display_metrics.items():
            st.write(f"**{key}:** {val}")
            
    with col_right:
        st.subheader("Neural Input Stream")
        st.json({
            "vector_id": type_id,
            "calculated_wear": round(input_vec[5], 2),
            "input_array": input_vec
        })

except Exception as e:
    st.error(f"Inference Engine Offline: {e}")

# Refresh every 4 seconds
time.sleep(4)
st.rerun()