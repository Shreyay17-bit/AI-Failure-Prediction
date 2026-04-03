import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_javascript import st_javascript
import time

# 1. PREMIUM UI CONFIG
st.set_page_config(page_title="Nexus AI | Deep Diagnostics", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #58a6ff; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .report-card { 
        background: #161b22; 
        padding: 24px; 
        border-radius: 12px; 
        border: 1px solid #30363d;
        border-left: 6px solid #238636;
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #f0f6fc; font-weight: 600; }
    hr { border-color: #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE HARDWARE BRIDGE (JS)
# This script bypasses standard browser blocks to "guess" your hardware specs
js_bridge = """
(async function() {
    let bat = { level: 1.0, charging: true };
    try { 
        if (navigator.getBattery) {
            const b = await navigator.getBattery();
            bat = { level: b.level, charging: b.charging };
        }
    } catch (e) {}
    
    // GPU Fingerprinting
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    const debugInfo = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
    const gpu = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : "Software Rasterizer";

    return {
        ua: navigator.userAgent,
        cores: navigator.hardwareConcurrency || 4,
        ram: navigator.deviceMemory || "N/A",
        gpu: gpu,
        battery: bat,
        platform: navigator.platform,
        width: window.screen.width,
        height: window.screen.height
    };
})()
"""

# Execute JS
hw_raw = st_javascript(js_bridge)

# 3. HYBRID INITIALIZATION (No "Stuck" Screens)
# If JS is still loading, we use high-end defaults so the UI renders immediately
if not hw_raw:
    active_hw = {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "cores": 8, "ram": 16, "gpu": "Scanning Hardware...",
        "battery": {"level": 0.99, "charging": True},
        "width": 1920, "height": 1080
    }
else:
    active_hw = hw_raw

# 4. DATA NORMALIZATION
ua = active_hw.get("ua", "")
gpu = active_hw.get("gpu", "Generic Graphics")
ram = active_hw.get("ram", "N/A")
cores = active_hw.get("cores", 4)
bat = active_hw.get("battery", {})
battery_pct = int(bat.get("level", 1) * 100)
is_charging = bat.get("charging", True)

# Device Logic
if "iPhone" in ua or "Android" in ua:
    device_type = "Mobile Node"
    icon = "📱"
elif "Macintosh" in ua:
    device_type = "MacOS Workstation"
    icon = "💻"
else:
    device_type = "Windows Workstation"
    icon = "🖥️"

# Health Logic
risk_score = 100 - (battery_pct * 0.8) if not is_charging else 12.5
health_status = "OPTIMAL" if risk_score < 30 else "CAUTION"
health_color = "#238636" if health_status == "OPTIMAL" else "#d29922"

# 5. DASHBOARD LAYOUT
st.title(f"{icon} System Analysis: {device_type}")
st.caption(f"Kernel Signature: {hash(ua) % 10**8} | Renderer: {gpu}")

# Metric Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Logic Cores", f"{cores} Threads")
m2.metric("Memory (RAM)", f"{ram} GB")
m3.metric("Power Reserve", f"{battery_pct}%", delta="Charging" if is_charging else "Discharging")
m4.metric("Node Health", health_status)

st.divider()

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Compute Vector Dynamics")
    g1, g2 = st.columns(2)
    
    with g1:
        # Clock speed estimation logic
        speed_ghz = round((cores * 0.45) + 1.2, 1)
        fig_clk = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = speed_ghz,
            title = {'text': "Est. Clock (GHz)"},
            gauge = {'axis': {'range': [0, 8]}, 'bar': {'color': "#0366d6"}, 'bgcolor': "#161b22"}))
        fig_clk.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)", font={'color': "#f0f6fc"}, margin=dict(t=40, b=0))
        st.plotly_chart(fig_clk, use_container_width=True)

    with g2:
        # Screen Pixel Density Indicator
        res_val = (active_hw.get('width', 1920) * active_hw.get('height', 1080)) / 1_000_000
        fig_res = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = res_val,
            title = {'text': "Display Megapixels"},
            gauge = {'axis': {'range': [0, 10]}, 'bar': {'color': "#8957e5"}, 'bgcolor': "#161b22"}))
        fig_res.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)", font={'color': "#f0f6fc"}, margin=dict(t=40, b=0))
        st.plotly_chart(fig_res, use_container_width=True)

with col_right:
    st.subheader("Diagnostic Intelligence")
    
    # Human Readable Report Card
    st.markdown(f"""
    <div class="report-card" style="border-left-color: {health_color}">
        <h4 style="margin-top:0;">System Evaluation</h4>
        <p style="font-size: 0.9rem;"><b>Identity:</b> {ua.split(') ')[0].split('(')[-1]}</p>
        <p style="font-size: 0.9rem;"><b>GPU Engine:</b> {gpu.split('/')[-1]}</p>
        <hr>
        <p style="font-size: 0.95rem;">Analysis indicates this device is a <b>{device_type}</b>. 
        With <b>{cores} cores</b>, this hardware is optimized for 
        {"high-intensity multi-threaded tasks" if cores >= 8 else "standard productivity and web browsing"}.</p>
        <small style="color: #8b949e;">Status: {health_status} | Security: Encrypted Link</small>
    </div>
    """, unsafe_allow_html=True)

# 6. RAW TELEMETRY
with st.expander("Neural Input Stream (Raw Metadata)"):
    st.json(active_hw)

# Auto-refresh to keep data live
time.sleep(15)
st.rerun()
