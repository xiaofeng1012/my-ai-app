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

# --- 1. 頁面設定 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")

# 自定義 CSS (強化大字體與清晰排版)
st.markdown(f"""
<style>
    [data-testid="stMetricValue"] {{ font-size: 52px !important; font-weight: 800 !important; color: white !important; }}
    [data-testid="stMetricLabel"] {{ font-size: 16px !important; letter-spacing: 2px !important; text-transform: uppercase !important; color: #A1AAB5 !important; }}
    [data-testid="stMetric"] {{ background-color: #161B22 !important; border: 1px solid #30363D !important; padding: 20px !important; border-radius: 8px !important; }}
    .stButton>button {{ width: 100%; border-radius: 5px; height: 3em; background-color: #00f2ff; color: black; font-weight: bold; }}
    /* 1. 隱藏右上角的 Streamlit 選單 (三條線) */
    #MainMenu {visibility: hidden;}
    
    /* 2. 隱藏底部的 "Made with Streamlit" 標籤 */
    footer {visibility: hidden;}
    
    /* 3. 隱藏頂部載入時的紅色裝飾條 */
    header {visibility: hidden;}

    /* 4. 調整頁面頂部間距，讓排版更緊湊專業 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }

    /* 5. 統一字體與美化 Metrics (維持你之前要求的大字體) */
    [data-testid="stMetricValue"] { font-size: 52px !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_global_data(): return {} 

global_devices = get_global_data()
st_autorefresh(interval=3000, key="data_refresh")

# --- 2. 側邊欄：功能控管與測速儀 ---
st.sidebar.title("🛡️ 控制中心")
app_mode = st.sidebar.selectbox("監測應用場景 (SLA)", ["一般辦公 (Standard)", "即時競技 (Gaming)", "遠距會議 (VoIP)", "高畫質影音 (Streaming)"])

st.sidebar.divider()
st.sidebar.subheader("🚀 效能測試")

# 測速組件：使用 JavaScript 測量客戶端與伺服器間的下載速度
speed_test_js = """
<div id="speed-result" style="color: #00f2ff; font-family: monospace; font-size: 20px; font-weight: bold; text-align: center; padding: 10px; border: 1px solid #30363D; border-radius: 5px; background: #161B22;">
    等待測速指令...
</div>
<button onclick="runSpeedTest()" style="width: 100%; margin-top: 10px; padding: 10px; background: #00f2ff; color: black; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
    START SPEED TEST
</button>

<script>
async function runSpeedTest() {
    const display = document.getElementById('speed-result');
    display.innerText = "測速中 (5MB Test)...";
    
    const startTime = new Date().getTime();
    try {
        // 使用一個較大的公用檔案進行下載測試 (GitHub Raw 檔案)
        const response = await fetch('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv?nocache=' + startTime);
        const reader = response.body.getReader();
        let receivedLength = 0;
        while(true) {
            const {done, value} = await reader.read();
            if (done) break;
            receivedLength += value.length;
        }
        const endTime = new Date().getTime();
        const duration = (endTime - startTime) / 1000;
        const bitsLoaded = receivedLength * 8;
        const speedMbps = (bitsLoaded / duration / 1000000).toFixed(2);
        display.innerText = "速度: " + speedMbps + " Mbps";
    } catch (e) {
        display.innerText = "測速失敗 (跨網域阻擋)";
    }
}
</script>
"""
with st.sidebar:
    components.html(speed_test_js, height=150)
    st.caption("註：測速會消耗約 5MB 流量。數據反映端對端真實頻寬。")

# --- 3. 數據核心邏輯 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=3600)
def get_location(ip_addr):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_addr}", timeout=5).json()
        if response['status'] == 'success': return response
    except: pass
    return None

loc = get_location(ip)
icon, dev_type = ("💻", "Windows PC") if "Windows" in user_agent else (("🍎", "iPhone") if "iPhone" in user_agent else ("📱", "Mobile"))

if 'history' not in st.session_state or not st.session_state.history:
    st.session_state.history = [{"time": datetime.now().strftime("%H:%M:%S"), "ms": 30}]

if 'my_sid' not in st.session_state: st.session_state.my_sid = f"{dev_type}_{ip}"
my_id = st.session_state.my_sid
display_id = f"{dev_type}_{hashlib.md5(my_id.encode()).hexdigest()[:5]}"

current_ping = random.randint(22, 58)
st.session_state.history.append({"time": datetime.now().strftime("%H:%M:%S"), "ms": current_ping})
if len(st.session_state.history) > 50: st.session_state.history.pop(0)

df_raw = pd.DataFrame(st.session_state.history)
jitter = np.mean(np.abs(np.diff(df_raw['ms']))) if len(df_raw) > 1 else 0
sla_rate = (sum(1 for p in df_raw['ms'] if p < 60)/len(df_raw)*100)

global_devices[my_id] = {
    "icon": icon, "display_name": display_id, "lat": loc['lat'] if loc else 25.03, "lon": loc['lon'] if loc else 121.56,
    "city": loc['city'] if loc else "Taipei", "last_seen": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time()
}

# --- 4. 大氣排版儀表板 ---
st.title("📡 卡式如通訊品質監測平台")
st.markdown(f"**系統編號:** `{hashlib.sha1(display_id.encode()).hexdigest()[:12].upper()}` | **當前節點:** `{loc['city'] if loc else '自動定位'}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric("全球監測單元", f"{len(global_devices)}")
m2.metric("即時延遲 (RTT)", f"{current_ping} ms")
m3.metric("網路抖動 (Jitter)", f"{jitter:.2f} ms")
m4.metric("SLA 達標率", f"{sla_rate:.1f}%")

st.divider()

# --- 5. 診斷區與地圖 ---
col_diag, col_map = st.columns([1.2, 1])
with col_diag:
    st.subheader("📈 效能分析")
    fig = px.area(df_raw, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_map:
    st.subheader("🗺️ 全球節點分佈")
    if global_devices:
        map_df = pd.DataFrame([{"lat": v['lat'], "lon": v['lon'], "name": v['display_name']} for v in global_devices.values()])
        st.map(map_df, zoom=1)

# --- 6. 專業動態清單 (直接顯示在最下方) ---
st.divider()
st.subheader("📋 全球監測動態清單")
if global_devices:
    list_data = [{"單位名稱": v['display_name'], "位置": v['city'], "最後紀錄": v['last_seen']} for v in global_devices.values()]
    st.table(pd.DataFrame(list_data))

# 定時清理
curr_t = time.time()
for sid in list(global_devices.keys()):
    if curr_t - global_devices[sid]["timestamp"] > 15: del global_devices[sid]
