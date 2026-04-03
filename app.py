import streamlit as st
import pandas as pd
import numpy as np
import pickle
import time
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Nexus AI - Diagnostics", layout="wide")

# -----------------------------
# 1. THE HARDWARE PROBE
# -----------------------------
# Simplified JS to pull UA and Cores immediately
js_code = """
(function() {
    return {
        ua: navigator.userAgent,
        cores: navigator.hardwareConcurrency || 4,
        ram: navigator.deviceMemory || 8
    };
})()
"""
hw = st_javascript(js_code)

# -----------------------------
# 2. THE BATTERY PROBE (SEPARATE)
# -----------------------------
# Separating this because it is the most likely part to be blocked
batt_js = "navigator.getBattery().then(b => b.level)"
raw_batt = st_javascript(batt_js)

# -----------------------------
# 3. DATA VALIDATION & OVERRIDE
# -----------------------------
st.sidebar.title("System Controls")

# If the browser blocks the battery, we use your 35% as a manual starting point
if raw_batt is None or raw_batt == 0:
    st.sidebar.warning("Hardware Sensors Restricted")
    battery_input = st.sidebar.slider("Manual Battery Override (%)", 0, 100, 35)
    is_auto = False
else:
    battery_input = int(raw_batt * 100)
    st.sidebar.success(f"Live Sensor Active: {battery_input}%")
    is_auto = True

# -----------------------------
# 4. PROCESSING & INFERENCE
# -----------------------------
if hw:
    ua = hw.get("ua", "")
    cores = hw.get("cores", 4)
    is_windows = "Windows" in ua
    
    # Risk Logic based on your 35%
    # Lower battery = Higher Wear = Higher Risk
    wear_idx = (100 - battery_input) * 2.3
    temp_k = 302 + (cores * 1.2)
    
    # Vector: [Type, AirTemp, ProcTemp, Speed, Torque, Wear]
    input_vec = [1 if is_windows else 0, temp_k, temp_k + 5, cores * 800, 45.0, wear_idx]

    # Dashboard
    st.title(f"System Diagnostics: {'Workstation' if is_windows else 'Mobile'}")
    
    c1, c2, c3 = st.columns(3)
    
    try:
        with open("model.pkl", "rb") as f:
            nexus = pickle.load(f)
        
        # This will finally move the 0.00% risk!
        prob = nexus["model"].predict_proba([input_vec])[0][1] * 100
        
        c1.metric("Failure Risk", f"{prob:.2f}%")
        c2.metric("Battery Level", f"{battery_input}%")
        c3.metric("Logic Cores", cores)
        
        st.divider()
        
        # Technical Details
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Hardware Detail")
            st.write(f"Identity: {ua[:50]}...")
            st.write(f"Sensor Mode: {'Automated' if is_auto else 'Manual Override'}")
        
        with col_b:
            st.subheader("Neural Input Stream")
            st.json({"wear": wear_idx, "temp": temp_k, "vec": input_vec})

    except Exception as e:
        st.error(f"Model Sync Error: {e}")

else:
    st.info("Initializing System Bridge...")

# Refresh
time.sleep(4)
st.rerun()