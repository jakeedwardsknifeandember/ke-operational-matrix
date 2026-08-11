import os
import streamlit as st

def apply_command_center_styles():
    """Injects dark-mode Command Center CSS."""
    st.markdown("""
        <style>
            .stApp { background-color: #0d090a; }
            .block-container {
                max-width: 480px !important;
                padding-top: 5rem !important;
                padding-bottom: 5rem !important;
                margin: 0 auto !important;
            }
            .cmd-header { text-align: center; margin-bottom: 25px; }
            .cmd-title {
                color: #ffffff;
                font-family: 'Times New Roman', Times, serif;
                font-size: 20px;
                font-weight: bold;
                letter-spacing: 2px;
                text-transform: uppercase;
                margin-top: 12px;
                margin-bottom: 2px;
            }
            .cmd-subtitle {
                color: #a81c1c;
                font-family: Arial, sans-serif;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2px;
                text-transform: uppercase;
            }
            div[data-testid="stForm"] {
                background-color: #141113;
                border: 1px solid #282124;
                border-radius: 12px;
                padding: 30px;
            }
            .stButton > button {
                background-color: #9e1b1b !important;
                color: white !important;
                font-weight: bold !important;
                border: none !important;
                border-radius: 6px !important;
                padding: 12px 20px !important;
                text-transform: uppercase !important;
                letter-spacing: 1px !important;
                width: 100% !important;
            }
            .stButton > button:hover { background-color: #bd2121 !important; }
        </style>
    """, unsafe_allow_html=True)

def render_login_screen(registered_users):
    """Renders the centered Command Center Login."""
    apply_command_center_styles()
    
    logo_path = None
    for p_logo in ["logo.png", "logo.jpg", "templates/logo.png", "assets/logo.png"]:
        if os.path.exists(p_logo):
            logo_path = p_logo
            break

    st.markdown('<div class="cmd-header">', unsafe_allow_html=True)
    if logo_path:
        st.image(logo_path, width=75)
    st.markdown('<div class="cmd-title">KNIFE & EMBER COMMAND CENTER</div>', unsafe_allow_html=True)
    st.markdown('<div class="cmd-subtitle">F&B MANAGEMENT PLATFORM</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    with st.form("command_center_login_form"):
        username_input = st.text_input("USERNAME", placeholder="Enter your assigned username", key="login_user_input")
        password_input = st.text_input("PASSWORD", type="password", placeholder="Enter access password", key="login_pass_input")
        
        st.markdown("<br>", unsafe_allow_html=True)
        login_submitted = st.form_submit_button("SIGN IN TO TERMINAL", use_container_width=True)

        if login_submitted:
            user_key = username_input.strip().lower()
            if user_key in registered_users and registered_users[user_key]["password"] == password_input:
                user_info = registered_users[user_key]
                st.session_state.logged_in = True
                st.session_state.user_role = user_info.get("role", "auditor")
                st.session_state.user_full_name = user_info.get("full_name", username_input)
                st.session_state.assigned_concepts = user_info.get("assigned_concepts", ["ALL"])
                st.rerun()
            else:
                st.error("Invalid username or password credentials.")