import streamlit as st
import base64
import os

def get_base64_image(file_path):
    """Safely loads an image file and converts it to a base64 string for HTML embedding."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def inject_command_center_theme():
    """Injects custom CSS to strictly replicate the Knife & Ember Command Center theme."""
    st.markdown("""
        <style>
        /* Base Background with Radial Red Glow */
        .stApp {
            background: radial-gradient(circle at 50% 15%, #3a0a0a 0%, #0d0808 40%, #050303 100%) !important;
            color: #ffffff !important;
            font-family: 'Segoe UI', Arial, sans-serif !important;
        }

        /* Hide Top Header & Adjust Padding to Center Content */
        header {visibility: hidden;}
        .main .block-container {
            max-width: 360px !important;
            padding-top: 8vh !important;
        }

        /* Logo Styling & Enhanced Glow */
        .logo-container {
            text-align: center;
            margin-bottom: 20px;
        }
        .logo-container img {
            width: 200px;
            filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.7));
        }

        /* Typography: Headers */
        .cc-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .cc-title {
            font-family: 'Times New Roman', Times, serif;
            font-size: 22px;
            font-weight: bold;
            color: #ffffff;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }
        .cc-subtitle {
            color: #a82828;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        /* Form Card Container */
        div[data-testid="stForm"] {
            background-color: #121316 !important;
            border: 1px solid #1f2128 !important;
            border-radius: 8px !important;
            padding: 25px !important;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.9) !important;
        }

        /* The Red Role Tab (Replaces Kitchen Terminal toggle) */
        .role-tab {
            background-color: #901619;
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            text-align: center;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 25px;
            border: 1px solid #aa1d20;
            box-shadow: inset 0 2px 4px rgba(255,255,255,0.1);
        }

        /* Text Input Labels */
        .stTextInput label p {
            color: #8c92a4 !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            margin-bottom: 2px !important;
        }

        /* Text Input Fields */
        .stTextInput input {
            background-color: #1a1c23 !important;
            color: #ffffff !important;
            border: 1px solid #282b36 !important;
            border-radius: 6px !important;
            padding: 12px 15px !important;
        }
        .stTextInput input:focus {
            border-color: #901619 !important;
            box-shadow: 0 0 0 1px #901619 !important;
        }

        /* Submit Button (Targeted strictly to avoid the password eye icon) */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #901619 !important;
            border: 1px solid #aa1d20 !important;
            color: #ffffff !important;
            padding: 15px !important;
            border-radius: 6px !important;
            margin-top: 10px !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
        }
        div[data-testid="stFormSubmitButton"] > button p {
            font-weight: 700 !important;
            font-size: 14px !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            color: #ffffff !important;
        }
        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #b82327 !important;
            border-color: #b82327 !important;
            box-shadow: 0 4px 15px rgba(154, 27, 30, 0.4) !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_login_screen(registered_users):
    """Renders the dark Knife & Ember login screen."""
    inject_command_center_theme()

    # Logo Setup - Updated to logo_1.png
    logo_path = "logo_1.png"
    logo_base64 = get_base64_image(logo_path)
    
    if logo_base64:
        st.markdown(f"""
            <div class="logo-container">
                <img src="data:image/png;base64,{logo_base64}" alt="Logo">
            </div>
        """, unsafe_allow_html=True)

    # Headers
    st.markdown("""
        <div class="cc-header">
            <div class="cc-title">KNIFE & EMBER COMMAND CENTER</div>
            <div class="cc-subtitle">Food Safety Surveillance Suite</div>
        </div>
    """, unsafe_allow_html=True)

    # Login Form
    with st.form("login_form", clear_on_submit=False):
        # Fake "Tab" for the FSCO Role
        st.markdown('<div class="role-tab">Food Safety Compliance Officer</div>', unsafe_allow_html=True)

        username_input = st.text_input("Username", placeholder="Enter your assigned username").strip().lower()
        password_input = st.text_input("Password", type="password", placeholder="Enter access password")

        # use_container_width=True forces it to stretch 100% across.
        submit_button = st.form_submit_button("Sign In As FSCO", use_container_width=True)

        if submit_button:
            if not username_input or not password_input:
                st.error("Please enter both username and password.")
            elif username_input in registered_users and registered_users[username_input].get("password") == password_input:
                user_data = registered_users[username_input]
                st.session_state.logged_in = True
                st.session_state.user_role = user_data.get("role", "auditor")
                st.session_state.user_full_name = user_data.get("full_name", username_input.title())
                st.session_state.assigned_concepts = user_data.get("assigned_concepts", ["ALL"])
                st.rerun()
            else:
                st.error("Invalid credentials.")