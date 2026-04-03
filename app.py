import streamlit as st
import pandas as pd
import numpy as np
import pickle
import time
from streamlit_javascript import st_javascript

st.set_page_config(page_title="Nexus AI - Hardware Interface", layout="wide")

# -----------------------------
# 1. HARDWARE DATA ACQUISITION
# -----------------------------
# Using JavaScript to bridge the browser-to-hardware gap
device_js = """
async function getHardwareData() {
    let battery = { level: 1, charging: true };
    try {
        if (navigator.getBattery) {
            const b = await navigator.getBattery();
            battery = { level: b.level, charging: b.charging };
        }
    } catch (e) { 
        console.log("Battery API Restricted"); 
    }

    return {
        ua: navigator.userAgent,
        memory: navigator.deviceMemory || "N/A", 
        logic_cores: navigator.hardwareConcurrency || "N/A",
        battery: battery
    };
}
getHardwareData();
"""

# Execute JS and catch result
hw_data = st_javascript(device_js)

# -----------------------------
# 2. LOGIC AND CLASSIFICATION
# -----------------------------
if hw_data:
    ua_string = hw_data.get("ua", "")
    
    # Categorize Device Type for the Model
    if "iPhone" in ua_string or "iPad" in ua_string:
        device_label = "Apple iOS Mobile"
        model_type_code = 0
    elif "Android" in ua_string:
        device_label = "Android Mobile"
        model_type_code = 2
    else:
        device_label = "Desktop Workstation"
        model_type_code = 1

    # Extract Accurate Values
    raw_battery = hw_data.get("battery", {}).get("level", 1.0)
    battery_pct = int(raw_battery * 100)
    core_count = hw_data.get("logic_cores", 4)
    ram_gb = hw_data.get("memory", "Standard")
    is_charging = hw_data.get("battery", {}).get("charging", True)

    # -----------------------------
    # 3. AI PREDICTION MAPPING
    # -----------------------------
    # Mapping real hardware metrics to the 6-column predictive model
    # [Type, AirTemp, ProcTemp, Speed, Torque, Wear]
    
    # We derive 'Wear' from Battery Level (Inverse relationship)
    # We derive 'Speed' from Hardware Cores
    simulated_temp_c = 32.5 + (core_count if isinstance(core_count, int) else 4) * 0.8
    wear_index = (100 - battery_pct) * 2.5
    
    input_vector = [
        model_type_code, 
        simulated_temp_c + 273.15, 
        simulated_temp_c + 278.15, 
        (core_count if isinstance(core_count, int) else 4) * 450, 
        42.5, 
        wear_index
    ]

    # -----------------------------
    # 4. PROFESSIONAL DASHBOARD
    # -----------------------------
    st.title(f"Hardware Diagnostics: {device_label}")
    st.caption(f"System UUID: {hash(ua_string) % 10**8} | Status: Synchronized")

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    
    # Load and Run Model
    try:
        with open("model.pkl", "rb") as f:
            nexus_engine = pickle.load(f)
        
        predictor = nexus_engine["model"]
        failure_probability = predictor.predict_proba([input_vector])[0][1] * 100
        
        m1.metric("Failure Risk", f"{failure_probability:.2f}%")
        m2.metric("Battery Level", f"{battery_pct}%")
        m3.metric("Logic Cores", core_count)
        m4.metric("Memory (RAM)", f"{ram_gb} GB")

        st.divider()

        # Detailed Technical Specs
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Device Metadata")
            st.text(f"User Agent: {ua_string[:80]}...")
            st.text(f"Power Source: {'AC Adapter' if is_charging else 'Battery Port'}")
            st.text(f"Architecture: {device_label}")

        with col_right:
            st.subheader("Model Input Vector")
            st.json({
                "Core_Temp_Kelvin": round(input_vector[2], 2),
                "Clock_Speed_Equivalent": input_vector[3],
                "Calculated_Wear_Index": round(wear_index, 2),
                "Machine_Type_ID": model_type_code
            })

    except Exception as error:
        st.error(f"Inference Engine Offline: {error}")

else:
    st.info("Initializing Hardware Handshake...")

# Automated Refresh Interval (3 Seconds)
time.sleep(3)
st.rerun()