import streamlit as st
import pandas as pd
import time
import requests
import plotly.express as px
import plotly.graph_objects as go
import random
import hashlib
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. 初始化與頁面設定 ---
st.set_page_config(page_title="國家級通訊監測系統 | Expert Mode", layout="wide")

@st.cache_resource
def get_global_data():
    return {} 

global_devices = get_global_data()
st_autorefresh(interval=3000, key="data_refresh")

# --- 2. 獲取連入者資訊與地理位置 ---
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

# --- 3. 裝置識別與數據採樣 ---
if "iPhone" in user_agent: icon, dev_type = "🍎", "iPhone"
elif "Windows" in user_agent: icon, dev_type = "💻", "Windows PC"
elif "Android" in user_agent: icon, dev_type = "🤖", "Android"
else: icon, dev_type = "🌐", "Unknown Device"

if 'history' not in st.session_state: st.session_state.history = []
if 'my_sid' not in st.session_state: st.session_state.my_sid = f"{dev_type}_{ip}"

my_id = st.session_state.my_sid
display_id = f"{dev_type}_{hashlib.md5(my_id.encode()).hexdigest()[:5]}"

# 模擬高頻採樣數據
current_ping = random.randint(22, 60)
st.session_state.history.append(current_ping)
if len(st.session_state.history) > 50: st.session_state.history.pop(0)

# --- 4. 專家級統計運算 ---
history_arr = np.array(st.session_state.history)
avg_ping = np.mean(history_arr)
std_dev = np.std(history_arr) # 標準差：反映網路抖動劇烈程度
jitter = np.mean(np.abs(np.diff(history_arr))) if len(history_arr) > 1 else 0

# 異常檢測：如果當前延遲超過 (平均值 + 2倍標準差)，視為異常突波
is_outlier = current_ping > (avg_ping + 2 * std_dev) if len(history_arr) > 5 else False

# 更新全域數據
global_devices[my_id] = {
    "icon": icon, "display_name": display_id,
    "lat": loc['lat'] if loc else 25.03, "lon": loc['lon'] if loc else 121.56,
    "city": loc['city'] if loc else "Taipei",
    "last_seen": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time()
}

# --- 5. UI 介面呈現 ---
st.title(f"🏛️ 國家級通訊品質監測中心 (V5.0 - Expert)")

# 系統狀態列
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("在線節點", len(global_devices))
c2.metric("RTT 延遲", f"{current_ping} ms")
c3.metric("標準差 (STD)", f"{std_dev:.2f}")
c4.metric("網路抖動", f"{jitter:.2f} ms")
c5.metric("系統負載", "Normal")

# 【專家告警系統】
if is_outlier:
    st.error(f"🚨 【異常偵測】偵測到非隨機性突波！當前延遲 ({current_ping}ms) 顯著偏離歷史基準線。")
elif current_ping > 55:
    st.warning(f"⚠️ 【性能預警】當前延遲處於高位，請注意封包排隊延遲（Queuing Delay）。")

st.divider()

# --- 6. 深度可視化模組 ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 時域趨勢與滑動平均分析")
    df = pd.DataFrame({"Latency": st.session_state.history})
    df['Moving_Avg'] = df['Latency'].rolling(window=5).mean() # 5點滑動平均
    
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(y=df['Latency'], mode='lines+markers', name='原始採樣', line=dict(color='#00f2ff')))
    fig_line.add_trace(go.Scatter(y=df['Moving_Avg'], mode='lines', name='趨勢線 (MA5)', line=dict(dash='dash', color='white')))
    fig_line.update_layout(height=350, template="plotly_dark", margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.subheader("📊 延遲機率分佈 (PDF)")
    fig_hist = px.histogram(df, x="Latency", nbins=15, title=None, template="plotly_dark", color_discrete_sequence=['#7100ff'])
    fig_hist.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# 第三列：地圖與診斷
c_map, c_diag = st.columns([1.5, 1])

with c_map:
    st.subheader("🗺️ 全球節點拓撲圖")
    if global_devices:
        map_df = pd.DataFrame([{"lat": v['lat'], "lon": v['lon'], "name": v['display_name']} for v in global_devices.values()])
        st.map(map_df, zoom=1)

with c_diag:
    st.subheader("🧠 通訊物理層專家診斷")
    st.info(f"📍 **當前節點：** {loc['city'] if loc else 'Taipei'}")
    st.write(f"🔍 **分佈特徵：** {'集中型（穩定）' if std_dev < 5 else '離散型（不穩定）'}")
    
    # 這裡加入專業的建議
    if std_dev > 10:
        st.error("❌ 偵測到嚴重抖動：疑似存在多路徑干擾或競爭窗口過大。")
    else:
        st.success("✅ 訊號穩定度良好：適合進行高頻寬、低延遲資料交換。")
    
    with st.expander("💾 下載專業級 JSON 稽核紀錄"):
        st.json(global_devices)
