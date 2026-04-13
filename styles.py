import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
            /* ... 複製原本的所有 CSS 內容 ... */
            .ksr-footer { text-align: center; color: #30363D; font-size: 12px; padding: 20px; }
        </style>
    """, unsafe_allow_html=True)