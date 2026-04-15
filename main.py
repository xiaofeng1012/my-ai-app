import streamlit as st
import pandas as pd
import requests
import random
import time
import json
import numpy as np
import plotly.express as px
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
st_autorefresh(interval=1000, key="ksr_main_refresh")

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

    # 🔥 關鍵修正：測速邏輯與 JSON 解析
    if st.session_state.auth_status:
        st.divider()
        st.title(f"🚀 {L['speed_test']}")
        speed_json = render_speed_test_ui(L)
        
        if speed_json:
            try:
                # 解析前端傳回的包裹
                res_data = json.loads(speed_json)
                mbps_val = res_data['mbps']
                ts_val = res_data['ts']
                
                # 只有當 timestamp 真正更新時才執行存檔 (避免 autorefresh 重複存)
                if "last_ts" not in st.session_state or st.session_state.last_ts != ts_val:
                    st.session_state.last_ts = ts_val
                    # 🔹 執行入庫
                    add_record(st.session_state.username, float(mbps_val), 0.0, "Success ✅")
                    st.toast(f"✅ Record Logged: {mbps_val} Mbps")
                    time.sleep(0.5)
                    st.rerun()
            except Exception as e:
                pass

# --- 4. Dashboard 數據展示 ---
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
current_time = datetime.now(tw_tz).strftime("%H:%M:%S")

global_devices = st.cache_resource(lambda: {})()
if st.session_state.auth_status:
    global_devices[st.session_state.username] = {
        "name": st.session_state.username, "ip": ip, "ts": time.time(), "status": "Online 🟢"
    }

# 清理離線節點
for sid in list(global_devices.keys()):
    if time.time() - global_devices[sid]["ts"] > 60: del global_devices[sid]

st.title(f"📡 {L['title']}")
m1, m2, m3, m4 = st.columns(4)
new_tick = pd.DataFrame([{"time": current_time, "ms": random.randint(22, 55)}])
st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_tick], ignore_index=True).iloc[-30:]

m1.metric(L['m1'], f"{len(global_devices)}")
m2.metric(L['m2'], f"{st.session_state.chart_data['ms'].iloc[-1]} ms")
m3.metric(L['m3'], f"{np.std(st.session_state.chart_data['ms']):.2f} ms")
m4.metric(L['m4'], "99.9%")

st.divider()
fig = px.area(st.session_state.chart_data, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), xaxis_showgrid=False)
st.plotly_chart(fig, use_container_width=True)

# --- 5. 數據列表 ---
st.divider()
if st.session_state.auth_status == "admin":
    t1, t2 = st.tabs(["Active Nodes", "System Logs"])
    with t1: st.dataframe(pd.DataFrame(global_devices.values()), use_container_width=True, hide_index=True)
    with t2:
        logs = get_records()
        st.dataframe(logs, use_container_width=True, hide_index=True)
        if st.button("⚠️ Clear All Records"):
            clear_all_records()
            st.rerun()
elif st.session_state.auth_status == "user":
    st.subheader(f"📜 {L['user_record']}")
    my_logs = get_records(st.session_state.username)
    if not my_logs.empty:
        st.dataframe(my_logs, use_container_width=True, hide_index=True)
        st.download_button("📥 Export CSV", my_logs.to_csv(index=False).encode('utf-8'), f"logs_{st.session_state.username}.csv")
    else:
        st.info("💡 目前無紀錄，請點擊左側測速按鈕。")
else:
    st.warning(L['lock_msg'])

st.markdown(f'<div class="ksr-footer">DEVELOPED BY {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
