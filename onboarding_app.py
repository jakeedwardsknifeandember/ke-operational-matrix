import streamlit as st
import gspread
import json
import os
import google.generativeai as genai
import docx
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- COMPLIANCE DATABASE & AI INITIALIZATION ---
credentials = json.loads(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# Helper function to add uniform thin borders to our multi-document headers
def set_cell_border(cell, color="CCCCCC", sz="4", val="single"):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        border = OxmlElement(f'w:{edge}')
        border.set(qn('w:val'), val)
        border.set(qn('w:sz'), sz)
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tcBorders.append(border)
    tcPr.append(tcBorders)

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

    with st.expander("𚚰 Utility, Waste & Infrastructure Engineering", expanded=False):
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
                with st.spinner(f"Gemini AI is intelligently customizing your binder collection..."):
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
                    Your task is to rewrite our master baseline text into a collection of different standalone file documents for {client_name}.

                    CLIENT DATA:
                    - Client Name: {client_name}
                    - Location/Branch: {client_location}
                    - Facility Type: {facility_type}
                    - Primary Regulation Scope: {regulatory_scope}
                    - High-Risk Operational Vectors: {vectors_str}

                    CORE TEMPLATE MANUAL TEXT STRUCTURE:
                    {core_text}

                    ABSOLUTE FILE ARCHITECTURE COMMANDS:
                    1. Do not print any summary lists or tables at the beginning of the text. Start immediately with the first document module.
                    2. Separate every single distinct PRP and SOP module by printing the exact text token string "[PAGE_BREAK]" on its own line.
                    3. Right after a "[PAGE_BREAK]" token, you must declare the formal Document Header Meta Name on its own separate line before printing the clauses (e.g., "PRP-01: PERSONNEL HYGIENE AND HEALTH POLICY" or "SOP-01: INBOUND RECEIVING PROTOCOLS").
                    4. For each document module, output the 9 core structural headings with their numbers:
                       1. Purpose
                       2. Scope
                       3. Definitions
                       4. Responsibility
                       5. Procedure
                       6. Monitoring
                       7. Corrective Action
                       8. Verification
                       9. Records
                    5. Format subheadings inside section 5 with subnumbers (e.g., '5.1 Uniform Standards', '5.2 Handwashing Protocol').
                    6. For specific operational items under procedures, output them using a plain keyword prefix label followed by a colon (e.g., 'Uniforms: All staff must...', 'Method: Staff must scrub...').
                    7. Do not use markdown syntax, asterisks (**), or tables. Do not copy source bracket citations like .
                    """

                    try:
                        response = model.generate_content(ai_prompt)
                        ai_output_text = response.text
                    except Exception as e:
                        st.error(f"Gemini AI Generation Failure: {e}")
                        st.stop()

                # --- PHASE C: RECONSTRUCT DOCUMENT WITH RUN-LEVEL STYLING & SPACING ---
                with st.spinner("Reconstructing file layout structure (Times New Roman 9pt)..."):
                    try:
                        final_doc = Document(master_path)
                        
                        # Completely wipe old text blocks to prevent empty top page gaps
                        while len(final_doc.paragraphs) > 0:
                            p_to_del = final_doc.paragraphs[0]
                            p_to_del._element.getparent().remove(p_to_del._element)
                        
                        ai_paragraphs = ai_output_text.split("\n")
                        
                        # Helper function to generate the clean file-collection header table block
                        def inject_corporate_header(doc_obj, title_text):
                            tbl = doc_obj.add_table(rows=2, cols=2)
                            tbl.autofit = False
                            tbl.columns[0].width = Inches(4.5)
                            tbl.columns[1].width = Inches(2.0)
                            
                            # Row 0, Cell 0: Corporate Brand Name Identification
                            cell_00 = tbl.cell(0, 0)
                            p_00 = cell_00.paragraphs[0]
                            p_00.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            r_00 = p_00.add_run(f"🏢 FOOD SAFETY MANAGEMENT SYSTEM | {client_name.upper()}")
                            r_00.font.name = 'Times New Roman'
                            r_00.font.size = Pt(8)
                            r_00.font.color.rgb = RGBColor(100, 100, 100)
                            
                            # Row 0, Cell 1: Compliance File Reference Tracking
                            cell_01 = tbl.cell(0, 1)
                            p_01 = cell_01.paragraphs[0]
                            p_01.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                            r_01 = p_01.add_run("Doc Ref: FSMS-PRP-SOP-2026")
                            r_01.font.name = 'Times New Roman'
                            r_01.font.size = Pt(8)
                            r_01.font.color.rgb = RGBColor(100, 100, 100)
                            
                            # Row 1, Cell 0: Distinct Document Module Title
                            cell_10 = tbl.cell(1, 0)
                            p_10 = cell_10.paragraphs[0]
                            p_10.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            r_10 = p_10.add_run(title_text.upper())
                            r_10.font.name = 'Times New Roman'
                            r_10.font.size = Pt(10)
                            r_10.bold = True
                            
                            # Row 1, Cell 1: Regulatory Standard Reference
                            cell_11 = tbl.cell(1, 1)
                            p_11 = cell_11.paragraphs[0]
                            p_11.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                            r_11 = p_11.add_run("Standard: RA 10611 / GHP")
                            r_11.font.name = 'Times New Roman'
                            r_11.font.size = Pt(8)
                            r_11.font.italic = True
                            r_11.font.color.rgb = RGBColor(100, 100, 100)
                            
                            # Format borders for every cell in the template header grid
                            for row in tbl.rows:
                                for cell in row.cells:
                                    set_cell_border(cell)
                            
                            # Add an anchor spacer paragraph below the table grid to separate it from content
                            spacer = doc_obj.add_paragraph()
                            spacer.paragraph_format.space_after = Pt(12)

                        # Boot the very first header tracker table on page 1
                        is_next_line_title = True
                        
                        for line in ai_paragraphs:
                            cleaned_line = line.strip()
                            if not cleaned_line:
                                continue
                            
                            # Process explicit page break boundaries
                            if cleaned_line == "[PAGE_BREAK]":
                                final_doc.add_page_break()
                                is_next_line_title = True
                                continue
                            
                            # Handle module title lines immediately following page breaks
                            if is_next_line_title:
                                inject_corporate_header(final_doc, cleaned_line)
                                is_next_line_title = False
                                continue
                            
                            # Detect structure heading rows
                            is_heading = False
                            first_word = cleaned_line.split(" ")[0] if " " in cleaned_line else cleaned_line
                            if (first_word and first_word[0].isdigit() and "." in first_word) or \
                               cleaned_line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")) or \
                               cleaned_line in ["Purpose", "Scope", "Definitions", "Responsibility", "Procedure", "Monitoring", "Corrective Action", "Verification", "Records"] or \
                               cleaned_line.startswith(("PRP-", "SOP-")):
                                is_heading = True
                            
                            new_p = final_doc.add_paragraph()
                            new_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                            
                            if is_heading:
                                # Primary Structure Section Headings - Full line bolded
                                run = new_p.add_run(cleaned_line)
                                run.font.name = 'Times New Roman'
                                run.font.size = Pt(9)
                                run.bold = True
                                new_p.paragraph_format.space_before = Pt(14) # Clean separation gap before headings
                                new_p.paragraph_format.space_after = Pt(4)
                            
                            elif ":" in cleaned_line and not cleaned_line.startswith("http"):
                                # Inline Field Definitions (e.g., "Uniforms: All staff...")
                                label_part, text_part = cleaned_line.split(":", 1)
                                
                                label_run = new_p.add_run(label_part + ":")
                                label_run.font.name = 'Times New Roman'
                                label_run.font.size = Pt(9)
                                label_run.bold = True
                                
                                text_run = new_p.add_run(text_part)
                                text_run.font.name = 'Times New Roman'
                                text_run.font.size = Pt(9)
                                text_run.bold = False
                                
                                # FIXED: Force a clean padding gap before this item so it never runs together compressed
                                new_p.paragraph_format.space_before = Pt(8)
                                new_p.paragraph_format.space_after = Pt(3)
                                
                            else:
                                # Standard body sentences
                                run = new_p.add_run(cleaned_line)
                                run.font.name = 'Times New Roman'
                                run.font.size = Pt(9)
                                run.bold = False
                                new_p.paragraph_format.space_before = Pt(0)
                                new_p.paragraph_format.space_after = Pt(4)

                        output_filename = f"{client_name.strip().replace(' ', '_')}_Custom_FSMS.docx"
                        final_doc.save(output_filename)
                        st.success(f"🟢 Collection compiled cleanly for {client_name}!")
                        
                        with open(output_filename, "rb") as file:
                            st.download_button(
                                label=f"📥 Download Collection FSMS Binder for {client_name} (.docx)",
                                data=file,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                        os.remove(output_filename)
                        
                    except Exception as e:
                        st.error(f"Style Preservation Mapping Failure: {e}")
