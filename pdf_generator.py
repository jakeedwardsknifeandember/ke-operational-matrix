import os
import tempfile
import re
from fpdf import FPDF
from PIL import Image

def clean_unicode_text(text):
    """Converts special symbols and unicode characters to ASCII/Latin-1 for FPDF."""
    if not text:
        return ""
    replacements = {
        '\u2014': '-',
        '\u2013': '-',
        '\u201c': '"',
        '\u201d': '"',
        '\u2018': "'",
        '\u2019': "'",
        '\u2022': '*',
        '\u2026': '...',
        '\u2264': '<=',
        '\u2265': '>=',
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    
    # Remove inline LaTeX $...$
    text = re.sub(r'\$([^\$]+)\$', r'\1', text)
    return text.encode('latin-1', 'replace').decode('latin-1')

def preprocess_report_text(raw_text):
    """Inserts explicit line breaks, fixes headers, and auto-converts 'deg' notation to '°'."""
    if not raw_text:
        return ""

    text = raw_text

    # Forcefully convert 'deg' text into real degree symbols
    text = re.sub(r'(?i)\bdeg\s*F\b', '°F', text)
    text = re.sub(r'(?i)\bdeg\s*C\b', '°C', text)
    text = re.sub(r'(?i)\bdeg\b', '°', text)

    # Force FSMS Administration: Changelog onto a single unified line so the Grey Banner parser detects it
    text = re.sub(r'2\.\s*FSMS Administration\s*\n*\s*:\s*Changelog', '2. FSMS Administration: Changelog', text, flags=re.IGNORECASE)

    main_headers = [
        r'1\.\s*Executive Summary',
        r'2\.\s*FSMS Administration:\s*Changelog',
        r'3\.\s*Audit Scoring\s*&\s*Finding Summary',
        r'3\.1\s*Quantitative Audit Metric Breakdown',
        r'3\.2\s*Detailed Finding\s*&\s*Resolution Plan',
        r'4\.\s*Corrective and Preventive Action\s*\(CAPA\)\s*Summary',
        r'4\.\s*CAPA Summary',
        r'5\.\s*Mandatory Compliance Toolkit',
        r'6\.\s*Historical Progress Summary',
        r'7\.\s*Auditor Notes\s*&\s*Recommendations'
    ]
    for header in main_headers:
        text = re.sub(f'({header})', r'\n\1\n', text, flags=re.IGNORECASE)

    text = re.sub(r'(\d+\.\s*Issue:)', r'\n\1', text)

    sub_labels = [
        r'Objective:',
        r'Current Compliance Status:',
        r'Administrative Breakdown:',
        r'Key Verdict:',
        r'Immediate Correction:',
        r'Root Cause:',
        r'Preventive Action:',
        r'Data:'
    ]
    for label in sub_labels:
        text = re.sub(f'({label})', r'\n\1', text, flags=re.IGNORECASE)

    text = re.sub(r'(-?\s*\[L[123]\])', r'\n\1', text)

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def generate_pdf_report(establishment_name, branch_name, fsco_name, audit_date, scores, cached_report_text, uploaded_photos_data, signature_saved):
    """Compiles the Knife & Ember official verification PDF document."""
    pdf = FPDF()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()
    
    # 1. Header Logo Auto-Detection
    logo_path = None
    for p_logo in ["logo.png", "logo.jpg", "templates/logo.png", "templates/logo.jpg", "assets/logo.png"]:
        if os.path.exists(p_logo):
            logo_path = p_logo
            break

    if logo_path:
        pdf.image(logo_path, x=150, y=8, w=45)

    # 2. Document Header Block
    pdf.set_font("Times", 'B', 14)
    pdf.cell(135, 8, txt="FSCO Monthly Surveillance & Verification Report", ln=True, align='L')
    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(5)
    
    pdf.set_font("Times", 'B', 10)
    pdf.cell(42, 5, "Establishment Name:", ln=False)
    pdf.set_font("Times", '', 10)
    pdf.cell(0, 5, f"{establishment_name}", ln=True)

    pdf.set_font("Times", 'B', 10)
    pdf.cell(42, 5, "Branch/Location:", ln=False)
    pdf.set_font("Times", '', 10)
    pdf.cell(0, 5, f"{branch_name}", ln=True)
    
    pdf.set_font("Times", 'B', 10)
    pdf.cell(42, 5, "Lead Auditor/FSCO:", ln=False)
    pdf.set_font("Times", '', 10)
    pdf.cell(0, 5, f"{fsco_name}", ln=True)
    
    pdf.set_font("Times", 'B', 10)
    pdf.cell(42, 5, "Audit Operation Date:", ln=False)
    pdf.set_font("Times", '', 10)
    pdf.cell(0, 5, f"{audit_date}", ln=True)
    pdf.ln(5)

    # 3. Visual Score Badge Banner
    score_val = scores.get('final_score', 100.0)
    if score_val >= 95.0:
        bg_r, bg_g, bg_b = 220, 245, 230
        border_r, border_g, border_b = 40, 167, 69
        txt_r, txt_g, txt_b = 20, 100, 35
        status_label = "EXCELLENT (OPTIMAL COMPLIANCE)"
    elif score_val >= 85.0:
        bg_r, bg_g, bg_b = 255, 243, 205
        border_r, border_g, border_b = 255, 193, 7
        txt_r, txt_g, txt_b = 133, 100, 4
        status_label = "GOOD (STABLE COMPLIANCE)"
    else:
        bg_r, bg_g, bg_b = 248, 215, 218
        border_r, border_g, border_b = 220, 53, 69
        txt_r, txt_g, txt_b = 114, 28, 36
        status_label = "NEEDS IMPROVEMENT (CRITICAL ACTION REQUIRED)"

    banner_y = pdf.get_y()
    pdf.set_fill_color(bg_r, bg_g, bg_b)
    pdf.set_draw_color(border_r, border_g, border_b)
    pdf.rect(10, banner_y, 190, 10, 'DF')

    pdf.set_xy(10, banner_y + 2)
    pdf.set_font("Times", 'B', 10)
    pdf.set_text_color(txt_r, txt_g, txt_b)
    pdf.cell(190, 6, txt=f"VERIFICATION SCORE: {score_val:.2f}% | STATUS: {status_label}", align='C', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)
    
    formatted_text = preprocess_report_text(cached_report_text)
    safe_text = clean_unicode_text(formatted_text)
    
    MAIN_SECTION_KEYWORDS = [
        "1. Executive Summary",
        "2. FSMS Administration: Changelog",
        "3. Audit Scoring & Finding Summary",
        "3.2 Detailed Finding & Resolution Plan",
        "4. Corrective and Preventive Action (CAPA) Summary",
        "5. Mandatory Compliance Toolkit",
        "6. Historical Progress Summary",
        "7. Auditor Notes & Recommendations"
    ]

    SUB_LABELS = [
        "Objective:",
        "Current Compliance Status:",
        "Administrative Breakdown:",
        "Key Verdict:",
        "Immediate Correction:",
        "Root Cause:",
        "Preventive Action:",
        "Data:"
    ]

    lines = safe_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("3.2") or "Detailed Finding" in line:
            pdf.add_page()
            
        is_main_header = any(re.search(re.escape(title), line, re.IGNORECASE) for title in MAIN_SECTION_KEYWORDS)
        
        # 4.1 Grey Banner Section Headers
        if is_main_header:
            if pdf.get_y() > 230:
                pdf.add_page()

            pdf.ln(4)
            current_y = pdf.get_y()
            pdf.set_fill_color(240, 240, 240)
            pdf.rect(10, current_y, 190, 8, 'F')
            
            pdf.set_font("Times", 'B', 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, txt=line, ln=True, fill=True)
            pdf.ln(3)
            
            if "3. Audit Scoring" in line or "Finding Summary" in line:
                pdf.set_font("Times", 'B', 10)
                pdf.cell(0, 6, txt="3.1 Quantitative Audit Metric Breakdown", ln=True)
                pdf.set_font("Times", '', 9)
                pdf.cell(0, 5, txt="Defects weighted across a baseline threshold of 1000 Operational System points.", ln=True)
                pdf.ln(2)
                
                pdf.set_fill_color(220, 225, 230)
                pdf.set_font("Times", 'B', 9)
                pdf.cell(60, 7, "Risk Metric Classification", border=1, align='L', fill=True)
                pdf.cell(40, 7, "Deduction Weight", border=1, align='C', fill=True)
                pdf.cell(40, 7, "Observed Deviations", border=1, align='C', fill=True)
                pdf.cell(50, 7, "Total Point Deficit", border=1, align='C', fill=True, ln=True)
                
                pdf.set_font("Times", '', 9)
                pdf.cell(60, 6, "Critical Deviations", border=1)
                pdf.cell(40, 6, "-25 pts/item", border=1, align='C')
                pdf.cell(40, 6, str(scores.get('count_L1', 0)), border=1, align='C')
                pdf.cell(50, 6, f"-{scores.get('count_L1', 0) * 25} pts", border=1, align='C', ln=True)
                
                pdf.cell(60, 6, "Major Deviations", border=1)
                pdf.cell(40, 6, "-10 pts/item", border=1, align='C')
                pdf.cell(40, 6, str(scores.get('count_L2', 0)), border=1, align='C')
                pdf.cell(50, 6, f"-{scores.get('count_L2', 0) * 10} pts", border=1, align='C', ln=True)
                
                pdf.cell(60, 6, "Minor Deviations", border=1)
                pdf.cell(40, 6, "-2 pts/item", border=1, align='C')
                pdf.cell(40, 6, str(scores.get('count_L3', 0)), border=1, align='C')
                pdf.cell(50, 6, f"-{scores.get('count_L3', 0) * 2} pts", border=1, align='C', ln=True)
                
                pdf.set_fill_color(245, 245, 245)
                pdf.set_font("Times", 'B', 9)
                pdf.cell(60, 7, "Final Metrics Aggregation", border=1, fill=True)
                pdf.cell(40, 7, f"Score: {scores.get('final_score', 100.0):.2f}%", border=1, align='C', fill=True)
                
                total_observed_count = scores.get('count_L1', 0) + scores.get('count_L2', 0) + scores.get('count_L3', 0)
                pdf.cell(40, 7, f"{total_observed_count} Items", border=1, align='C', fill=True)
                pdf.cell(50, 7, f"-{scores.get('deductions', 0)} pts", border=1, align='C', fill=True, ln=True)
                pdf.ln(4)

        # 4.2 CAPA Issue Headers
        elif re.match(r'^\d+\.\s*Issue:', line, re.IGNORECASE) or line.startswith("Issue "):
            if pdf.get_y() > 240:
                pdf.add_page()
            pdf.ln(3)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            
            parts = line.split(":", 1)
            pdf.set_font("Times", 'B', 10)
            pdf.set_text_color(160, 30, 30)
            pdf.cell(0, 5, txt=parts[0] + ":", ln=True)
            
            if len(parts) > 1 and parts[1].strip():
                pdf.set_font("Times", 'B', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 5, txt=parts[1].strip())
            pdf.ln(1)

        # 4.3 Sub-Section Labels
        elif any(line.lower().startswith(label.lower()) for label in SUB_LABELS):
            parts = line.split(":", 1)
            label = parts[0].strip() + ":"
            body_val = parts[1].strip() if len(parts) > 1 else ""
            
            pdf.set_font("Times", 'B', 10)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(0, 5, txt=label, ln=True)
            
            if body_val:
                pdf.set_font("Times", '', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 5, txt=body_val)
            pdf.ln(2)

        # 4.4 Regular Body Paragraphs and Inline Colored Bullet Points
        else:
            pdf.set_font("Times", '', 10)
            
            # Extract just the tag (e.g., "- [L1]") to color it, keeping the rest black
            match = re.match(r'^(\s*-?\s*\[L([123])\])(.*)', line)
            if match:
                tag_str = match.group(1)
                level = match.group(2)
                body_str = match.group(3)
                
                # Set specific tag color
                if level == '1':
                    pdf.set_text_color(220, 53, 69)   # Red
                elif level == '2':
                    pdf.set_text_color(204, 153, 0)   # Dark Yellow / Amber
                elif level == '3':
                    pdf.set_text_color(40, 167, 69)   # Green
                
                pdf.write(5, tag_str + " ")
                
                # Reset to black for the description text
                pdf.set_text_color(0, 0, 0)
                pdf.write(5, body_str)
                pdf.ln(7) # Move cursor down and add standard spacing
            else:
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 5, txt=line)
                pdf.ln(2)

    # 5. Photographic Evidence Annex
    temp_image_files = []
    if uploaded_photos_data:
        if pdf.get_y() > 190:
            pdf.add_page()
        
        pdf.ln(4)
        current_y = pdf.get_y()
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(10, current_y, 190, 8, 'F')
        pdf.set_font("Times", 'B', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, txt="8. Photographic Evidence Log", ln=True, fill=True)
        pdf.ln(4)

        col_x_positions = [12, 105]
        col_width = 83

        for p_pair_idx in range(0, len(uploaded_photos_data), 2):
            pair = uploaded_photos_data[p_pair_idx:p_pair_idx+2]
            if pdf.get_y() > 180:
                pdf.add_page()

            row_start_y = pdf.get_y()
            max_row_bottom_y = row_start_y

            for c_offset, photo_item in enumerate(pair):
                u_file = photo_item["file"]
                cap_text = photo_item["caption"].strip() if photo_item["caption"].strip() else f"Field Evidence #{p_pair_idx + c_offset + 1}"
                x_pos = col_x_positions[c_offset]

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    img = Image.open(u_file)
                    img.convert("RGB").save(tmp.name)
                    tmp_path = tmp.name
                    temp_image_files.append(tmp_path)

                pdf.set_xy(x_pos, row_start_y)
                pdf.set_font("Times", 'B', 9)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(col_width, 4, txt=clean_unicode_text(f"Exhibit 8.{p_pair_idx + c_offset + 1}: {cap_text}"))
                
                caption_end_y = pdf.get_y() + 1

                with Image.open(tmp_path) as pil_img:
                    img_w, img_h = pil_img.size
                    calc_h = col_width * (img_h / img_w)

                pdf.image(tmp_path, x=x_pos, y=caption_end_y, w=col_width)
                col_bottom_y = caption_end_y + calc_h + 4

                if col_bottom_y > max_row_bottom_y:
                    max_row_bottom_y = col_bottom_y

            pdf.set_y(max_row_bottom_y)

    # 6. Signature Block
    if signature_saved and os.path.exists("fsco_signature_temp.png"):
        if pdf.get_y() > 210:
            pdf.add_page()
        
        pdf.ln(6)
        pdf.set_font("Times", 'B', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 5, txt="Authorized Verification Signature:", ln=True)
        pdf.ln(2)
        pdf.image("fsco_signature_temp.png", x=12, w=55)
        pdf.ln(2)
        pdf.set_font("Times", '', 9)
        pdf.cell(0, 4, txt=f"{fsco_name} | Certified Food Safety Officer", ln=True)
        pdf.cell(0, 4, txt="Knife & Ember Food Consultancy Services", ln=True)
        os.remove("fsco_signature_temp.png") 

    safe_est = "".join(c for c in establishment_name if c.isalnum() or c in (' ', '_', '-')).strip() if establishment_name else "Audit_Report"
    safe_br = "".join(c for c in branch_name if c.isalnum() or c in (' ', '_', '-')).strip()
    pdf_filename = f"{safe_est} ({safe_br}) - Executive Summary Report - {audit_date}.pdf" if safe_br else f"{safe_est} - Executive Summary Report - {audit_date}.pdf"

    pdf.output(pdf_filename)

    for tmp_img in temp_image_files:
        if os.path.exists(tmp_img):
            os.remove(tmp_img)

    return pdf_filename