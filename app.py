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

# --- THE SETTINGS ---
BASE_SCORE = 1000

if 'custom_findings' not in st.session_state:
    st.session_state.custom_findings = [{"note": "", "level": "None (No deduction)", "changelog": False}]

def add_custom_finding():
    st.session_state.custom_findings.append({"note": "", "level": "None (No deduction)", "changelog": False})

st.title("📋 Dynamic FSMS System")

# --- APP NAVIGATION (TABS) ---
tab1, tab2 = st.tabs(["📋 Conduct Audit", "📈 Analytics Dashboard"])

# ==========================================
# TAB 1: THE AUDIT FORM
# ==========================================
with tab1:
    st.subheader("Audit Details")
    col1, col2 = st.columns(2)
    with col1:
        establishment_name = st.text_input("Establishment Name:", value="Tata's Chicks")
    with col2:
        fsco_name = st.text_input("Lead Auditor / FSCO:", value="Jake-Edwards L. Yboa")
        
    audit_date = st.date_input("What is the date of the audit?", datetime.date.today())

    st.divider()

    # --- THE FULL CHECKLIST DATA ---
    MASTER_CHECKLIST = {
        "Module 1: Personnel Hygiene": [
            {"Fail?": False, "ID": "1.1", "Description": "Staff observed washing hands for 20s before cooking.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "1.2", "Description": "Handwashing observed after touching face, phone, or trash.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "1.3", "Description": "No bare-hand contact with Ready-to-Eat (RTE) pasta/bread.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "1.4", "Description": "Service gloves changed when soiled or task switching.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "1.5", "Description": "Hand sinks fully stocked with soap & paper towels.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "1.6", "Description": "All kitchen staff wearing effective hair/beard nets.", "Class": "L3", "Notes": ""},
            {"Fail?": False, "ID": "1.7", "Description": "No jewelry worn except for a plain wedding band.", "Class": "L3", "Notes": ""},
            {"Fail?": False, "ID": "1.8", "Description": "Uniforms are clean; no staff working in personal clothes.", "Class": "L3", "Notes": ""},
            {"Fail?": False, "ID": "1.9", "Description": "[LOG CHECK] LOG-GHP-01 current and signed by manager.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "1.10", "Description": "Staff can correctly explain the '48-hour sickness rule.'", "Class": "L2", "Notes": ""}
        ],
        "Module 2: Thermal Control": [
            {"Fail?": False, "ID": "2.1", "Description": "Fried Chicken batch internal temp >= 165 F for 15s.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "2.2", "Description": "Probe thermometers sanitized before/after each use.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "2.3", "Description": "[LOG CHECK] LOG-COOK-01 shows entries for every batch.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "2.4", "Description": "No room-temp thawing observed on prep tables.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "2.5", "Description": "Pasta cooled from 135 F to 70 F within 2 hours.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "2.6", "Description": "Chiller/Reach-in units maintain food temp <= 41 F.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "2.7", "Description": "Freezer maintains food solid at <= 0 F.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "2.8", "Description": "Permanent hanging thermometers present in all units.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "2.9", "Description": "[LOG CHECK] LOG-TEMP-01 (AM/PM checks) has no gaps.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "2.10", "Description": "LOG-CAL-01 (Weekly Ice point) is up to date.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "2.11", "Description": "Digital probes are accurate within 2 F.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "2.12", "Description": "Thawing items stored on the bottom shelf of refrigeration.", "Class": "L2", "Notes": ""}
        ],
        "Module 3: Preparation & Cross-Contamination": [
            {"Fail?": False, "ID": "3.1", "Description": "Breading flour sifted every 2 hours.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "3.2", "Description": "Breading 'dip' water changed and basin sanitized.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "3.3", "Description": "[LOG CHECK] LOG-BREAD-01 is initialed and current.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "3.4", "Description": "Red tongs used for raw chicken; Green/White for RTE.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "3.5", "Description": "Sifters and breading bins are stainless steel/food-grade.", "Class": "L3", "Notes": ""},
            {"Fail?": False, "ID": "3.6", "Description": "Separation of at least 4ft maintained between raw and RTE.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "3.7", "Description": "Raw chicken stored strictly below cooked pasta/veg.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "3.8", "Description": "Wiping cloths stored in sanitizer buckets between uses.", "Class": "L2", "Notes": ""}
        ],
        "Module 4: Supply Chain & Traceability": [
            {"Fail?": False, "ID": "4.1", "Description": "Incoming TCS deliveries <= 41 F.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "4.2", "Description": "[LOG CHECK] LOG-REC-01 includes temp data.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "4.3", "Description": "All prep containers labeled with Prod Date + Expiry.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "4.4", "Description": "Open dry goods (flour/pasta) decanted or sealed.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "4.5", "Description": "[LOG CHECK] LOG-TRACE-01 links Commissary # to Batch ID.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "4.6", "Description": "FIFO rotation followed (Older stock in front).", "Class": "L3", "Notes": ""},
            {"Fail?": False, "ID": "4.7", "Description": "No expired ingredients found in storage or prep.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "4.8", "Description": "Packaging is free of leaks, dents, or signs of tampering.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "4.9", "Description": "Food stored 6 inches off the floor on approved racking.", "Class": "L3", "Notes": ""},
            {"Fail?": False, "ID": "4.10", "Description": "Only approved chemicals used (Sanitizer/Degreaser).", "Class": "L2", "Notes": ""}
        ],
        "Module 5: Sanitation, Pests & Infrastructure": [
            {"Fail?": False, "ID": "5.1", "Description": "3-Basin manual setup active (Sink 1, Sink 2, Tub 3).", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "5.2", "Description": "Sanitizer (Chlorine/Quat) at correct ppm.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "5.3", "Description": "All utensils/pans air-dried; no towels used.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "5.4", "Description": "[LOG CHECK] LOG-CLN-01 identifies D/W tasks completed.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "5.5", "Description": "No evidence of rodent droppings or gnaw marks.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "5.6", "Description": "No active fly or cockroach activity in food zones.", "Class": "L1", "Notes": ""},
            {"Fail?": False, "ID": "5.7", "Description": "Hole in the back door remains permanently sealed.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "5.8", "Description": "Grease trap waste layer < 25% of total depth.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "5.9", "Description": "Broken floor tiles repaired (Harborage prevention).", "Class": "L3", "Notes": ""},
            {"Fail?": False, "ID": "5.10", "Description": "PCO professional service report on file.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "5.11", "Description": "Exhaust hood filters are free of dripping grease.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "5.12", "Description": "All light bulbs in kitchen are shielded or shatterproof.", "Class": "L3", "Notes": ""},
            {"Fail?": False, "ID": "5.13", "Description": "Handwashing reminder signs posted at all sinks.", "Class": "L3", "Notes": ""},
            {"Fail?": False, "ID": "5.14", "Description": "Floor drains are screened, cleaned, and free of odors.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "5.15", "Description": "Trash bins are covered and emptied frequently.", "Class": "L2", "Notes": ""},
            {"Fail?": False, "ID": "5.16", "Description": "All non-food contact surfaces are clean to sight/touch.", "Class": "L2", "Notes": ""}
        ]
    }

    edited_modules = {}

    for module_name, checkpoints in MASTER_CHECKLIST.items():
        with st.expander(f"📁 {module_name}", expanded=False):
            df = pd.DataFrame(checkpoints)
            edited_df = st.data_editor(
                df,
                column_config={
                    "Fail?": st.column_config.CheckboxColumn("Fail?", default=False),
                    "ID": st.column_config.TextColumn("Ref ID", disabled=True),
                    "Description": st.column_config.TextColumn("Checkpoint", disabled=True),
                    "Class": st.column_config.TextColumn("Class", disabled=True),
                    "Notes": st.column_config.TextColumn("Notes / Evidence")
                },
                hide_index=True,
                use_container_width=True,
                key=module_name 
            )
            edited_modules[module_name] = edited_df

    st.divider()

    # --- CUSTOM FINDINGS ---
    st.subheader("➕ Add Custom Findings (On-the-Fly)")
    for i, finding in enumerate(st.session_state.custom_findings):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            finding["note"] = st.text_input(f"Violation Note #{i+1}", value=finding["note"], key=f"note_{i}")
        with col2:
            options = ["None (No deduction)", "L1 Critical (-25 pts)", "L2 Major (-10 pts)", "L3 Minor (-2 pts)"]
            finding["level"] = st.selectbox("Risk Level", options, index=options.index(finding["level"]), key=f"lvl_{i}")
        with col3:
            st.write(" ")
            st.write(" ")
            finding["changelog"] = st.checkbox("Add to Changelog", value=finding["changelog"], key=f"log_{i}")

    st.button("➕ Add Another Custom Finding", on_click=add_custom_finding)
    st.divider()

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

    # --- THE ON-DEMAND AI ACTION GUIDE ---
    st.subheader("🚨 On-Site Action Guide")
    if st.button("💡 Consult SOPs for Immediate Actions"):
        current_failures = get_all_failures()
        
        if len(current_failures) == 0:
            st.success("No deviations flagged yet! Everything looks good.")
        else:
            company_standards = ""
            try:
                for filename in os.listdir("standards"):
                    if filename.endswith(".docx"):
                        doc = docx.Document(os.path.join("standards", filename))
                        company_standards += f"\n--- {filename} ---\n" + "\n".join([p.text for p in doc.paragraphs])
            except Exception:
                company_standards = "WARNING: Could not read standards folder."
                
            with st.spinner("Consulting Tata's Chicks SOPs for immediate fixes..."):
                guide_prompt = f"""
                You are the FSCO for {establishment_name}. I am currently auditing the kitchen.
                Here are the items that just failed: {current_failures}
                
                Based STRICTLY on the following company SOPs, tell me what EXACT immediate physical action I need to instruct the staff to take right now to fix these specific issues.
                Do not give me root causes or long-term preventive actions. Just short, bulleted immediate instructions.
                
                SOPs:
                {company_standards}
                """
                try:
                    response = model.generate_content(guide_prompt)
                    st.warning(response.text)
                except Exception as e:
                    st.error(f"Error consulting SOPs: {e}")

    st.divider()

    # --- THE MASTER ENGINE (Final Report Generator) ---
    if st.button("Calculate, Save, & Generate Final Report"):
        
        deductions = 0
        count_L1, count_L2, count_L3 = 0, 0, 0
        changelog_items = []
        failed_items = get_all_failures()
        failed_items_formatted = "\n".join([f"- {item}" for item in failed_items]) if failed_items else "No violations found."
        
        for item in failed_items:
            if "[L1]" in item: 
                deductions += 25
                count_L1 += 1
            elif "[L2]" in item: 
                deductions += 10
                count_L2 += 1
            elif "[L3]" in item: 
                deductions += 2
                count_L3 += 1
                
        for finding in st.session_state.custom_findings:
            if finding["note"].strip() != "" and finding["changelog"]:
                changelog_items.append(finding["note"])
            
        final_score = (1 - (deductions / BASE_SCORE)) * 100
        
        if final_score >= 95: rating = "Excellent (95-100%)"
        elif final_score >= 85: rating = "Good (85-94%)"
        elif final_score >= 75: rating = "Okay (75-84%)"
        else: rating = "Needs Improvement (<75%)"
        
        st.write(f"**Total Deductions:** {deductions}")
        st.write(f"**Final Score:** {final_score:.1f}% - {rating}")
        
        # --- NEW: FETCH PROGRESS DATA BEFORE SAVING NEW AUDIT ---
        progress_context = ""
        with st.spinner("Analyzing historical trends and saving data..."):
            try:
                sheet = gc.open("Audit_Database").sheet1
                existing_data = sheet.get_all_values()
                
                # Search backwards through the sheet for the last time we audited THIS establishment
                previous_score = None
                for row in reversed(existing_data):
                    # Ensure the row has the new format (Date, Establishment, Score, etc.)
                    if len(row) >= 5 and row[1] == establishment_name:
                        try:
                            previous_score = float(row[2].replace('%', ''))
                            break # We found the most recent past audit!
                        except ValueError:
                            continue
                            
                # Calculate the Trend for Gemini
                if previous_score is not None:
                    diff = final_score - previous_score
                    if diff > 0:
                        trend = f"Improved by {diff:.1f}%"
                    elif diff < 0:
                        trend = f"Declined by {abs(diff):.1f}%"
                    else:
                        trend = "Unchanged"
                    progress_context = f"Previous Audit Score: {previous_score:.1f}% | Current Score: {final_score:.1f}% | Trajectory: {trend}"
                else:
                    progress_context = "No previous historical data found. This is the baseline audit."
                    
                # Now append the NEW audit data to the sheet
                violations_text = " | ".join(failed_items)
                if violations_text == "" : violations_text = "No violations found."
                sheet.append_row([str(audit_date), establishment_name, f"{final_score:.1f}%", deductions, violations_text])
                st.success("💾 Audit data saved successfully to Google Sheets!")
                
            except Exception as e:
                st.error(f"Could not save to Google Sheets or fetch history. Diagnostic Error: {e}")
                progress_context = "Historical data unavailable due to database error."

        st.divider()
        st.subheader("🤖 Executive Summary")
        
        if len(changelog_items) > 0:
            changelog_prompt = "\n".join([f"- {item}" for item in changelog_items])
        else:
            changelog_prompt = "No dynamic updates required for this cycle."

        company_standards = ""
        try:
            for filename in os.listdir("standards"):
                if filename.endswith(".docx"):
                    doc = docx.Document(os.path.join("standards", filename))
                    company_standards += f"\n--- {filename} ---\n" + "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            company_standards = f"WARNING: Could not read standards folder. Error: {e}"
        
        with st.spinner(f"Gemini is generating the final official report..."):
            prompt = f"""
            You are an expert Lead Food Safety Compliance Officer (FSCO) for {establishment_name}. 
            I just finished an audit on {audit_date}. 
            The final score is {final_score}% ({deductions} points in deductions). 
            The specific violations found were: 
            {failed_items_formatted}
            
            CRITICAL RULEBOOK ({establishment_name} PRPs & SOPs):
            You MUST base your Root Cause analysis and Preventive Actions EXACTLY on these company standards. 
            Do not invent generic solutions if a solution exists in these rules. 
            ---
            {company_standards}
            ---
            
            Write a detailed, highly clinical Audit Executive Summary Report.
            
            CRITICAL FORMATTING RULES:
            - ONLY use **bold** text for entire lines that are section titles or headers.
            - DO NOT use inline bolding inside of paragraphs.
            
            Format the report STRICTLY with these sections exactly as named:

            **1. Executive Summary**
            Objective: Summarize the surveillance audit purpose.
            Current Compliance Status: State the score.
            Administrative Breakdown: Hypothesize the root cause of the systemic failures based on our standards.
            Key Verdict: Give a strict directive for immediate next steps.

            **2. FSMS Administration: Changelog**
            Based on the auditor's explicit instructions, here are the items that MUST be added to the manual's changelog:
            {changelog_prompt}
            Format this cleanly. If it says "No dynamic updates required", output exactly that.

            **3. Audit Scoring & Finding Summary**
            Write exactly: "See quantitative table below."

            **3.2 Detailed Finding & Resolution Plan**
            Provide a clean list of the specific violations found.

            **4. Corrective and Preventive Action (CAPA) Summary**
            For every L1 and L2 violation, provide a recommended action plan. Number each violation sequentially (e.g., 1., 2., 3.). 
            Format EXACTLY like this:
            1. Issue: (State the violation)
            Immediate Correction: (What to do today)
            Root Cause: (Hypothesize why it happened)
            Preventive Action: (How to stop it happening again)

            **5. Mandatory Compliance Toolkit**
            List any physical safety equipment that must be procured based on the specific violations.

            **6. Historical Progress Summary**
            Data: [{progress_context}]
            Provide a concise, professional 1-2 sentence commentary on the facility's compliance trajectory based on the provided data.
            """
            
            try:
                response = model.generate_content(prompt)
                st.write(response.text.replace('**', ''))
                
                pdf = FPDF()
                pdf.add_page()
                
                pdf.set_font("Times", 'B', 12)
                pdf.cell(0, 6, txt="FSCO Monthly Surveillance & Verification Report", ln=True)
                pdf.set_font("Times", '', 9)
                pdf.cell(0, 5, txt=f"Establishment: {establishment_name}", ln=True)
                pdf.cell(0, 5, txt=f"Lead Auditor/FSCO: {fsco_name}", ln=True)
                pdf.cell(0, 5, txt=f"Audit Date: {audit_date}", ln=True)
                pdf.ln(5)
                
                safe_text = response.text.encode('latin-1', 'replace').decode('latin-1')
                
                for line in safe_text.split('\n'):
                    line = line.strip()
                    
                    if not line:
                        pdf.ln(2)
                        continue
                    
                    if line.startswith('**') and line.endswith('**'):
                        header_text = line.replace('**', '')
                        pdf.set_font("Times", 'B', 11)
                        pdf.ln(3)
                        pdf.multi_cell(0, 6, header_text)
                        
                        if "3. Audit Scoring" in header_text:
                            pdf.set_font("Times", 'B', 10)
                            pdf.cell(0, 6, txt="3.1 Quantitative Audit Result", ln=True)
                            pdf.set_font("Times", '', 9)
                            pdf.cell(0, 6, txt="The score is derived from a 1000-point base evaluating 60+ checkpoints across 5 Operational Modules.", ln=True)
                            pdf.ln(2)
                            
                            pdf.set_font("Times", 'B', 9)
                            pdf.cell(50, 6, "Metric", border=1, align='C')
                            pdf.cell(30, 6, "Findings", border=1, align='C')
                            pdf.cell(110, 6, "Point Deduction", border=1, align='C', ln=True)
                            
                            pdf.set_font("Times", '', 9)
                            pdf.cell(50, 6, "L1: Critical Deviations", border=1)
                            pdf.cell(30, 6, str(count_L1), border=1, align='C')
                            pdf.cell(110, 6, f"-{count_L1 * 25} pts", border=1, align='C', ln=True)
                            
                            pdf.cell(50, 6, "L2: Major Deviations", border=1)
                            pdf.cell(30, 6, str(count_L2), border=1, align='C')
                            pdf.cell(110, 6, f"-{count_L2 * 10} pts", border=1, align='C', ln=True)
                            
                            pdf.cell(50, 6, "L3: Minor Deviations", border=1)
                            pdf.cell(30, 6, str(count_L3), border=1, align='C')
                            pdf.cell(110, 6, f"-{count_L3 * 2} pts", border=1, align='C', ln=True)
                            
                            pdf.set_font("Times", 'B', 9)
                            pdf.cell(50, 6, "Final Compliance Score", border=1)
                            pdf.cell(30, 6, f"{final_score:.1f}%", border=1, align='C')
                            pdf.cell(110, 6, f"Rating: {rating}", border=1, align='C', ln=True)
                            pdf.ln(5)
                    
                    elif ":" in line and len(line.split(":")[0]) < 40:
                        parts = line.split(":", 1)
                        pdf.set_font("Times", 'B', 9)
                        pdf.write(5, parts[0] + ": ")
                        pdf.set_font("Times", '', 9)
                        pdf.write(5, parts[1].strip() + "\n")
                        pdf.ln(1) 
                        
                    else:
                        pdf.set_font("Times", '', 9)
                        pdf.multi_cell(0, 5, line.replace('**', ''))
                
                pdf_filename = f"Audit_Report_{audit_date}.pdf"
                pdf.output(pdf_filename)
                
                with open(pdf_filename, "rb") as pdf_file:
                    PDFbyte = pdf_file.read()

                st.download_button(
                    label="📥 Download Official Executive Summary PDF",
                    data=PDFbyte,
                    file_name=pdf_filename,
                    mime='application/octet-stream'
                )
                
                os.remove(pdf_filename)
                    
            except Exception as e:
                st.error(f"Diagnostic Error: {e}")

# ==========================================
# TAB 2: ANALYTICS DASHBOARD
# ==========================================
with tab2:
    st.subheader("📈 Audit Progress Dashboard")
    st.write("Track the historical performance of your establishments based on saved Google Sheets data.")
    
    if st.button("🔄 Refresh Dashboard Data"):
        with st.spinner("Fetching data from the Google Sheets vault..."):
            try:
                sheet = gc.open("Audit_Database").sheet1
                data = sheet.get_all_values()
                
                # Make sure there is at least a header row AND one data row
                if len(data) > 1: 
                    # Put the data (skipping the header row) into pandas
                    df = pd.DataFrame(data[1:])
                    
                    # Force our standard internal names onto the first 5 columns
                    df = df.iloc[:, :5]
                    df.columns = ["Date", "Establishment", "Score", "Deductions", "Violations"]
                    
                    # Clean the data safely
                    df["Score"] = df["Score"].astype(str).str.replace("%", "").str.strip()
                    df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
                    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                    
                    # Drop bad/empty rows and sort chronologically
                    df = df.dropna(subset=["Score", "Date"])
                    df = df.sort_values(by="Date")
                    
                    # Draw the chart
                    st.line_chart(data=df, x="Date", y="Score", use_container_width=True)
                    
                    st.write("**Raw Historical Data:**")
                    st.dataframe(df, use_container_width=True)
                    
                else:
                    st.info("No audit data found in the database yet.")
                    
            except Exception as e:
                st.error(f"Could not load dashboard. Diagnostic Error: {e}")
