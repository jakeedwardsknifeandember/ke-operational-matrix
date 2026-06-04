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

# Safely paths your active key from your environment dashboard
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# Helper function to append thin borders around our multi-document metadata grids
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
    st.markdown("Compile smart, layout-perfect compliance manuals that preserve your professional consulting document layouts.")
    st.divider()
    
    # --- STEP 1: ESTABLISHMENT BACKGROUND & CORE ARCHITECTURE ---
    st.header("🏢 1. Establishment Background & Core Architecture")
    col1, col2 = st.columns(2)
    with col1:
        # FIXED: Placeholders removed completely for a clean text slot entry
        client_name = st.text_input("Brand Name / Legal Entity Name:", placeholder="")
        client_location = st.text_input("Operational Unit Address / Province:", placeholder="")
    with col2:
        facility_type = st.selectbox(
            "Facility Operational Classification:",
            [
                "Central Commissary Kitchen", 
                "Full-Service Dine-In Restaurant", 
                "Cafe / Specialty Coffee Shop (Light Cooking)", 
                "Micro-Kiosk / Street-Side Retail Stand", 
                "Pastry Shop & Bakery (No Raw Protein Prep)"
            ]
        )
        regulatory_scope = st.selectbox(
            "Primary Regulatory Oversight Framework:",
            [
                "Local Government LGU Sanitation Code (Standard Retail)", 
                "FDA GHP/HACCP Mandatory Scope (Manufacturing/Commissaries)", 
                "NMIS Meat Inspection Enforcement (Primary Meat Processing)"
            ]
        )

    # --- STEP 2: INFRASTRUCTURE & STRUCTURAL UTILITIES ---
    st.header("🏗️ 2. Infrastructure & Structural Utilities")
    
    with st.expander("🛠️ Countertop Fabrication & Cold-Chain Shelving Materials", expanded=True):
        st.markdown("**Worktop & Prep Surface Fabrication:**")
        c_ss = st.checkbox("Food-Grade 304 Stainless Steel (Standard Corrosion Resistance)")
        c_stone = st.checkbox("Natural Stone / Marble & Granite (Porous, Temp-Retaining Dough Prep)")
        c_wood = st.checkbox("Hardwood / Butcher Block Prep Counters (Highly Porous Artisian Surfaces)")
        
        st.markdown("---")
        st.markdown("**Cold-Chain Storage Shelving Units:**")
        s_epoxy = st.checkbox("Epoxy-Coated / Plastic Composite Shelving (High-Moisture Coolers)")
        s_chrome = st.checkbox("Chrome-Plated Wire Shelving (Dry Storage Only)")

    with st.expander("🚰 Environmental & Water Engineering Toggles", expanded=False):
        u_open = st.checkbox("Open-Air / Street-Facing Kiosk Facility Environment (Exposed Vector Risks)")
        u_manual_water = st.checkbox("Containerized / Manual Gravity Water Supply (No Connected Mains Plumbing)")
        u_ice = st.checkbox("On-Site Commercial Ice Production Equipment (High Slime/Mold Biofilm Risks)")
        u_hoods = st.checkbox("Commercial Ventilation Hoods & Active ANSUL Fire Suppression Arrays")

    # --- STEP 3: DRINK CAPABILITIES & BEVERAGE MATRIX ---
    st.header("🥤 3. Beverage Capabilities Matrix")
    with st.expander("☕ Specialty Beverage Program Toggles", expanded=False):
        d_coffee = st.checkbox("Coffee Based Operations (Espresso Lines / Steam-Wand Management)")
        d_tea = st.checkbox("Tea Based Programs (Bulk Brewed Batching / Infused Syrups)")
        d_milk = st.checkbox("Milk Based / Fresh Liquid Dairy Creamers (High-Risk Temperature Loops)")
        d_nondairy = st.checkbox("Non-Dairy Alternative Milks (Almond, Soy, Oat Allergen Segregation)")
        d_frappe = st.checkbox("Frappes / Milkshakes served with Whipping Cream Siphon Canisters")
        d_soda = st.checkbox("Soda Based Operations (Pressurized CO2 Gas Lines / Post-Mix Systems)")

    # --- STEP 4: CULINARY MENU CATEGORIES MATRIX ---
    st.header("🍕 4. Culinary Menu Categories Matrix")
    with st.expander("🍔 Active Food Menu Item Classifications", expanded=True):
        f_app = st.checkbox("Appetizers & Finger Foods (Nachos, Fries, Quesadillas)")
        f_rice = st.checkbox("Rice Bowls / Mass Grains Batching (Bacillus Cereus Mitigation Scope)")
        f_pasta = st.checkbox("Pre-boiled Pasta Handling & Starch Lines")
        f_pizza = st.checkbox("Pizza Production (High Flour Dust Allergen & Deck Oven Risks)")
        f_pastry = st.checkbox("Pastries & Pre-Baked Confectionery Goods")
        f_icecream = st.checkbox("Soft Serve Ice Cream Operations (High-Risk Liquid Hopper Wash Loops)")
        f_sandwich = st.checkbox("Sandwiches & Cold Ready-To-Eat (RTE) Manual Assemblies")
        f_burger = st.checkbox("Burgers & Flat-Top Griddle Operations (High-Velocity Ground Proteins)")
        f_salad = st.checkbox("Salads & Fresh Raw Produce Washes (Surface Pathogen Controls)")
        f_poultry = st.checkbox("Chicken Processing (Raw Poultry Cross-Contamination Boundaries)")
        f_meat = st.checkbox("Pork or Beef Whole Muscle Cuts")
        f_seafood = st.checkbox("Seafood & Raw/Chilled Marine Proteins")

    st.divider()

    # --- STEP 5: AUTOMATION EXECUTION ---
    st.header("🚀 5. Execute AI Document Generation")
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
                    # Map structural selections
                    infra_list = []
                    if c_ss: infra_list.append("Stainless Steel Counters")
                    if c_stone: infra_list.append("Natural Stone Surfaces")
                    if c_wood: infra_list.append("Hardwood Butcher Blocks")
                    if s_epoxy: infra_list.append("Epoxy-Coated Storage Racks")
                    if s_chrome: infra_list.append("Chrome Wire Shelving")
                    if u_open: infra_list.append("Open-Air Kiosk Environment")
                    if u_manual_water: infra_list.append("Manual Gravity Containerized Water Tank")
                    if u_ice: infra_list.append("On-Site Commercial Ice Machines")
                    if u_hoods: infra_list.append("Ventilation Hoods & ANSUL System")
                    
                    # Map drink parameters
                    drink_list = []
                    if d_coffee: drink_list.append("Espresso Coffee Operations")
                    if d_tea: drink_list.append("Brewed Teas & Syrups")
                    if d_milk: drink_list.append("Liquid Dairy Creamers")
                    if d_nondairy: drink_list.append("Plant-Based Alternative Milks (Soy/Almond)")
                    if d_frappe: drink_list.append("Frappes & Whipped Cream Siphons")
                    if d_soda: drink_list.append("Soda Post-Mix & CO2 Gas Systems")
                    
                    # Map culinary parameters
                    menu_list = []
                    if f_app: menu_list.append("Appetizers (Fries/Nachos)")
                    if f_rice: menu_list.append("Rice Bowls (Mass Cooked Grains)")
                    if f_pasta: menu_list.append("Pre-boiled Pasta Handling")
                    if f_pizza: menu_list.append("Pizza & Heavy Flour Dough Assembly")
                    if f_pastry: menu_list.append("Pastries & Baked Confectionery")
                    if f_icecream: menu_list.append("Soft Serve Ice Cream Machine Hoppers")
                    if f_sandwich: menu_list.append("Sandwiches & Ready-To-Eat Cold Lines")
                    if f_burger: menu_list.append("Burgers & High-Velocity Flat-Top Griddles")
                    if f_salad: menu_list.append("Salads & Fresh Raw Produce Chlorination Wash")
                    if f_poultry: menu_list.append("Raw Poultry (Chicken Processing)")
                    if f_meat: menu_list.append("Pork/Beef Whole Muscle Cuts")
                    if f_seafood: menu_list.append("Seafood & Marine Proteins")

                    infra_str = ", ".join(infra_list) if infra_list else "Standard Sealed Structural Layout"
                    drink_str = ", ".join(drink_list) if drink_list else "No Beverage Operations"
                    menu_str = ", ".join(menu_list) if menu_list else "Standard Baseline Food Processing"

                    ai_prompt = f"""
                    You are an expert Food Safety Compliance Officer operating under Philippine regulations (RA 10611, FDA, and NMIS guidelines).
                    Your task is to take the baseline rules of our manual and rewrite them into a customized collection of separate file documents for our client.

                    CLIENT PROFILE DATA:
                    - Client Name: {client_name}
                    - Location/Branch: {client_location}
                    - Facility Classification: {facility_type}
                    - Primary Regulation Scope: {regulatory_scope}
                    - Infrastructure Profile: {infra_str}
                    - Beverage Capabilities: {drink_str}
                    - Menu Category Grid: {menu_str}

                    CORE TEMPLATE MANUAL TEXT:
                    {core_text}

                    ABSOLUTE COMPLIANCE ENGINEERING DIRECTIONS:
                    1. Separate every single distinct PRP and SOP program block by printing the exact text token string "[PAGE_BREAK]" on its own separate line.
                    2. Right after a "[PAGE_BREAK]" token, print the formal document tracking title on its own line before starting the headers (e.g., "PRP-01: PERSONNEL HYGIENE AND HEALTH POLICY").
                    3. Do not generate markdown tables, summary tables, or lists at the beginning of the response. Weave all specific metrics (like PPM levels or cooking temperatures) directly into the text procedures of the corresponding SOP/PRP paragraphs.
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
                    6. For specific operational parameters under procedures, use a plain keyword label prefix followed by a colon (e.g., 'Uniforms: All staff must...', 'Method: Staff must scrub...').
                    7. Do not include markdown asterisks (**), hashtags (##), or source bracket citations like [source: X]. Output clean, text lines.
                    """

                    try:
                        response = model.generate_content(ai_prompt)
                        ai_output_text = response.text
                    except Exception as e:
                        st.error(f"Gemini AI Generation Failure: {e}")
                        st.stop()

                # --- PHASE C: RECONSTRUCT DOCUMENT WITH RUN-LEVEL STYLING & SPACING ---
                with st.spinner("Executing run-level styling overrides (Times New Roman 9pt)..."):
                    try:
                        final_doc = Document(master_path)
                        
                        # Completely wipe old text containers out of the file layout structure
                        while len(final_doc.paragraphs) > 0:
                            p_to_del = final_doc.paragraphs[0]
                            p_to_del._element.getparent().remove(p_to_del._element)
                        
                        ai_paragraphs = ai_output_text.split("\n")
                        
                        # Generates the thin-bordered tracking box header at the top of each standalone document page
                        def inject_corporate_header(doc_obj, title_text):
                            tbl = doc_obj.add_table(rows=2, cols=2)
                            tbl.autofit = False
                            tbl.columns[0].width = Inches(4.5)
                            tbl.columns[1].width = Inches(2.0)
                            
                            cell_00 = tbl.cell(0, 0)
                            p_00 = cell_00.paragraphs[0]
                            p_00.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            r_00 = p_00.add_run(f"🏢 FOOD SAFETY MANAGEMENT SYSTEM | {client_name.upper()}")
                            r_00.font.name = 'Times New Roman'
                            r_00.font.size = Pt(8)
                            r_00.font.color.rgb = RGBColor(100, 100, 100)
                            
                            cell_01 = tbl.cell(0, 1)
                            p_01 = cell_01.paragraphs[0]
                            p_01.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                            r_01 = p_01.add_run("Doc Ref: FSMS-PRP-SOP-2026")
                            r_01.font.name = 'Times New Roman'
                            r_01.font.size = Pt(8)
                            r_01.font.color.rgb = RGBColor(100, 100, 100)
                            
                            cell_10 = tbl.cell(1, 0)
                            p_10 = cell_10.paragraphs[0]
                            p_10.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            r_10 = p_10.add_run(title_text.upper())
                            r_10.font.name = 'Times New Roman'
                            r_10.font.size = Pt(10)
                            r_10.bold = True
                            
                            cell_11 = tbl.cell(1, 1)
                            p_11 = cell_11.paragraphs[0]
                            p_11.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                            r_11 = p_11.add_run("Standard: RA 10611 / GHP")
                            r_11.font.name = 'Times New Roman'
                            r_11.font.size = Pt(8)
                            r_11.font.italic = True
                            r_11.font.color.rgb = RGBColor(100, 100, 100)
                            
                            for row in tbl.rows:
                                for cell in row.cells:
                                    set_cell_border(cell)
                            
                            spacer = doc_obj.add_paragraph()
                            spacer.paragraph_format.space_after = Pt(12)

                        # Set page 1 tracker trigger
                        is_next_line_title = True
                        
                        for line in ai_paragraphs:
                            cleaned_line = line.strip()
                            if not cleaned_line:
                                continue
                            
                            if cleaned_line == "[PAGE_BREAK]":
                                final_doc.add_page_break()
                                is_next_line_title = True
                                continue
                            
                            if is_next_line_title:
                                inject_corporate_header(final_doc, cleaned_line)
                                is_next_line_title = False
                                continue
                            
                            # Advanced structural title matching logic
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
                                # Primary Section Headings - Full run bolded
                                run = new_p.add_run(cleaned_line)
                                run.font.name = 'Times New Roman'
                                run.font.size = Pt(9)
                                run.bold = True
                                new_p.paragraph_format.space_before = Pt(14)
                                new_p.paragraph_format.space_after = Pt(4)
                            
                            elif ":" in cleaned_line and not cleaned_line.startswith("http"):
                                # Inline Definition Spacing Fix (e.g., "Uniforms: All staff...")
                                label_part, text_part = cleaned_line.split(":", 1)
                                
                                label_run = new_p.add_run(label_part + ":")
                                label_run.font.name = 'Times New Roman'
                                label_run.font.size = Pt(9)
                                label_run.bold = True
                                
                                text_run = new_p.add_run(text_part)
                                text_run.font.name = 'Times New Roman'
                                text_run.font.size = Pt(9)
                                text_run.bold = False
                                
                                # FIXED: Applies breathing space before the item so it never feels compressed
                                new_p.paragraph_format.space_before = Pt(8)
                                new_p.paragraph_format.space_after = Pt(3)
                                
                            else:
                                # Standard body blocks
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
