# auth.py
import streamlit as st
from datetime import datetime

def init_auth_state():
    """初始化權限相關的 Session 狀態"""
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False

def admin_login_listener():
    """注入 JavaScript 監聽 Shift + A 快捷鍵"""
    st.components.v1.html(
        """
        <script>
        var doc = window.parent.document;
        doc.addEventListener('keydown', function(e) {
            // 監聽 Shift + A
            if (e.shiftKey && e.key === 'A') {
                window.parent.postMessage({
                    type: 'streamlit:set_login',
                    value: true
                }, '*');
            }
        });
        </script>
        """,
        height=0,
    )
    # 這裡預留給未來擴充更複雜的 JS 通訊邏輯

def render_login_ui():
    """渲染管理員登入介面"""
    if st.session_state.show_login and not st.session_state.is_admin:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.warning("🔐 **管理員模式驗證** (Admin Verification)")
            user = st.text_input("Username", placeholder="請輸入帳號", key="admin_user")
            pw = st.text_input("Password", type="password", placeholder="請輸入密碼", key="admin_pw")
            
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("✅ 登入 (Login)", use_container_width=True):
                if user == "Admin" and pw == "2812":
                    st.session_state.is_admin = True
                    st.session_state.show_login = False
                    st.success("驗證成功，權限已開啟")
                    st.rerun()
                else:
                    st.error("帳號或密碼錯誤！")
            
            if btn_col2.button("❌ 關閉 (Close)", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()
        st.markdown("---")

def check_admin_access():
    """簡單的權限檢查工具"""
    return st.session_state.is_admin
