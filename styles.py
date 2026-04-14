# styles.py
import streamlit as st

def apply_ksr_styles():
    st.markdown("""
        <style>
            /* =========================================
               🚀 [重磅修正] 徹底封殺右上角所有 Streamlit 元素
               ========================================= */

            /* 1. 隱藏底部 footer */
            footer {visibility: hidden !important; display: none !important;} 

            /* 2. [地毯式轟炸] 針對右上角所有工具欄、帳號、選單容器 */
            /* 這些是 2026 年常見的 Streamlit 右上角容器選擇器 */
            div[data-testid="stStatusWidget"],
            .stAppDeployButton,
            header[data-testid="stHeader"] > div:nth-child(2), /* 右側容器 */
            div[class^="st-emotion-cache"] > button[id^="text_input_"], /* 某些帳號按鈕 */
            #MainMenu,
            div[data-testid="stToolbar"] {
                visibility: hidden !important;
                display: none !important;
                opacity: 0 !important;
                pointer-events: none !important; /* 確保點不到 */
                width: 0 !important;
                height: 0 !important;
            }

            /* 3. [死守] 強制保留並美化左上角控制中心開關 (Sidebar Toggle) */
            /* 這是我們唯一的活口，必須用最高優先權(!)保護 */
            header[data-testid="stHeader"] button[data-testid="stSidebarCollapseButton"] {
                color: #00f2ff !important;
                background-color: rgba(0, 242, 255, 0.15) !important;
                border: 1px solid rgba(0, 242, 255, 0.4) !important;
                visibility: visible !important; /* 強制可見 */
                display: flex !important; /* 強制顯示 */
                opacity: 1 !important;
                pointer-events: auto !important;
                position: absolute !important;
                left: 10px !important;
                top: 10px !important;
                z-index: 999999 !important; /* 確保在最上層 */
            }
            
            /* 讓透明的 Header 不要擋到主畫面 */
            header[data-testid="stHeader"] {
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                pointer-events: none !important; /* 讓 Header 本身不擋點擊 */
            }
            /* 但要讓 Header 內的按鈕可以點擊 */
            header[data-testid="stHeader"] * {
                pointer-events: auto;
            }

            /* =========================================
               🎨 工業級大字體 Metrics 設定 (保持不變)
               ========================================= */
            [data-testid="stMetricValue"] { 
                font-size: 52px !important; 
                font-weight: 800 !important; 
                color: #00f2ff !important; 
                font-family: 'JetBrains Mono', monospace !important; 
            }
            [data-testid="stMetricLabel"] { 
                font-size: 14px !important; 
                letter-spacing: 1px !important; 
                text-transform: uppercase !important; 
                color: #A1AAB5 !important; 
            }
            [data-testid="stMetric"] { 
                background-color: #161B22 !important; 
                border: 1px solid #30363D !important; 
                padding: 20px !important; 
                border-radius: 10px !important; 
            }
            
            .block-container { padding-top: 4rem; }
            .ksr-footer {
                text-align: center; color: #30363D; font-size: 11px; padding: 25px; letter-spacing: 1px;
            }
        </style>
    """, unsafe_allow_html=True)
