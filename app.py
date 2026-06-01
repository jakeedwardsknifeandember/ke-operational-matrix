import streamlit as st
import datetime
import pandas as pd
import google.generativeai as genai
import gspread
import os
from fpdf import FPDF
import json
import docx

# --- SECURE CLOUD SETUP ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash') 

credentials = json.loads(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# --- APP MEMORY (The Fix for Quota Errors) ---
if 'custom_findings' not in st.session_state:
    st.session_state.custom_findings = [{"note": "", "level": "None (No deduction)", "changelog": False}]
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'report_text' not in st.session_state:
    st.session_state.report_text = None
if 'progress_context' not in st.session_state:
    st.session_state.progress_context = None

def add_custom_finding():
    st.session_state.custom_findings.append({"note": "", "level": "None (No deduction)", "changelog": False})

st.title("📋 Dynamic FSMS System")

# ==========================================
# LOGIN SCREEN
# ==========================================
if not st.session_state.logged_in:
    st.subheader("🔒 Access Restricted")
    password_input = st.text_input("Password", type="password")
    if st.button("Login"):
        if password_input == st.secrets["APP_PASSWORD"]:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Incorrect password.")

# ==========================================
# MAIN APP
# ==========================================
if st.session_state.logged_in:
    tab1, tab2 = st.tabs(["📋 Conduct Audit", "📈 Analytics Dashboard"])

    with tab1:
        st.subheader("Audit Details")
        col1, col2 = st.columns(2)
        with col1:
            establishment_name = st.text_input("Establishment Name:", value="Tata's Chicks")
        with col2:
            fsco_name = st.text_input("Lead Auditor / FSCO:", value="Jake-Edwards L. Yboa")
        audit_date = st.date_input("Audit Date?", datetime.date.today())

        st.divider()

        # --- MODULE DATA (Condensed for brevity, keep your full list here) ---
        # [Your full MASTER_CHECKLIST dictionary remains here]

        # [Your edited_modules logic remains here]

        def get_all_failures():
            current_failures = []
            for module_name, df in edited_modules.items():
                failed_rows = df[df["Fail?"] == True]
                for index, row in failed_rows.iterrows():
                    current_failures.append(f"[{row['Class']}] {row['ID']} {row['Description']} - Notes: {row['Notes']}")
            for finding in st.session_state.custom_findings:
                if finding["note"].strip() != "":
                    lvl_code = finding["level"].split()[0]
                    current_failures.append(f"[{lvl_code}] Custom Finding: {finding['note']}")
            return current_failures

        # --- GENERATE BUTTON ---
        if st.button("🔥 Generate Report & Save Data"):
            failed_items = get_all_failures()
            failed_items_formatted = "\n".join([f"- {item}" for item in failed_items]) if failed_items else "No violations found."
            
            # 1. Fetch History & Save to Sheets
            try:
                sheet = gc.open("Audit_Database").sheet1
                existing_data = sheet.get_all_values()
                previous_score = None
                for row in reversed(existing_data):
                    if len(row) >= 5 and row[1] == establishment_name:
                        previous_score = float(row[2].replace('%', ''))
                        break
                
                # Math & Saving
                # [Your deduction/score calculation logic here]
                
                st.session_state.progress_context = f"Prev: {previous_score}% | Current: {final_score}%"
                sheet.append_row([str(audit_date), establishment_name, f"{final_score:.1f}%", deductions, " | ".join(failed_items)])
            except Exception as e:
                st.error(f"Database Error: {e}")

            # 2. AI GENERATION (The "Only Once" Logic)
            with st.spinner("Generating Summary..."):
                prompt = f"..." # [Your full prompt here]
                try:
                    response = model.generate_content(prompt)
                    # SAVE TO MEMORY
                    st.session_state.report_text = response.text.replace('**', '')
                except Exception as e:
                    st.error(f"AI Quota Error: {e}")

        # --- DISPLAY & DOWNLOAD (Reads from Memory) ---
        if st.session_state.report_text:
            st.divider()
            st.subheader("🤖 Executive Summary")
            st.write(st.session_state.report_text)
            
            # [Your PDF Generation Logic here, reading from st.session_state.report_text]
            # [This ensures the Download button doesn't trigger a new AI call]
