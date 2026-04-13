import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 【關鍵修正】建立全域共享的裝置清單 ---
@st.cache_resource
def get_global_devices():
    return {} # 這是一個所有使用者共用的字典

global_devices = get_global_devices()

# --- 獲取當前連入者資訊 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")

# 簡單解析裝置類型 (維持原樣)
if "iPhone" in user_agent:
    icon, dev_type = "🍎", "iPhone"
elif "Windows" in user_agent:
    icon, dev_type = "💻", "Windows PC"
else:
    icon, dev_type = "📱", "Mobile Device"

# 建立 Session ID (確保每個分頁唯一)
if 'my_sid' not in st.session_state:
    st.session_state.my_sid = f"{dev_type}_{int(time.time())}"

# 【修正點】將資料寫入「全域字典」而非 session_state
now = datetime.now().strftime("%H:%M:%S")
global_devices[st.session_state.my_sid] = {
    "icon": icon,
    "name": dev_type,
    "last_seen": now
}

# --- UI 介面 ---
st.title("📡 全球通訊裝置即時監測站")

# 顯示在線裝置總數 (現在會看到 2 了！)
st.metric("目前在線裝置", len(global_devices))

st.divider()

# 顯示所有裝置卡片
cols = st.columns(4)
for i, (sid, info) in enumerate(global_devices.items()):
    with cols[i % 4]:
        is_me = sid == st.session_state.my_sid
        with st.container(border=True):
            st.markdown(f"### {info['icon']} {info['name']}")
            if is_me: st.write("**(就是你)**")
            st.write(f"🕒 最後活動: {info['last_seen']}")

# 自動重整
time.sleep(3)
st.rerun()
