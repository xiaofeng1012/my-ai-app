# auth.py
import streamlit as st
import streamlit.components.v1 as components

def init_auth_state():
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False

def admin_login_listener():
    # 這裡使用更強大的 JS 監聽，並直接修改 Streamlit 的狀態元件
    components.html(
        """
        <script>
        const doc = window.parent.document;
        doc.addEventListener('keydown', function(e) {
            // 監聽 Shift + A
            if (e.shiftKey && e.key === 'A') {
                // 發送一個自定義事件給 Streamlit
                const btn = doc.querySelector('button[kind="secondary"]'); 
                // 這是最後手段：點擊頁面上某個按鈕或觸發狀態
                window.parent.postMessage({type: 'streamlit:set_login', value: true}, '*');
                alert("管理員模式已觸發！請查看頁面。"); // 測試用，成功後可刪除
            }
        });
        </script>
        """,
        height=0,
    )

def render_login_ui():
    # 備援方案：如果快捷鍵真的死掉，我們在頁面最下方放一個極小的隱藏點擊區
    if st.session_state.show_login and not st.session_state.is_admin:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.warning("🔐 **管理員驗證模式**")
            user = st.text_input("Username", key="admin_user_input")
            pw = st.text_input("Password", type="password", key="admin_pw_input")
            
            b1, b2 = st.columns(2)
            if b1.button("✅ Login", use_container_width=True):
                if user == "Admin" and pw == "2812":
                    st.session_state.is_admin = True
                    st.session_state.show_login = False
                    st.rerun()
                else:
                    st.error("密碼錯誤")
            if b2.button("❌ Close", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()
