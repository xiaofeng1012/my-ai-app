import streamlit as st
import pandas as pd
import requests
import random
import time
import numpy as np
import plotly.express as px
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 全域匯入：確保所有自定義模組都在最頂層加載 ---
from language_pack import lang_pack
from styles import apply_ksr_styles
from database import init_db, register_user, login_user, add_record, get_records, clear_all_records
from components import render_speed_test_ui

# --- 1. 系統初始化與樣式加載 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
init_db()  # 初始化 SQLite 資料庫
tw_tz = timezone(timedelta(hours=8))
apply_ksr_styles()
st_autorefresh(interval=1000, key="ksr_refresh_global")

# Session State 初始化
if 'lang' not in st.session_state: st.session_state.lang = "繁體中文"
if 'auth_status' not in st.session_state: st.session_state.auth_status = None
if 'username' not in st.session_state: st.session_state.username = "Guest"
if 'chart_data' not in st.session_state: st.session_state.chart_data = pd.DataFrame(columns=["time", "ms"])

# --- 2. 側邊欄控制中心 ---
with st.sidebar:
    # 數位時鐘渲染
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

    # 身份驗證系統
    st.title(f"🔐 {L['login_section']}")
    if st.session_state.auth_status is None:
        tab1, tab2 = st.tabs([L['tab_login'], L['tab_register']])
        with tab1:
            u = st.text_input(L['user_label'], key="login_u")
            p = st.text_input(L['pass_label'], type="password", key="login_p")
            if st.button(L['btn_signin'], use_container_width=True):
                role = login_user(u, p)
                if role:
                    st.session_state.auth_status = role
                    st.session_state.username = u
                    st.rerun()
                else: st.error(L['err_auth'])
        with tab2:
            new_u = st.text_input(L['user_label'], key="reg_u")
            new_p = st.text_input(L['pass_label'], type="password", key="reg_p")
            if st.button(L['btn_signup'], use_container_width=True):
                if register_user(new_u, new_p): st.success(L['reg_success'])
                else: st.error(L['err_exists'])
    else:
        st.success(f"👤 {L['auth_welcome']}, {st.session_state.username}")
        st.caption(f"Access Level: {st.session_state.auth_status.upper()}")
        if st.button(L['auth_logout'], use_container_width=True):
            st.session_state.auth_status = None
            st.session_state.username = "Guest"
            st.rerun()

    # 🔥 權限鎖定：只有登入後才顯示測速 UI 並接收回傳值
    if st.session_state.auth_status:
        st.divider()
        st.title(f"🚀 {L['speed_test']}")
        speed_val = render_speed_test_ui(L)
        
        # 接收前端 JavaScript 傳回的數據
        if speed_val is not None:
            # 防重複寫入檢查
            if "last_logged_s" not in st.session_state or st.session_state.last_logged_s != speed_val:
                try:
                    numeric_val = float(speed_val)
                    st.session_state.last_logged_s = speed_val
                    # 自動存入 SQLite
                    add_record(st.session_state.username, numeric_val, 0.0, "Auto-Log ✅")
                    st.rerun()
                except ValueError:
                    pass

# --- 3. Telemetry 數據處理 ---
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
current_now_str = datetime.now(tw_tz).strftime("%H:%M:%S")

@st.cache_data(ttl=86400)
def fetch_location(ip_addr):
    if ip_addr in ["127.0.0.1", "localhost"]: return {"country": "Local Host"}
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}?lang=en", timeout=3).json()
        return r if r.get('status') == 'success' else {"country": "Unknown"}
    except: return {"country": "Unknown"}

loc = fetch_location(ip)
user_country = loc.get('country', "Taiwan")
global_devices = st.cache_resource(lambda: {})()

# 即時心跳紀錄 (供 Admin 查看)
if st.session_state.auth_status:
    global_devices[st.session_state.username] = {
        "name": st.session_state.username,
        "ip": ip,
        "location": user_country,
        "last": current_now_str,
        "ts": time.time(),
        "status": "Online 🟢"
    }

# 清除離線節點 (超過 60 秒未活動)
current_ts = time.time()
for sid in list(global_devices.keys()):
    if current_ts - global_devices[sid]["ts"] > 10:
        global_devices[sid]["status"] = "Inactive 🔴"
    if current_ts - global_devices[sid]["ts"] > 60:
        del global_devices[sid]

# --- 4. Dashboard 主視覺 ---
st.title(f"📡 {L['title']}")
m1, m2, m3, m4 = st.columns(4)

# 圖表動態更新 (僅供視覺展示趨勢)
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
    # 🏆 管理員：全系統控制與紀錄中心
    tab_active, tab_all_logs = st.tabs(["⚡ Active Nodes", "📜 Full System History"])
    
    with tab_active:
        st.subheader(f"📋 {L['db_title']}")
        st.dataframe(pd.DataFrame(global_devices.values()), use_container_width=True, hide_index=True)
    
    with tab_all_logs:
        full_logs = get_records()  # 管理員視角讀取全部
        st.dataframe(full_logs, use_container_width=True, hide_index=True)
        if st.button("⚠️ Clear All Test Records", type="primary"):
            clear_all_records()
            st.rerun()

elif st.session_state.auth_status == "user":
    # 👤 一般使用者：個人測速歷史 (永久儲存)
    st.subheader(f"📜 {L['user_record']}")
    personal_logs = get_records(st.session_state.username)
    if not personal_logs.empty:
        st.dataframe(personal_logs, use_container_width=True, hide_index=True)
        st.download_button("📥 " + L['export_btn'], personal_logs.to_csv(index=False).encode('utf-8'), f"logs_{st.session_state.username}.csv")
    else:
        st.info("💡 目前無紀錄，請在左側執行測速。")

else:
    # 訪客模式
    st.warning(L['lock_msg'])

st.markdown(f'<div class="ksr-footer">DEVELOPED BY {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
