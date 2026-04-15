# main.py
import streamlit as st
import pandas as pd
import requests
import random
import hashlib
import time
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.express as px

# 匯入自定義與資料庫模組
from language_pack import lang_pack
from styles import apply_ksr_styles
from database import init_db, register_user, login_user

# --- 1. 初始化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
init_db() # 啟動 SQLite
tw_tz = timezone(timedelta(hours=8))
apply_ksr_styles()
st_autorefresh(interval=1000, key="data_refresh_1s")

if 'auth_status' not in st.session_state: st.session_state.auth_status = None
if 'username' not in st.session_state: st.session_state.username = "Guest"
if 'chart_data' not in st.session_state: st.session_state.chart_data = pd.DataFrame(columns=["time", "ms"])

# --- 2. 側邊欄：登入與註冊系統 ---
with st.sidebar:
    st.session_state.lang = st.selectbox("🌐 Language", ["繁體中文", "English"])
    L = lang_pack[st.session_state.lang]
    st.divider()

    if st.session_state.auth_status is None:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            u = st.text_input("User", key="l_u")
            p = st.text_input("Pass", type="password", key="l_p")
            if st.button("Sign In", use_container_width=True):
                role = login_user(u, p)
                if role:
                    st.session_state.auth_status = role
                    st.session_state.username = u
                    st.rerun()
                else: st.error("Error")
        with tab2:
            new_u = st.text_input("New User", key="r_u")
            new_p = st.text_input("New Pass", type="password", key="r_p")
            if st.button("Sign Up", use_container_width=True):
                if register_user(new_u, new_p): st.success("Success!")
                else: st.error("User exists")
    else:
        st.success(f"Welcome, {st.session_state.username} ({st.session_state.auth_status})")
        if st.button("Logout", use_container_width=True):
            st.session_state.auth_status = None
            st.session_state.username = "Guest"
            st.rerun()

# --- 3. Telemetry 數據處理 (帳號為核心) ---
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
current_now_str = datetime.now(tw_tz).strftime("%H:%M:%S")

# 使用「帳號」作為唯一 Identifier
user_id = st.session_state.username

global_devices = st.cache_resource(lambda: {})()

# 只有登入後才開始紀錄該帳號的心跳
if st.session_state.auth_status:
    global_devices[user_id] = {
        "name": user_id,
        "ip": ip,
        "last": current_now_str,
        "ts": time.time(),
        "status": "Online 🟢"
    }

# 離線自動清理 (同前邏輯)
ct = time.time()
for sid in list(global_devices.keys()):
    if ct - global_devices[sid]["ts"] > 10:
        global_devices[sid]["status"] = "Offline 🔴"
    if ct - global_devices[sid]["ts"] > 60: del global_devices[sid]

# --- 4. Dashboard 渲染 ---
st.title(f"📡 {L['title']}")
st.subheader(f"📊 {L['diag_title']}")

# 圖表動態更新
new_tick = pd.DataFrame([{"time": current_now_str, "ms": random.randint(22, 55)}])
st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_tick], ignore_index=True).iloc[-30:]
fig = px.area(st.session_state.chart_data, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
st.plotly_chart(fig, use_container_width=True)

# --- 5. 權限過濾清單 ---
st.divider()
if st.session_state.auth_status == "admin":
    st.subheader("📋 DataBase: 全系統帳號即時狀態")
    admin_df = pd.DataFrame(global_devices.values())
    st.table(admin_df if not admin_df.empty else pd.DataFrame(columns=["name", "status"]))
elif st.session_state.auth_status == "user":
    st.subheader(f"📋 個人監測紀錄: {user_id}")
    if user_id in global_devices:
        st.table(pd.DataFrame([global_devices[user_id]]))
else:
    st.warning("🔒 請登入以啟動網路監測與數據儲存。")
