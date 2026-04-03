import streamlit as st
import pandas as pd
import numpy as np
import pickle
import time
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Nexus AI - Hardware Diagnostics", layout="wide")

# -----------------------------
# 1. UNIFIED HARDWARE BRIDGE
# -----------------------------
# Detects User Agent, CPU Cores, and Battery in one go
js_bridge = """
async function getFullSystem() {
    let bat = { level: 0.35, charging: false };
    try {
        if (navigator.getBattery) {
            const b = await navigator.getBattery();
            bat = { level: b.level, charging: b.charging };
        }
    } catch (e) {}

    return {
        ua: navigator.userAgent,
        cores: navigator.hardwareConcurrency || 4,
        battery: bat
    };
}
getFullSystem();
"""
hw = st_javascript(js_bridge)

# -----------------------------
# 2. SIDEBAR & MODE SELECTION
# -----------------------------
st.sidebar.title("System Controls")

# Analysis Target Toggle
analysis_mode = st.sidebar.radio(
    "Analysis Target",
    ["Live Connected Device", "Industrial CNC Mill"]
)

# -----------------------------
# 3. CORE LOGIC & PARAMETER MAPPING
# -----------------------------
# We initialize variables with safe defaults to prevent the 'Initializing' hang
battery_val = 35 
core_count = 4
is_windows = True
is_charging = False

if hw:
    # Accurate Data Extraction from Bridge
    ua = hw.get("ua", "")
    core_count = hw.get("cores", 4)
    raw_bat = hw.get("battery", {}).get("level", 0.35)
    battery_val = int(raw_bat * 100)
    is_charging = hw.get("battery", {}).get("charging", False)
    is_windows = "Windows" in ua
    
    st.sidebar.success(f"System Sync: ACTIVE ({battery_val}%)")
else:
    st.sidebar.warning("Sync Pending: Using Manual Defaults")
    # Manual Override slider if hardware is slow
    battery_val = st.sidebar.slider("Manual Battery Override (%)", 0, 100, 35)

# -----------------------------
# 4. DATA MAPPING FOR AI MODEL
# -----------------------------
if analysis_mode == "Live Connected Device":
    device_name = "Desktop Workstation" if is_windows else "Mobile Device"
    type_id = 1 if is_windows else 0
    
    # Map real battery to AI 'Wear'
    wear_idx = (100 - battery_val) * 2.2
    temp_k = 302 + (core_count * 1.5)
    speed_sim = core_count * 750
    
    input_vec = [type_id, temp_k, temp_k + 5, speed_sim, 45.0, wear_idx]
    display_metrics = {
        "Ambient": f"{temp_k - 273.15:.1f} °C",
        "Core": f"{temp_k - 268.15:.1f} °C",
        "Clock": f"{speed_sim} MHz",
        "Source": "External AC" if is_charging else "Battery Port"
    }

else:
    device_name = "Industrial CNC Mill"
    type_id = 1 # Industrial class
    
    # Industrial Mode uses different scaling
    st.sidebar.subheader("CNC Spindle Controls")
    rpm = st.sidebar.slider("Rotational Speed (RPM)", 0, 5000, 1800)
    torque = st.sidebar.slider("Torque (Nm)", 0, 100, 45)
    
    input_vec = [type_id, 298.0, 310.0, rpm, torque, 20.0]
    display_metrics = {
        "Ambient": "298.0 K",
        "Spindle": "310.0 K",
        "Speed": f"{rpm} RPM",
        "Load": f"{torque} Nm"
    }

# -----------------------------
# 5. DASHBOARD UI
# -----------------------------
st.title(f"System Diagnostics: {device_name}")

c1, c2, c3 = st.columns(3)

try:
    with open("model.pkl", "rb") as f:
        nexus = pickle.load(f)
    
    # Run Inference
    risk = nexus["model"].predict_proba([input_vec])[0][1] * 100
    
    c1.metric("Failure Risk", f"{risk:.2f}%")
    c2.metric("Primary Sensor", f"{battery_val if analysis_mode == 'Live Connected Device' else rpm}%")
    c3.metric("Health Status", "OPTIMAL" if risk < 30 else "WARNING")

    st.divider()
    
    # Detailed Data Grid
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Sensor Details")
        for k, v in display_metrics.items():
            st.write(f"**{k}:** {v}")
            
    with col_right:
        st.subheader("Neural Input Stream")
        st.json({"vector": input_vec, "wear_index": input_vec[5]})

except Exception as e:
    st.error(f"Inference Engine Offline: {e}")

# Automated Refresh
time.sleep(4)
st.rerun()