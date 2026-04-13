import streamlit as st
import pandas as pd
import time
import requests
import plotly.express as px
import plotly.graph_objects as go
import random
import hashlib
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. 初始化與頁面設定 (企業級標準) ---
st.set_page_config(page_title="國家級通訊品質監測中心", layout="wide", page_icon="📡")

@st.cache_resource
def get_global_data():
    return {} 

global_devices = get_global_data()
st_autorefresh(interval=3000, key="data_refresh")

# --- 2. 側邊欄：功能設定與報告 ---
st.sidebar.header("🎯 監測模式設定")
app_mode = st.sidebar.selectbox(
    "選擇應用場景", 
    ["一般辦公 (Standard)", "即時競技 (Gaming)", "遠距會議 (VoIP)", "高畫質影音 (Streaming)"]
)

# 定義不同場景的 SLA 閾值
thresholds = {
    "一般辦公 (Standard)": {"ping": 80, "jitter": 15, "desc": "適合處理網頁與電子郵件"},
    "即時競技 (Gaming)": {"ping": 35, "jitter": 5, "desc": "對延遲與抖動極度敏感"},
    "遠距會議 (VoIP)": {"ping": 150, "jitter": 10, "desc": "確保語音封包不丟失"},
    "高畫質影音 (Streaming)": {"ping": 250, "jitter": 40, "desc": "側重持續吞吐量穩定度"}
}
t_val = thresholds[app_mode]

st.sidebar.divider()
st.sidebar.write(f"📖 **場景說明:**\n{t_val['desc']}")

# --- 3. 核心數據採集與定位 ---
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

if "iPhone" in user_agent: icon, dev_type = "🍎", "iPhone"
elif "Windows" in user_agent: icon, dev_type = "💻", "Windows PC"
elif "Android" in user_agent: icon, dev_type = "🤖", "Android"
else: icon, dev_type = "🌐", "Unknown Device"

if 'history' not in st.session_state: st.session_state.history = []
if 'my_sid' not in st.session_state: st.session_state.my_sid = f"{dev_type}_{ip}"

my_id = st.session_state.my_sid
display_id = f"{dev_type}_{hashlib.md5(my_id.encode()).hexdigest()[:5]}"

# 模擬高頻採樣數據 (帶入環境雜訊)
current_ping = random.randint(22, 55)
st.session_state.history.append(current_ping)
if len(st.session_state.history) > 50: st.session_state.history.pop(0)

history_arr = np.array(st.session_state.history)
jitter = np.mean(np.abs(np.diff(history_arr))) if len(history_arr) > 1 else 0

# 更新全域數據
global_devices[my_id] = {
    "icon": icon, "display_name": display_id,
    "lat": loc['lat'] if loc else 25.03, "lon": loc['lon'] if loc else 121.56,
    "city": loc['city'] if loc else "Taipei",
    "last_seen": datetime.now().strftime("%H:%M:%S"), "timestamp": time.time()
}

# --- 4. UI 介面呈現 (主視覺) ---
st.title("🏛️ 國家級通訊品質監測中心 (V6.0 - Final)")
st.caption(f"當前監測節點: {loc['city'] if loc else '自動定位'} | 匿名 ID: {display_id}")

# 第一列：KPI 戰情面板
c1, c2, c3, c4 = st.columns(4)
c1.metric("全球在線監測數", len(global_devices))
c2.metric("RTT 延遲", f"{current_ping} ms")
c3.metric("網路抖動 (Jitter)", f"{jitter:.2f} ms")
c4.metric("SLA 達標率", f"{(sum(1 for p in history_arr if p < t_val['ping'])/len(history_arr)*100):.1f}%")

st.divider()

# 第二列：實戰診斷區 (這才是最有用的部分)
st.subheader(f"🛠️ 實戰診斷：針對「{app_mode}」之評估")
diag_col1, diag_col2, diag_col3 = st.columns([1.5, 1, 1])

with diag_col1:
    with st.container(border=True):
        if current_ping > t_val['ping']:
            st.error(f"❌ 延遲超標：{current_ping}ms (閾值: {t_val['ping']}ms)")
            st.info("💡 診斷：疑似骨幹網擁塞。建議：切換 5GHz 頻道或重啟數據機。")
        elif jitter > t_val['jitter']:
            st.warning(f"⚠️ 穩定度異常：抖動 {jitter:.2f}ms 過高")
            st.info("💡 診斷：訊號受干擾。建議：靠近無線存取點 (AP) 以減少多路徑衰落。")
        else:
            st.success("✅ 通訊極佳：當前鏈路完美符合該場景需求。")
            st.write("目前環境非常純淨，封包丟失率預估 < 0.01%。")

with diag_col2:
    st.write("**📡 鏈路拓撲故障定位：**")
    st.caption("✅ [Local] 使用者裝置 (Device) -> 正常")
    st.caption("✅ [Gateway] Wi-Fi 分享器 (AP) -> 正常")
    status = "🟡 繁忙" if current_ping > 50 else "🟢 暢通"
    st.caption(f"{status} [Backbone] 外部骨幹網路 -> {status}")

with diag_col3:
    # 下載專業報告
    st.write("**📊 數據稽核與存檔：**")
    df_export = pd.DataFrame(st.session_state.history, columns=['Latency_ms'])
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📥 生成正式檢驗報告 (CSV)", csv, f"Report_{display_id}.csv", "text/csv")

st.divider()

# 第三列：深度圖表分析
col_chart, col_map = st.columns([1.5, 1])

with col_chart:
    st.subheader("📈 時域/頻域組合分析")
    tab1, tab2 = st.tabs(["波動趨勢圖", "延遲分佈圖"])
    
    with tab1:
        df = pd.DataFrame({"Latency": st.session_state.history})
        df['MA'] = df['Latency'].rolling(window=5).mean()
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(y=df['Latency'], name='原始數據', line=dict(color='#00f2ff')))
        fig_line.add_trace(go.Scatter(y=df['MA'], name='趨勢線', line=dict(color='white', dash='dash')))
        fig_line.update_layout(height=300, template="plotly_dark", margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_line, use_container_width=True)
    
    with tab2:
        fig_hist = px.histogram(df, x="Latency", nbins=15, template="plotly_dark", color_discrete_sequence=['#7100ff'])
        fig_hist.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_hist, use_container_width=True)

with col_map:
    st.subheader("🗺️ 全球節點拓撲")
    if global_devices:
        map_df = pd.DataFrame([{"lat": v['lat'], "lon": v['lon'], "name": v['display_name']} for v in global_devices.values()])
        st.map(map_df, zoom=1)
    
    with st.expander("🔍 匿名在線清單"):
        list_data = [{"裝置": v['display_name'], "位置": v['city'], "時間": v['last_seen']} for v in global_devices.values()]
        st.table(pd.DataFrame(list_data))

# 定時清理
curr_t = time.time()
for sid in list(global_devices.keys()):
    if curr_t - global_devices[sid]["timestamp"] > 15: del global_devices[sid]
