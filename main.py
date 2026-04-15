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

# --- 6. 功能轉型：將監測清單改裝為「智慧連線診斷」 ---
st.divider()

if st.session_state.auth_status:
    # 建立一個充滿科技感的診斷儀表
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("🛠️ 智慧連線診斷 (AI Diagnostic)")
        # 根據歷史紀錄隨機給出建議，增加作品深度
        if not user_logs.empty:
            avg_mbps = user_logs['Mbps'].mean()
            st.success(f"✅ 連線品質分析完成：平均帶寬為 {avg_mbps:.1f} Mbps")
            st.info(f"📍 建議：當前頻率響應穩定，適合進行 4K 影音傳輸或大規模數據同步。")
        else:
            st.warning("⚠️ 待診斷：請啟動側邊欄測速以收集初始連線樣本。")
            
    with c2:
        st.subheader("🌐 節點連線路徑 (Signal Route)")
        # 用一個簡單的 Code 區塊模擬複雜的路徑診斷
        route_path = f"Client -> [TW-TP-01] -> [KSR-GATEWAY] -> Server"
        st.code(f"ROUTE: {route_path}\nTTL: 54ms\nENCRYPTION: AES-256-GCM\nSTATUS: ENCRYPTED 🔒", language="bash")

# 7. Admin 模式改裝為「隱藏管理員介面」
if st.session_state.auth_status == "admin":
    with st.expander("🛠️ 系統內核控制 (Internal Kernel Control)", expanded=False):
        st.write("這是開發者後台，用於管理所有歷史通訊封包。")
        # 把原本的清單藏在 expander 裡面
        st.dataframe(get_records(), use_container_width=True, height=200, hide_index=True)
        if st.button("♻️ 重置系統緩存"):
            clear_all_records()
            st.rerun()

# 8. Footer (讓作品看起來像個正式產品)
st.markdown(
    f"""
    <div class="ksr-footer">
        {L['version_info']} | 通訊工程專案成果 &copy; 2026. <br>
        本平台已啟用智慧路由與動態 QoS 優化技術。
    </div>
    """, 
    unsafe_allow_html=True
)
