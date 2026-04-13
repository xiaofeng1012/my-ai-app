import streamlit as st
import pandas as pd
import time
import requests
import plotly.express as px
import random
import hashlib
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. 頁面設定 (政府級專案標準：寬螢幕佈局) ---
st.set_page_config(page_title="國家級通訊品質監測系統", layout="wide")

# --- 2. 全域資源共享 (核心後端) ---
@st.cache_resource
def get_global_data():
    return {} 

global_devices = get_global_data()

# 自動刷新 (設定 3 秒，兼顧即時性與伺服器負載)
st_autorefresh(interval=3000, key="data_refresh")

# --- 3. 獲取連入者資訊與地理位置 ---
headers = st.context.headers
user_agent = headers.get("User-Agent", "Unknown")
ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]

@st.cache_data(ttl=3600)
def get_location(ip_addr):
    try:
        # 使用 IP-API 進行地理追蹤
        response = requests.get(f"http://ip-api.com/json/{ip_addr}", timeout=5).json()
        if response['status'] == 'success':
            return response
    except:
        pass
    return None

loc = get_location(ip)

# --- 4. 裝置識別與數據初始化 ---
if "iPhone" in user_agent:
    icon, dev_type = "🍎", "iPhone"
elif "Windows" in user_agent:
    icon, dev_type = "💻", "Windows PC"
elif "Android" in user_agent:
    icon, dev_type = "🤖", "Android"
else:
    icon, dev_type = "🌐", "Unknown Device"

if 'history' not in st.session_state:
    st.session_state.history = []
if 'my_sid' not in st.session_state:
    st.session_state.my_sid = f"{dev_type}_{ip}"

# 【資安脫敏】生成匿名顯示 ID，不洩漏 IP
my_id = st.session_state.my_sid
display_id = f"{dev_type}_{hashlib.md5(my_id.encode()).hexdigest()[:5]}"

# 數據採樣 (模擬 RTT 延遲)
current_ping = random.randint(20, 65) # 稍微擴大範圍以測試告警
st.session_state.history.append(current_ping)
if len(st.session_state.history) > 30: 
    st.session_state.history.pop(0)

# --- 5. 通訊專業指標計算 (SLA/Jitter) ---
history_arr = np.array(st.session_state.history)
avg_ping = np.mean(history_arr)
# Jitter 計算：相鄰封包延遲差的平均值 (通訊系核心指標)
jitter = np.mean(np.abs(np.diff(history_arr))) if len(history_arr) > 1 else 0
# 可靠度：延遲小於 100ms 的比例
reliability = (sum(1 for p in history_arr if p < 100) / len(history_arr)) * 100

# 更新全域字典
global_devices[my_id] = {
    "icon": icon,
    "display_name": display_id,
    "lat": loc['lat'] if loc else 25.03,
    "lon": loc['lon'] if loc else 121.56,
    "city": loc['city'] if loc else "Taipei",
    "last_seen": datetime.now().strftime("%H:%M:%S"),
    "timestamp": time.time()
}

# 清理超時連線 (15秒斷開)
curr_t = time.time()
for sid in list(global_devices.keys()):
    if curr_t - global_devices[sid]["timestamp"] > 15:
        del global_devices[sid]

# --- 6. UI 介面呈現 ---
st.title("🏛️ 國家級通訊品質監測中心 (V4.0)")

# 側邊欄：稽核與報告
with st.sidebar:
    st.header("📋 系統審計報告")
    st.metric("今日平均可靠度", f"{reliability:.1f}%")
    st.write(f"⏱️ 監測頻率: 3000ms")
    st.write(f"🌐 節點位置: {loc['city'] if loc else '自動定位'}")
    st.divider()
    df_export = pd.DataFrame(st.session_state.history, columns=['Latency_ms'])
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📥 下載正式監測報告 (CSV)", csv, f"Report_{display_id}.csv", "text/csv")

# 第一列：KPI 儀表板
c1, c2, c3, c4 = st.columns(4)
c1.metric("在線監測裝置", f"{len(global_devices)} Units")
c2.metric("即時延遲 (RTT)", f"{current_ping} ms")
c3.metric("網路抖動 (Jitter)", f"{jitter:.2f} ms")
c4.metric("封包成功率", "100%")

# 【告警系統】檢查關鍵指標並發出警告
if current_ping > 60:
    st.error(f"⚠️ 嚴重警告：偵測到鏈路延遲異常 ({current_ping}ms)，可能影響即時通訊品質！")
elif jitter > 10:
    st.warning(f"⚠️ 性能預警：網路抖動過高 ({jitter:.2f}ms)，建議檢查物理層干擾。")

st.divider()

# 第二列：深度分析與地圖
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📈 鏈路效能時域分析")
    with st.container(border=True):
        df_analysis = pd.DataFrame({
            "採樣點": range(len(st.session_state.history)),
            "延遲 (ms)": st.session_state.history
        })
        fig = px.area(df_analysis, x="採樣點", y="延遲 (ms)", 
                     title="訊號波動趨勢 (SLA Tracking)", template="plotly_dark")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # 匿名名單 (只顯示 Name 和 Seen)
        with st.expander("🔍 查看目前所有匿名在線名單"):
            list_data = []
            for sid, info in global_devices.items():
                list_data.append({
                    "裝置名稱": info['display_name'],
                    "最後活動": info['last_seen']
                })
            st.table(pd.DataFrame(list_data))

with col_right:
    st.subheader("🗺️ 全球地理位置監測")
    if global_devices:
        map_data = pd.DataFrame([
            {"lat": v['lat'], "lon": v['lon'], "name": v['display_name']} 
            for v in global_devices.values()
        ])
        st.map(map_data, zoom=1)

st.divider()

# 第三列：AI 診斷引擎
st.subheader("🧠 專家診斷系統建議")
if reliability > 95 and jitter < 5:
    st.info("💡 系統評估：當前鏈路符合 Tier-1 電信級標準，適合執行關鍵任務。")
else:
    st.write("💡 系統建議：偵測到環境微幅變動，請持續觀測抖動值變化。")
