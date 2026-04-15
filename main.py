import streamlit as st
import pandas as pd
import requests
import random
import time
import numpy as np
import plotly.express as px
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 核心匯入：確保所有自定義模組都在最頂層加載 ---
from language_pack import lang_pack
from styles import apply_ksr_styles
from database import init_db, register_user, login_user, add_record, get_records, clear_all_records
from components import render_speed_test_ui

# --- 1. 系統初始化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
init_db()  # 初始化 SQLite 資料庫結構
tw_tz = timezone(timedelta(hours=8))
apply_ksr_styles()
st_autorefresh(interval=1000, key="ksr_refresh_main")

# Session State 初始化
if 'lang' not in st.session_state: st.session_state.lang = "繁體中文"
if 'auth_status' not in st.session_state: st.session_state.auth_status = None
if 'username' not in st.session_state: st.session_state.username = "Guest"
if 'chart_data' not in st.session_state: st.session_state.chart_data = pd.DataFrame(columns=["time", "ms"])

# --- 2. 側邊欄控制中心 ---
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

    # 語系選擇
    st.session_state.lang = st.selectbox("🌐 Language", ["繁體中文", "English"], 
                                       index=0 if st.session_state.lang == "繁體中文" else 1)
    L = lang_pack[st.session_state.lang]
    st.divider()

    # 帳號存取系統
    st.title(f"🔐 {L['login_section']}")
    if st.session_state.auth_status is None:
        tab1, tab2 = st.tabs([L['tab_login'], L['tab_register']])
        with tab1:
            u = st.text_input(L['user_label'], key="login_u")
            p = st.text_input(L['pass_label'], type="password", key="login_p")
            if st.button(L['btn_signin'], use_container_width=True):
                role = login_user(u, p)
                if role:
                    st.session_state.auth_status, st.session_state.username = role, u
                    st.rerun()
                else: st.error(L['err_auth'])
        with tab2:
            ru, rp = st.text_input(L['user_label'], key="reg_u"), st.text_input(L['pass_label'], type="password", key="reg_p")
            if st.button(L['btn_signup'], use_container_width=True):
                if register_user(ru, rp): st.success(L['reg_success'])
                else: st.error(L['err_exists'])
    else:
        st.success(f"👤 {L['auth_welcome']}, {st.session_state.username}")
        if st.button(L['auth_logout'], use_container_width=True):
            st.session_state.auth_status = None
            st.rerun()

    # 🔥 功能鎖定：登入後才載入測速功能並處理回傳值
    if st.session_state.auth_status:
        st.divider()
        st.title(f"🚀 {L['speed_test']}")
        speed_val = render_speed_test_ui(L)
        
        # 修正 TypeError：確保 speed_val 不是 None 且格式正確才處理
        if speed_val is not None:
            if "last_s" not in st.session_state or st.session_state.last_s != speed_val:
                try:
                    numeric_speed = float(speed_val) # 安全轉換
                    st.session_state.last_s = speed_val
                    # 自動寫入資料庫
                    add_record(st.session_state.username, numeric_speed, 0.0, "Auto-Log ✅")
                    st.rerun() # 重新讀取資料庫顯示新紀錄
                except (ValueError, TypeError):
                    pass # 過濾非數字的回傳值

# --- 3. Telemetry 數據與即時監控 ---
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
current_now_str = datetime.now(tw_tz).strftime("%H:%M:%S")

@st.cache_data(ttl=86400)
def get_ip_loc(ip_addr):
    if ip_addr in ["127.0.0.1", "localhost"]: return {"country": "Taiwan"}
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}?lang=en", timeout=3).json()
        return r if r.get('status') == 'success' else {"country": "Taiwan"}
    except: return {"country": "Taiwan"}

loc_data = get_ip_loc(ip)
display_country = loc_data.get('country', "Taiwan")
global_devices = st.cache_resource(lambda: {})()

# 即時心跳 (供 Admin 監控)
if st.session_state.auth_status:
    global_devices[st.session_state.username] = {
        "name": st.session_state.username, "ip": ip, "location": display_country, 
        "last": current_now_str, "ts": time.time(), "status": "Online 🟢"
    }

# 清除離線節點
ct = time.time()
for sid in list(global_devices.keys()):
    if ct - global_devices[sid]["ts"] > 10: global_devices[sid]["status"] = "Inactive 🔴"
    if ct - global_devices[sid]["ts"] > 60: del global_devices[sid]

# --- 4. Dashboard 主介面視覺 ---
st.title(f"📡 {L['title']}")
m1, m2, m3, m4 = st.columns(4)

# 模擬圖表數據更新
new_entry = pd.DataFrame([{"time": current_now_str, "ms": random.randint(22, 55)}])
st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_entry], ignore_index=True).iloc[-30:]

m1.metric(L['m1'], f"{len(global_devices)}")
m2.metric(L['m2'], f"{st.session_state.chart_data['ms'].iloc[-1]} ms")
m3.metric(L['m3'], f"{np.std(st.session_state.chart_data['ms']):.2f} ms")
m4.metric(L['m4'], "99.9%")

st.divider()
st.subheader(f"📊 {L['diag_title']}")
fig = px.area(st.session_state.chart_data, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), xaxis_showgrid=False)
st.plotly_chart(fig, use_container_width=True)

# --- 5. 分級渲染控制台 ---
st.divider()
if st.session_state.auth_status == "admin":
    # 🏆 管理員：監控中心
    t1, t2 = st.tabs(["Active Nodes", "Full History Logs"])
    with t1:
        st.dataframe(pd.DataFrame(global_devices.values()), use_container_width=True, hide_index=True)
    with t2:
        all_logs = get_records()
        st.dataframe(all_logs, use_container_width=True, hide_index=True)
        if st.button("⚠️ Clear DB Records", type="primary"):
            clear_all_records()
            st.rerun()

elif st.session_state.auth_status == "user":
    # 👤 一般使用者：個人紀錄
    st.subheader(f"📜 {L['user_record']}")
    my_logs = get_records(st.session_state.username)
    if not my_logs.empty:
        st.dataframe(my_logs, use_container_width=True, hide_index=True)
        st.download_button("📥 Export CSV", my_logs.to_csv(index=False).encode('utf-8'), f"logs_{st.session_state.username}.csv")
    else:
        st.info("💡 尚無數據，請在左側執行測速。")
else:
    st.warning(L['lock_msg'])

st.markdown(f'<div class="ksr-footer">DEVELOPED BY {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
