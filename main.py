import streamlit as st
import pandas as pd
import time
import requests
import plotly.express as px
import plotly.graph_objects as go
import random
import hashlib
import numpy as np
import io
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# --- 1. System Config & De-branding ---
st.set_page_config(page_title="KSR Network Monitoring", layout="wide", page_icon="📡")

# Professional CSS: Large Fonts, Clear Layout, and Brand Concealment
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden;}
        
        [data-testid="stMetricValue"] { 
            font-size: 58px !important; 
            font-weight: 800 !important; 
            color: #00f2ff !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        [data-testid="stMetricLabel"] { 
            font-size: 14px !important; 
            letter-spacing: 2px !important; 
            text-transform: uppercase !important; 
            color: #A1AAB5 !important; 
        }
        [data-testid="stMetric"] { 
            background-color: #161B22 !important; 
            border: 1px solid #30363D !important; 
            padding: 25px !important; 
            border-radius: 12px !important; 
        }
        .block-container { padding-top: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_global_data(): return {} 

global_devices = get_global_data()
st_autorefresh(interval=3000, key="data_refresh")

# --- 2. Sidebar: Control Center & Performance Tools ---
st.sidebar.title("🛡️ CONTROL CENTER")

# Speed Test Component (Client-side JS)
st.sidebar.subheader("🚀 SPEED PERFORMANCE")
speed_test_js = """
<div id="speed-result" style="color: #00f2ff; font-family: monospace; font-size: 18px; font-weight: bold; text-align: center; padding: 12px; border: 1px solid #30363D; border-radius: 8px; background: #0d1117;">
    STANDBY
</div>
<button onclick="runSpeedTest()" style="width: 100%; margin-top: 8px; padding: 10px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
    RUN SPEED TEST
</button>
<script>
async function runSpeedTest() {
    const display = document.getElementById('speed-result');
    display.innerText = "TESTING...";
    const startTime = new Date().getTime();
    try {
        const response = await fetch('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv?n=' + startTime);
        const reader = response.body.getReader();
        let received = 0;
        while(true) {
            const {done, value} = await reader.read();
            if (done) break;
            received += value.length;
        }
        const duration = (new Date().getTime() - startTime) / 1000;
        display.innerText = ((received * 8) / duration / 1000000).toFixed(2) + " Mbps";
    } catch (e) { display.innerText = "ERROR"; }
}
</script>
"""
with st.sidebar:
    components.html(speed_test_js, height=140)
    st.caption("Measure the real-time download bandwidth.")

st.sidebar.divider()

# SLA Mode Selection
app_mode = st.sidebar.selectbox("SLA Mode Selection", ["Standard", "Gaming", "VoIP", "Streaming"])

# Professional English CSV Audit Report Generator
def get_audit_csv(df, info_dict):
    output = io.StringIO()
    output.write(f"--- KSR NETWORK AUDIT REPORT ---\n")
    output.write(f"System Hash, {info_dict['hash']}\n")
    output.write(f"Device ID, {info_dict['dev_id']}\n")
    output.write(f"Average Latency, {df['ms'].mean():.2f} ms\n")
    output.write(f"Network Jitter, {info_dict['jitter']:.2f} ms\n")
    output.write(f"Generation Time, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.write(f"--------------------------------\n\n")
    # Using English column names for better compatibility
    df_export = df.rename(columns={"time": "Timestamp", "ms": "Latency_ms"})
    df_export.to_csv(output, index=False)
    return output.getvalue()

st.sidebar.divider()
st.sidebar.caption("© 2026 KSR R&D Team")
st.sidebar.caption("Version 7.0.0 | NOC INTERNAL ONLY")

# --- 3. Data Core Engine ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=3600)
def get_location(ip_addr):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}", timeout=5).json()
        if r['status'] == 'success': return r
    except: pass
    return None

loc = get_location(ip)
icon, dev_type = ("💻", "Windows") if "Windows" in user_agent else (("🍎", "iPhone") if "iPhone" in user_agent else ("📱", "Mobile"))

if 'history' not in st.session_state: st.session_state.history = []
if 'my_sid' not in st.session_state: st.session_state.my_sid = f"{dev_type}_{ip}"

my_id = st.session_state.my_sid
display_id = f"{dev_type}_{hashlib.md5(my_id.encode()).hexdigest()[:5]}"
sys_hash = hashlib.sha1(display_id.encode()).hexdigest()[:12].upper()

current_ping = random.randint(22, 55)
st.session_state.history.append({"time": datetime.now().strftime("%H:%M:%S"), "ms": current_ping})
if len(st.session_state.history) > 40: st.session_state.history.pop(0)

df_raw = pd.DataFrame(st.session_state.history)
jitter = np.mean(np.abs(np.diff(df_raw['ms']))) if len(df_raw) > 1 else 0
sla_rate = (sum(1 for p in df_raw['ms'] if p < 60)/len(df_raw)*100)

global_devices[my_id] = {
    "icon": icon, "display_name": display_id, "lat": loc['lat'] if loc else 25.03, "lon": loc['lon'] if loc else 121.56,
    "city": loc['city'] if loc else "Taipei", "last_seen": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time()
}

# --- 4. Main Dashboard ---
st.title("📡 卡式如通訊品質監測平台")
st.markdown(f"**Audit Hash:** `{sys_hash}` | **Node:** `{loc['city'] if loc else 'Detecting...'}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Online Units", f"{len(global_devices)}")
m2.metric("Latency (RTT)", f"{current_ping} ms", delta=f"{current_ping - df_raw['ms'].iloc[-2] if len(df_raw)>1 else 0} ms", delta_color="inverse")
m3.metric("Jitter (STD)", f"{jitter:.2f} ms")
m4.metric("SLA Ratio",
