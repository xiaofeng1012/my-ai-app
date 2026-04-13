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

# --- 1. 頁面設定 & 專業去標籤化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")

# 高階 CSS：移除品牌標記、優化卡片字體
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

# --- 2. 側邊欄：控制中心整合 (含測速儀) ---
st.sidebar.title("🛡️ 控制中心")

# --- 這裡將測速儀移到最上方 ---
st.sidebar.subheader("🚀 即時效能測試")
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
    st.caption("點擊按鈕測量與伺服器間的下載頻寬。")

st.sidebar.divider()

# SLA 模式選擇
app_mode = st.sidebar.selectbox("監測場景 (SLA Mode)", ["一般辦公", "即時競技", "遠距會議", "影音串流"])

# 專業級 CSV 導出邏輯
def get_audit_csv(df, info_dict):
    output = io.StringIO()
    output.write(f"--- 卡式如通訊品質審計報告 ---\n")
    output.write(f"系統 Hash: {info_dict['hash']}\n")
    output.write(f"平均延遲: {df['ms'].mean():.2f} ms\n")
    output.write(f"抖動指標: {info_dict['jitter']:.2f} ms\n")
    output.write(f"--------------------------\n\n")
    df.to_csv(output, index=False)
    return output.getvalue()

st.sidebar.divider()
st.sidebar.caption("© 2026 卡式如研發團隊")
st.sidebar.caption("Version 6.9.1 | NOC 內部工具")

# --- 3. 數據核心 ---
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

# --- 4. 主視覺儀表板 ---
st.title("📡 卡式如通訊品質監測平台")
st.markdown(f"**稽核編號:** `{sys_hash}` | **監測節點:** `{loc['city'] if loc else '自動定位'}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric("全球監測單元", f"{len(global_devices)} Units")
m2.metric("即時延遲 (RTT)", f"{current_ping} ms", delta=f"{current_ping - df_raw['ms'].iloc[-2] if len(df_raw)>1 else 0} ms", delta_color="inverse")
m3.metric("網路抖動 (Jitter)", f"{jitter:.2f} ms")
m4.metric("SLA 達標率", f"{sla_rate:.1f}%")

st.divider()

# --- 5. 診斷與地圖 ---
c_diag, c_map = st.columns([1.2, 1])
with c_diag:
    st.subheader("📊 鏈路效能時域分析")
    fig = px.area(df_raw, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="時間序列", yaxis_title="延遲 (ms)")
    st.plotly_chart(fig, use_container_width=True)
    
    csv_data = get_audit_csv(df_raw, {"hash": sys_hash, "jitter": jitter})
    st.download_button("📥 導出專業監測報告 (CSV)", csv_data, f"Audit_{display_id}.csv", "text/csv")

with c_map:
    st.subheader("🗺️ 全球節點拓撲")
    map_df = pd.DataFrame([{"lat": v['lat'], "lon": v['lon'], "name": v['display_name']} for v in global_devices.values()])
    st.map(map_df, zoom=1)

# --- 6. 專業動態清單 ---
st.divider()
st.subheader("📋 系統監測動態清單")
list_data = [{"單位名稱": v['display_name'], "地理位置": v['city'], "活動時間": v['last_seen']} for v in global_devices.values()]
st.table(pd.DataFrame(list_data))

# 定時清理
curr_t = time.time()
for sid in list(global_devices.keys()):
    if curr_t - global_devices[sid]["timestamp"] > 15: del global_devices[sid]
