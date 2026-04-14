# styles.py
import streamlit as st

def apply_ksr_styles():
    st.markdown("""
        <style>
            /* 1. 徹底去標籤化：隱藏多餘元素，但保留 Sidebar Toggle */
            #MainMenu {visibility: hidden;} 
            footer {visibility: hidden;} 
            
            /* 修正：不要隱藏整個 header，而是隱藏 header 的背景與裝飾線 */
            header[data-testid="stHeader"] {
                background-color: rgba(0,0,0,0) !important;
                border: none !important;
            }
            
            /* 2. 強化側邊欄按鈕（那個箭頭）的可見度 */
            button[kind="headerNoPadding"] {
                color: #00f2ff !important; /* 讓按鈕變青色，顯眼好找 */
                background-color: rgba(0, 242, 255, 0.1) !important;
                border-radius: 50% !important;
                margin: 10px !important;
            }

            /* 隱藏右側工具欄（Deploy按鈕等） */
            div[data-testid="stToolbar"] {visibility: hidden;}
            
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
            
            /* 頁面邊距微調 */
            .block-container { padding-top: 2rem; }
            
            /* 頁尾版權 */
            .ksr-footer {
                text-align: center; color: #30363D; font-size: 11px; padding: 25px; letter-spacing: 1px;
            }
        </style>
    """, unsafe_allow_html=True)
