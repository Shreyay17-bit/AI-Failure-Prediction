import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_javascript import st_javascript
import time

# 1. PREMIUM UI CONFIG
st.set_page_config(page_title="Nexus AI | Pro Diagnostics", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #58a6ff; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .report-card { 
        background: #161b22; 
        padding: 24px; 
        border-radius: 12px; 
        border: 1px solid #30363d;
        border-left: 6px solid #238636;
    }
    h1, h2, h3 { color: #f0f6fc; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# 2. HARDWARE BRIDGE (JavaScript)
js_bridge = """
(async function() {
    let bat = { level: 0.99, charging: true };
    try { 
        if (navigator.getBattery) {
            const b = await navigator.getBattery();
            bat = { level: b.level, charging: b.charging };
        }
    } catch (e) {}
    
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    const debugInfo = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
    const gpu = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : "Integrated Graphics";

    return {
        ua: navigator.userAgent,
        cores: navigator.hardwareConcurrency || 8,
        ram: navigator.deviceMemory || 16,
        gpu: gpu,
        battery: bat,
        platform: navigator.platform,
        width: window.screen.width,
        height: window.screen.height
    };
})()
"""

# Execute JS (Returns None if blocked or loading)
hw = st_javascript(js_bridge)

# 3. DATA INITIALIZATION (No "Scanning" Hangs)
# We use standard high-end defaults so the app renders even if JS is blocked
active_hw = hw if hw else {
    "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "cores": 8, "ram": 16, "gpu": "Standard Renderer",
    "battery": {"level": 0.99, "charging": True},
    "width": 1920, "height": 1080, "platform": "Win32"
}

# 4. DATA EXTRACTION
ua = active_hw.get("ua", "")
bat_data = active_hw.get("battery", {})
raw_level = bat_data.get("level", 0.99)
battery_pct = int(raw_level * 100) if isinstance(raw_level, (int, float)) else 99
is_charging = bat_data.get("charging", True)
cores = active_hw.get("cores", 8)
ram = active_hw.get("ram", 16)
gpu = active_hw.get("gpu", "Standard Graphics")

# Identify Device Type
is_mobile = any(x in ua for x in ["iPhone", "Android", "Mobile"])
device_name = "📱 Mobile Node" if is_mobile else "💻 Desktop Workstation"

# 5. DASHBOARD UI
st.title(f"Diagnostic Analysis: {device_name}")
st.caption(f"Hardware Signature: {gpu}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Battery Status", f"{battery_pct}%", delta="Charging" if is_charging else "On Battery")
m2.metric("CPU Threads", f"{cores} Cores")
m3.metric("System RAM", f"{ram} GB")
m4.metric("Screen Resolution", f"{active_hw.get('width')}x{active_hw.get('height')}")

st.divider()

col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("Hardware Dynamics")
    g1, g2 = st.columns(2)
    
    with g1:
        # Battery Health Gauge
        fig_bat = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = battery_pct,
            title = {'text': "Battery Capacity %"},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#238636" if battery_pct > 20 else "#f85149"}}))
        fig_bat.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", font={'color': "#f0f6fc"}, margin=dict(t=50, b=0))
        st.plotly_chart(fig_bat, use_container_width=True)

    with g2:
        # Processing Tier Gauge
        try:
            val_cores = int(cores) if str(cores).isdigit() else 8
        except:
            val_cores = 8
        fig_perf = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = val_cores * 1.5,
            title = {'text': "Processing Tier (1-20)"},
            gauge = {'axis': {'range': [0, 20]}, 'bar': {'color': "#58a6ff"}}))
        fig_perf.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", font={'color': "#f0f6fc"}, margin=dict(t=50, b=0))
        st.plotly_chart(fig_perf, use_container_width=True)

with col_right:
    st.subheader("AI System Evaluation")
    
    # Safe logic to prevent "ValueError"
    core_val = int(cores) if str(cores).isdigit() else 8
    health = "OPTIMAL" if battery_pct > 20 else "LOW POWER"
    perf_text = "Performance is peaked for high-load tasks." if core_val >= 8 else "System is optimized for power-saving productivity."

    st.markdown(f"""
    <div class="report-card" style="border-left-color: {'#238636' if health == 'OPTIMAL' else '#f85149'}">
        <h4 style="margin-top:0;">Node Summary</h4>
        <p><b>GPU Engine:</b> {gpu.split('/')[-1]}</p>
        <p><b>Status:</b> {health}</p>
        <hr>
        <p style="font-size: 0.95rem;">This <b>{device_name}</b> is operating with <b>{cores} logic cores</b>. 
        {perf_text}</p>
    </div>
    """, unsafe_allow_html=True)

# 6. RAW DATA
with st.expander("Neural Telemetry (JSON Stream)"):
    st.json(active_hw)
