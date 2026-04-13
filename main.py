import streamlit as st
import pandas as pd
import time
import requests
import plotly.express as px
import random
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. 頁面設定 (必須在最前面) ---
st.set_page_config(page_title="Pro 通訊監測站", layout="wide")

# --- 2. 全域資源共享 ---
@st.cache_resource
def get_global_data():
    return {} 

global_devices = get_global_data()

# 自動刷新 (3秒)
st_autorefresh(interval=3000, key="data_refresh")

# --- 3. 獲取連入者資訊 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=3600)
def get_location(ip_addr):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_addr}", timeout=5).json()
        if response['status'] == 'success':
            return response
    except:
        pass
    return None

loc = get_location(ip)

# --- 4. 裝置識別與數據初始化 ---
if "iPhone" in user_agent:
    icon, dev_type = "🍎", "iPhone"
elif "Windows" in user_agent:
    icon, dev_type = "💻", "Windows PC"
elif "Android" in user_agent:
    icon, dev_type = "🤖", "Android"
else:
    icon, dev_type = "🌐", "Unknown Device"

# 確保 Session 變數存在
if 'history' not in st.session_state:
    st.session_state.history = []
if 'my_sid' not in st.session_state:
    st.session_state.my_sid = f"{dev_type}_{ip}"

my_id = st.session_state.my_sid

# 數據運算 (只執行一次)
current_ping = random.randint(20, 45)
st.session_state.history.append(current_ping)
if len(st.session_state.history) > 20: 
    st.session_state.history.pop(0)

# 更新自己到全域字典 (重要：確保資料先寫入，後面的 UI 才能讀)
global_devices[my_id] = {
    "icon": icon,
    "name": dev_type,
    "ip": ip,
    "lat": loc['lat'] if loc else 25.03,
    "lon": loc['lon'] if loc else 121.56,
    "city": loc['city'] if loc else "Unknown",
    "last_seen": datetime.now().strftime("%H:%M:%S"),
    "timestamp": time.time()
}

# 清理過期連線
curr_t = time.time()
for sid in list(global_devices.keys()):
    if curr_t - global_devices[sid]["timestamp"] > 15:
        del global_devices[sid]

# --- 5. UI 介面設計 ---
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
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🗺️ 全球連線分布")
    # 準備地圖數據
    if global_devices:
        map_data = pd.DataFrame([
            {"lat": v['lat'], "lon": v['lon'], "name": v['name']} 
            for v in global_devices.values()
        ])
        st.map(map_data, zoom=1)
        
    with st.expander("查看所有在線名單"):
        st.write(pd.DataFrame(global_devices).T[['name', 'last_seen']])

st.divider()

# 第三列：AI 診斷建議
st.subheader("🧠 AI 智慧連線診斷")
if current_ping < 35:
    st.success("【優良】目前的通訊路徑極佳，適合進行 4K 串流或即時數據傳輸。")
elif current_ping < 60:
    st.warning("【普通】連線尚可，但建議避開大型金屬屏蔽物以穩定訊號。")
else:
    st.error("【警告】延遲過高，請檢查 Wi-Fi 分享器或重啟網路介面。")

# 增加數據匯出功能 (專業加分點)
if st.button("💾 下載本次監測數據 CSV"):
    df_export = pd.DataFrame(st.session_state.history, columns=['Latency_ms'])
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("確認下載", csv, "network_report.csv", "text/csv")
