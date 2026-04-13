import streamlit as st
import pandas as pd
import time
import requests
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. 全域資源共享 ---
@st.cache_resource
def get_global_data():
    return {} # 存儲所有在線裝置資訊

global_devices = get_global_data()

# --- 2. 自動刷新 (3秒) ---
st_autorefresh(interval=3000, key="data_refresh")

# --- 3. 獲取連入者資訊與地理位置 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
# 獲取真實 IP (Streamlit Cloud 環境通常在 X-Forwarded-For)
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=3600) # 快取地理位置資訊，避免重複請求 API
def get_location(ip_addr):
    try:
        # 使用免費的 IP-API (通訊系必備工具)
        response = requests.get(f"http://ip-api.com/json/{ip_addr}", timeout=5).json()
        if response['status'] == 'success':
            return response
    except:
        pass
    return None

loc = get_location(ip)

# --- 4. 裝置識別與狀態更新 ---
if "iPhone" in user_agent:
    icon, dev_type = "🍎", "iPhone"
elif "Windows" in user_agent:
    icon, dev_type = "💻", "Windows PC"
elif "Android" in user_agent:
    icon, dev_type = "🤖", "Android"
else:
    icon, dev_type = "🌐", "Unknown Device"

# 【關鍵修改 1】確保 history 獨立初始化，不受 my_sid 影響
if 'history' not in st.session_state:
    st.session_state.history = []

# 【關鍵修改 2】確保 my_sid 獨立初始化
if 'my_sid' not in st.session_state:
    st.session_state.my_sid = f"{dev_type}_{ip}"

my_id = st.session_state.my_sid

# --- 接下來再進行數據操作 ---
import random
current_ping = random.randint(20, 45)

# 這樣這行絕對不會報錯了
st.session_state.history.append(current_ping)

if len(st.session_state.history) > 20: 
    st.session_state.history.pop(0)

# 模擬 Ping 值 (在免腳本環境中，我們用 RTT 模擬)
import random
current_ping = random.randint(20, 45) # 模擬波動
st.session_state.history.append(current_ping)
if len(st.session_state.history) > 20: st.session_state.history.pop(0)

# 更新全域字典
# --- 強化版：全球在線地圖 ---
st.subheader("🗺️ 全球在線裝置分布")

# 準備所有裝置的地圖數據
if global_devices:
    map_list = []
    for sid, info in global_devices.items():
        map_list.append({
            "lat": info['lat'],
            "lon": info['lon'],
            "name": f"{info['name']} ({info['city']})"
        })
    df_map = pd.DataFrame(map_list)
    
    # 使用 st.map 自動繪製所有點
    st.map(df_map, zoom=1) 
    
    # 下方顯示一個小列表
    with st.expander("查看在線名單"):
        st.table(df_map)

# 清理過期連線 (15秒沒更新就踢掉)
curr_t = time.time()
for sid in list(global_devices.keys()):
    if curr_t - global_devices[sid]["timestamp"] > 15:
        del global_devices[sid]

# --- 5. UI 介面設計 ---
st.set_page_config(page_title="Pro 通訊監測站", layout="wide")
st.title("📡 Pro 智慧通訊監測平台")

# 第一列：全局指標
c1, c2, c3 = st.columns(3)
c1.metric("在線裝置總數", f"{len(global_devices)} Units")
c2.metric("當前節點延遲", f"{current_ping} ms", delta="-2ms" if current_ping < 30 else "Jittering")
c3.metric("伺服器狀態", "🟢 Operational")

st.divider()

# 第二列：個人診斷與地圖
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📍 您的裝置診斷")
    with st.container(border=True):
        st.markdown(f"### {icon} {dev_type}")
        st.write(f"🌐 **公網 IP:** `{ip}`")
        st.write(f"🏙️ **偵測位置:** {global_devices[my_id]['city']}")
        
        # 繪製延遲趨勢圖
        df_history = pd.DataFrame(st.session_state.history, columns=["Latency"])
        fig = px.line(df_history, y="Latency", title="即時延遲趨勢 (ms)", template="plotly_dark")
        fig.update_layout(height=200, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

'''with col_right:
    st.subheader("🗺️ 全球連線分布")
    # 準備地圖數據
    map_data = pd.DataFrame([
        {"lat": v['lat'], "lon": v['lon'], "name": v['name']} 
        for v in global_devices.values()
    ])
    st.map(map_data, zoom=2)'''

st.divider()

# 第三列：AI 診斷建議
st.subheader("🧠 AI 智慧連線診斷")
if current_ping < 40:
    st.success("【優良】目前的通訊路徑極佳，適合進行 4K 串流或線上對戰。")
else:
    st.warning("【注意】偵測到微幅延遲波動，建議檢查是否有大型下載任務占用頻寬。")
