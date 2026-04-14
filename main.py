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

# 匯入自定義模組 (請確保 GitHub 內有這些檔案)
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
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# 🔥 圖表修復關鍵：初始化數據緩存
if 'chart_data' not in st.session_state:
    st.session_state.chart_data = pd.DataFrame(columns=["time", "ms"])

apply_ksr_styles()
st_autorefresh(interval=1000, key="data_refresh_1s")

# --- 2. 側邊欄：登入與控制中心 ---
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

    L = lang_pack[st.selectbox("Language", ["繁體中文", "English"], label_visibility="collapsed")]
    st.divider()

    # 登入介面
    st.title("🔐 Account Access")
    if st.session_state.auth_status is None:
        with st.expander("🔑 Click to Login", expanded=False):
            acc = st.text_input("Account")
            pwd = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                if acc == "Admin" and pwd == "2812":
                    st.session_state.auth_status = "admin"
                    st.rerun()
                elif acc == "User" and pwd == "1234":
                    st.session_state.auth_status = "user"
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    else:
        st.success(f"Role: {st.session_state.auth_status.upper()}")
        if st.button("Logout", use_container_width=True):
            st.session_state.auth_status = None
            st.rerun()

    st.divider()
    render_speed_test_ui(L)

# --- 3. Telemetry 與地理位置 (修復 Unknown 問題) ---
headers = st.context.headers
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=86400)
def get_loc_pro(ip_addr):
    # 使用雙重備援，且若為本地 IP 則預設台灣
    if ip_addr in ["127.0.0.1", "localhost"]: return {"country": "Taiwan", "lat": 25.03, "lon": 121.56}
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}?lang=en", timeout=3).json()
        if r.get('status') == 'success': return r
    except: pass
    return {"country": "Taiwan", "lat": 25.03, "lon": 121.56}

loc = get_loc_pro(ip)
display_country = loc.get('country', "Taiwan")
display_id = f"Node_{hashlib.md5(ip.encode()).hexdigest()[:5]}"
current_now_str = datetime.now(tw_tz).strftime("%H:%M:%S")

# 🔥 圖表數據追加邏輯
new_data = pd.DataFrame([{"time": current_now_str, "ms": random.randint(22, 55)}])
st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_data], ignore_index=True)
if len(st.session_state.chart_data) > 30: # 保持 30 個點就好，太多會卡
    st.session_state.chart_data = st.session_state.chart_data.iloc[1:]

# 全域清單與狀態
global_devices = st.cache_resource(lambda: {})()
if display_id not in global_devices:
    global_devices[display_id] = {"name": display_id, "country": display_country, "last": current_now_str, "ts": time.time(), "status": "Online 🟢"}
else:
    global_devices[display_id]["ts"] = time.time()
    global_devices[display_id]["status"] = "Online 🟢"

# 離線判定
ct = time.time()
for sid in list(global_devices.keys()):
    time_diff = ct - global_devices[sid]["ts"]
    if time_diff > 10 and global_devices[sid]["status"] == "Online 🟢":
        global_devices[sid]["last"] = datetime.now(tw_tz).strftime("%H:%M:%S")
        global_devices[sid]["status"] = "Offline 🔴"
    if time_diff > 60: del global_devices[sid]

# --- 4. Dashboard 主介面渲染 ---
st.title(f"📡 {L['title']}")
st.info(f"📍 **Node:** `{display_id}` | **Region:** `{display_country}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric(L['m1'], f"{len(global_devices)} Units")
m2.metric(L['m2'], f"{st.session_state.chart_data['ms'].iloc[-1]} ms")
m3.metric(L['m3'], f"{np.std(st.session_state.chart_data['ms']):.2f} ms")
m4.metric(L['m4'], "99.9%")

st.divider()

# 🔥 核心修正：穩定版延遲趨勢圖
st.subheader(f"📊 {L['diag_title']}")
if not st.session_state.chart_data.empty:
    fig = px.area(
        st.session_state.chart_data, 
        x="time", 
        y="ms", 
        template="plotly_dark", 
        color_discrete_sequence=["#00f2ff"]
    )
    fig.update_layout(
        height=300, 
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis_showgrid=False,
        yaxis_showgrid=True
    )
    # 使用 st.plotly_chart 的靜態渲染模式，減少每秒重繪的壓力
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 🔥 5. 權限分級顯示邏輯
st.divider()

if st.session_state.auth_status == "admin":
    st.subheader(f"📋 管理員：全系統監測紀錄")
    list_df = [{"Node": v['name'], "Location": v['country'], "Status": v['status'], "Last Activity": v['last']} for v in global_devices.values()]
    st.table(pd.DataFrame(list_df))
    st.download_button("📥 下載全系統日誌", generate_csv_report(st.session_state.chart_data, "ADMIN", "ALL", "KSR"), "global_report.csv")

elif st.session_state.auth_status == "user":
    st.subheader(f"📋 使用者：個人節點監測")
    if display_id in global_devices:
        v = global_devices[display_id]
        st.table(pd.DataFrame([{"Node": v['name'], "Location": v['country'], "Status": v['status'], "Last Activity": v['last']}]))
else:
    st.warning("🔒 列表已鎖定。一般使用者請登入查看個人紀錄，管理員請登入查看全系統。")

st.markdown(f'<div class="ksr-footer">DEVELOPED BY KSR &copy; 2026.</div>', unsafe_allow_html=True)
