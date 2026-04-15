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

# 🔄 2秒刷新，兼顧即時性與防止捲軸跳動
st_autorefresh(interval=2000, key="ksr_refresh_final_admin")

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
        st.success(f"👤 {L['auth_welcome']}, {st.session_state.username} ({st.session_state.auth_status})")
        if st.button(L['auth_logout'], use_container_width=True):
            st.session_state.auth_status, st.session_state.username = None, "Guest"
            st.rerun()

    # --- main.py 側邊欄內的測速處理區 ---
    
    if st.session_state.auth_status:
        st.divider()
        st.title(f"🚀 {L['speed_test']}")
        
        # 呼叫我們之前寫好的 render_speed_test_ui (含 JS Loader 那個版本)
        speed_json = render_speed_test_ui(L)
        
        if speed_json:
            try:
                data = json.loads(speed_json)
                # 判斷 JS 是否回傳了完成狀態
                if data.get("status") == "done":
                    mbps_val = data['mbps']
                    ts_val = data['ts']
                    
                    # 檢查是否為重複發送的數據
                    if "last_ts" not in st.session_state or st.session_state.last_ts != ts_val:
                        st.session_state.last_ts = ts_val
                        
                        # 1. 執行資料庫寫入
                        add_record(st.session_state.username, float(mbps_val), 0.0, "Pass ✅")
                        
                        # 2. 顯示成功提示
                        st.toast(f"✅ 已成功存入資料庫: {mbps_val} Mbps")
                        
                        # 3. 關鍵一步：給予極短的緩衝並強制全頁重整
                        # 這樣 get_records 才會被重新執行，清單才會出現最新一筆
                        time.sleep(0.5) 
                        st.rerun() 
            except Exception as e:
                st.error(f"數據同步錯誤: {e}")

# --- 4. Dashboard 數據處理 ---
current_time = datetime.now(tw_tz).strftime("%H:%M:%S")
new_tick = pd.DataFrame([{"time": current_time, "ms": random.randint(22, 55)}])
st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_tick], ignore_index=True).iloc[-25:]

# 在線節點模擬與數據獲取
global_devices = st.cache_resource(lambda: {})()
if st.session_state.auth_status:
    global_devices[st.session_state.username] = {"name": st.session_state.username, "ip": "127.0.0.1", "ts": time.time(), "status": "Online 🟢"}

# --- 5. Dashboard UI 渲染 ---
st.title(f"📡 {L['title']}")
m1, m2, m3, m4 = st.columns(4)

# 獲取紀錄計算 SLA
user_logs = get_records(st.session_state.username)
sla_val = f"{(len(user_logs[user_logs['狀態'].str.contains('Pass|Success', na=False)]) / len(user_logs)) * 100:.1f}%" if not user_logs.empty else "100%"

m1.metric(L['m1'], f"{len(global_devices)}")
m2.metric(L['m2'], f"{st.session_state.chart_data['ms'].iloc[-1]} ms")
m3.metric(L['m3'], f"{np.std(st.session_state.chart_data['ms']):.2f} ms")
m4.metric(L['m4'], sla_val)

st.divider()

# 📊 圖表區 (縮減高度防止置頂問題)
fig = px.area(st.session_state.chart_data, x="time", y="ms", template="plotly_dark", color_discrete_sequence=["#00f2ff"])
fig.update_layout(height=220, margin=dict(l=0, r=0, t=5, b=5), xaxis_showgrid=False, transition_duration=400, yaxis=dict(range=[0, 100], fixedrange=True, title=None))
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- 6. 權限分級內容渲染 (重點修復) ---
st.divider()

if st.session_state.auth_status == "admin":
    # 👑 Admin 模式：Tab 分頁顯示全系統資訊
    st.subheader("🛠️ Admin Control Panel")
    t_nodes, t_logs = st.tabs(["🌐 Active Nodes", "📜 All System Logs"])
    with t_nodes:
        st.dataframe(pd.DataFrame(global_devices.values()), use_container_width=True, height=250, hide_index=True)
    with t_logs:
        full_logs = get_records() # Admin 讀取全部
        st.dataframe(full_logs, use_container_width=True, height=250, hide_index=True)
        if st.button("⚠️ Clear All Database Records", type="primary"):
            clear_all_records(); st.rerun()

elif st.session_state.auth_status == "user":
    # 👤 一般用戶：僅顯示個人紀錄
    st.subheader(f"📜 {L['user_record']}")
    if not user_logs.empty:
        st.dataframe(user_logs, use_container_width=True, height=300, hide_index=True)
    else:
        st.info("💡 目前無紀錄，請啟動測速。")

else:
    st.warning(L['lock_msg'])

# Footer
st.markdown(f'<div class="ksr-footer">{L["version_info"]} | {L["team_name"]} &copy; 2026.</div>', unsafe_allow_html=True)
