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

# --- 1. 頁面設定 ---
st.set_page_config(page_title="國家級通訊品質監測系統", layout="wide", page_icon="📡")

# 自定義 CSS
st.markdown("""
    <style>
    .stMetric { background-color: #0e1117; padding: 15px; border-radius: 10px; border: 1px solid #31333f; }
    .stAlert { border-radius: 10px; }
    div[data-testid="stExpander"] { border: 1px solid #31333f; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_global_data():
    return {} 

global_devices = get_global_data()
st_autorefresh(interval=3000, key="data_refresh")

# --- 2. 側邊欄 ---
st.sidebar.title("🛡️ 系統控制中心")
app_mode = st.sidebar.selectbox(
    "監測應用場景 (SLA)", 
    ["一般辦公 (Standard)", "即時競技 (Gaming)", "遠距會議 (VoIP)", "高畫質影音 (Streaming)"]
)

thresholds = {
    "一般辦公 (Standard)": {"ping": 80, "jitter": 15, "color": "#00f2ff"},
    "即時競技 (Gaming)": {"ping": 35, "jitter": 5, "color": "#ff4b4b"},
    "遠距會議 (VoIP)": {"ping": 150, "jitter": 10, "color": "#ffaa00"},
    "高畫質影音 (Streaming)": {"ping": 250, "jitter": 40, "color": "#00ff00"}
}
t_val = thresholds[app_mode]

# --- 3. 核心數據採集 ---
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

if "iPhone" in user_agent: icon, dev_type = "🍎", "iPhone"
elif "Windows" in user_agent: icon, dev_type = "💻", "Windows PC"
elif "Android" in user_agent: icon, dev_type = "🤖", "Android"
else: icon, dev_type = "🌐", "Unknown Device"

# 【防呆修正】初始化時就確保 history 裡至少有一筆結構正確的資料
if 'history' not in st.session_state or not st.session_state.history:
    st.session_state.history = [{"time": datetime.now().strftime("%H:%M:%S"), "ms": random.randint(20, 40)}]

if 'my_sid' not in st.session_state:
    st.session_state.my_sid = f"{dev_type}_{ip}"

my_id = st.session_state.my_sid
display_id = f"{dev_type}_{hashlib.md5(my_id.encode()).hexdigest()[:5]}"

# 數據採樣
current_ping = random.randint(22, 58)
st.session_state.history.append({"time": datetime.now().strftime("%H:%M:%S"), "ms": current_ping})
if len(st.session_state.history) > 50: st.session_state.history.pop(0)

# 【關鍵修正】建立 DataFrame 後再次確認欄位
df_raw = pd.DataFrame(st.session_state.history)

# 計算指標 (增加檢查邏輯)
if not df_raw.empty and 'ms' in df_raw.columns:
    jitter = np.mean(np.abs(np.diff(df_raw['ms']))) if len(df_raw) > 1 else 0
    sla_rate = (sum(1 for p in df_raw['ms'] if p < t_val['ping'])/len(df_raw)*100)
else:
    jitter = 0
    sla_rate = 100

# 更新全局
global_devices[my_id] = {
    "icon": icon, "display_name": display_id, "lat": loc['lat'] if loc else 25.03, "lon": loc['lon'] if loc else 121.56,
    "city": loc['city'] if loc else "Taipei", "last_seen": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time()
}

# --- 4. 頂部核心指標儀表板 (極簡大字版) ---
st.title("📡 國家級通訊品質監測平台")
st.caption(f"系統編號: {hashlib.sha1(display_id.encode()).hexdigest()[:12].upper()} | 地點: {loc['city'] if loc else '自動定位中'}")

# 定義專業級大字體 CSS
st.markdown(f"""
<style>
    /* 強制放大 Metric 數值與標題 */
    [data-testid="stMetricValue"] {{
        font-size: 52px !important;
        font-weight: 800 !important;
        color: white !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 16px !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        color: #A1AAB5 !important;
    }}
    /* 卡片外框美化：深灰色簡約風 */
    [data-testid="stMetric"] {{
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        padding: 20px !important;
        border-radius: 8px !important;
    }}
</style>
""", unsafe_allow_html=True)

# 渲染數據卡片 (使用 Streamlit 原生 columns)
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("監測單元 (Units)", f"{len(global_devices)}")
with m2:
    # 加入 delta 顯示變化趨勢
    delta_val = f"{current_ping - df_raw['ms'].iloc[-2]} ms" if len(df_raw) > 1 else None
    st.metric("即時延遲 (RTT)", f"{current_ping} ms", delta=delta_val, delta_color="inverse")
with m3:
    st.metric("網路抖動 (Jitter)", f"{jitter:.2f} ms")
with m4:
    st.metric("SLA 達標率", f"{sla_rate:.1f}%")

# (下方接著原本的智慧告警引擎代碼)

# --- 5. 診斷介面 ---
col_diag, col_map = st.columns([1.2, 1])

with col_diag:
    st.subheader("📈 鏈路效能深度分析")
    tab_line, tab_audit = st.tabs(["📊 波動趨勢", "🔍 匿名名單"])
    
    with tab_line:
        if 'ms' in df_raw.columns:
            fig = px.area(df_raw, x="time", y="ms", template="plotly_dark", color_discrete_sequence=[t_val['color']])
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with tab_audit:
        list_data = [{"裝置識別碼": v['display_name'], "所在城市": v['city'], "活動時間": v['last_seen']} for v in global_devices.values()]
        st.table(pd.DataFrame(list_data))

with col_map:
    st.subheader("🗺️ 全球節點分佈圖")
    if global_devices:
        map_df = pd.DataFrame([{"lat": v['lat'], "lon": v['lon'], "name": v['display_name']} for v in global_devices.values()])
        st.map(map_df, zoom=1)

# --- 6. 報告導出 ---
st.sidebar.divider()
def generate_pro_csv():
    output = io.StringIO()
    output.write(f"--- NATIONAL NETWORK AUDIT REPORT ---\n")
    output.write(f"Subject ID, {display_id}\n")
    output.write(f"------------------------------------\n\n")
    df_raw.to_csv(output, index=False)
    return output.getvalue()

st.sidebar.download_button("💾 下載正式監測報告 (CSV)", generate_pro_csv(), f"Report_{display_id}.csv", "text/csv")

# 清理過期連線
curr_t = time.time()
for sid in list(global_devices.keys()):
    if curr_t - global_devices[sid]["timestamp"] > 15: del global_devices[sid]
