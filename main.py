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
from auth import init_auth_state, admin_login_listener, render_login_ui, check_admin_access

# --- 1. 系統初始化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
tw_tz = timezone(timedelta(hours=8))

# 初始化權限狀態與樣式
init_auth_state()
apply_ksr_styles()

# 注入快捷鍵監聽 (Shift + A)
admin_login_listener()

# 設定每秒刷新
st_autorefresh(interval=1000, key="data_refresh_1s")

# 初始化 session state
if 'history' not in st.session_state: 
    st.session_state.history = [{"time": datetime.now(tw_tz).strftime("%H:%M:%S"), "ms": 30}]

@st.cache_resource
def get_global_data(): return {} 
global_devices = get_global_data()

# --- 2. 登入邏輯觸發 ---
# 透過隱藏按鈕或快捷鍵觸發顯示登入 UI
render_login_ui()

# --- 3. 側邊欄控制中心 ---
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

    sel_lang = st.selectbox("Language", ["繁體中文", "English"], label_visibility="collapsed")
    L = lang_pack[sel_lang]

    st.divider()
    st.title(f"🛡️ {L['control_center']}")
    
    # 管理員專屬：登出按鈕
    if check_admin_access():
        if st.button("🚪 Logout Admin", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()
    
    app_mode = st.selectbox(L['sla_mode'], L['modes'])
    st.divider()
    render_speed_test_ui(L)
    st.sidebar.caption("Version 9.0.0-PRO | KSR NOC")

# --- 4. Telemetry 數據處理 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=86400)
def get_loc(ip_addr):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}?lang=en", timeout=3).json()
        return r if r['status'] == 'success' else None
    except: pass
    return None

loc = get_loc(ip)
display_country = loc.get('country', "Taiwan") if loc else "Taiwan"
display_id = f"Node_{hashlib.md5(ip.encode()).hexdigest()[:5]}"
current_now_str = datetime.now(tw_tz).strftime("%H:%M:%S")

# 更新全局清單與狀態
if display_id not in global_devices:
    global_devices[display_id] = {"name": display_id, "country": display_country, "last": current_now_str, "ts": time.time(), "status": "Online 🟢"}
else:
    global_devices[display_id]["ts"] = time.time()
    global_devices[display_id]["status"] = "Online 🟢"

# 離線判定與定格
ct = time.time()
for sid in list(global_devices.keys()):
    time_diff = ct - global_devices[sid]["ts"]
    if time_diff > 10 and global_devices[sid]["status"] == "Online 🟢":
        global_devices[sid]["last"] = datetime.now(tw_tz).strftime("%H:%M:%S")
        global_devices[sid]["status"] = "Offline 🔴"
    if time_diff > 60: del global_devices[sid]

# --- 5. Dashboard 主介面渲染 ---
st.title(f"📡 {L['title']}")
st.markdown(f"**Node ID:** `{display_id}` | **Location:** `{display_country}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric(L['m1'], f"{len(global_devices)} Units")
m2.metric(L['m2'], f"{random.randint(22, 55)} ms")
m3.metric(L['m3'], f"{np.mean(np.abs(np.diff([d['ms'] for d in st.session_state.history]))):.2f} ms")
m4.metric(L['m4'], "99.9%")

st.divider()

# 📊 延遲趨勢圖 (所有人可見)
st.subheader(f"📊 {L['diag_title']}")
fig = px.area(pd.DataFrame(st.session_state.history), x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

# 🔥 核心權限門禁：只有 Admin 可以看到動態清單
if check_admin_access():
    st.divider()
    st.subheader(f"📋 {L['list_title']} (Admin Only)")
    list_df = []
    for v in global_devices.values():
        list_df.append({L['unit_name']: v['name'], L['location']: v['country'], "Status": v['status'], L['last_seen']: v['last']})
    st.table(pd.DataFrame(list_df))
    
    # 管理員報表匯出
    csv_data = generate_csv_report(pd.DataFrame(st.session_state.history), "ADMIN", display_id, "KSR")
    st.download_button(f"📥 {L['export_btn']}", csv_data, f"KSR_Admin_Report.csv", "text/csv")
else:
    st.info("💡 提示：系統監測動態清單僅供管理員觀看。請按下快捷鍵登入。")

st.markdown(f'<div class="ksr-footer">DEVELOPED BY {lang_pack["English"]["team_name"].upper()} &copy; 2026.</div>', unsafe_allow_html=True)
