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

# --- 1. 系統初始化 ---
st.set_page_config(
    page_title="卡式如通訊品質監測平台", 
    layout="wide", 
    page_icon="📡"
)

# 定義台北時區
tw_tz = timezone(timedelta(hours=8))

# 套用客製化 CSS
apply_ksr_styles()

# 設定每秒刷新 (1000ms)
st_autorefresh(interval=1000, key="data_refresh_1s")

# 初始化 session state
if 'history' not in st.session_state: 
    st.session_state.history = [{"time": datetime.now(tw_tz).strftime("%H:%M:%S"), "ms": 30}]

@st.cache_resource
def get_global_data(): return {} 
global_devices = get_global_data()

# --- 2. 側邊欄控制中心 ---
with st.sidebar:
    st.title("🌐 Language Selection")
    sel_lang = st.selectbox("Language", ["繁體中文", "English"], label_visibility="collapsed")
    L = lang_pack[sel_lang]

    st.divider()
    st.title(f"🛡️ {L['control_center']}")
    app_mode = st.selectbox(L['sla_mode'], L['modes'])

    st.divider()
    st.subheader(f"🚀 {L['speed_test']}")
    render_speed_test_ui(L)

    st.divider()
    st.sidebar.markdown(f"**Designed by {L['team_name']}**")
    st.sidebar.caption("Version 8.8.6-COUNTRY | KSR NOC")


# --- 3. Telemetry 數據處理 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=3600)
def get_loc(ip_addr):
    try:
        # 加上 lang=en 確保取得國際通用國家名
        r = requests.get(f"http://ip-api.com/json/{ip_addr}?lang=en", timeout=5).json()
        return r if r['status'] == 'success' else None
    except: return None

loc = get_loc(ip)
if "Windows" in user_agent:
    icon, dev_type = "💻", "Windows"
elif "iPhone" in user_agent:
    icon, dev_type = "🍎", "iPhone"
else:
    icon, dev_type = "📱", "Mobile"

display_id = f"{dev_type}_{hashlib.md5(f'{dev_type}_{ip}'.encode()).hexdigest()[:5]}"
sys_hash = hashlib.sha1(display_id.encode()).hexdigest()[:12].upper()

# 獲取校準後的台北時間
current_now = datetime.now(tw_tz).strftime("%H:%M:%S")

curr_p = random.randint(22, 55)
st.session_state.history.append({"time": current_now, "ms": curr_p})
if len(st.session_state.history) > 40: st.session_state.history.pop(0)

df_raw = pd.DataFrame(st.session_state.history)
jitter = np.mean(np.abs(np.diff(df_raw['ms']))) if len(df_raw) > 1 else 0
sla = (sum(1 for p in df_raw['ms'] if p < 60)/len(df_raw)*100)

# 🔥 核心修改 1：全域清單只儲存國家
global_devices[display_id] = {
    "name": display_id, 
    "country": loc['country'] if loc else "Unknown", 
    "lat": loc['lat'] if loc else 25.03, 
    "lon": loc['lon'] if loc else 121.56,
    "last": current_now,
    "ts": time.time()
}

# 每秒清理邏輯
ct = time.time()
for sid in list(global_devices.keys()):
    if ct - global_devices[sid]["ts"] > 8: 
        del global_devices[sid]

# --- 4. Dashboard 主介面渲染 ---
st.title(f"📡 {L['title']}")

# 🔥 核心修改 2：頂部標題資訊改為顯示國家
current_country = loc['country'] if loc else 'Detecting...'
st.markdown(f"**{L['audit_hash']}:** `{sys_hash}` | **{L['node']}:** `{current_country}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric(L['m1'], f"{len(global_devices)} Units")
m2.metric(L['m2'], f"{curr_p} ms", delta=f"{curr_p - df_raw['ms'].iloc[-2] if len(df_raw)>1 else 0} ms", delta_color="inverse")
m3.metric(L['m3'], f"{jitter:.2f} ms")
m4.metric(L['m4'], f"{sla:.1f}%")

st.divider()

c_diag, c_map = st.columns([1.2, 1])
with c_diag:
    st.subheader(f"📊 {L['diag_title']}")
    fig = px.area(df_raw, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    csv_data = generate_csv_report(df_raw, sys_hash, display_id, lang_pack['English']['team_name'])
    st.download_button(f"📥 {L['export_btn']}", csv_data, f"KSR_Audit_{display_id}.csv", "text/csv")

with c_map:
    st.subheader(f"🗺️ {L['map_title']}")
    if global_devices:
        map_df = pd.DataFrame([
            {"lat": v.get('lat', 25.03), "lon": v.get('lon', 121.56), "name": v.get('name', 'Unknown')} 
            for v in global_devices.values()
        ])
        st.map(map_df, zoom=1)

st.divider()
st.subheader(f"📋 {L['list_title']}")

# 🔥 核心修改 3：表格欄位強制對應國家
st.table(pd.DataFrame([
    {
        L['unit_name']: v['name'], 
        L['location']: v['country'], # 這裡絕對只會出現國家
        L['last_seen']: v['last']
    } for v in global_devices.values()
]))

st.markdown(f'<div class="ksr-footer">DEVELOPED BY {lang_pack["English"]["team_name"].upper()} &copy; 2026. ALL RIGHTS RESERVED.</div>', unsafe_allow_html=True)
