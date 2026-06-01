import streamlit as st
import gspread
import json
import os
from docx import Document

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- COMPLIANCE DATABASE SECRETS CONNECT ---
credentials = json.loads(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)

# ==========================================
# ADMINISTRATIVE AUTHENTICATION GATEWAY
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
# ENTERPRISE FOOD SAFETY ONBOARDING FACTORY
# ==========================================
if st.session_state.logged_in:
    st.title("🏭 FSMS Client Onboarding & Automation Factory")
    st.markdown("Construct customized cloud audit frameworks and format-preserved prerequisite compliance manuals.")
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
    
    # --- STEP 2: EXPANDED RISK & HAZARD PROFILING ENGINE ---
    st.header("🎛️ 2. Advanced Hazard & Operational Profiling (The 20% Split)")
    st.markdown("Toggle active high-risk vectors to determine dynamic Prerequisite Program (PRP) inclusions:")
    
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
    st.header("🚀 3. Execute Infrastructure Deployment")
    if st.button("🔥 Compile & Provision Client Assets", use_container_width=True):
        if not client_name.strip() or not client_location.strip():
            st.error("Compilation Halted: Brand Name and Address parameters cannot be empty.")
        else:
            formatted_sheet_name = client_name.strip().replace(" ", "_")
            
            # --- PHASE A: DYNAMIC GOOGLE SHEET AUDIT FRAMEWORK GENERATION ---
            with st.spinner("Provisioning synchronized Google Sheet architecture..."):
                try:
                    db = gc.open("Audit_Database")
                    
                    try:
                        db.worksheet(formatted_sheet_name)
                        st.warning(f"Database structures for '{formatted_sheet_name}' already active. Overwrite skipped.")
                    except gspread.exceptions.WorksheetNotFound:
                        new_worksheet = db.add_worksheet(title=formatted_sheet_name, rows="150", cols="4")
                        new_worksheet.append_row(["Module", "Ref ID", "Description", "Class"])
                        
                        # Build a production-grade 80% Core Operational Checklist
                        checklist_data = [
                            ["Module 1: Personnel Hygiene", "1.1", "Food handlers observed executing verified 20-second handwashing protocols prior to station entry.", "L1"],
                            ["Module 1: Personnel Hygiene", "1.2", "Handwashing executed post handling trash, un-sanitized surfaces, or personal communication mobile hardware.", "L1"],
                            ["Module 1: Personnel Hygiene", "1.3", "Proper hair restraints, beard snoods, and clean protective uniform compliance checked across all active processing areas.", "L2"],
                            ["Module 2: Thermal Control", "2.1", "Walk-in chillers and raw storage infrastructure maintain ambient temperatures strictly at or below 41°F (5°C).", "L1"],
                            ["Module 2: Thermal Control", "2.2", "Blast freezing units maintain strict holding conditions holding items solid at or below 0°F (-18°C).", "L1"],
                            ["Module 3: Cross-Contamination", "3.1", "Color-coded cutting boards and dedicated sanitizing processing knives utilized to enforce structural protein segregation.", "L1"],
                            ["Module 4: Chemical Controls", "4.1", "Toxic compounds, cleaning detergents, and sanitizers stored inside restricted lockers fully isolated from food contact packaging zones.", "L2"],
                            ["Module 5: Infrastructure & Pest Control", "5.1", "Integrated Pest Management (IPM) perimeter bait matrices and indoor mechanical multi-catch traps verified secure.", "L1"],
                            ["Module 5: Infrastructure & Pest Control", "5.2", "Active food contact surface sanitizing steps utilize verified chemical titrations (Chlorine 50-100 ppm / Quat 200 ppm).", "L1"]
                        ]
                        
                        # Dynamically inject the remaining 20% specialized critical risk parameters
                        if facility_type == "Central Commissary Kitchen":
                            checklist_data.append(["Module 6: Industrial Commissary Systems", "6.1", "Mass batch cooking cooling parameters track drop from 135°F to 70°F within 2 hours, and to 41°F within an additional 4 hours.", "L1"])
                        if v_poultry:
                            checklist_data.append(["Module 2: Thermal Control", "2.3", "Internal endpoint thermal processing for raw poultry logs minimum internal parameters of 165°F (74°C) for 15 seconds.", "L1"])
                        if v_vacuum:
                            checklist_data.append(["Module 2: Thermal Control", "2.4", "Sous-vide execution parameters utilize calibrated internal needle probes; raw cook data logs critical control deviations.", "L1"])
                        if v_well:
                            checklist_data.append(["Module 5: Infrastructure & Pest Control", "5.3", "Microbiological potability analysis records (Total Coliform/E. coli) updated monthly for private ground water well ports.", "L1"])
                        if v_trap:
                            checklist_data.append(["Module 5: Infrastructure & Pest Control", "5.4", "Grease traps verified free from structural blockage; waste layers check out below the standard 25% max accumulation line.", "L2"])
                        if v_cold:
                            checklist_data.append(["Module 7: Supply Chain Cold Logistics", "7.1", "Refrigerated distribution truck dataloggers confirm continuous transit temperatures below 41°F during out-of-hub shipments.", "L1"])
                            
                        new_worksheet.append_rows(checklist_data)
                        st.success(f"🟢 Cloud Database Framework Deployed.")
                except Exception as e:
                    st.error(f"Google Sheets Integration Failure: {e}")
            
            # --- PHASE B: FORMAT-PRESERVED TOKEN DOCUMENT PARSING ---
            with st.spinner("Generating customized, format-preserved documentation..."):
                master_path = "templates/master_core_fsms.docx"
                
                if not os.path.exists(master_path):
                    st.error("Compilation Stopped: Master layout template file was not located inside the templates directory.")
                else:
                    try:
                        # Open the master file directly to preserve ALL formatting layouts, styles, and headers
                        doc = Document(master_path)
                        
                        # Generate the custom 20% text block based on active hazard checks
                        dynamic_risk_text = ""
                        if v_poultry:
                            dynamic_risk_text += (
                                "ADDENDUM CONTROL A-1: RAW POULTRY & THERMAL PROCESS PROTOCOLS\n"
                                "Enforced under NMIS guidelines. All raw poultry processing lines must maintain a strict physical boundary "
                                "segregation from ready-to-eat assembly stations. The continuous batch deep-frying systems must be monitored "
                                "using calibrated digital stem thermometers. The critical control limit requires an internal core temperature "
                                "of >=165°F (74°C) maintained for at least 15 continuous seconds. Frying oil chemistry metrics must be verified "
                                "using total polar material (TPM) test strips daily.\n\n"
                            )
                        if v_thermal:
                            dynamic_risk_text += (
                                "ADDENDUM CONTROL A-2: COLD CHAIN HOLDING & LIQUID DAIRY CONTROLS\n"
                                "To manage risk profiles associated with Listeria monocytogenes, open dairy systems, cream batches, and espresso "
                                "steamer arrays must execute a high-frequency sanitation cycle. Ambient holding units must maintain continuous "
                                "metrics at or below 41°F (5°C). Any product breaching this temperature envelope for more than 2 hours must be flagged for disposal.\n\n"
                            )
                        if v_well:
                            dynamic_risk_text += (
                                "ADDENDUM CONTROL B-1: INDEPENDENT WATER DISTRIBUTION & TESTING METRICS\n"
                                "Because the facility utilizes private sub-surface ground water wells, water safety compliance falls under local "
                                "LGU Sanitation codes. The facility must run an active on-site chlorination pump matrix maintaining free residual "
                                "chlorine at 0.5 ppm to 1.5 ppm at all distribution lines. Physical water logs must include monthly total coliform "
                                "and E. coli laboratory potability certificates.\n\n"
                            )
                        if v_trap:
                            dynamic_risk_text += (
                                "ADDENDUM CONTROL B-2: WASTEWATER INTERCEPTION & GREASE TRAP MANAGEMENT\n"
                                "Commercial grease interceptors must undergo a rigorous cleaning schedule executed at a minimum frequency of every "
                                "14 operating days. The FSCO must inspect structural grease layers to ensure total solid accumulation remains below "
                                "the 25% system threshold capacity rule.\n\n"
                            )
                        
                        if not dynamic_risk_text:
                            dynamic_risk_text = "No additional high-risk operational vectors declared for this profile allocation."

                        # High-Grade Run-Level Character Substitution Function (Preserves Fonts & Styles)
                        def format_preserved_replace(target_doc, token, replacement):
                            for paragraph in target_doc.paragraphs:
                                if token in paragraph.text:
                                    for run in paragraph.runs:
                                        if token in run.text:
                                            run.text = run.text.replace(token, replacement)
                            
                            for table in target_doc.tables:
                                for row in table.rows:
                                    for cell in row.cells:
                                        for paragraph in cell.paragraphs:
                                            if token in paragraph.text:
                                                for run in paragraph.runs:
                                                    if token in run.text:
                                                        run.text = run.text.replace(token, replacement)
                                                        
                            for section in target_doc.sections:
                                for paragraph in section.header.paragraphs:
                                    if token in paragraph.text:
                                        for run in paragraph.runs:
                                            if token in run.text:
                                                run.text = run.text.replace(token, replacement)
                                for paragraph in section.footer.paragraphs:
                                    if token in paragraph.text:
                                        for run in paragraph.runs:
                                            if token in run.text:
                                                run.text = run.text.replace(token, replacement)

                        # Execute font-safe character substitutions
                        format_preserved_replace(doc, "{{CLIENT_NAME}}", client_name.strip())
                        format_preserved_replace(doc, "{{LOCATION}}", client_location.strip())
                        format_preserved_replace(doc, "{{RISK_OPERATIONAL_PROCEDURES}}", dynamic_risk_text)

                        output_filename = f"{formatted_sheet_name}_Tailored_FSMS.docx"
                        doc.save(output_filename)
                        st.success("🟢 Format-preserved executive manuals compiled cleanly.")
                        
                        # Expose the download button portal
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
                        st.error(f"Word Engine Token Modification Failure: {e}")
