import streamlit as st
import gspread
import json
import os
from docx import Document

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- SECRETS & REPO VERIFICATION ---
# This matches your working JSON format perfectly
credentials = json.loads(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# ==========================================
# ADMINISTRATIVE LOGIN GATEKEEPER
# ==========================================
if not st.session_state.logged_in:
    st.title("🪵 Knife & Ember Onboarding Suite")
    st.subheader("🔒 Administrative Access Required")
    
    password_input = st.text_input("System Password", type="password")
    if st.button("Authenticate"):
        if password_input == st.secrets["APP_PASSWORD"]:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials.")

# ==========================================
# ADMINISTRATIVE WORKSPACE
# ==========================================
if st.session_state.logged_in:
    st.title("🏭 FSMS Client Onboarding Factory")
    st.markdown("Generate tailored prerequisite programs and automated audit infrastructure for new accounts.")
    st.divider()
    # 🔍 TEMPORARY DIAGNOSTIC TOOL
    st.info("📂 Server Directory Scan:")
    for root, dirs, files in os.walk("."):
        # Ignore hidden git/venv system folders to keep it clean
        if ".git" not in root and ".streamlit" not in root:
            for file in files:
                st.write(os.path.join(root, file))
    st.divider()
    
    # --- SECTION 1: CLIENT PROFILE ---
    st.header("🏢 Client Profile Allocation")
    client_name = st.text_input("Establishment Brand Name (e.g., Cafe Manila):", value="")
    client_location = st.text_input("Operational Unit Address / Branch:", value="")
    
    st.divider()
    
    # --- SECTION 2: RISK PROFILE ---
    st.header("🍕 Menu & Equipment Risk Profiling")
    st.write("Toggle the specialized operational vectors active at this facility:")
    
    has_poultry = st.checkbox("Facility processes raw poultry / deep-fried items")
    has_dairy = st.checkbox("Facility operates espresso systems / temperature-controlled dairy")
    has_seafood = st.checkbox("Facility handles raw seafood / high-risk marine proteins")
    has_grease_trap = st.checkbox("Facility utilizes commercial underground grease traps")

    st.divider()

    # --- SECTION 3: AUTOMATION ENGINE ---
    if st.button("🔥 Run Client Deployment Engine", use_container_width=True):
        if not client_name.strip():
            st.error("Deployment halted: Please provide a valid Establishment Brand Name.")
        else:
            # Clean up space characters for technical spreadsheet tabs
            formatted_sheet_name = client_name.strip().replace(" ", "_")
            
            # --- PHASE 3A: GOOGLE SHEET TAB CREATION ---
            with st.spinner("Step 1: Constructing cloud database infrastructure..."):
                try:
                    db = gc.open("Audit_Database")
                    
                    # Prevent overwriting an existing client tab
                    try:
                        db.worksheet(formatted_sheet_name)
                        st.warning(f"Database infrastructure for {client_name} already exists.")
                    except gspread.exceptions.WorksheetNotFound:
                        # Create a fresh sheet tab
                        new_worksheet = db.add_worksheet(title=formatted_sheet_name, rows="100", cols="4")
                        
                        # Apply standard headers
                        headers = ["Module", "Ref ID", "Description", "Class"]
                        new_worksheet.append_row(headers)
                        
                        # Define the universal 80% Core Checklist rows
                        core_checklist_rows = [
                            ["Module 1: Personnel Hygiene", "1.1", "Staff observed washing hands for 20s before cooking.", "L1"],
                            ["Module 1: Personnel Hygiene", "1.2", "Handwashing observed after touching face, phone, or trash.", "L1"],
                            ["Module 1: Personnel Hygiene", "1.5", "Hand sinks fully stocked with soap and paper towels.", "L2"],
                            ["Module 2: Thermal Control", "2.6", "Chiller/Reach-in units maintain food temp <= 41 F.", "L1"],
                            ["Module 5: Sanitation, Pests & Infrastructure", "5.2", "Sanitizer (Chlorine/Quat) at correct ppm.", "L1"],
                            ["Module 5: Sanitation, Pests & Infrastructure", "5.5", "No evidence of rodent droppings or gnaw marks.", "L1"]
                        ]
                        
                        # Dynamically inject 20% risk rows based on toggles
                        if has_poultry:
                            core_checklist_rows.append(["Module 2: Thermal Control", "2.1", "Fried Chicken batch internal temp >= 165 F for 15s.", "L1"])
                        if has_dairy:
                            core_checklist_rows.append(["Module 2: Thermal Control", "2.6", "Milk cooling and hold parameters strictly verified under 41 F.", "L1"])
                        if has_grease_trap:
                            core_checklist_rows.append(["Module 5: Sanitation, Pests & Infrastructure", "5.8", "Grease trap waste layer < 25% of total depth.", "L2"])
                            
                        # Batch upload everything to the new tab
                        new_worksheet.append_rows(core_checklist_rows)
                        st.success(f"🟢 Google Sheet tab '{formatted_sheet_name}' successfully provisioned.")
                except Exception as e:
                    st.error(f"Database Provisioning Failure: {e}")
            
            # --- PHASE 3B: WORD DOCUMENT CUSTOMIZATION ---
            with st.spinner("Step 2: Slicing core master document structures..."):
                # List of all possible folder and file case combinations
                possible_paths = [
                    "templates/master_core_fsms.docx",
                    "Templates/master_core_fsms.docx",
                    "standards/master_core_fsms.docx",
                    "Standards/master_core_fsms.docx",
                    "templates/Master_Core_Fsms.docx",
                    "Templates/Master_Core_Fsms.docx"
                ]
                
                master_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        master_path = path
                        break
                
                if not master_path:
                    st.error("Document Halted: Master file not found. Please verify the folder name matches exactly on GitHub.")
                else:
                    try:
                        doc = Document(master_path)
                        new_doc = Document()
                        
                        # Write the localized custom metadata cover blocks
                        new_doc.add_heading(f"Food Safety Management System (FSMS)", level=0)
                        new_doc.add_paragraph(f"Prepared For: {client_name}")
                        new_doc.add_paragraph(f"Location: {client_location}")
                        new_doc.add_paragraph("Compiled by Knife and Ember Food Consultancy Services")
                        new_doc.add_page_break()
                        
                        # Duplicate content layout mapping 
                        for paragraph in doc.paragraphs:
                            new_doc.add_paragraph(paragraph.text)
                        
                        output_filename = f"{formatted_sheet_name}_FSMS_Manual.docx"
                        new_doc.save(output_filename)
                        st.success("🟢 Customized compliance manuals cleanly compiled.")
                        
                        # Show download button to save to your local machine
                        with open(output_filename, "rb") as file:
                            st.download_button(
                                label="📥 Download Tailored FSMS Manual (.docx)",
                                data=file,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                        os.remove(output_filename)
                        
                    except Exception as e:
                        st.error(f"Document Generation Failure: {e}")

    # --- FOOTER CONTROLS ---
    st.divider()
    st.caption("Knife and Ember Food Safety Infrastructure Automation Engine")
