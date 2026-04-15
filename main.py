# main.py
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
# 🔹 確保 components.py 是原本只有按鈕的版本，不要有 Canvas
from components import render_speed_test_ui

# --- 2. 系統初始化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
init_db()
tw_tz = timezone(timedelta(hours=8))
apply_ksr_styles()
# 🔄 刷新時間可以調長到 3000ms (3秒) 以進一步減少閃爍感，不影響即時性
st_autorefresh(interval=1000, key="ksr_refresh_final")

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
    # ... (登入邏輯維持原樣) ...
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

    # 🔥 核心測速入庫
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
                    st.toast(f"✅ Record Logged: {mbps_val} Mbps")
                    # 延遲刷新以同步數據
                    time.sleep(0.5)
                    st.rerun()
            except: pass

# --- 4. Dashboard 數據運算 ---
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
current_time = datetime.now(tw_tz).strftime("%H:%M:%S")

# 即時狀態紀錄
global_devices = st.cache_resource(lambda: {})()
if st.session_state.auth_status:
    global_devices[st.session_state.username] = {"name": st.session_state.username, "ip": ip, "ts": time.time(), "status": "Online 🟢"}

# 更新模擬數據圖表 (後台數據源)
new_tick = pd.DataFrame([{"time": current_time, "ms": random.randint(22, 55)}])
# 限制在線紀錄數為 30 筆
st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_tick], ignore_index=True).iloc[-30:]

# 獲取紀錄來計算 SLA
user_logs = get_records(st.session_state.username)
if not user_logs.empty:
    sla_val = f"{(len(user_logs[user_logs['狀態'].str.contains('Pass|Success', na=False)]) / len(user_logs)) * 100:.1f}%"
else:
    sla_val = "100%"

# --- 5. Dashboard UI 渲染 (大視覺回歸版) ---
st.title(f"📡 {L['title']}")
m1, m2, m3, m4 = st.columns(4)

m1.metric(L['m1'], f"{len(global_devices)}")
m2.metric(L['m2'], f"{st.session_state.chart_data['ms'].iloc[-1]} ms")
m3.metric(L['m3'], f"{np.std(st.session_state.chart_data['ms']):.2f} ms")
m4.metric(L['m4'], sla_val)

st.divider()

# 📊 🔥 重頭戲：把圖表請回來！ (平滑動畫優化版)
st.subheader(f"📊 {L['diag_title']}")

# 預留容器，防止頁面上下跳動
chart_placeholder = st.empty()

# 建立圖表
fig = px.area(
    st.session_state.chart_data, 
    x="time", 
    y="ms", 
    template="plotly_dark", 
    color_discrete_sequence=["#00f2ff"]
)

# 🔥 優化佈局：固定 Y 軸以減少重繪閃爍
fig.update_layout(
    height=320, 
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis_showgrid=False,
    # 動畫過渡效果
    transition_duration=500,
    transition_easing="cubic-in-out",
    # 固定座標軸範圍 (0-100)，防止自動縮放閃爍
    yaxis=dict(range=[0, 100], fixedrange=True, title="Latency (ms)"),
    xaxis=dict(fixedrange=True, title=None, tickangle=0) # 保持 X 軸平整
)

# 渲染到預留容器中
chart_placeholder.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- 6. 下方日誌清單 ---
st.divider()
st.subheader(f"📜 {L['user_record']}")
if not user_logs.empty:
    st.dataframe(user_logs, use_container_width=True, height=400)
else:
    st.info("💡 目前無紀錄，請啟動左側測速。")

# 底部 Footer
st.markdown(f'<div class="ksr-footer">{L["version_info"]} | DEVELOPED BY {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
