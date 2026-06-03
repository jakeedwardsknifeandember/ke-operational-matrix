import streamlit as st
import gspread
import json
import os
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- COMPLIANCE DATABASE & AI INITIALIZATION ---
credentials = json.loads(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# Securely boots your API Key parameters
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
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
    st.markdown("Generate smart, clean compliance manuals matching your custom consulting design templates exactly.")
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
    
    # --- STEP 2: RISK MATRIX ---
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
                    Your task is to rewrite our master baseline text into an immaculate compliance manual tailored for {client_name}.

                    CLIENT PROFILE DATA:
                    - Client Name: {client_name}
                    - Location/Branch: {client_location}
                    - Facility Type: {facility_type}
                    - Primary Regulation Scope: {regulatory_scope}
                    - High-Risk Operational Vectors: {vectors_str}

                    CORE TEMPLATE MANUAL TEXT STRUCTURE:
                    {core_text}

                    ABSOLUTE COMMAND LAYOUT INSTRUCTIONS:
                    1. Separate every distinct Prerequisite Program (PRP) and Standard Operating Procedure (SOP) by printing the single line text token "[PAGE_BREAK]".
                    2. For each program module, you must include the full numbered prefix for the core headings exactly like this:
                       1. Purpose
                       2. Scope
                       3. Definitions
                       4. Responsibility
                       5. Procedure
                       6. Monitoring
                       7. Corrective Action
                       8. Verification
                       9. Records
                    3. For subheadings inside section 5, you must prefix with clause numbers (e.g., '5.1 Personal Cleanliness and Uniform Standards', '5.2 Handwashing Protocol').
                    4. For specific operational item definition fields under procedures, output them using a plain keyword label prefix followed by a colon (e.g., 'Uniforms: All staff must arrive...', 'Method: Staff must scrub...', 'Reporting: Staff must report...').
                    5. DO NOT generate markdown characters, tables, asterisks (**), or hashtags (##). 
                    6. DO NOT copy any source bracket footnotes, citations, or numbers like or trailing citation superscript digits. Output only clean text sentences.
                    """

                    try:
                        response = model.generate_content(ai_prompt)
                        ai_output_text = response.text
                    except Exception as e:
                        st.error(f"Gemini AI Generation Failure: {e}")
                        st.stop()

                # --- PHASE C: RECONSTRUCT DOCUMENT WITH ABSOLUTE TYPOGRAPHY LAYOUT ENGINE ---
                with st.spinner("Reconstructing layout and forcing justification (Times New Roman 9pt)..."):
                    try:
                        final_doc = Document(master_path)
                        
                        # FIXED: Permanently delete placeholder text blocks from the XML tree
                        # This eliminates the 5 empty page gap completely while leaving margins and headers active
                        while len(final_doc.paragraphs) > 0:
                            p_to_del = final_doc.paragraphs[0]
                            p_to_del._element.getparent().remove(p_to_del._element)
                        
                        ai_paragraphs = ai_output_text.split("\n")
                        
                        for line in ai_paragraphs:
                            cleaned_line = line.strip()
                            if not cleaned_line:
                                continue
                            
                            # Catch the page break delimiter
                            if cleaned_line == "[PAGE_BREAK]":
                                final_doc.add_page_break()
                                continue
                            
                            # Clean out runaway markdown characters safely
                            cleaned_line = cleaned_line.replace("**", "").replace("*", "").replace("##", "").replace("#", "")
                            
                            # Advanced Heading Detection (Matches digits or structural FSMS section labels)
                            is_heading = False
                            first_word = cleaned_line.split(" ")[0] if " " in cleaned_line else cleaned_line
                            
                            # Matches "1. ", "5.1 ", "PRP-", or any primary section text values
                            if (first_word and first_word[0].isdigit() and "." in first_word) or \
                               cleaned_line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")) or \
                               cleaned_line in ["Purpose", "Scope", "Definitions", "Responsibility", "Procedure", "Monitoring", "Corrective Action", "Verification", "Records"] or \
                               "PRP-" in cleaned_line or "SOP-" in cleaned_line:
                                is_heading = True
                            
                            new_p = final_doc.add_paragraph()
                            # FIXED: Forces text to be perfectly justified along both page margins
                            new_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                            
                            if is_heading:
                                # Full Structural Section Headings - Entire run bolded
                                run = new_p.add_run(cleaned_line)
                                run.font.name = 'Times New Roman'
                                run.font.size = Pt(9)
                                run.bold = True
                                new_p.paragraph_format.space_before = Pt(12)
                                new_p.paragraph_format.space_after = Pt(4)
                            
                            elif ":" in cleaned_line and not cleaned_line.startswith("http"):
                                # Inline Definition Layout (e.g., "Uniforms: All staff...")
                                label_part, text_part = cleaned_line.split(":", 1)
                                
                                # Add and bold the prefix label keyword run
                                label_run = new_p.add_run(label_part + ":")
                                label_run.font.name = 'Times New Roman'
                                label_run.font.size = Pt(9)
                                label_run.bold = True
                                
                                # Add the descriptive tail run as normal unbolded text
                                text_run = new_p.add_run(text_part)
                                text_run.font.name = 'Times New Roman'
                                text_run.font.size = Pt(9)
                                text_run.bold = False
                                
                                new_p.paragraph_format.space_before = Pt(2)
                                new_p.paragraph_format.space_after = Pt(3)
                                
                            else:
                                # Standard body sentences
                                run = new_p.add_run(cleaned_line)
                                run.font.name = 'Times New Roman'
                                run.font.size = Pt(9)
                                run.bold = False
                                new_p.paragraph_format.space_before = Pt(0)
                                new_p.paragraph_format.space_after = Pt(3.5)

                        output_filename = f"{client_name.strip().replace(' ', '_')}_Custom_FSMS.docx"
                        final_doc.save(output_filename)
                        st.success(f"🟢 Custom manual compiled for {client_name}!")
                        
                        with open(output_filename, "rb") as file:
                            st.download_button(
                                label=f"📥 Download Structured FSMS Manual for {client_name} (.docx)",
                                data=file,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                        os.remove(output_filename)
                        
                    except Exception as e:
                        st.error(f"Style Preservation Mapping Failure: {e}")
