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
from database import init_db, register_user, login_user, add_record, get_records, clear_all_records

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

# --- 2. 側邊欄：帳號與功能控制 ---
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

    st.session_state.lang = st.selectbox("🌐 Language", ["繁體中文", "English"], 
                                       index=0 if st.session_state.lang == "繁體中文" else 1)
    L = lang_pack[st.session_state.lang]
    st.divider()

    # 帳號存取區塊
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

    # 🔥 關鍵修正：只有在登入狀態（auth_status 不為 None）時，才會顯示測速功能
    if st.session_state.auth_status:
        st.divider()
        st.title(f"🚀 {L['speed_test']}")
        from components import render_speed_test_ui
        render_speed_test_ui(L)

# --- 3. Telemetry 處理 ---
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
current_now_str = datetime.now(tw_tz).strftime("%H:%M:%S")

@st.cache_data(ttl=86400)
def get_loc_pro(ip_addr):
    if ip_addr in ["127.0.0.1", "localhost"]: return {"country": "Taiwan"}
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}?lang=en", timeout=3).json()
        return r if r.get('status') == 'success' else {"country": "Taiwan"}
    except: return {"country": "Taiwan"}

loc = get_loc_pro(ip)
display_country = loc.get('country', "Taiwan")
user_id = st.session_state.username
global_devices = st.cache_resource(lambda: {})()

# 心跳紀錄 (用於管理員查看即時在線)
if st.session_state.auth_status:
    if user_id not in global_devices:
        global_devices[user_id] = {
            "name": user_id, "ip": ip, "location": display_country, 
            "start_time": current_now_str, "last": current_now_str, "ts": time.time(),
            "status": "Online 🟢" if st.session_state.lang == "繁體中文" else "Online 🟢"
        }
    else:
        global_devices[user_id]["ts"] = time.time()
        global_devices[user_id]["status"] = "Online 🟢" if st.session_state.lang == "繁體中文" else "Online 🟢"

# 清理離線節點
ct = time.time()
for sid in list(global_devices.keys()):
    time_diff = ct - global_devices[sid]["ts"]
    if time_diff > 10 and "🟢" in global_devices[sid]["status"]:
        global_devices[sid]["status"] = "Offline 🔴" if st.session_state.lang == "繁體中文" else "Offline 🔴"
        global_devices[sid]["last"] = datetime.now(tw_tz).strftime("%H:%M:%S")
    if time_diff > 60: del global_devices[sid]

# --- 4. Dashboard 主介面 ---
st.title(f"📡 {L['title']}")
m1, m2, m3, m4 = st.columns(4)

new_tick = pd.DataFrame([{"time": current_now_str, "ms": random.randint(22, 55)}])
st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_tick], ignore_index=True).iloc[-30:]

m1.metric(L['m1'], f"{len(global_devices)}")
m2.metric(L['m2'], f"{st.session_state.chart_data['ms'].iloc[-1]} ms")
m3.metric(L['m3'], f"{np.std(st.session_state.chart_data['ms']):.2f} ms")
m4.metric(L['m4'], "99.9%")

st.divider()
st.subheader(f"📊 {L['diag_title']}")
fig = px.area(st.session_state.chart_data, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), xaxis_showgrid=False)
st.plotly_chart(fig, use_container_width=True)

# --- 5. 分級渲染核心 ---
st.divider()

if st.session_state.auth_status == "admin":
    tab_active, tab_history = st.tabs(["Active Nodes", "Full Database Logs"])
    
    with tab_active:
        st.subheader(f"📋 {L['db_title']}")
        col_ip_title = "IP Address" if st.session_state.lang == "English" else "網路位址 (IP)"
        col_start_title = "Session Start" if st.session_state.lang == "English" else "登入使用時間"
        admin_active = [{L['unit_name']: v['name'], col_ip_title: v['ip'], L['location']: v['location'], 
                         col_start_title: v['start_time'], L['last_seen']: v['last'], "Status": v['status']} 
                        for v in global_devices.values()]
        st.dataframe(pd.DataFrame(admin_active), use_container_width=True, hide_index=True)

    with tab_history:
        st.subheader("🗄️ 全系統歷史測速數據庫")
        all_logs = get_records() 
        st.dataframe(all_logs, use_container_width=True, hide_index=True)
        
        if st.button("⚠️ 清空資料庫所有測速紀錄", type="primary"):
            clear_all_records()
            st.success("Database Cleared!")
            st.rerun()

elif st.session_state.auth_status == "user":
    st.subheader(f"📜 {L['user_record']}")
    my_logs = get_records(st.session_state.username)
    if not my_logs.empty:
        st.dataframe(my_logs, use_container_width=True, hide_index=True)
        st.download_button("📥 " + L['export_btn'], my_logs.to_csv(index=False).encode('utf-8'), f"history_{user_id}.csv")
    else:
        st.info("💡 尚無數據。請使用側邊欄測速功能開始紀錄。" if st.session_state.lang == "繁體中文" else "No data. Please use the sidebar test function.")

else:
    # 訪客模式：隱藏清單並顯示鎖定提示
    st.warning(L['lock_msg'])

st.markdown(f'<div class="ksr-footer">DEVELOPED BY {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
