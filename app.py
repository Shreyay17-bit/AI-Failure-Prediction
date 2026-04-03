import streamlit as st
import pandas as pd
import numpy as np
import pickle
import time
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Nexus AI - Live Hardware", layout="wide")

# -----------------------------
# 1. THE EXACT HARDWARE PROBE
# -----------------------------
# This script waits specifically for the Battery Manager to return 
# the REAL value from your Windows/Android/iOS power management.
device_js = """
async function getLiveHardware() {
    let batteryData = { level: null, charging: null };
    
    try {
        if (navigator.getBattery) {
            const bat = await navigator.getBattery();
            batteryData.level = bat.level; // Returns 0.34 for 34%
            batteryData.charging = bat.charging;
        }
    } catch (e) {
        console.error("Hardware Access Denied");
    }

    return {
        ua: navigator.userAgent,
        memory: navigator.deviceMemory || 8,
        cores: navigator.hardwareConcurrency || 4,
        battery: batteryData
    };
}
getLiveHardware();
"""

hw = st_javascript(device_js)

# -----------------------------
# 2. VALIDATION & FALLBACK
# -----------------------------
if hw and hw.get("battery") and hw["battery"]["level"] is not None:
    # SUCCESS: We have the real 34%
    real_pct = int(hw["battery"]["level"] * 100)
    is_charging = hw["battery"]["charging"]
    device_ua = hw.get("ua", "Unknown")
    cores = hw.get("cores", 4)
else:
    # WAITING: Show a loading state instead of a wrong number
    st.info("Synchronizing with System Power Management... Please wait.")
    st.stop() # Prevents the rest of the app from loading with wrong data

# -----------------------------
# 3. DYNAMIC AI RISK LOGIC
# -----------------------------
# Now the Failure Risk will change BASED on your 34%
# Lower battery = Higher simulated wear = Higher Risk
wear_logic = (100 - real_pct) * 2.1
temp_logic = 32 + (cores * 1.5)

input_vector = [
    1 if "Windows" in device_ua else 0, # Type
    temp_logic + 273,                   # AirTemp
    temp_logic + 279,                   # ProcTemp
    cores * 600,                        # Speed
    45.0,                               # Torque
    wear_logic                          # Wear
]

# -----------------------------
# 4. OUTPUT
# -----------------------------
st.title(f"Hardware System: {'Workstation' if 'Windows' in device_ua else 'Mobile'}")

col1, col2, col3 = st.columns(3)

try:
    with open("model.pkl", "rb") as f:
        model_data = pickle.load(f)
    
    risk = model_data["model"].predict_proba([input_vector])[0][1] * 100
    
    col1.metric("Failure Risk", f"{risk:.2f}%")
    col2.metric("Actual Battery", f"{real_pct}%")
    col3.metric("Power Source", "AC Adapter" if is_charging else "Battery")

    st.divider()
    st.subheader("Raw AI Input Stream")
    st.write(f"Calculated Degradation Index: {wear_logic:.2f}")

except Exception as e:
    st.error(f"Model Error: {e}")

# Refresh every 5 seconds to catch battery drops
time.sleep(5)
st.rerun()