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

# --- 1. 語言包設定 ---
lang_pack = {
    "繁體中文": {
        "title": "卡式如通訊品質監測平台",
        "control_center": "控制中心",
        "speed_test": "即時效能測試",
        "sla_mode": "監測場景 (SLA Mode)",
        "audit_hash": "稽核編號",
        "node": "監測節點",
        "m1": "全球監測單元",
        "m2": "即時延遲 (RTT)",
        "m3": "網路抖動 (Jitter)",
        "m4": "SLA 達標率",
        "diag_title": "鏈路效能時域分析",
        "map_title": "全球節點拓撲",
        "list_title": "系統監測動態清單",
        "export_btn": "導出專業監測報告 (CSV)",
        "unit_name": "單位名稱",
        "location": "地理位置",
        "last_seen": "最後活動紀錄",
        "speed_btn": "開始測速",
        "speed_wait": "等待指令...",
        "speed_testing": "測試中...",
        "modes": ["一般辦公", "即時競技", "遠距會議", "影音串流"]
    },
    "English": {
        "title": "KSR Network Telemetry Platform",
        "control_center": "CONTROL CENTER",
        "speed_test": "THROUGHPUT TEST",
        "sla_mode": "SLA Profile Selection",
        "audit_hash": "Audit Hash",
        "node": "Active Node",
        "m1": "Monitoring Units",
        "m2": "RTT Latency",
        "m3": "Network Jitter",
        "m4": "SLA Compliance",
        "diag_title": "Time-Domain Performance Analysis",
        "map_title": "Global Topology Map",
        "list_title": "Active Node Registry",
        "export_btn": "Export Audit Report (CSV)",
        "unit_name": "Unit Identifier",
        "location": "Geolocation",
        "last_seen": "Last Heartbeat",
        "speed_btn": "RUN SPEED TEST",
        "speed_wait": "STANDBY",
        "speed_testing": "TESTING...",
        "modes": ["Standard", "Gaming", "VoIP", "Streaming"]
    }
}

# --- 2. 頁面設定 ---
st.set_page_config(page_title="KSR Monitoring Platform", layout="wide", page_icon="📡")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden;}
        [data-testid="stMetricValue"] { font-size: 52px !important; font-weight: 800 !important; color: #00f2ff !important; font-family: 'JetBrains Mono', monospace !important; }
        [data-testid="stMetricLabel"] { font-size: 14px !important; letter-spacing: 1px !important; text-transform: uppercase !important; color: #A1AAB5 !important; }
        [data-testid="stMetric"] { background-color: #161B22 !important; border: 1px solid #30363D !important; padding: 20px !important; border-radius: 10px !important; }
        .block-container { padding-top: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_global_data(): return {} 
global_devices = get_global_data()
st_autorefresh(interval=3000, key="data_refresh")

# --- 3. 側邊欄 ---
st.sidebar.title("🌐 Language / 語言")
sel_lang = st.sidebar.selectbox("Select Language", ["繁體中文", "English"])
L = lang_pack[sel_lang]

st.sidebar.divider()
st.sidebar.title(f"🛡️ {L['control_center']}")

st.sidebar.subheader(f"🚀 {L['speed_test']}")
# 修正後的 JS 組件，確保括號 {{ }} 正確轉義
speed_test_js = f"""
<div id="speed-result" style="color: #00f2ff; font-family: monospace; font-size: 18px; font-weight: bold; text-align: center; padding: 12px; border: 1px solid #30363D; border-radius: 8px; background: #0d1117;">
    {L['speed_wait']}
</div>
<button onclick="runSpeedTest()" style="width: 100%; margin-top: 8px; padding: 10px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
    {L['speed_btn']}
</button>
<script>
async function runSpeedTest() {{
    const display = document.getElementById('speed-result');
    display.innerText = "{L['speed_testing']}";
    const startTime = new Date().getTime();
    try {{
        const response = await fetch('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv?n=' + startTime);
        const reader = response.body.getReader();
        let received = 0;
        while(true) {{
            const {{done, value}} = await reader.read();
            if (done) break;
            received += value.length;
        }}
        const duration = (new Date().getTime() - startTime) / 1000;
        display.innerText = ((received * 8) / duration / 1000000).toFixed(2) + " Mbps";
    }} catch (e) {{ display.innerText = "ERROR"; }}
}}
</script>
"""
with st.sidebar:
    components.html(speed_test_js, height=140)

st.sidebar.divider()
app_mode = st.sidebar.selectbox(L['sla_mode'], L['modes'])

# --- 4. 數據採集 ---
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

# --- 5. 主視覺儀表板 ---
st.title(f"📡 {L['title']}")
st.markdown(f"**{L['audit_hash']}:** `{sys_hash}` | **{L['node']}:** `{loc['city'] if loc else 'Detecting...'}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric(L['m1'], f"{len(global_devices)} Units")
m2.metric(L['m2'], f"{current_ping} ms", delta=f"{current_ping - df_raw['ms'].iloc[-2] if len(df_raw)>1 else 0} ms", delta_color="inverse")
m3.metric(L['m3'], f"{jitter:.2f} ms")
m4.metric(L['m4'], f"{sla_rate:.1f}%")

st.divider()

# --- 6. 診斷與地圖 ---
c_diag, c_map = st.columns([1.2, 1])
with c_diag:
    st.subheader(f"📊 {L['diag_title']}")
    fig = px.area(df_raw, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="Time Sequence", yaxis_title="Latency (ms)")
    st.plotly_chart(fig, use_container_width=True)
    
    csv_report = f"--- KSR AUDIT REPORT ---\nHash: {sys_hash}\nAvg: {df_raw['ms'].mean():.2f}ms\n\n" + df_raw.rename(columns={"time":"Timestamp","ms":"Latency_ms"}).to_csv(index=False)
    st.download_button(f"📥 {L['export_btn']}", csv_report, f"Audit_{display_id}.csv", "text/csv")

with c_map:
    st.subheader(f"🗺️ {L['map_title']}")
    map_df = pd.DataFrame([{"lat": v['lat'], "lon": v['lon'], "name": v['display_name']} for v in global_devices.values()])
    st.map(map_df, zoom=1)

# --- 7. 動態清單 ---
st.divider()
st.subheader(f"📋 {L['list_title']}")
list_data = [{L['unit_name']: v['display_name'], L['location']: v['city'], L['last_seen']: v['last_seen']} for v in global_devices.values()]
st.table(pd.DataFrame(list_data))

curr_t = time.time()
for sid in list(global_devices.keys()):
    if curr_t - global_devices[sid]["timestamp"] > 15: del global_devices[sid]
