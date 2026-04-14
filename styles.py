# styles.py
import streamlit as st

def apply_ksr_styles():
    st.markdown("""
        <style>
            /* 1. 隱藏最礙眼的官方 Footer */
            footer {visibility: hidden;} 

            /* 2. 隱藏右上角的三條線選單 (MainMenu) */
            #MainMenu {visibility: hidden;}
            
            /* 3. 保留 Header，但讓它變透明，這樣左上角的按鈕就不會被蓋住 */
            header[data-testid="stHeader"] {
                background: transparent !important;
                border: none !important;
            }

            /* 4. 工業級大字體 Metrics 設定 - 這部分最穩定，一定要留著 */
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
            
            /* 調整主畫面間距 */
            .block-container { padding-top: 2rem; }
            
            /* 頁尾版權標註 */
            .ksr-footer {
                text-align: center; color: #30363D; font-size: 11px; padding: 25px; letter-spacing: 1px;
            }
        </style>
    """, unsafe_allow_html=True)
