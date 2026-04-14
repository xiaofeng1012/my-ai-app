# main.py
import streamlit as st
import pandas as pd
import requests
import random
import hashlib
import time
import numpy as np
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 匯入自定義模組
from language_pack import lang_pack
from styles import apply_ksr_styles
from components import render_speed_test_ui
from utils import generate_csv_report

# --- 1. 系統初始化 (符合 2026 規範) ---
st.set_page_config(
    page_title="卡式如通訊品質監測平台", 
    layout="wide", 
    page_icon="📡"
)

# 套用客製化 CSS (含手機版選單修復)
apply_ksr_styles()

# 設定自動刷新 (3秒)
st_autorefresh(interval=3000, key="data_refresh")

# 初始化 session state
if 'history' not in st.session_state: 
    st.session_state.history = [{"time": datetime.now().strftime("%H:%M:%S"), "ms": 30}]

@st.cache_resource
def get_global_data(): return {} 
global_devices = get_global_data()

# --- 2. 側邊欄控制中心 (排版優化) ---
with st.sidebar:
    st.title("🌐 Language Selection")
    sel_lang = st.selectbox("Language", ["繁體中文", "English"], label_visibility="collapsed")
    L = lang_pack[sel_lang]

    st.sidebar.divider()
    st.sidebar.title(f"🛡️ {L['control_center']}")

    # A. 監測場景選擇 (放在控制中心頂部)
    app_mode = st.selectbox(L['sla_mode'], L['modes'])

    st.sidebar.divider()

    # B. 即時效能測試 (放在監測場景下方)
    st.sidebar.subheader(f"🚀 {L['speed_test']}")
    # 調用 components.py 內的 st.iframe 測速組件
    render_speed_test_ui(L)

    st.sidebar.divider()
    st.sidebar.markdown(f"**Designed by {L['team_name']}**")
    st.sidebar.caption("Version 8.7.0-LTS | KSR NOC")


# --- 3. Telemetry 數據處理邏輯 (抓取即時時間) ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=3600)
def get_loc(ip_addr):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_addr}", timeout=5).json()
        return r if r['status'] == 'success' else None
    except: return None

loc = get_loc(ip)
# 設備類型偵測
if "Windows" in user_agent:
    icon, dev_type = "💻", "Windows"
elif "iPhone" in user_agent:
    icon, dev_type = "🍎", "iPhone"
else:
    icon, dev_type = "📱", "Mobile"

# 生成唯一識別碼與系統 Hash
display_id = f"{dev_type}_{hashlib.md5(f'{dev_type}_{ip}'.encode()).hexdigest()[:5]}"
sys_hash = hashlib.sha1(display_id.encode()).hexdigest()[:12].upper()

# 抓取「當下即時」的時間
current_now = datetime.now().strftime("%H:%M:%S")

# 模擬/更新即時延遲數據
curr_p = random.randint(22, 55)
st.session_state.history.append({"time": current_now, "ms": curr_p})
if len(st.session_state.history) > 40: st.session_state.history.pop(0)

df_raw = pd.DataFrame(st.session_state.history)

# 指標計算
jitter = np.mean(np.abs(np.diff(df_raw['ms']))) if len(df_raw) > 1 else 0
sla = (sum(1 for p in df_raw['ms'] if p < 60)/len(df_raw)*100)

# 更新全域節點清單 (寫入即時時間)
global_devices[display_id] = {
    "name": display_id, 
    "city": loc['city'] if loc else "Unknown", 
    "lat": loc['lat'] if loc else 25.03, 
    "lon": loc['lon'] if loc else 121.56,
    "last": current_now,  # 同步即時時間
    "ts": time.time()     # 用於後台清理判斷
}

# --- 4. Dashboard 主介面渲染 ---
st.title(f"📡 {L['title']}")
st.markdown(f"**{L['audit_hash']}:** `{sys_hash}` | **{L['node']}:** `{loc['city'] if loc else 'Detecting...'}`")

# 頂部核心指標卡片
m1, m2, m3, m4 = st.columns(4)
m1.metric(L['m1'], f"{len(global_devices)} Units")
m2.metric(L['m2'], f"{curr_p} ms", delta=f"{curr_p - df_raw['ms'].iloc[-2] if len(df_raw)>1 else 0} ms", delta_color="inverse")
m3.metric(L['m3'], f"{jitter:.2f} ms")
m4.metric(L['m4'], f"{sla:.1f}%")

st.divider()

# 中層：圖表與地圖
c_diag, c_map = st.columns([1.2, 1])
with c_diag:
    st.subheader(f"📊 {L['diag_title']}")
    fig = px.area(df_raw, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
    
    # 符合 2026 規範：使用 width='stretch'
    st.plotly_chart(fig, width='stretch')
    
    # 導出 CSV 報告 (內含英文團隊名標註)
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

# 下層：動態節點清單
st.divider()
st.subheader(f"📋 {L['list_title']}")
# 使用大表格展示即時活動紀錄
st.table(pd.DataFrame([{L['unit_name']: v['name'], L['location']: v['city'], L['last_seen']: v['last']} for v in global_devices.values()]))

# 底部版權宣告 (卡式如團隊著名)
st.markdown(f'<div class="ksr-footer">DEVELOPED BY {lang_pack["English"]["team_name"].upper()} &copy; 2026. ALL RIGHTS RESERVED.</div>', unsafe_allow_html=True)

# 節點清理邏輯 (15秒無跳動即視為離線)
ct = time.time()
for sid in list(global_devices.keys()):
    if ct - global_devices[sid]["ts"] > 15: del global_devices[sid]
