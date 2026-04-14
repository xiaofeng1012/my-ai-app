# styles.py
import streamlit as st

def apply_ksr_styles():
    st.markdown("""
        <style>
            /* 1. 隱藏官方 footer 與選單，但保留核心佈局 */
            #MainMenu {visibility: hidden;} 
            footer {visibility: hidden;} 
            div[data-testid="stToolbar"] {visibility: hidden;}

            /* 2. 關鍵修正：修復側邊欄按鈕消失的問題 */
            /* 我們不隱藏 header，而是讓它變透明，這樣開啟按鈕才抓得到 */
            header[data-testid="stHeader"] {
                background-color: rgba(0,0,0,0) !important;
                border: none !important;
                height: 3rem !important;
            }

            /* 強化側邊欄開啟按鈕（那個 > 符號）的顏色與寬度 */
            button[kind="headerNoPadding"] {
                color: #00f2ff !important;
                background-color: rgba(0, 242, 255, 0.1) !important;
                border: 1px solid rgba(0, 242, 255, 0.2) !important;
                margin-left: 10px !important;
            }

            /* 3. 工業級大字體 Metrics */
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
            
            /* 4. 修正手機版側邊欄寬度與顯示 */
            @media (max-width: 768px) {
                [data-testid="stSidebar"] {
                    width: 80vw !important;
                }
            }
            
            .block-container { padding-top: 3.5rem; }
            .ksr-footer {
                text-align: center; color: #30363D; font-size: 11px; padding: 25px; letter-spacing: 1px;
            }
        </style>
    """, unsafe_allow_html=True)
