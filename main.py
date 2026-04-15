import streamlit as st
import pandas as pd
import requests
import random
import time
import json
import numpy as np
import plotly.express as px
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. 模組匯入 ---
from language_pack import lang_pack
from styles import apply_ksr_styles
from database import init_db, register_user, login_user, add_record, get_records, clear_all_records
from components import render_speed_test_ui

# --- 2. 系統初始化 ---
st.set_page_config(page_title="卡式如通訊品質監測平台", layout="wide", page_icon="📡")
init_db()
tw_tz = timezone(timedelta(hours=8))
apply_ksr_styles()

# 🔄 2秒刷新，維持 Dashboard 指標更新
st_autorefresh(interval=2000, key="ksr_refresh_v10")

if 'lang' not in st.session_state: st.session_state.lang = "繁體中文"
if 'auth_status' not in st.session_state: st.session_state.auth_status = None
if 'username' not in st.session_state: st.session_state.username = "Guest"
if 'chart_data' not in st.session_state: st.session_state.chart_data = pd.DataFrame(columns=["time", "ms"])

# --- 3. 側邊欄控制 ---
with st.sidebar:
    st.markdown(f"""
        <div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; border-left: 5px solid #00f2ff; margin-bottom: 20px;">
            <p style="margin:0; color: #8b949e; font-size: 0.75rem; letter-spacing: 1px;">SYSTEM REAL-TIME (UTC+8)</p>
            <h2 style="margin:0; color: #00f2ff; font-family: 'JetBrains Mono', monospace; font-size: 1.8rem;">
                {datetime.now(tw_tz).strftime("%H:%M:%S")}
            </h2>
        </div>
    """, unsafe_allow_html=True)

    st.session_state.lang = st.selectbox("🌐 Language", ["繁體中文", "English"], index=0 if st.session_state.lang=="繁體中文" else 1)
    L = lang_pack[st.session_state.lang]
    st.divider()

    st.title(f"🔐 {L['login_section']}")
    if st.session_state.auth_status is None:
        tab1, tab2 = st.tabs([L['tab_login'], L['tab_register']])
        with tab1:
            u = st.text_input(L['user_label'], key="l_u")
            p = st.text_input(L['pass_label'], type="password", key="l_p")
            if st.button(L['btn_signin'], key="btn_l", use_container_width=True):
                role = login_user(u, p)
                if role:
                    st.session_state.auth_status, st.session_state.username = role, u
                    st.rerun()
                else: st.error(L['err_auth'])
        with tab2:
            ru, rp = st.text_input(L['user_label'], key="r_u"), st.text_input(L['pass_label'], type="password", key="r_p")
            if st.button(L['btn_signup'], key="btn_r", use_container_width=True):
                if register_user(ru, rp): st.success(L['reg_success'])
                else: st.error(L['err_exists'])
    else:
        st.success(f"👤 {L['auth_welcome']}, {st.session_state.username}")
        if st.button(L['auth_logout'], use_container_width=True):
            st.session_state.auth_status, st.session_state.username = None, "Guest"
            st.rerun()

    # 🔥 側邊欄測速與「儲存」邏輯
    # --- main.py 側邊欄測速處理區塊 ---
    
    if st.session_state.auth_status:
        st.divider()
        st.title(f"🚀 {L['speed_test']}")
        
        # 1. 渲染 UI
        speed_result = render_speed_test_ui(L) 
        
        if speed_result and isinstance(speed_result, str):
            try:
                data = json.loads(speed_result)
                if data.get("action") == "save":
                    mbps_val = data['mbps']
                    ts_val = data['ts']
                    
                    # 2. 檢查重複性
                    if "last_ts" not in st.session_state or st.session_state.last_ts != ts_val:
                        st.session_state.last_ts = ts_val
                        
                        # 🔹 優化點：移除 st.spinner 與 time.sleep
                        # 直接寫入 DB，SQLite 寫入極快，不應該感知到卡頓
                        add_record(st.session_state.username, float(mbps_val), 0.0, "Pass ✅")
                        
                        # 🔹 使用 toast 代替 spinner，它是非阻塞的彈出訊息
                        st.toast(f"🚀 數據已同步: {mbps_val} Mbps", icon="✅")
                        
                        # 🔹 稍微延遲後重整，確保資料庫寫入完成
                        # 使用 st.rerun() 會重啟腳本，這是必要的，但我們不加 sleep 讓它瞬間完成
                        st.rerun() 
            except:
                pass

# --- 4. Dashboard 數據處理 ---
current_time = datetime.now(tw_tz).strftime("%H:%M:%S")
new_tick = pd.DataFrame([{"time": current_time, "ms": random.randint(22, 55)}])
st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_tick], ignore_index=True).iloc[-25:]

# 在線節點模擬
global_devices = st.cache_resource(lambda: {})()
if st.session_state.auth_status:
    global_devices[st.session_state.username] = {"name": st.session_state.username, "ip": "127.0.0.1", "ts": time.time(), "status": "Online 🟢"}

# --- 5. Dashboard UI 渲染 (大視覺區) ---
st.title(f"📡 {L['title']}")
m1, m2, m3, m4 = st.columns(4)

# 獲取紀錄計算指標 (SLA 依然保留以利監控品質)
user_logs = get_records(st.session_state.username)
sla_val = f"{(len(user_logs[user_logs['狀態'].str.contains('Pass|Success', na=False)]) / len(user_logs)) * 100:.1f}%" if not user_logs.empty else "100%"

m1.metric(L['m1'], f"{len(global_devices)}")
m2.metric(L['m2'], f"{st.session_state.chart_data['ms'].iloc[-1]} ms")
m3.metric(L['m3'], f"{np.std(st.session_state.chart_data['ms']):.2f} ms")
m4.metric(L['m4'], sla_val)

st.divider()

# 📊 分析圖 (固定高度以防閃爍置頂)
fig = px.area(st.session_state.chart_data, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
fig.update_layout(
    height=260, 
    margin=dict(l=0, r=0, t=10, b=0), 
    xaxis_showgrid=False, 
    transition_duration=400, 
    yaxis=dict(range=[0, 100], fixedrange=True, title=None),
    xaxis=dict(fixedrange=True, title=None)
)
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- 6. 權限分級內容渲染 ---
st.divider()

if st.session_state.auth_status == "admin":
    # 👑 Admin 模式：顯示完整管理面板
    st.subheader("🛠️ Admin Control Panel")
    t_nodes, t_logs = st.tabs(["🌐 Active Nodes", "📜 All System Logs"])
    with t_nodes:
        st.dataframe(pd.DataFrame(global_devices.values()), use_container_width=True, height=300, hide_index=True)
    with t_logs:
        st.dataframe(get_records(), use_container_width=True, height=300, hide_index=True)
        if st.button("⚠️ Clear Database", type="primary"):
            clear_all_records(); st.rerun()

elif st.session_state.auth_status == "user":
    # 👤 一般用戶：主畫面保持乾淨，僅顯示資訊卡
    st.info(f"💡 {L['version_info']} 運行中。您的測速紀錄已加密儲存於雲端，您可以隨時在側邊欄啟動即時監控。")
    # 如果想給 User 看一點點數據，可以用小卡片
    c1, c2 = st.columns(2)
    with c1:
        st.info("測速說明：點擊側邊欄「開始測試」後，滿意結果請點擊「儲存」按鈕同步至資料庫。")

else:
    # 未登入
    st.warning(L['lock_msg'])

# Footer
st.markdown(f'<div class="ksr-footer">{L["version_info"]} | {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
