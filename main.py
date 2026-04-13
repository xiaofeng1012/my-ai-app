import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 1. 全域共享字典 (不變) ---
@st.cache_resource
def get_global_devices():
    return {}

global_devices = get_global_devices()

# --- 2. 修正：穩定辨識裝置 (核心改動) ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
# 獲取 IP 作為輔助辨識
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

# 解析裝置類型
if "iPhone" in user_agent:
    icon, dev_type = "🍎", "iPhone"
elif "Windows" in user_agent:
    icon, dev_type = "💻", "Windows PC"
else:
    icon, dev_type = "📱", "Mobile Device"

# 【關鍵】如果 Session 中還沒有 ID，就建立一個「基於類型與IP」的固定 ID
# 這樣同一台裝置重新整理後，ID 會保持不變
if 'my_sid' not in st.session_state:
    st.session_state.my_sid = f"{dev_type}_{ip}"

my_id = st.session_state.my_sid

# 更新全域字典 (使用固定的 my_id)
now = datetime.now().strftime("%H:%M:%S")
global_devices[my_id] = {
    "icon": icon,
    "name": dev_type,
    "last_seen": now,
    "timestamp": time.time() # 用來判斷是否斷線
}

# --- 3. 額外功能：自動清理「已離開」的裝置 ---
# 如果某個裝置超過 10 秒沒更新，就從清單移除
current_time = time.time()
for sid in list(global_devices.keys()):
    if current_time - global_devices[sid]["timestamp"] > 10:
        del global_devices[sid]

# --- 4. UI 呈現 ---
st.title("📡 全球通訊監測站")
st.metric("目前在線裝置", len(global_devices))

cols = st.columns(4)
for i, (sid, info) in enumerate(global_devices.items()):
    with cols[i % 4]:
        is_me = (sid == my_id)
        with st.container(border=True):
            st.markdown(f"### {info['icon']} {info['name']}")
            if is_me: st.write("**(就是你)**")
            st.write(f"🕒 最後活動: {info['last_seen']}")

time.sleep(3)
st.rerun()
