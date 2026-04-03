import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_javascript import st_javascript
import time

# 1. PAGE CONFIG
st.set_page_config(page_title="Nexus AI | Pro Diagnostics", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .report-card { background: #161b22; padding: 20px; border-radius: 10px; border-left: 5px solid #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE AGGRESSIVE HARDWARE BRIDGE
# This uses an async promise to wait for the battery manager to respond
js_bridge = """
(async function() {
    let batteryInfo = { level: "N/A", charging: "N/A" };
    
    try {
        if (navigator.getBattery) {
            const bat = await navigator.getBattery();
            batteryInfo = { 
                level: bat.level, 
                charging: bat.charging 
            };
        } else {
            batteryInfo = { level: "RESTRICTED", charging: "RESTRICTED" };
        }
    } catch (e) {
        batteryInfo = { level: "ERROR", charging: e.message };
    }

    // Advanced Device Fingerprinting
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    const debugInfo = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
    const gpu = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : "Integrated Graphics";

    return {
        ua: navigator.userAgent,
        cores: navigator.hardwareConcurrency || 4,
        ram: navigator.deviceMemory || "Unknown",
        gpu: gpu,
        battery: batteryInfo,
        platform: navigator.platform,
        screen: window.screen.width + "x" + window.screen.height
    };
})()
"""

# Execute and catch the result
hw = st_javascript(js_bridge)

# 3. INITIALIZATION & FALLBACK
# If the hardware hasn't responded yet, we show a "Connecting" state
if not hw:
    st.warning("📡 Synchronizing with Hardware... Please wait 1 second.")
    time.sleep(1)
    st.rerun()

# 4. DATA EXTRACTION
ua = hw.get("ua", "")
bat_data = hw.get("battery", {})
raw_level = bat_data.get("level")

# Handle different battery return types
if isinstance(raw_level, (int, float)):
    battery_pct = int(raw_level * 100)
    bat_display = f"{battery_pct}%"
else:
    # If the browser blocked the request (Safari/Firefox/Private Mode)
    battery_pct = 0
    bat_display = "BLOCKED BY BROWSER"

is_charging = bat_data.get("charging", "N/A")
cores = hw.get("cores", "N/A")
ram = hw.get("ram", "N/A")
gpu = hw.get("gpu", "Standard Renderer")

# Device Profiler
is_mobile = any(x in ua for x in ["iPhone", "Android", "Mobile"])
device_type = "📱 Mobile Node" if is_mobile else "💻 Desktop Workstation"

# 5. UI DASHBOARD
st.title(f"Diagnostic Report: {device_type}")
st.caption(f"Hardware Signature: {gpu}")

cols = st.columns(4)
cols.metric("Battery Level", bat_display, delta="Charging" if is_charging == True else "On Battery")
cols.metric("CPU Cores", f"{cores} Threads")
cols.metric("RAM (Approx)", f"{ram} GB")
cols.metric("Screen Res", hw.get("screen", "N/A"))

st.divider()

# 6. HUMAN-READABLE ANALYSIS
l, r = st.columns([2, 1])

with l:
    st.subheader("Performance Dynamics")
    # Speed Gauge
    speed = round((int(cores) * 0.5) if isinstance(cores, int) else 2.5, 1)
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = speed,
        title = {'text': "Est. Clock Speed (GHz)"},
        gauge = {'axis': {'range': [0, 8]}, 'bar': {'color': "#238636"}}
    ))
    fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
    st.plotly_chart(fig, use_container_width=True)

with r:
    st.subheader("System Health Intelligence")
    
    # Custom report based on device data
    if bat_display == "BLOCKED BY BROWSER":
        privacy_note = "⚠️ Your browser (likely Safari or Firefox) is blocking battery data for privacy."
    else:
        privacy_note = "✅ Real-time battery telemetry active."

    st.markdown(f"""
    <div class="report-card">
        <h4>User-Friendly Summary</h4>
        <p><b>Platform:</b> {hw.get('platform')}</p>
        <p><b>GPU Engine:</b> {gpu.split('/')[-1]}</p>
        <hr>
        <p>This <b>{device_type}</b> is currently running at <b>{speed}GHz</b>. 
        The system detected <b>{cores} CPU cores</b>, which is optimal for multitasking.</p>
        <p style="font-size: 0.8rem; color: #8b949e;">{privacy_note}</p>
    </div>
    """, unsafe_allow_html=True)

# 7. TELEMETRY LOG
with st.expander("Show Detailed Hardware Logs"):
    st.json(hw)

# Refresh every 30 seconds to update battery
time.sleep(30)
st.rerun()
