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

# 匯入你的自定義模組
from language_pack import lang_pack
from styles import apply_ksr_styles
from components import render_speed_test_ui
from utils import generate_csv_report

# --- 1. 系統初始化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
tw_tz = timezone(timedelta(hours=8))

# 初始化權限與使用者狀態
if 'auth_status' not in st.session_state:
    st.session_state.auth_status = None
if 'lang' not in st.session_state:
    st.session_state.lang = "繁體中文"

# 初始化數據緩存 (解決分析圖壞掉的問題)
if 'chart_data' not in st.session_state:
    st.session_state.chart_data = pd.DataFrame(columns=["time", "ms"])

apply_ksr_styles()
st_autorefresh(interval=1000, key="data_refresh_1s")

# --- 2. 側邊欄：控制中心與語系切換 ---
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

    # 語系切換邏輯
    st.session_state.lang = st.selectbox(
        "🌐 Language Selection", 
        ["繁體中文", "English"], 
        index=0 if st.session_state.lang == "繁體中文" else 1,
        key="lang_selector"
    )
    L = lang_pack[st.session_state.lang]
    
    st.divider()

    # 登入介面 (對應 language_pack)
    st.title("🔐 Login")
    if st.session_state.auth_status is None:
        with st.expander("🔑 Access Terminal", expanded=False):
            acc = st.text_input("Account", key="acc_in")
            pwd = st.text_input("Password", type="password", key="pwd_in")
            if st.button("Login", use_container_width=True):
                if acc == "Admin" and pwd == "2812":
                    st.session_state.auth_status = "admin"
                    st.rerun()
                elif acc == "User" and pwd == "1234":
                    st.session_state.auth_status = "user"
                    st.rerun()
                else:
                    st.error("Access Denied")
    else:
        st.success(f"Role: {st.session_state.auth_status.upper()}")
        if st.button("Logout", use_container_width=True):
            st.session_state.auth_status = None
            st.rerun()

    st.divider()
    st.title(f"🛡️ {L['control_center']}")
    render_speed_test_ui(L)
    st.sidebar.caption(f"Version 10.3.0 | {L['team_name']}")

# --- 3. Telemetry 數據處理 ---
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=86400)
def get_loc_pro(ip_addr):
    if ip_addr in ["127.0.0.1", "localhost"]: return {"country": "Taiwan"}
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}?lang=en", timeout=3).json()
        return r if r.get('status') == 'success' else {"country": "Taiwan"}
    except: return {"country": "Taiwan"}

loc = get_loc_pro(ip)
display_country = loc.get('country', "Taiwan")
display_id = f"Node_{hashlib.md5(ip.encode()).hexdigest()[:5]}"
current_now_str = datetime.now(tw_tz).strftime("%H:%M:%S")

# 圖表數據追加：確保圖表有連續性
new_tick = pd.DataFrame([{"time": current_now_str, "ms": random.randint(22, 55)}])
st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_tick], ignore_index=True)
if len(st.session_state.chart_data) > 30:
    st.session_state.chart_data = st.session_state.chart_data.iloc[1:]

# 全域清單與定格邏輯
global_devices = st.cache_resource(lambda: {})()
# 狀態字串也支援語系
online_tag = "在線 🟢" if st.session_state.lang == "繁體中文" else "Online 🟢"
offline_tag = "離線 🔴" if st.session_state.lang == "繁體中文" else "Offline 🔴"

if display_id not in global_devices:
    global_devices[display_id] = {"name": display_id, "country": display_country, "last": current_now_str, "ts": time.time(), "status": online_tag}
else:
    global_devices[display_id]["ts"] = time.time()
    global_devices[display_id]["status"] = online_tag

# 離線判定
ct = time.time()
for sid in list(global_devices.keys()):
    time_diff = ct - global_devices[sid]["ts"]
    if time_diff > 10 and "🟢" in global_devices[sid]["status"]:
        global_devices[sid]["last"] = datetime.now(tw_tz).strftime("%H:%M:%S")
        global_devices[sid]["status"] = offline_tag
    if time_diff > 60: del global_devices[sid]

# --- 4. Dashboard 主介面渲染 ---
st.title(f"📡 {L['title']}")
st.info(f"📍 **{L['node']}:** `{display_id}` | **{L['location']}:** `{display_country}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric(L['m1'], f"{len(global_devices)} Units")
m2.metric(L['m2'], f"{st.session_state.chart_data['ms'].iloc[-1]} ms")
m3.metric(L['m3'], f"{np.std(st.session_state.chart_data['ms']):.2f} ms")
m4.metric(L['m4'], "99.9%")

st.divider()

# 圖表區域 (修復後的穩定版)
st.subheader(f"📊 {L['diag_title']}")
if not st.session_state.chart_data.empty:
    fig = px.area(st.session_state.chart_data, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), xaxis_showgrid=False, yaxis_showgrid=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- 5. 權限分級顯示清單 ---
st.divider()

if st.session_state.auth_status == "admin":
    st.subheader(f"📋 {L['list_title']} (ADMIN)")
    # 使用 language_pack 內的欄位名稱
    list_df = [{
        L['unit_name']: v['name'], 
        L['location']: v['country'], 
        "Status": v['status'], 
        L['last_seen']: v['last']
    } for v in global_devices.values()]
    st.table(pd.DataFrame(list_df))
    st.download_button(L['export_btn'], generate_csv_report(st.session_state.chart_data, "ADMIN", "ALL", "KSR"), "global_report.csv")

elif st.session_state.auth_status == "user":
    st.subheader(f"📋 {L['list_title']} (USER)")
    if display_id in global_devices:
        v = global_devices[display_id]
        st.table(pd.DataFrame([{L['unit_name']: v['name'], L['location']: v['country'], "Status": v['status'], L['last_seen']: v['last']}]))
else:
    st.warning("🔒 " + ("列表已鎖定。一般使用者請登入查看個人紀錄，管理員請登入查看全系統。" if st.session_state.lang == "繁體中文" else "List locked. Please login to view node registry."))

st.markdown(f'<div class="ksr-footer">DEVELOPED BY {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
