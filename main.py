import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 1. 頁面設定 ---
st.set_page_config(page_title="全球通訊監測站", layout="wide", page_icon="📡")

# 使用 st.cache_resource 確保所有連入的使用者都共享同一個「裝置清單」
if 'global_devices' not in st.session_state:
    st.session_state.global_devices = {}

# --- 2. 獲取當前連入者資訊 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")

# 簡單解析裝置類型
if "iPhone" in user_agent:
    icon, dev_type = "🍎", "iPhone"
elif "Android" in user_agent:
    icon, dev_type = "🤖", "Android"
elif "Windows" in user_agent:
    icon, dev_type = "💻", "Windows PC"
elif "Macintosh" in user_agent:
    icon, dev_type = "💻", "MacBook"
else:
    icon, dev_type = "🌐", "Unknown Device"

# 建立一個唯一的 Session ID (每個分頁不同)
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"{dev_type}_{int(time.time())}"

# 更新全局裝置狀態
now = datetime.now().strftime("%H:%M:%S")
st.session_state.global_devices[st.session_state.session_id] = {
    "icon": icon,
    "name": dev_type,
    "last_seen": now,
    "ua": user_agent[:50] + "..."
}

# --- 3. UI 介面 ---
st.title("📡 全球通訊裝置即時監測站")
st.write("只要點開此網頁，你的裝置就會自動同步到監控面板。")
st.divider()

# 顯示當前裝置狀態
st.subheader(f"📍 你的裝置狀態：{icon} {dev_type}")
c1, c2, c3 = st.columns(3)
c1.metric("連線狀態", "🟢 已連線")
c2.metric("同步頻率", "3.0s")
c3.metric("目前在線裝置", len(st.session_state.global_devices))

st.divider()

# --- 4. 監控面板 (顯示所有人) ---
st.subheader("📊 所有連入裝置實時面板")
cols = st.columns(4)

# 移除超過 10 秒沒更新的「死掉」連線（模擬斷線偵測）
current_time_int = int(time.time())
# (這部分在生產環境需要更複雜的邏輯，這裡先簡單展示)

for i, (sid, info) in enumerate(st.session_state.global_devices.items()):
    with cols[i % 4]:
        # 凸顯「你自己」的卡片
        is_me = sid == st.session_state.session_id
        border_color = "solid #FF4B4B" if is_me else "none"
        
        with st.container(border=True):
            st.markdown(f"### {info['icon']} {info['name']}")
            if is_me: st.write("**(就是你)**")
            st.write(f"🕒 最後活動: {info['last_seen']}")
            st.caption(f"ID: {sid}")
            
            # 加上一個模擬的通訊品質條
            val = 80 if is_me else 60
            st.progress(val, text="預估鏈路品質")

# 每 3 秒自動刷頁
time.sleep(3)
st.rerun()