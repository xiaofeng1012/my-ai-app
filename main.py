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

# 匯入自定義與資料庫模組
from language_pack import lang_pack
from styles import apply_ksr_styles
from database import init_db, register_user, login_user

# --- 1. 初始化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
init_db() 
tw_tz = timezone(timedelta(hours=8))
apply_ksr_styles()
st_autorefresh(interval=1000, key="data_refresh_1s")

if 'lang' not in st.session_state: st.session_state.lang = "繁體中文"
if 'auth_status' not in st.session_state: st.session_state.auth_status = None
if 'username' not in st.session_state: st.session_state.username = "Guest"
if 'chart_data' not in st.session_state: st.session_state.chart_data = pd.DataFrame(columns=["time", "ms"])

# --- 2. 側邊欄：登入與語系 ---
with st.sidebar:
    # 數位時鐘
    st.markdown(f"""
        <div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; border-left: 5px solid #00f2ff; margin-bottom: 20px;">
            <p style="margin:0; color: #8b949e; font-size: 0.75rem; letter-spacing: 1px;">SYSTEM REAL-TIME (UTC+8)</p>
            <h2 style="margin:0; color: #00f2ff; font-family: 'JetBrains Mono', monospace; font-size: 1.8rem;">
                {datetime.now(tw_tz).strftime("%H:%M:%S")}
            </h2>
        </div>
    """, unsafe_allow_html=True)

    # 語系切換
    st.session_state.lang = st.selectbox("🌐 Language", ["繁體中文", "English"], 
                                       index=0 if st.session_state.lang == "繁體中文" else 1)
    L = lang_pack[st.session_state.lang]
    st.divider()

    # 登入註冊系統
    st.title(f"🔐 {L['login_section']}")
    if st.session_state.auth_status is None:
        tab1, tab2 = st.tabs([L['tab_login'], L['tab_register']])
        with tab1:
            u = st.text_input(L['user_label'], key="l_u")
            p = st.text_input(L['pass_label'], type="password", key="l_p")
            if st.button(L['btn_signin'], use_container_width=True):
                role = login_user(u, p)
                if role:
                    st.session_state.auth_status = role
                    st.session_state.username = u
                    st.rerun()
                else: st.error(L['err_auth'])
        with tab2:
            new_u = st.text_input(L['user_label'], key="r_u")
            new_p = st.text_input(L['pass_label'], type="password", key="r_p")
            if st.button(L['btn_signup'], use_container_width=True):
                if register_user(new_u, new_p): st.success(L['reg_success'])
                else: st.error(L['err_exists'])
    else:
        st.success(f"👤 {L['auth_welcome']}, {st.session_state.username}")
        st.caption(f"{L['auth_role']}: {st.session_state.auth_status.upper()}")
        if st.button(L['auth_logout'], use_container_width=True):
            st.session_state.auth_status = None
            st.session_state.username = "Guest"
            st.rerun()

    st.divider()
    from components import render_speed_test_ui
    render_speed_test_ui(L)

# --- 3. Telemetry 處理 ---
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
current_now_str = datetime.now(tw_tz).strftime("%H:%M:%S")

# 使用「帳號」為唯一辨識碼
user_id = st.session_state.username
global_devices = st.cache_resource(lambda: {})()

# 只有在登入狀態才紀錄心跳
if st.session_state.auth_status:
    global_devices[user_id] = {
        "name": user_id,
        "location": "Taiwan", # 此處可連動 get_loc 邏輯
        "last": current_now_str,
        "ts": time.time(),
        "status": "Online 🟢" if st.session_state.lang == "繁體中文" else "Online 🟢"
    }

# 清理離線節點
ct = time.time()
for sid in list(global_devices.keys()):
    if ct - global_devices[sid]["ts"] > 10:
        global_devices[sid]["status"] = "Offline 🔴" if st.session_state.lang == "繁體中文" else "Offline 🔴"
    if ct - global_devices[sid]["ts"] > 60: del global_devices[sid]

# --- 4. Dashboard 主介面 ---
st.title(f"📡 {L['title']}")
m1, m2, m3, m4 = st.columns(4)
# 更新分析圖數據
new_tick = pd.DataFrame([{"time": current_now_str, "ms": random.randint(22, 55)}])
st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_tick], ignore_index=True).iloc[-30:]

m1.metric(L['m1'], f"{len(global_devices)}")
m2.metric(L['m2'], f"{st.session_state.chart_data['ms'].iloc[-1]} ms")
m3.metric(L['m3'], f"{np.std(st.session_state.chart_data['ms']):.2f} ms")
m4.metric(L['m4'], "99.9%")

st.divider()
st.subheader(f"📊 {L['diag_title']}")
fig = px.area(st.session_state.chart_data, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
st.plotly_chart(fig, use_container_width=True)

# --- 5. 分級清單渲染 ---
st.divider()
if st.session_state.auth_status == "admin":
    st.subheader(f"📋 {L['db_title']}")
    # 動態欄位名稱切換
    admin_df = pd.DataFrame([{
        L['unit_name']: v['name'],
        L['location']: v['location'],
        "Status": v['status'],
        L['last_seen']: v['last']
    } for v in global_devices.values()])
    st.table(admin_df if not admin_df.empty else pd.DataFrame())
    st.download_button(L['export_btn'], generate_csv_report(st.session_state.chart_data, "ADMIN", "ALL", "KSR"), "ksr_audit.csv")

elif st.session_status == "user":
    st.subheader(f"📋 {L['user_record']}: {user_id}")
    if user_id in global_devices:
        v = global_devices[user_id]
        st.table(pd.DataFrame([{L['unit_name']: v['name'], L['location']: v['location'], "Status": v['status'], L['last_seen']: v['last']}]))
else:
    st.warning(L['lock_msg'])

st.markdown(f'<div class="ksr-footer">DEVELOPED BY {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
