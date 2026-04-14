# main.py
import streamlit as st
import pandas as pd
import requests
import random
import hashlib
import time
import numpy as np
import plotly.express as px
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh

# 匯入自定義模組
from language_pack import lang_pack
from styles import apply_ksr_styles
from components import render_speed_test_ui
from utils import generate_csv_report

# --- 1. 系統初始化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
tw_tz = timezone(timedelta(hours=8))

# 初始化權限與使用者狀態
if 'auth_status' not in st.session_state:
    st.session_state.auth_status = None  # None, "user", "admin"
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

apply_ksr_styles()
st_autorefresh(interval=1000, key="data_refresh_1s")

# --- 2. 側邊欄：登入與控制中心 ---
with st.sidebar:
    # 數位即時時鐘
    st.markdown(f"""
        <div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; border-left: 5px solid #00f2ff; margin-bottom: 20px;">
            <p style="margin:0; color: #8b949e; font-size: 0.75rem; letter-spacing: 1px;">SYSTEM REAL-TIME (UTC+8)</p>
            <h2 style="margin:0; color: #00f2ff; font-family: 'JetBrains Mono', monospace; font-size: 1.8rem;">
                {datetime.now(tw_tz).strftime("%H:%M:%S")}
            </h2>
        </div>
    """, unsafe_allow_html=True)

    # 語言選擇
    L = lang_pack[st.selectbox("Language", ["繁體中文", "English"], label_visibility="collapsed")]
    st.divider()

    # --- 登入系統介面 ---
    st.title("🔐 Account Access")
    if st.session_state.auth_status is None:
        with st.expander("🔑 Click to Login", expanded=False):
            acc = st.text_input("Account")
            pwd = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                if acc == "Admin" and pwd == "2812":
                    st.session_state.auth_status = "admin"
                    st.session_state.user_id = "ADMIN_ROOT"
                    st.rerun()
                elif acc == "User" and pwd == "1234": # 這裡預設一個通用測試帳號
                    st.session_state.auth_status = "user"
                    st.session_state.user_id = "USER_NODE_01"
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    else:
        st.success(f"Logged in as: {st.session_state.auth_status.upper()}")
        if st.button("Logout", use_container_width=True):
            st.session_state.auth_status = None
            st.session_state.user_id = None
            st.rerun()

    st.divider()
    st.title(f"🛡️ {L['control_center']}")
    render_speed_test_ui(L)

# --- 3. Telemetry 數據處理 ---
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=86400)
def get_loc(ip_addr):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}?lang=en", timeout=3).json()
        return r if r['status'] == 'success' else None
    except: return None

loc = get_loc(ip)
display_country = loc.get('country', "Taiwan") if loc else "Taiwan"
# 建立一個基於 IP 的顯示 ID
display_id = f"Node_{hashlib.md5(ip.encode()).hexdigest()[:5]}"
current_now_str = datetime.now(tw_tz).strftime("%H:%M:%S")

# 全域清單與定格邏輯
global_devices = st.cache_resource(lambda: {})()
if display_id not in global_devices:
    global_devices[display_id] = {"name": display_id, "country": display_country, "last": current_now_str, "ts": time.time(), "status": "Online 🟢"}
else:
    global_devices[display_id]["ts"] = time.time()
    global_devices[display_id]["status"] = "Online 🟢"

# 離線判定
ct = time.time()
for sid in list(global_devices.keys()):
    if ct - global_devices[sid]["ts"] > 10 and global_devices[sid]["status"] == "Online 🟢":
        global_devices[sid]["last"] = datetime.now(tw_tz).strftime("%H:%M:%S")
        global_devices[sid]["status"] = "Offline 🔴"
    if ct - global_devices[sid]["ts"] > 60: del global_devices[sid]

# --- 4. Dashboard 主介面 ---
st.title(f"📡 {L['title']}")
st.info(f"📍 **Current Node:** `{display_id}` | **Region:** `{display_country}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric(L['m1'], f"{len(global_devices)} Units")
m2.metric(L['m2'], f"{random.randint(22, 55)} ms")
m3.metric(L['m3'], "1.42 ms")
m4.metric(L['m4'], "99.9%")

st.divider()

# 📊 延遲趨勢圖
fig = px.area(pd.DataFrame([{"time": datetime.now(tw_tz).strftime("%H:%M:%S"), "ms": random.randint(25, 45)} for _ in range(20)]), 
             x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
st.plotly_chart(fig, use_container_width=True)

# 🔥 5. 權限分級顯示邏輯
st.divider()

if st.session_state.auth_status == "admin":
    st.subheader(f"📋 管理員模式：全系統監測動態清單")
    list_df = [{"Node": v['name'], "Location": v['country'], "Status": v['status'], "Last Activity": v['last']} for v in global_devices.values()]
    st.table(pd.DataFrame(list_df))
    st.download_button("📥 匯出全系統日誌", generate_csv_report(pd.DataFrame(), "ADMIN", "ALL", "KSR"), "global_report.csv")

elif st.session_state.auth_status == "user":
    st.subheader(f"📋 使用者模式：個人節點紀錄")
    # 只顯示跟目前 display_id 匹配的紀錄
    if display_id in global_devices:
        v = global_devices[display_id]
        user_df = [{"Node": v['name'], "Location": v['country'], "Status": v['status'], "Last Activity": v['last']}]
        st.table(pd.DataFrame(user_df))
    else:
        st.warning("找不到您的節點紀錄。")
else:
    st.warning("🔒 監測動態清單已鎖定。一般使用者請登入觀看個人紀錄，管理員請登入觀看全系統清單。")

st.markdown(f'<div class="ksr-footer">DEVELOPED BY KSR &copy; 2026. ALL RIGHTS RESERVED.</div>', unsafe_allow_html=True)
