import streamlit as st
import pandas as pd
import time
import requests
import plotly.express as px
import plotly.graph_objects as go
import random
import hashlib
import numpy as np
import io
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. 頁面設定與國家級 UI 美化 ---
st.set_page_config(page_title="國家級通訊品質監測系統", layout="wide", page_icon="📡")

# 自定義 CSS：強化數據卡片視覺質感
st.markdown("""
    <style>
    .stMetric { background-color: #0e1117; padding: 15px; border-radius: 10px; border: 1px solid #31333f; }
    .stAlert { border-radius: 10px; }
    div[data-testid="stExpander"] { border: 1px solid #31333f; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_global_data():
    return {} 

global_devices = get_global_data()

# 採樣頻率：3000ms 為電信級監測之平衡點
st_autorefresh(interval=3000, key="data_refresh")

# --- 2. 側邊欄：場景控管與正式報告導出 ---
st.sidebar.title("🛡️ 系統監測控制中心")
app_mode = st.sidebar.selectbox(
    "監測應用場景 (SLA Mode)", 
    ["一般辦公 (Standard)", "即時競技 (Gaming)", "遠距會議 (VoIP)", "高畫質影音 (Streaming)"]
)

thresholds = {
    "一般辦公 (Standard)": {"ping": 80, "jitter": 15, "color": "#00f2ff"},
    "即時競技 (Gaming)": {"ping": 35, "jitter": 5, "color": "#ff4b4b"},
    "遠距會議 (VoIP)": {"ping": 150, "jitter": 10, "color": "#ffaa00"},
    "高畫質影音 (Streaming)": {"ping": 250, "jitter": 40, "color": "#00ff00"}
}
t_val = thresholds[app_mode]

# --- 3. 通訊核心：數據採樣與地理定位 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=3600)
def get_location(ip_addr):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_addr}", timeout=5).json()
        if response['status'] == 'success': return response
    except: pass
    return None

loc = get_location(ip)

# 裝置指紋辨識
if "iPhone" in user_agent: icon, dev_type = "🍎", "iPhone"
elif "Windows" in user_agent: icon, dev_type = "💻", "Windows PC"
elif "Android" in user_agent: icon, dev_type = "🤖", "Android"
else: icon, dev_type = "🌐", "Unknown Device"

# Session 狀態持久化
if 'history' not in st.session_state: st.session_state.history = []
if 'my_sid' not in st.session_state: st.session_state.my_sid = f"{dev_type}_{ip}"

# 【資安脫敏】使用雜湊加密 ID，保護用戶隱私
my_id = st.session_state.my_sid
display_id = f"{dev_type}_{hashlib.md5(my_id.encode()).hexdigest()[:5]}"

# 模擬即時 RTT 採樣
current_ping = random.randint(22, 58)
st.session_state.history.append({"time": datetime.now().strftime("%H:%M:%S"), "ms": current_ping})
if len(st.session_state.history) > 50: st.session_state.history.pop(0)

df_raw = pd.DataFrame(st.session_state.history)
jitter = np.mean(np.abs(np.diff(df_raw['ms']))) if len(df_raw) > 1 else 0
sla_rate = (sum(1 for p in df_raw['ms'] if p < t_val['ping'])/len(df_raw)*100)

# 更新全局同步字典
global_devices[my_id] = {
    "icon": icon, "display_name": display_id, "lat": loc['lat'] if loc else 25.03, "lon": loc['lon'] if loc else 121.56,
    "city": loc['city'] if loc else "Taipei", "last_seen": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time()
}

# --- 4. 頂部核心指標儀表板 ---
st.title("📡 國家級通訊品質監測平台")
st.markdown(f"**系統編號:** `{hashlib.sha1(display_id.encode()).hexdigest()[:12]}` | **地理節點:** `{loc['city'] if loc else '自動定位中'}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric("全球監測單元", f"{len(global_devices)} Units")
m2.metric("即時延遲 (RTT)", f"{current_ping} ms", 
          delta=f"{current_ping - df_raw['ms'].iloc[-2] if len(df_raw)>1 else 0} ms", delta_color="inverse")
m3.metric("網路抖動 (Jitter)", f"{jitter:.2f} ms")
m4.metric("SLA 達標率", f"{sla_rate:.1f}%")

# 智慧告警引擎
if current_ping > t_val['ping']:
    st.error(f"🚨 **[SLA 嚴重告警]** 當前延遲 ({current_ping}ms) 已超過「{app_mode}」之服務品質標準。")
elif jitter > t_val['jitter']:
    st.warning(f"⚠️ **[性能預警]** 偵測到抖動異常 ({jitter:.2f}ms)，可能導致封包失序。")

st.divider()

# --- 5. 專業深度診斷介面 ---
col_diag, col_map = st.columns([1.2, 1])

with col_diag:
    st.subheader("📈 鏈路效能深度分析")
    tab_line, tab_hist, tab_audit = st.tabs(["📊 波動趨勢", "📉 分佈統計", "🔍 匿名名單"])
    
    with tab_line:
        fig = px.area(df_raw, x="time", y="ms", title=None, template="plotly_dark", color_discrete_sequence=[t_val['color']])
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="Time Sequence", yaxis_title="Latency (ms)")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab_hist:
        fig_h = px.histogram(df_raw, x="ms", nbins=15, template="plotly_dark", color_discrete_sequence=["#ffffff"])
        fig_h.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_h, use_container_width=True)

    with tab_audit:
        list_data = [{"裝置識別碼": v['display_name'], "所在城市": v['city'], "活動時間": v['last_seen']} for v in global_devices.values()]
        st.table(pd.DataFrame(list_data))

with col_map:
    st.subheader("🗺️ 全球節點分佈圖")
    if global_devices:
        map_df = pd.DataFrame([{"lat": v['lat'], "lon": v['lon'], "name": v['display_name']} for v in global_devices.values()])
        st.map(map_df, zoom=1)
    
    st.info(f"💡 **AI 專家診斷:** 當前網路環境對 **{app_mode}** {'完全兼容' if sla_rate > 90 else '存在潛在瓶頸'}。")

# --- 6. 專業級 CSV 稽核報告生成 ---
st.sidebar.divider()
st.sidebar.subheader("📄 數據稽核報告")

def generate_pro_csv():
    output = io.StringIO()
    output.write(f"--- NATIONAL NETWORK AUDIT REPORT ---\n")
    output.write(f"Report Serial, {hashlib.sha1(display_id.encode()).hexdigest()[:10].upper()}\n")
    output.write(f"Subject ID, {display_id}\n")
    output.write(f"Timestamp, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.write(f"SLA Profile, {app_mode}\n")
    output.write(f"Metric, Mean:{df_raw['ms'].mean():.2f}ms | Jitter:{jitter:.2f}ms\n")
    output.write(f"------------------------------------\n\n")
    df_raw.to_csv(output, index=False)
    return output.getvalue()

st.sidebar.download_button(
    label="💾 下載正式監測報告 (CSV)",
    data=generate_pro_csv(),
    file_name=f"Report_{display_id}.csv",
    mime="text/csv"
)

# 清理過期連線
curr_t = time.time()
for sid in list(global_devices.keys()):
    if curr_t - global_devices[sid]["timestamp"] > 15: del global_devices[sid]
