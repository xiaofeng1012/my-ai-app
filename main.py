# main.py
import streamlit as st
import pandas as pd
import requests
import random
import time
import json
import numpy as np
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. 模組匯入 ---
from language_pack import lang_pack
from styles import apply_ksr_styles
from database import init_db, register_user, login_user, add_record, get_records, clear_all_records
from components import render_speed_test_ui

# --- 2. 系統初始化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
init_db()
tw_tz = timezone(timedelta(hours=8))
apply_ksr_styles()
st_autorefresh(interval=1000, key="ksr_main_refresh_v2")

if 'lang' not in st.session_state: st.session_state.lang = "繁體中文"
if 'auth_status' not in st.session_state: st.session_state.auth_status = None
if 'username' not in st.session_state: st.session_state.username = "Guest"
if 'chart_data' not in st.session_state: st.session_state.chart_data = pd.DataFrame(columns=["time", "ms"])

# --- 3. 側邊欄：帳號與功能 ---
with st.sidebar:
    st.markdown(f"""
        <div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; border-left: 5px solid #00f2ff; margin-bottom: 20px;">
            <p style="margin:0; color: #8b949e; font-size: 0.75rem; letter-spacing: 1px;">SYSTEM REAL-TIME (UTC+8)</p>
            <h2 style="margin:0; color: #00f2ff; font-family: 'JetBrains Mono', monospace; font-size: 1.8rem;">
                {datetime.now(tw_tz).strftime("%H:%M:%S")}
            </h2>
        </div>
    """, unsafe_allow_html=True)

    st.session_state.lang = st.selectbox("🌐 Language", ["繁體中文", "English"], 
                                       index=0 if st.session_state.lang == "繁體中文" else 1)
    L = lang_pack[st.session_state.lang]
    st.divider()

    st.title(f"🔐 {L['login_section']}")
    if st.session_state.auth_status is None:
        tab1, tab2 = st.tabs([L['tab_login'], L['tab_register']])
        with tab1:
            u = st.text_input(L['user_label'], key="l_u")
            p = st.text_input(L['pass_label'], type="password", key="l_p")
            if st.button(L['btn_signin'], key="btn_l", use_container_width=True):
                role = login_user(u, p)
                if role:
                    st.session_state.auth_status, st.session_state.username = role, u
                    st.rerun()
                else: st.error(L['err_auth'])
        with tab2:
            ru, rp = st.text_input(L['user_label'], key="r_u"), st.text_input(L['pass_label'], type="password", key="r_p")
            if st.button(L['btn_signup'], key="btn_r", use_container_width=True):
                if register_user(ru, rp): st.success(L['reg_success'])
                else: st.error(L['err_exists'])
    else:
        st.success(f"👤 {L['auth_welcome']}, {st.session_state.username}")
        if st.button(L['auth_logout'], use_container_width=True):
            st.session_state.auth_status, st.session_state.username = None, "Guest"
            st.rerun()

    # 🔥 核心測速入庫邏輯 (含 Canvas 動畫)
    if st.session_state.auth_status:
        st.divider()
        st.title(f"🚀 {L['speed_test']}")
        speed_json = render_speed_test_ui(L)
        
        if speed_json:
            try:
                data = json.loads(speed_json)
                mbps_val, ts_val = data['mbps'], data['ts']
                if "last_ts" not in st.session_state or st.session_state.last_ts != ts_val:
                    st.session_state.last_ts = ts_val
                    add_record(st.session_state.username, float(mbps_val), 0.0, "Pass ✅")
                    st.toast(f"✅ Record Saved: {mbps_val} Mbps")
                    time.sleep(0.5)
                    st.rerun()
            except: pass

# --- 4. Dashboard 視覺渲染 ---
st.title(f"📡 {L['title']}")
m1, m2, m3, m4 = st.columns(4)

# 模擬後台趨勢 (供 Metric 顯示)
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
current_time = datetime.now(tw_tz).strftime("%H:%M:%S")
global_devices = st.cache_resource(lambda: {})()
if st.session_state.auth_status:
    global_devices[st.session_state.username] = {"name": st.session_state.username, "ip": ip, "ts": time.time(), "status": "Online 🟢"}

# 計算 SLA
current_logs = get_records(st.session_state.username)
if not current_logs.empty:
    sla_val = f"{(len(current_logs[current_logs['狀態'].str.contains('Pass|Success', na=False)]) / len(current_logs)) * 100:.1f}%"
else:
    sla_val = "100%"

m1.metric(L['m1'], f"{len(global_devices)}")
m2.metric(L['m2'], f"{random.randint(45, 52)} ms")
m3.metric(L['m3'], f"{random.uniform(6, 9):.2f} ms")
m4.metric(L['m4'], sla_val)

st.divider()

# 下方並排佈局
col_a, col_b = st.columns([1.2, 0.8])
with col_a:
    st.subheader(f"📜 {L['user_record']}")
    if not current_logs.empty:
        st.dataframe(current_logs, use_container_width=True, height=450)
    else:
        st.info("💡 目前無紀錄，請啟動左側測速。")

with col_b:
    st.subheader("🌐 Active Nodes")
    st.dataframe(pd.DataFrame(global_devices.values()), use_container_width=True, height=450)

st.markdown(f'<div class="ksr-footer">{L["version_info"]} | DEVELOPED BY {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
