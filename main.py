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

# 設定每秒刷新 (1000ms)，確保側邊欄時鐘與離線判定精確
st_autorefresh(interval=1000, key="data_refresh_1s")

# 初始化 session state
if 'history' not in st.session_state: 
    st.session_state.history = [{"time": datetime.now(tw_tz).strftime("%H:%M:%S"), "ms": 30}]

# 初始化本次連線進入時間
if 'session_start_time' not in st.session_state:
    st.session_state.session_start_time = datetime.now(tw_tz).strftime("%H:%M:%S")

@st.cache_resource
def get_global_data(): return {} 
global_devices = get_global_data()

# --- 2. 側邊欄控制中心 (內建即時時鐘) ---
with st.sidebar:
    # 數位時鐘：提供系統運作的動態視覺感
    st.markdown(f"""
        <div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; border-left: 5px solid #00f2ff; margin-bottom: 20px;">
            <p style="margin:0; color: #8b949e; font-size: 0.75rem; letter-spacing: 1px;">SYSTEM REAL-TIME (UTC+8)</p>
            <h2 style="margin:0; color: #00f2ff; font-family: 'JetBrains Mono', monospace; font-size: 1.8rem;">
                {datetime.now(tw_tz).strftime("%H:%M:%S")}
            </h2>
        </div>
    """, unsafe_allow_html=True)

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
    st.sidebar.caption("Version 8.9.0-FINAL | KSR NOC")


# --- 3. Telemetry 數據處理 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=86400) # 國家位置一天抓一次，提升效能並避免被 API 封鎖
def get_loc_advanced(ip_addr):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}?lang=en", timeout=3).json()
        if r.get('status') == 'success':
            return {"country": r.get('country'), "lat": r.get('lat'), "lon": r.get('lon')}
    except: pass
    return None

loc_data = get_loc_advanced(ip)
display_country = loc_data.get('country', "Taiwan") if loc_data else "Taiwan"
display_lat = loc_data.get('lat', 25.03) if loc_data else 25.03
display_lon = loc_data.get('lon', 121.56) if loc_data else 121.56

if "Windows" in user_agent:
    icon, dev_type = "💻", "Windows"
elif "iPhone" in user_agent:
    icon, dev_type = "🍎", "iPhone"
else:
    icon, dev_type = "📱", "Mobile"

display_id = f"{dev_type}_{hashlib.md5(f'{dev_type}_{ip}'.encode()).hexdigest()[:5]}"
sys_hash = hashlib.sha1(display_id.encode()).hexdigest()[:12].upper()

# 獲取校準後的台北時間
current_now_str = datetime.now(tw_tz).strftime("%H:%M:%S")

# 模擬延遲數據
curr_p = random.randint(22, 55)
st.session_state.history.append({"time": current_now_str, "ms": curr_p})
if len(st.session_state.history) > 40: st.session_state.history.pop(0)

df_raw = pd.DataFrame(st.session_state.history)
jitter = np.mean(np.abs(np.diff(df_raw['ms']))) if len(df_raw) > 1 else 0
sla = (sum(1 for p in df_raw['ms'] if p < 60)/len(df_raw)*100)

# 🔥 核心狀態機邏輯：離線定格紀錄
if display_id not in global_devices:
    # 首次進入，紀錄起始時間
    global_devices[display_id] = {
        "name": display_id, 
        "country": display_country, 
        "last": current_now_str, 
        "ts": time.time(),
        "status": "Online 🟢"
    }
else:
    # 在線中，僅更新背景心跳戳記 (ts)，不更新顯示字串 (last)
    global_devices[display_id]["ts"] = time.time()
    global_devices[display_id]["status"] = "Online 🟢"

# 離線判定邏輯
ct = time.time()
for sid in list(global_devices.keys()):
    time_diff = ct - global_devices[sid]["ts"]
    
    # 若超過 10 秒沒心跳，標記離線並捕捉離開時間
    if time_diff > 10:
        if global_devices[sid]["status"] == "Online 🟢":
            global_devices[sid]["last"] = datetime.now(tw_tz).strftime("%H:%M:%S")
            global_devices[sid]["status"] = "Offline 🔴"
        
        # 斷線超過 60 秒後徹底移除
        if time_diff > 60:
            del global_devices[sid]

# --- 4. Dashboard 主介面渲染 ---
st.title(f"📡 {L['title']}")
st.markdown(f"**{L['audit_hash']}:** `{sys_hash}` | **{L['node']}:** `{display_country}`")

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

# 渲染智慧列表：在線時時間靜止，離線時顯示最後活動
list_df = []
for v in global_devices.values():
    list_df.append({
        L['unit_name']: v['name'], 
        L['location']: v['country'], 
        "Status": v['status'],
        L['last_seen']: v['last'] 
    })

st.table(pd.DataFrame(list_df))

st.markdown(f'<div class="ksr-footer">DEVELOPED BY {lang_pack["English"]["team_name"].upper()} &copy; 2026. ALL RIGHTS RESERVED.</div>', unsafe_allow_html=True)
