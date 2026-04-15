import streamlit as st
import pandas as pd
import requests
import random
import time
import numpy as np
import plotly.express as px
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh

# 全域匯入，防止 NameError
from language_pack import lang_pack
from styles import apply_ksr_styles
from database import init_db, register_user, login_user, add_record, get_records, clear_all_records
from components import render_speed_test_ui

# --- 1. 初始化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
init_db()
tw_tz = timezone(timedelta(hours=8))
apply_ksr_styles()
st_autorefresh(interval=1000, key="refresh_1s")

if 'lang' not in st.session_state: st.session_state.lang = "繁體中文"
if 'auth_status' not in st.session_state: st.session_state.auth_status = None
if 'username' not in st.session_state: st.session_state.username = "Guest"
if 'chart_data' not in st.session_state: st.session_state.chart_data = pd.DataFrame(columns=["time", "ms"])

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown(f"""<div style="background-color:#161b22;padding:15px;border-radius:10px;border-left:5px solid #00f2ff;">
        <p style="margin:0;color:#8b949e;font-size:0.75rem;">SYSTEM TIME</p>
        <h2 style="margin:0;color:#00f2ff;font-family:monospace;">{datetime.now(tw_tz).strftime("%H:%M:%S")}</h2>
    </div>""", unsafe_allow_html=True)

    st.session_state.lang = st.selectbox("🌐 Language", ["繁體中文", "English"], index=0 if st.session_state.lang=="繁體中文" else 1)
    L = lang_pack[st.session_state.lang]
    st.divider()

    st.title(f"🔐 {L['login_section']}")
    if st.session_state.auth_status is None:
        tab1, tab2 = st.tabs([L['tab_login'], L['tab_register']])
        with tab1:
            u = st.text_input(L['user_label'], key="l_u")
            p = st.text_input(L['pass_label'], type="password", key="l_p")
            if st.button(L['btn_signin'], use_container_width=True):
                role = login_user(u, p)
                if role:
                    st.session_state.auth_status, st.session_state.username = role, u
                    st.rerun()
                else: st.error(L['err_auth'])
        with tab2:
            ru, rp = st.text_input(L['user_label'], key="r_u"), st.text_input(L['pass_label'], type="password", key="r_p")
            if st.button(L['btn_signup'], use_container_width=True):
                if register_user(ru, rp): st.success(L['reg_success'])
                else: st.error(L['err_exists'])
    else:
        st.success(f"👤 {L['auth_welcome']}, {st.session_state.username}")
        if st.button(L['auth_logout'], use_container_width=True):
            st.session_state.auth_status = None
            st.rerun()

    # 登入後顯示測速
    if st.session_state.auth_status:
        st.divider()
        st.title(f"🚀 {L['speed_test']}")
        speed_val = render_speed_test_ui(L)
        # 防錯與防重複寫入邏輯
        if speed_val is not None:
            if "last_s" not in st.session_state or st.session_state.last_s != speed_val:
                try:
                    add_record(st.session_state.username, float(speed_val), 0.0, "Success ✅")
                    st.session_state.last_s = speed_val
                    st.rerun()
                except: pass

# --- 3. Telemetry & Dashboard ---
# (Telemetry 邏輯維持原樣...)
# (Dashboard 圖表邏輯維持原樣...)

# --- 5. 分級渲染 ---
st.divider()
if st.session_state.auth_status == "admin":
    t1, t2 = st.tabs(["Active Nodes", "Full Logs"])
    with t1:
        st.dataframe(pd.DataFrame(global_devices.values()), use_container_width=True, hide_index=True)
    with t2:
        logs = get_records()
        st.dataframe(logs, use_container_width=True, hide_index=True)
        if st.button("⚠️ Clear DB"):
            clear_all_records()
            st.rerun()
elif st.session_state.auth_status == "user":
    st.subheader(f"📜 {L['user_record']}")
    my_logs = get_records(st.session_state.username)
    st.dataframe(my_logs, use_container_width=True, hide_index=True)
else:
    st.warning(L['lock_msg'])

st.markdown(f'<div class="ksr-footer">DEVELOPED BY {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
