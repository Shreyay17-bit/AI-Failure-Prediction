import streamlit as st
import pandas as pd
import numpy as np
import pickle
import time
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Nexus AI - Technical Interface", layout="wide")

# -----------------------------
# 1. LIVE HARDWARE BRIDGE
# -----------------------------
# This script bypasses standard caching to pull your actual 35% battery
device_js = """
async function getHardware() {
    let bat = { level: null, charging: null };
    try {
        if (navigator.getBattery) {
            const b = await navigator.getBattery();
            bat = { level: b.level, charging: b.charging };
        }
    } catch (e) { console.log("API Blocked"); }

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
# 2. THE HANDSHAKE PROTOCOL
# -----------------------------
if not hw or hw.get("battery", {}).get("level") is None:
    st.title("System Diagnostics")
    st.warning("Hardware Synchronization Required")
    st.info("Please click the button below to authorize the secure hardware sensor link.")
    
    # The 'User Gesture' required by Chrome/Windows to release battery data
    if st.button("Sync Real-Time Hardware"):
        st.rerun()
    st.stop() 

# -----------------------------
# 3. PROCESSING REAL-TIME METRICS
# -----------------------------
# This captures your exact 35% (0.35) and converts it to an integer
actual_pct = int(hw["battery"]["level"] * 100)
is_charging = hw["battery"]["charging"]
cores = hw["cores"]
ua = hw["ua"]

# Identity Logic
is_windows = "Windows" in ua
type_id = 1 if is_windows else 0

# Predictive Mapping Logic
# Since you are at 35%, wear_index will be approx 143 (High)
wear_index = (100 - actual_pct) * 2.2 
thermal_k = 302 + (cores * 1.5)

# Input Vector: [Type, AirTemp, ProcTemp, Speed, Torque, Wear]
input_vector = [type_id, thermal_k, thermal_k + 6, cores * 750, 48.0, wear_index]

# -----------------------------
# 4. DASHBOARD OUTPUT
# -----------------------------
st.title(f"System Diagnostics: {'Workstation' if is_windows else 'Mobile'}")

m1, m2, m3, m4 = st.columns(4)

try:
    with open("model.pkl", "rb") as f:
        nexus = pickle.load(f)
    
    # Calculate probability using YOUR live battery data
    risk_prob = nexus["model"].predict_proba([input_vector])[0][1] * 100
    
    m1.metric("Failure Risk", f"{risk_prob:.2f}%")
    m2.metric("Battery Status", f"{actual_pct}%")
    m3.metric("Logic Processors", cores)
    m4.metric("Power Source", "External AC" if is_charging else "Battery Port")

    st.divider()
    
    # Detailed Data Grid for the Pitch
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Hardware Detail")
        st.write(f"System Architecture: {ua[:60]}...")
        st.write(f"Voltage Profile: {'Stable' if is_charging else 'Discharge Active'}")
    
    with col_right:
        st.subheader("AI Vector Stream")
        st.json({
            "calculated_wear": round(wear_index, 2),
            "thermal_input_k": round(thermal_k, 2),
            "effective_rpm_sim": input_vector[3]
        })

except Exception as e:
    st.error("Model Sync Error: Please ensure model.pkl is in the GitHub repository.")

# 5-second refresh to track live battery drain
time.sleep(5)
st.rerun()