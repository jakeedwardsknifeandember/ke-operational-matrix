import os
import json
import datetime
import smtplib
import re
import pandas as pd

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

DRAFT_FILE_PATH = "audit_draft_backup.json"
USERS_FILE_PATH = "users.json"

def get_secret(st, key, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default

def load_users(st):
    if not os.path.exists(USERS_FILE_PATH):
        admin_pass = get_secret(st, "ADMIN_PASSWORD", get_secret(st, "APP_PASSWORD", "admin123"))
        default_users = {
            "admin": {
                "password": admin_pass,
                "role": "admin",
                "full_name": "Jake-Edwards L. Yboa",
                "assigned_concepts": ["ALL"]
            }
        }
        with open(USERS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=2)
        return default_users
    try:
        with open(USERS_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users_data):
    try:
        with open(USERS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(users_data, f, indent=2)
        return True
    except Exception:
        return False

def save_audit_draft(concept_name, est_name, branch_loc, fsco, date_val, notes, custom_f, edited_mods):
    try:
        module_snapshots = {}
        for mod_name, mod_df in edited_mods.items():
            if isinstance(mod_df, pd.DataFrame):
                module_snapshots[mod_name] = mod_df.to_dict(orient="records")

        draft_payload = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "concept_name": concept_name,
            "establishment_name": est_name,
            "branch_name": branch_loc,
            "fsco_name": fsco,
            "audit_date": str(date_val),
            "auditor_notes": notes,
            "custom_findings": custom_f,
            "module_states": module_snapshots
        }
        
        with open(DRAFT_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(draft_payload, f, indent=2)
        return True
    except Exception:
        return False

def clear_audit_draft():
    if os.path.exists(DRAFT_FILE_PATH):
        try:
            os.remove(DRAFT_FILE_PATH)
        except Exception:
            pass

def _clean_str(val):
    """Sanitizes punctuation, quotes, whitespace, and casing for foolproof Google Sheet matching."""
    if not val:
        return ""
    s = str(val).strip().lower()
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def sync_sheets_and_fetch_history(gc, active_sheet_name, establishment_name, branch_name, audit_date, final_score, deductions, failed_items):
    """Logs numerical row to Google Sheets and calculates previous baseline trend using complete client label."""
    full_label = f"{establishment_name} - {branch_name}" if (establishment_name and branch_name) else (establishment_name or branch_name or "Store")
    
    if gc is None:
        return f"Historical data unavailable for {full_label} (Database connection unconfigured)."
        
    try:
        sheet = gc.open(active_sheet_name).sheet1
        existing_data = sheet.get_all_values()
        
        target_est = _clean_str(establishment_name)
        target_branch = _clean_str(branch_name)
        
        previous_score = None
        
        # Scan backward from most recent historical records
        for row in reversed(existing_data):
            if not row or len(row) < 2:
                continue
                
            clean_row = [_clean_str(cell) for cell in row]
            raw_row = [str(cell).strip() for cell in row]
            
            # Skip header rows
            if any(h in clean_row[0] for h in ["date", "brand", "establishment", "score"]):
                continue
                
            # Check brand match
            est_match = False
            if len(clean_row) > 1 and clean_row[1]:
                if target_est == clean_row[1] or target_est in clean_row[1] or clean_row[1] in target_est:
                    est_match = True
            
            if not est_match:
                continue
                
            # Check branch match if branch is provided
            branch_match = True
            if target_branch:
                branch_match = False
                if len(clean_row) > 2 and clean_row[2]:
                    if target_branch == clean_row[2] or target_branch in clean_row[2] or clean_row[2] in target_branch:
                        branch_match = True
                elif len(clean_row) > 1 and target_branch in clean_row[1]:
                    branch_match = True
            
            if not branch_match:
                continue
                
            # Extract numeric score percentage from columns
            for col_idx in range(len(raw_row) - 1, 0, -1):
                val_str = raw_row[col_idx].replace('%', '').strip()
                try:
                    score_val = float(val_str)
                    if 0.0 <= score_val <= 100.0:
                        previous_score = score_val
                        break
                except ValueError:
                    continue
            
            if previous_score is not None:
                break
                    
        if previous_score is not None:
            diff = final_score - previous_score
            trend = f"Improved by {diff:.2f}%" if diff > 0 else (f"Declined by {abs(diff):.2f}%" if diff < 0 else "Unchanged")
            progress_context = f"Previous Audit Score ({full_label}): {previous_score:.2f}% | Current Score: {final_score:.2f}% | Trajectory: {trend}"
        else:
            progress_context = f"No previous historical data found for {full_label}. This is the baseline audit."
            
        violations_text = " | ".join(failed_items) if failed_items else "No violations found."
        sheet.append_row([
            str(audit_date), 
            establishment_name, 
            branch_name, 
            f"{final_score:.2f}%", 
            deductions, 
            violations_text
        ])
        return progress_context
    except Exception as e:
        return f"Historical data unavailable for {full_label} due to database error: {e}"

def auto_email_report(st, recipient_email, pdf_path, client_name, branch_name, score, status, cc_email=None):
    """Dispatches automated email report with optional stakeholder CC recipient."""
    smtp_user = get_secret(st, "smtp_username")
    smtp_server_val = get_secret(st, "smtp_server")
    smtp_port_val = get_secret(st, "smtp_port")
    smtp_pass = get_secret(st, "smtp_password")

    if not all([smtp_user, smtp_server_val, smtp_port_val, smtp_pass]):
        st.error("Missing SMTP credentials in secrets configuration.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Knife & Ember <{smtp_user}>"
        msg['To'] = recipient_email
        
        if cc_email and str(cc_email).strip():
            msg['Cc'] = str(cc_email).strip()
            
        full_title = f"{client_name} - {branch_name}" if branch_name else client_name
        msg['Subject'] = f"Food Safety Audit Report: {full_title} - {score:.2f}% ({status})"
        
        body = f"""Dear Management,

Please find attached the official FSCO Monthly Surveillance & Verification Report for {full_title}.

Audit Execution Date: {datetime.date.today()}
Final Verification Score: {score:.2f}%
Current Operational Status: {status}

This document serves as an official record of operational safety metrics. Required corrective actions (CAPA) must be initiated within the mandated 24-48 hour parameters.

Best regards,
Jake-Edwards L. Yboa, FSCO
Lead Auditor | Knife & Ember Food Consultancy Services
"""
        msg.attach(MIMEText(body, 'plain'))
        
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(pdf_path)}")
            msg.attach(part)
            
        server = smtplib.SMTP(smtp_server_val, int(smtp_port_val))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to deliver automated email: {e}")
        return False