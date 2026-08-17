import streamlit as st
import datetime
import pandas as pd
import gspread
import os
import json
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas

# IMPORT ISOLATED MODULES
from ai_engine import extract_concept_only, read_company_standards, generate_ai_report, generate_sop_guide
from pdf_generator import generate_pdf_report
from db_handler import get_secret, load_users, save_users, save_audit_draft, clear_audit_draft, sync_sheets_and_fetch_history, auto_email_report, DRAFT_FILE_PATH
from ui_components import render_login_screen

# --- SYSTEM CONSTANTS ---
PRIMARY_RECIPIENT_EMAIL = "jakeedwards.knifeandember@gmail.com"
BASE_SCORE = 1000

# --- SECURE CLOUD SETUP ---
gemini_key = get_secret(st, "GEMINI_API_KEY")

gc = None
gcp_secret = get_secret(st, "gcp_service_account")
if gcp_secret:
    try:
        credentials = json.loads(gcp_secret)
        gc = gspread.service_account_from_dict(credentials)
    except Exception:
        gc = None

# --- DYNAMIC CHECKLIST LOADER ---
def load_all_checklists():
    checklists = {}
    checklists_dir = "checklists"
    if os.path.exists(checklists_dir) and os.path.isdir(checklists_dir):
        for filename in os.listdir(checklists_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(checklists_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        checklists[data.get("concept_name", filename)] = data
                except Exception:
                    pass
    if not checklists:
        checklists["Default Checklist"] = {
            "concept_name": "Default",
            "folder_slug": "default",
            "sheet_name": "Audit_Database",
            "checklist": {"Module 1: General Hygiene": [{"Fail?": False, "ID": "1.1", "Description": "General sanitation observed.", "Class": "L1", "Notes": ""}]}
        }
    return checklists

CHECKLIST_LIBRARY = load_all_checklists()

# --- APP MEMORY SHIELD ---
if 'custom_findings' not in st.session_state:
    st.session_state.custom_findings = [{"note": "", "level": "None (No deduction)", "changelog": False}]
if 'camera_snaps' not in st.session_state:
    st.session_state.camera_snaps = []
if 'bulk_captions' not in st.session_state:
    st.session_state.bulk_captions = {}
if 'restored_module_states' not in st.session_state:
    st.session_state.restored_module_states = {}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_full_name' not in st.session_state:
    st.session_state.user_full_name = "Jake-Edwards L. Yboa"
if 'assigned_concepts' not in st.session_state:
    st.session_state.assigned_concepts = ["ALL"]
if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False
if 'cached_report_text' not in st.session_state:
    st.session_state.cached_report_text = ""
if 'cached_score_data' not in st.session_state:
    st.session_state.cached_score_data = {}
if 'saved_signature_data' not in st.session_state:
    st.session_state.saved_signature_data = None

def add_custom_finding():
    st.session_state.custom_findings.append({"note": "", "level": "None (No deduction)", "changelog": False})

def add_camera_slot():
    st.session_state.camera_snaps.append({"caption": "", "file": None})

# ==========================================
# GATEKEEPER LOGIN
# ==========================================
if not st.session_state.logged_in:
    registered_users = load_users(st)
    render_login_screen(registered_users)

# ==========================================
# MAIN APPLICATION
# ==========================================
if st.session_state.logged_in:
    st.sidebar.markdown("### Knife & Ember")
    st.sidebar.markdown("*Food Consultancy Services*")
    st.sidebar.caption(f"User: **{st.session_state.user_full_name}** ({st.session_state.user_role.upper()})")
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Control Panel")
    
    concept_keys = list(CHECKLIST_LIBRARY.keys())
    user_assigned = st.session_state.get('assigned_concepts', ["ALL"])
    selectable_concepts = concept_keys if (st.session_state.user_role == "admin" or "ALL" in user_assigned) else [c for c in concept_keys if c in user_assigned]
    if not selectable_concepts:
        selectable_concepts = concept_keys

    default_concept_idx = 0
    if 'restored_concept' in st.session_state and st.session_state.restored_concept in selectable_concepts:
        default_concept_idx = selectable_concepts.index(st.session_state.restored_concept)

    selected_concept_name = st.sidebar.selectbox("Select Checklist Profile:", options=selectable_concepts, index=default_concept_idx, format_func=extract_concept_only)
    active_concept_display = extract_concept_only(selected_concept_name)
    selected_profile = CHECKLIST_LIBRARY[selected_concept_name]
    active_folder_slug = selected_profile.get("folder_slug", "default")
    active_sheet_name = selected_profile.get("sheet_name", "Audit_Database")
    active_checklist = selected_profile.get("checklist", {})
    
    establishment_name = st.sidebar.text_input("Brand / Establishment Name:", value=st.session_state.get('restored_est_name', ""), placeholder="Enter store name")
    branch_name = st.sidebar.text_input("Branch / Location:", value=st.session_state.get('restored_branch_name', ""), placeholder="Enter store location")
    fsco_name = st.sidebar.text_input("Lead Auditor / FSCO:", value=st.session_state.get('restored_fsco_name', st.session_state.user_full_name))
    audit_date = st.sidebar.date_input("Audit Date:", datetime.date.today())
    client_cc_email = st.sidebar.text_input("Client / Store Manager Email (CC):", value="", placeholder="manager@store.com")
    
    st.sidebar.markdown("---")
    email_info_text = f"Primary Recipient:\n`{PRIMARY_RECIPIENT_EMAIL}`"
    if client_cc_email.strip():
        email_info_text += f"\n\nStakeholder CC:\n`{client_cc_email.strip()}`"
    st.sidebar.info(email_info_text)

    st.title("Operational Surveillance Suite")
    header_client_label = f"{establishment_name} - {branch_name}" if (establishment_name or branch_name) else "New Audit Inspection"
    st.markdown(f"**Active Client:** {header_client_label}")
    st.divider()

    tab1, tab2 = (st.tabs(["Conduct Operational Audit", "Portfolio Analytics & Account Management"]) if st.session_state.user_role == "admin" else (st.container(), None))

    with tab1:
        if os.path.exists(DRAFT_FILE_PATH):
            st.warning("Unsaved audit draft detected.")
            d_col1, d_col2 = st.columns([1, 4])
            with d_col1:
                if st.button("Restore Draft", use_container_width=True):
                    with open(DRAFT_FILE_PATH, "r", encoding="utf-8") as f:
                        draft_data = json.load(f)
                    st.session_state.restored_concept = draft_data.get("concept_name", selected_concept_name)
                    st.session_state.restored_est_name = draft_data.get("establishment_name", establishment_name)
                    st.session_state.restored_branch_name = draft_data.get("branch_name", branch_name)
                    st.session_state.restored_fsco_name = draft_data.get("fsco_name", fsco_name)
                    st.session_state.custom_findings = draft_data.get("custom_findings", [])
                    st.session_state.restored_notes = draft_data.get("auditor_notes", "")
                    st.session_state.restored_module_states = draft_data.get("module_states", {})
                    st.rerun()
            with d_col2:
                if st.button("Discard Draft", use_container_width=True):
                    clear_audit_draft()
                    st.rerun()

        st.subheader("Operational Checkpoints")
        edited_modules = {}
        for module_name, checkpoints in active_checklist.items():
            with st.expander(f"{module_name}", expanded=False):
                df = pd.DataFrame(st.session_state.restored_module_states.get(module_name, checkpoints))
                edited_df = st.data_editor(
                    df,
                    column_config={"Fail?": st.column_config.CheckboxColumn("Fail?", default=False), "ID": st.column_config.TextColumn("Ref ID", disabled=True), "Description": st.column_config.TextColumn("Checkpoint", disabled=True), "Class": st.column_config.TextColumn("Class", disabled=True), "Notes": st.column_config.TextColumn("Notes")},
                    hide_index=True, use_container_width=True, key=f"{selected_concept_name}_{module_name}"
                )
                edited_modules[module_name] = edited_df

        if st.sidebar.button("Save Draft Progress", use_container_width=True):
            if save_audit_draft(selected_concept_name, establishment_name, branch_name, fsco_name, audit_date, st.session_state.get("auditor_notes_field", ""), st.session_state.custom_findings, edited_modules):
                st.sidebar.success("Draft saved!")

        st.divider()
        st.subheader("Add Custom Findings")
        for i, finding in enumerate(st.session_state.custom_findings):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1: finding["note"] = st.text_input(f"Note #{i+1}", value=finding["note"], key=f"note_{i}")
            with col2: finding["level"] = st.selectbox("Risk Level", ["None (No deduction)", "L1 Critical (-25 pts)", "L2 Major (-10 pts)", "L3 Minor (-2 pts)"], index=["None (No deduction)", "L1 Critical (-25 pts)", "L2 Major (-10 pts)", "L3 Minor (-2 pts)"].index(finding["level"]), key=f"lvl_{i}")
            with col3: finding["changelog"] = st.checkbox("Changelog", value=finding["changelog"], key=f"log_{i}")

        st.button("Add Finding", on_click=add_custom_finding)
        st.divider()

        st.subheader("On-Site Photo Evidence Vault")
        uploaded_photos_data = []

        # 1. Bulk File Uploader (Supports .jpg, .jpeg, .png, .jfif, .webp)
        bulk_files = st.file_uploader(
            "Bulk Upload Photos (Select or drag multiple images):",
            type=["jpg", "jpeg", "png", "jfif", "webp"],
            accept_multiple_files=True,
            key="bulk_evidence_uploader"
        )

        if bulk_files:
            st.markdown(f"**Loaded {len(bulk_files)} Photo(s) for Report:**")
            for b_idx, b_file in enumerate(bulk_files):
                f_key = f"{b_file.name}_{b_file.size}"
                default_cap = st.session_state.bulk_captions.get(f_key, b_file.name.rsplit(".", 1)[0].replace("_", " ").replace("-", " "))
                
                b_col1, b_col2 = st.columns([1, 3])
                with b_col1:
                    st.image(b_file, width=120)
                with b_col2:
                    caption_val = st.text_input(f"Caption for Photo #{b_idx+1}:", value=default_cap, key=f"cap_bulk_{b_idx}")
                    st.session_state.bulk_captions[f_key] = caption_val
                    
                uploaded_photos_data.append({"file": b_file, "caption": caption_val})

        st.markdown("---")
        st.markdown("**Direct Camera Snap Evidence:**")
        
        # 2. Camera Snaps for Live On-Site Audits
        for c_idx, snap_item in enumerate(st.session_state.camera_snaps):
            c_col1, c_col2 = st.columns([3, 2])
            with c_col1:
                cam_file = st.camera_input(f"Live Camera Snap #{c_idx+1}", key=f"cam_live_{c_idx}")
            with c_col2:
                cam_caption = st.text_input(f"Snap Caption #{c_idx+1}", value=snap_item.get("caption", ""), key=f"cam_cap_{c_idx}")
            if cam_file:
                uploaded_photos_data.append({"file": cam_file, "caption": cam_caption})

        st.button("Add Camera Snap Slot", on_click=add_camera_slot)
        st.divider()

        auditor_notes = st.text_area("Auditor Notes:", value=st.session_state.get('restored_notes', ""), height=110, key="auditor_notes_field")
        st.divider()

        def get_all_failures():
            failures = []
            for m_name, df in edited_modules.items():
                for _, row in df[df["Fail?"] == True].iterrows():
                    failures.append(f"[{row['Class']}] {row['ID']} {row['Description']} - Notes: {row['Notes']}")
            for finding in st.session_state.custom_findings:
                if finding["note"].strip(): failures.append(f"[{finding['level'].split()[0]}] Custom Finding: {finding['note']}")
            return failures

        if st.button("Consult SOPs for Immediate Actions"):
            failures = get_all_failures()
            if not failures: st.success("No deviations flagged.")
            elif not gemini_key: st.error("Gemini API Key missing.")
            else:
                standards = read_company_standards(active_folder_slug, failures)
                try:
                    guide_res = generate_sop_guide(gemini_key, header_client_label, failures, standards)
                    st.warning(guide_res)
                except Exception as e:
                    st.error(f"Error consulting SOPs: {e}")

        st.divider()
        st.subheader("Verification Sign-Off")
        canvas_result = st_canvas(fill_color="rgba(255, 255, 255, 0)", stroke_width=3, stroke_color="#000000", background_color="#FFFFFF", height=150, width=400, drawing_mode="freedraw", key="fsco_signature_canvas")
        
        # Lock signature canvas pixels into session state to prevent state loss on UI reruns
        if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
            st.session_state.saved_signature_data = canvas_result.image_data
            
        if st.session_state.get('saved_signature_data') is not None and np.any(st.session_state.saved_signature_data[:, :, 3] > 0):
            st.caption("Signature captured and preserved in session memory.")
        st.divider()

        if st.button("Process Metrics & Generate Final Report", use_container_width=True):
            deductions, count_L1, count_L2, count_L3 = 0, 0, 0, 0
            changelog_items = []
            failed_items = get_all_failures()
            failed_items_formatted = "\n".join([f"- {item}" for item in failed_items]) if failed_items else "No violations found."
            
            for item in failed_items:
                if "[L1]" in item: deductions += 25; count_L1 += 1
                elif "[L2]" in item: deductions += 10; count_L2 += 1
                elif "[L3]" in item: deductions += 2; count_L3 += 1
                    
            for finding in st.session_state.custom_findings:
                if finding["note"].strip() and finding["changelog"]: changelog_items.append(finding["note"])
                
            final_score = round((1 - (deductions / BASE_SCORE)) * 100, 2)
            rating = "Excellent (95-100%)" if final_score >= 95 else ("Good (85-94%)" if final_score >= 85 else ("Okay (75-84%)" if final_score >= 75 else "Needs Improvement (<75%)"))
            
            st.session_state.cached_score_data = {"deductions": deductions, "final_score": final_score, "rating": rating, "count_L1": count_L1, "count_L2": count_L2, "count_L3": count_L3}
            progress_context = sync_sheets_and_fetch_history(gc, active_sheet_name, establishment_name, branch_name, audit_date, final_score, deductions, failed_items)

            changelog_prompt = "\n".join([f"- {item}" for item in changelog_items]) if changelog_items else "No dynamic updates required for this cycle."
            notes_prompt = auditor_notes.strip() if auditor_notes.strip() else "No additional auditor notes recorded for this cycle."
            company_standards = read_company_standards(active_folder_slug, failed_items)
            
            if not gemini_key:
                st.error("Gemini API Key missing.")
                st.session_state.report_generated = False
            else:
                with st.spinner("Generating official report..."):
                    try:
                        ai_report_text = generate_ai_report(gemini_key, header_client_label, audit_date, final_score, deductions, failed_items_formatted, changelog_prompt, notes_prompt, company_standards, progress_context)
                        st.session_state.cached_report_text = ai_report_text
                        st.session_state.report_generated = True
                        clear_audit_draft()
                    except Exception as e:
                        st.session_state.report_generated = False
                        st.error(f"API Generation Error: {e}")

        if st.session_state.get('report_generated', False):
            st.divider()
            
            scores = st.session_state.cached_score_data
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Score", f"{scores['final_score']:.2f}%")
            m_col2.metric("Deductions", f"-{scores['deductions']} pts")
            m_col3.metric("Status", scores['rating'].split()[0])
            st.write(st.session_state.cached_report_text)

            signature_saved = False
            sig_data_to_use = canvas_result.image_data if (canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0)) else st.session_state.get('saved_signature_data')
            
            if sig_data_to_use is not None and np.any(sig_data_to_use[:, :, 3] > 0):
                raw_sketch = Image.fromarray(sig_data_to_use.astype('uint8'), 'RGBA')
                rgb_signature = Image.new("RGB", raw_sketch.size, (255, 255, 255))
                rgb_signature.paste(raw_sketch, mask=raw_sketch.split()[3])
                rgb_signature.save("fsco_signature_temp.png", "PNG")
                signature_saved = True

            try:
                pdf_filename = generate_pdf_report(establishment_name, branch_name, fsco_name, audit_date, scores, st.session_state.cached_report_text, uploaded_photos_data, signature_saved)
                with st.spinner("Dispatching automated email..."):
                    if auto_email_report(st, PRIMARY_RECIPIENT_EMAIL, pdf_filename, establishment_name, branch_name, scores['final_score'], scores['rating'].split()[0], cc_email=client_cc_email):
                        disp_cc = f" (CC: `{client_cc_email.strip()}`)" if client_cc_email.strip() else ""
                        st.success(f"Report dispatched to `{PRIMARY_RECIPIENT_EMAIL}`{disp_cc}")
                if os.path.exists(pdf_filename): os.remove(pdf_filename)
            except Exception as e:
                st.error(f"PDF Delivery Error: {e}")

    if tab2:
        with tab2:
            admin_subtab1, admin_subtab2 = st.tabs(["Historical Metric Tracker", "Auditor Account Management"])
            with admin_subtab1:
                if st.button("Sync Database Records", use_container_width=True):
                    if gc:
                        sheet = gc.open(active_sheet_name).sheet1
                        data = sheet.get_all_values()
                        if len(data) > 1:
                            raw_df = pd.DataFrame(data[1:])
                            df = raw_df.iloc[:, :6] if raw_df.shape[1] >= 6 else raw_df.iloc[:, :5]
                            df.columns = ["Date", "Brand", "Branch", "Score", "Deductions", "Violations"] if raw_df.shape[1] >= 6 else ["Date", "Brand", "Score", "Deductions", "Violations"]
                            if "Branch" not in df.columns: df["Branch"] = "Main Branch"
                            df["Score"] = pd.to_numeric(df["Score"].astype(str).str.replace("%", "").str.strip(), errors="coerce")
                            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                            df = df.dropna(subset=["Score", "Date"]).sort_values(by="Date")
                            
                            sel_br = st.selectbox("Select Branch View:", options=["All Branches"] + sorted(list(df["Branch"].astype(str).unique())))
                            f_df = df if sel_br == "All Branches" else df[df["Branch"] == sel_br]
                            st.line_chart(data=f_df, x="Date", y="Score", use_container_width=True)
                            st.dataframe(f_df, use_container_width=True, hide_index=True)

            with admin_subtab2:
                current_users = load_users(st)
                with st.form("create_auditor_form"):
                    st.markdown("**Provision New Auditor Account**")
                    c1, c2, c3 = st.columns(3)
                    new_u = c1.text_input("Username", placeholder="e.g. auditor_john")
                    new_f = c2.text_input("Full Name", placeholder="e.g. John Doe, FSCO")
                    new_p = c3.text_input("Password", type="password", placeholder="Enter password")
                    assigned_mods = st.multiselect("Assign Allowed Store Concepts:", options=concept_keys, default=concept_keys, format_func=extract_concept_only)
                    
                    if st.form_submit_button("Create Auditor Account"):
                        u_key = new_u.strip().lower()
                        if not u_key or not new_p.strip() or not new_f.strip() or not assigned_mods:
                            st.error("All fields required.")
                        elif u_key in current_users:
                            st.error(f"Username '{u_key}' exists.")
                        else:
                            current_users[u_key] = {"password": new_p.strip(), "role": "auditor", "full_name": new_f.strip(), "assigned_concepts": assigned_mods}
                            if save_users(current_users):
                                st.success("Account created!")
                                st.rerun()

                st.divider()
                st.markdown("**Registered Account Registry**")
                user_list = [{"Username": u, "Full Name": d.get("full_name", "-"), "Access Role": d.get("role", "auditor").upper(), "Allowed Store Concepts": ("All Concepts (Admin)" if "ALL" in d.get("assigned_concepts", []) else ", ".join([extract_concept_only(c) for c in d.get("assigned_concepts", [])]))} for u, d in current_users.items()]
                st.dataframe(pd.DataFrame(user_list), use_container_width=True, hide_index=True)

                st.markdown("**Revoke Access**")
                deletable_usernames = [u for u, d in current_users.items() if d.get("role") != "admin"]
                if deletable_usernames:
                    r_col1, r_col2 = st.columns([3, 1])
                    target_revoke = r_col1.selectbox("Select Auditor Account to Revoke:", options=deletable_usernames)
                    if r_col2.button("Revoke Access", type="primary"):
                        del current_users[target_revoke]
                        save_users(current_users)
                        st.toast(f"Revoked: {target_revoke}")
                        st.rerun()

    st.sidebar.button("End Session (Log Out)", on_click=lambda: st.session_state.update(logged_in=False, user_role=None, user_full_name="Jake-Edwards L. Yboa", assigned_concepts=["ALL"], report_generated=False, cached_report_text=""), use_container_width=True)