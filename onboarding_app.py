import streamlit as st
import gspread
import json
import os
import google.generativeai as genai
from docx import Document

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- COMPLIANCE DATABASE & AI INITIALIZATION ---
credentials = json.loads(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# FIXED: Safely reads the lookup label parameter from your dashboard
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# FIXED: Directed to a live, production-active reasoning engine
model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# ADMINISTRATIVE GATEKEEPER
# ==========================================
if not st.session_state.logged_in:
    st.title("🪵 Knife & Ember Workspace")
    st.subheader("🔒 FSCO Administrative Authentication")
    
    password_input = st.text_input("System Password", type="password")
    if st.button("Authenticate Panel", use_container_width=True):
        if password_input == st.secrets["APP_PASSWORD"]:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Access Denied: Invalid Administrative Token.")

# ==========================================
# ENTERPRISE AI ONBOARDING FACTORY
# ==========================================
if st.session_state.logged_in:
    st.title("🏭 FSMS Client Onboarding & AI Factory")
    st.markdown("Generate smart, AI-tailored compliance manuals that preserve your professional document design layouts.")
    st.divider()
    
    # --- STEP 1: ESTABLISHMENT ARCHITECTURE ---
    st.header("🏢 1. Establishment Architecture")
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Brand Name / Legal Entity Name:", placeholder="e.g., Lava Craze Group")
        client_location = st.text_input("Operational Unit Address / Province:", placeholder="e.g., Pampanga Cluster")
    with col2:
        facility_type = st.selectbox(
            "Facility Operational Classification:",
            ["Central Commissary Kitchen", "Commercial Cloud Kitchen Network", "Full-Service Dine-In Restaurant", "High-Volume Logistics / Distribution Hub"]
        )
        regulatory_scope = st.selectbox(
            "Primary Regulatory Oversight Framework:",
            ["FDA GHP/HACCP Mandatory Scope", "NMIS Meat Inspection Enforcement", "Local Government LGU Sanitation Code"]
        )

    st.divider()
    
    # --- STEP 2: HAck-Proof RISK MATRIX ---
    st.header("🎛️ 2. Advanced Hazard & Operational Profiling")
    st.markdown("Toggle active hazard vectors to guide the Gemini compliance generation engine:")
    
    with st.expander("🛡️ Biological, Thermal & Cross-Contamination Vectors", expanded=True):
        v_poultry = st.checkbox("Processing Raw Poultry / Mass Deep-Frying Operations (Salmonella/Campylobacter Control)")
        v_thermal = st.checkbox("Extended Temperature-Controlled Holding / Dairy & Cream Systems (Listeria Monitoring)")
        v_rte = st.checkbox("High-Risk Ready-to-Eat (RTE) Seafood / Raw Protein Assemblies (Vibrio/Parasite Protocols)")
        v_vacuum = st.checkbox("Reduced Oxygen Packaging (ROP) / Sous-Vide Processing (Clostridium botulinum Control)")

    with st.expander("🚰 Utility, Waste & Infrastructure Engineering", expanded=False):
        v_well = st.checkbox("Utilizes Independent Ground Well-Water / On-site Water Filtration Matrix")
        v_trap = st.checkbox("Commercial Sub-surface Grease Traps with High-Frequency Waste Output")
        v_cold = st.checkbox("Operates Owned Active Cold-Chain Fleet / Logistics Cross-Docking")

    st.divider()

    # --- STEP 3: AUTOMATION EXECUTION ---
    st.header("🚀 3. Execute AI Document Generation")
    if st.button("🔥 Run AI Compilation Engine", use_container_width=True):
        if not client_name.strip() or not client_location.strip():
            st.error("Compilation Halted: Brand Name and Address parameters cannot be empty.")
        else:
            formatted_sheet_name = client_name.strip().replace(" ", "_")
            master_path = "templates/master_core_fsms.docx"
            
            if not os.path.exists(master_path):
                st.error("Compilation Stopped: master_core_fsms.docx was not located inside your templates directory.")
            else:
                # --- PHASE A: READ MASTER DATA FOR AI CONTEXT ---
                with st.spinner("Analyzing master_core_fsms.docx structure..."):
                    try:
                        template_doc = Document(master_path)
                        core_text = "\n".join([p.text for p in template_doc.paragraphs if p.text.strip()])
                    except Exception as e:
                        st.error(f"Failed to read master layout text: {e}")
                        st.stop()

                # --- PHASE B: LIVE AI CUSTOMIZATION FRAMEWORK ---
                with st.spinner(f"Gemini AI is intelligently customizing your manual for {client_name}..."):
                    active_vectors = []
                    if v_poultry: active_vectors.append("Raw Poultry Processing / Mass Deep-Frying")
                    if v_thermal: active_vectors.append("Extended Cold/Dairy Temp Control")
                    if v_rte: active_vectors.append("Ready-to-Eat Seafood Assembly")
                    if v_vacuum: active_vectors.append("Sous-Vide / Reduced Oxygen Packaging")
                    if v_well: active_vectors.append("Independent Ground Well-Water Extraction")
                    if v_trap: active_vectors.append("Commercial Grease Interceptors")
                    if v_cold: active_vectors.append("Owned Cold-Chain Logistics Fleet")
                    
                    vectors_str = ", ".join(active_vectors) if active_vectors else "Standard Low-Risk Baseline Operations"

                    ai_prompt = f"""
                    You are an expert Food Safety Compliance Officer operating under Philippine regulations (RA 10611, FDA, and NMIS guidelines).
                    Your task is to take the baseline text of our manual and rewrite it into a highly tailored, custom manual for our new client.

                    CLIENT PROFILE DATA:
                    - Client Name: {client_name}
                    - Location/Branch: {client_location}
                    - Facility Type: {facility_type}
                    - Primary Regulation Scope: {regulatory_scope}
                    - High-Risk Operational Vectors: {vectors_str}

                    CORE TEMPLATE MANUAL TEXT (Follow this exact tone and structure):
                    {core_text}

                    CRITICAL GENERATION INSTRUCTIONS:
                    1. Maintain the exact layout structure from the template (e.g., 1. Purpose, 2. Scope, 3. Definitions, 4. Responsibility, 5. Procedure, etc.).
                    2. Intelligently integrate the client's name and location naturally throughout the clauses.
                    3. Under the Procedures/Monitoring sections, add highly specific, expert standard operating procedures tailored directly to their active high-risk vectors (e.g., if they handle poultry, write specific rules regarding poultry cross-contamination, breading stations, and minimum internal cooking temperatures of 165°F).
                    4. Output the finalized document content as clear text lines. Do not use markdown syntax or asterisks. If a line represents a heading (e.g., 1. Purpose), ensure it matches that format perfectly.
                    """

                    try:
                        response = model.generate_content(ai_prompt)
                        ai_output_text = response.text
                    except Exception as e:
                        st.error(f"Gemini AI Generation Failure: {e}")
                        st.stop()

                # --- PHASE C: RECONSTRUCT DOCUMENT AND PRESERVE FORMATTING ---
                with st.spinner("Injecting AI text back into your styled layout..."):
                    try:
                        final_doc = Document(master_path)
                        
                        for p in final_doc.paragraphs:
                            p.text = ""
                        
                        ai_paragraphs = ai_output_text.split("\n")
                        
                        for line in ai_paragraphs:
                            cleaned_line = line.strip()
                            if not cleaned_line:
                                continue
                            
                            is_heading = False
                            first_word = cleaned_line.split(" ")[0]
                            if first_word and first_word[0].isdigit() and "." in first_word:
                                is_heading = True
                            
                            if is_heading:
                                new_p = final_doc.add_paragraph(cleaned_line)
                                new_p.style = final_doc.styles['Heading 1'] if "." not in first_word[first_word.find(".")+1:] else final_doc.styles['Heading 2']
                                for run in new_p.runs:
                                    run.bold = True
                            else:
                                new_p = final_doc.add_paragraph(cleaned_line)
                                new_p.style = final_doc.styles['Normal']

                        output_filename = f"{client_name.strip().replace(' ', '_')}_Custom_FSMS.docx"
                        final_doc.save(output_filename)
                        st.success(f"🟢 Customized, styled manual compiled for {client_name}!")
                        
                        with open(output_filename, "rb") as file:
                            st.download_button(
                                label=f"📥 Download Tailored FSMS Manual for {client_name} (.docx)",
                                data=file,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                        os.remove(output_filename)
                        
                    except Exception as e:
                        st.error(f"Style Preservation Mapping Failure: {e}")
