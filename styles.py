# styles.py
import streamlit as st

def apply_ksr_styles():
    st.markdown("""
        <style>
            /* 1. 隱藏底部 Made with Streamlit */
            footer {visibility: hidden;} 

            /* 2. 精準隱藏右上角選單 (三條線) 與帳號資訊 */
            /* 我們不再針對整個 header，而是針對右側的容器 */
            div[data-testid="stStatusWidget"] {display: none;}
            #MainMenu {visibility: hidden;}
            
            /* 針對右上角所有的按鈕組件（包含 Deploy 和帳號選單）進行封殺 */
            .stAppDeployButton {display: none !important;}
            [data-testid="stAppViewBlockContainer"] header { background: transparent; }
            
            /* 3. 強制保留並美化左上角的控制中心開關 (Sidebar Toggle) */
            /* 確保左邊的按鈕是可見且具備「卡式如」品牌色的 */
            button[data-testid="stSidebarCollapseButton"] {
                color: #00f2ff !important;
                background-color: rgba(0, 242, 255, 0.1) !important;
                border: 1px solid rgba(0, 242, 255, 0.3) !important;
                visibility: visible !important; /* 強制可見 */
                display: flex !important;
            }

            /* 4. 工業級大字體 Metrics 設定 */
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
