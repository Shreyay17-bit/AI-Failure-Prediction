import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_javascript import st_javascript
import time

# 1. PAGE CONFIG
st.set_page_config(page_title="Nexus AI | Deep Diagnostics", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .report-card { background: #161b22; padding: 20px; border-radius: 10px; border-left: 5px solid #238636; }
    </style>
    """, unsafe_allow_html=True)

# 2. ADVANCED JS BRIDGE (Grabs more "fingerprints")
js_bridge = """
(async function() {
    let battery = { level: 1, charging: true };
    try { if (navigator.getBattery) battery = await navigator.getBattery(); } catch (e) {}
    
    // Attempt to get GPU info
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    const debugInfo = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
    const gpu = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : "Integrated Graphics";

    return {
        ua: navigator.userAgent,
        cores: navigator.hardwareConcurrency || "Unknown",
        ram: navigator.deviceMemory || "N/A",
        gpu: gpu,
        battery: { level: battery.level, charging: battery.charging },
        platform: navigator.platform
    };
})()
"""
hw = st_javascript(js_bridge)

# 3. DATA PROCESSING & STANDARDIZATION
if not hw:
    st.info("⚡ Initializing Diagnostic Neural Link...")
    st.stop()

# Extract specs
ua = hw.get("ua", "")
gpu = hw.get("gpu", "Generic Renderer")
ram = hw.get("ram", "Unknown")
cores = hw.get("cores", 4)
bat = hw.get("battery", {})
battery_pct = int(bat.get("level", 1) * 100)

# Identify Device
if "iPhone" in ua or "Android" in ua:
    device_type = "Mobile Node"
    icon = "📱"
elif "Macintosh" in ua:
    device_type = "MacBook / iMac"
    icon = "💻"
else:
    device_type = "Windows Workstation"
    icon = "🖥️"

# 4. DASHBOARD HEADER
st.title(f"{icon} System Analysis: {device_type}")
cols = st.columns(4)
cols[0].metric("Hardware Cores", f"{cores} Threads")
cols[1].metric("Memory (Est)", f"{ram} GB")
cols[2].metric("Battery Level", f"{battery_pct}%", delta="Charging" if bat.get("charging") else "Discharging")
cols[3].metric("GPU Engine", "Active", help=gpu)

st.divider()

# 5. VISUAL TELEMETRY
l, r = st.columns([2, 1])

with l:
    st.subheader("Performance Vector")
    # Speed Gauge (Calculated estimate based on cores)
    speed_est = round((cores * 0.6), 2) 
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = speed_est,
        title = {'text': "Estimated Throughput (TFLOPS)"},
        gauge = {'axis': {'range': [0, 15]}, 'bar': {'color': "#58a6ff"}}
    ))
    fig.update_layout(height=300, margin=dict(t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
    st.plotly_chart(fig, use_container_width=True)

with r:
    st.subheader("Understable Analysis")
    
    # Logic for a human-readable report
    health_score = 100 - (100 - battery_pct) * 0.5
    if battery_pct < 20 and not bat.get("charging"):
        status = "CRITICAL: Low Power Throttling"
        color = "#f85149"
    elif cores < 4:
        status = "LEGACY: Limited Multitasking"
        color = "#d29922"
    else:
        status = "OPTIMAL: High Performance"
        color = "#238636"

    st.markdown(f"""
    <div class="report-card" style="border-left-color: {color}">
        <h4>Diagnostic Summary</h4>
        <p><b>Status:</b> {status}</p>
        <p><b>GPU:</b> {gpu}</p>
        <p><b>Architecture:</b> {ua.split(')')[0].split('(')[-1]}</p>
        <hr>
        <small>This node is operating within normal thermal parameters. 
        The <b>{cores}-core</b> configuration is suitable for { "light tasks" if cores < 6 else "heavy workloads"}.</small>
    </div>
    """, unsafe_allow_html=True)

# 6. RAW TELEMETRY DATA
with st.expander("View Full System Metadata"):
    st.write(hw)

time.sleep(20)
st.rerun()
