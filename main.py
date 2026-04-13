import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 1. 全域共享字典 (用來算總人數) ---
@st.cache_resource
def get_global_devices():
    return {}

global_devices = get_global_devices()

# --- 2. 裝置識別邏輯 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

# 解析裝置類型
if "iPhone" in user_agent:
    icon, dev_type = "🍎", "iPhone"
elif "Windows" in user_agent:
    icon, dev_type = "💻", "Windows PC"
elif "Android" in user_agent:
    icon, dev_type = "🤖", "Android Mobile"
else:
    icon, dev_type = "📱", "Mobile Device"

# 確保 ID 固定
if 'my_sid' not in st.session_state:
    st.session_state.my_sid = f"{dev_type}_{ip}"

my_id = st.session_state.my_sid

# 更新自己到全域字典
now_dt = datetime.now()
global_devices[my_id] = {
    "icon": icon,
    "name": dev_type,
    "last_seen": now_dt.strftime("%H:%M:%S"),
    "timestamp": time.time()
}

# --- 3. 自動清理過期連線 (保持在線人數精準) ---
current_time = time.time()
for sid in list(global_devices.keys()):
    if current_time - global_devices[sid]["timestamp"] > 10: # 10秒沒動就踢掉
        del global_devices[sid]

# --- 4. UI 介面設計 ---
st.title("📡 個人通訊品質診斷站")

# 區塊 A：全網概況
st.subheader("🌐 全球連線概況")
st.metric("目前全網在線裝置數", f"{len(global_devices)} 台")
st.caption("每 3 秒自動刷新數據")

st.divider()

# 區塊 B：個人專屬 UI (只顯示自己的 ID 資料)
st.subheader("📍 您的裝置資訊")

if my_id in global_devices:
    me = global_devices[my_id]
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown(f"## {me['icon']}")
            st.write(f"**{me['name']}**")
        
        with col2:
            st.write(f"🆔 **裝置識別碼:** `{my_id}`")
            st.write(f"🕒 **最後更新時間:** {me['last_seen']}")
            
            # 加入一個模擬的通訊品質條
            # 實際上這可以連結你之前的 Ping 或訊號邏輯
            st.write("🛰️ **預估連線品質:**")
            st.progress(90, text="Excellent (穩定連線中)")

# --- 5. 自動重整 ---

st.rerun()
