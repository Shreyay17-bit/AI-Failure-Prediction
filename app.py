import streamlit as st
import pandas as pd
import numpy as np
import pickle
import time
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Nexus AI - Technical Interface", layout="wide")

# -----------------------------
# 1. HARDWARE PROBE (ACCURACY MODE)
# -----------------------------
# This script specifically queries the Windows/Android Power Manager
device_js = """
async function getHardware() {
    let bat = { level: null, charging: null };
    try {
        if (navigator.getBattery) {
            const b = await navigator.getBattery();
            bat = { level: b.level, charging: b.charging };
        }
    } catch (e) { console.log("Blocked"); }

    return {
        ua: navigator.userAgent,
        cores: navigator.hardwareConcurrency || 4,
        battery: bat
    };
}
getHardware();
"""

hw = st_javascript(device_js)

# -----------------------------
# 2. VALIDATION & UI TRIGGER
# -----------------------------
if not hw or hw.get("battery", {}).get("level") is None:
    # If we don't have the 35% yet, show this screen
    st.title("System Diagnostics")
    st.warning("Hardware Synchronization Required")
    st.info("Browser privacy settings are restricting hardware access. Please click the button below to authorize the real-time sensor link.")
    
    # This button creates the 'User Gesture' the browser needs
    if st.button("Sync Real-Time Hardware"):
        st.rerun()
    st.stop() 

# -----------------------------
# 3. PROCESSING ACTUAL DATA
# -----------------------------
# Now we have the real 35% (0.35)
actual_pct = int(hw["battery"]["level"] * 100)
is_charging = hw["battery"]["charging"]
cores = hw["cores"]
ua = hw["ua"]

# Determine Device ID for the Model
type_id = 1 if "Windows" in ua else (0 if "iPhone" in ua else 2)

# Wear is calculated directly from your 35%
# Lower battery = higher wear in the AI logic
wear_index = (100 - actual_pct) * 2.2 
thermal_k = 300 + (cores * 1.8)

input_vector = [type_id, thermal_k, thermal_k + 5, cores * 600, 45.0, wear_index]

# -----------------------------
# 4. DASHBOARD OUTPUT
# -----------------------------
st.title(f"System Diagnostics: {'Workstation' if type_id == 1 else 'Mobile'}")

m1, m2, m3 = st.columns(3)

try:
    with open("model.pkl", "rb") as f:
        nexus = pickle.load(f)
    
    # Prediction based on YOUR real battery life
    risk = nexus["model"].predict_proba([input_vector])[0][1] * 100
    
    m1.metric("Failure Risk", f"{risk:.2f}%")
    m2.metric("Battery Status", f"{actual_pct}%") # This will now show 35%
    m3.metric("Power Source", "External AC" if is_charging else "Battery Port")

    st.divider()
    
    # Professional Data Stream
    st.subheader("Neural Network Input stream")
    st.json({
        "calculated_wear": round(wear_index, 2),
        "detected_cores": cores,
        "input_vector": input_vector
    })

except Exception as e:
    st.error("Model Sync Error. Ensure model.pkl is in the root directory.")

# Automated Refresh to track battery changes
time.sleep(5)
st.rerun()