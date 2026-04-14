# styles.py
import streamlit as st

def apply_ksr_styles():
    st.markdown("""
        <style>
            /* 1. 隱藏官方 footer */
            footer {visibility: hidden !important;} 

            /* 2. [手術刀方案] 只隱藏 header 的右半部內容 */
            /* 針對 header 內部的右側工具欄區塊進行封殺 */
            div[data-testid="stHeaderActionElements"],
            .stAppDeployButton,
            div[data-testid="stStatusWidget"] {
                display: none !important;
            }

            /* 3. 強制確保左側側邊欄按鈕的可見度與樣式 */
            button[data-testid="stSidebarCollapseButton"] {
                color: #00f2ff !important;
                background-color: rgba(0, 242, 255, 0.1) !important;
                border: 1px solid rgba(0, 242, 255, 0.3) !important;
                visibility: visible !important;
                display: flex !important;
            }

            /* 4. 專業 Metrics 視覺設定 (保持一致) */
            [data-testid="stMetricValue"] { 
                font-size: 52px !important; 
                font-weight: 800 !important; 
                color: #00f2ff !important; 
                font-family: 'JetBrains Mono', monospace !important; 
            }
            [data-testid="stMetricLabel"] { 
                font-size: 14px !important; 
                color: #A1AAB5 !important; 
            }
            [data-testid="stMetric"] { 
                background-color: #161B22 !important; 
                border: 1px solid #30363D !important; 
                padding: 20px !important; 
                border-radius: 10px !important; 
            }
            
            .block-container { padding-top: 3rem; }
            .ksr-footer {
                text-align: center; color: #30363D; font-size: 11px; padding: 25px;
            }
        </style>
    """, unsafe_allow_html=True)
