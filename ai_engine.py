import os
import re
import docx
import google.generativeai as genai

def extract_concept_only(name):
    """Strips store establishment name and extracts concept in parentheses."""
    if not name:
        return ""
    if '(' in name and ')' in name:
        return name[name.find('(') + 1:name.rfind(')')].strip()
    return name.strip()

def sanitize_ai_output(text):
    """Strips fake section numbers and clause codes while preserving form codes and newlines."""
    if not text:
        return ""
    text = re.sub(r'\bSection\s+\d+(?:\.\d+)*\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bClause\s+\d+(?:\.\d+)*\b', '', text, flags=re.IGNORECASE)
    
    # Preserve newlines (\n) by only cleaning horizontal spaces and tabs
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'[ \t]+([.,;:!\?])', r'\1', text)
    return text.strip()

def read_company_standards(concept_folder, failed_items=None):
    """Scans all docx files in standards/<concept_folder>/."""
    target_path = os.path.join("standards", concept_folder)
    
    if os.path.exists(target_path) and os.path.isdir(target_path):
        scan_folder = target_path
    elif os.path.exists("standards") and os.path.isdir("standards"):
        scan_folder = "standards"
    else:
        return "WARNING: No standards directory found for this establishment."

    try:
        found_docs = False
        all_paragraphs = []

        for root, dirs, files in os.walk(scan_folder):
            for filename in files:
                if filename.endswith(".docx"):
                    found_docs = True
                    doc_path = os.path.join(root, filename)
                    doc = docx.Document(doc_path)
                    for p in doc.paragraphs:
                        text = p.text.strip()
                        if text:
                            all_paragraphs.append((filename, text))
        
        if not found_docs:
            return f"WARNING: No .docx SOP files found in '{scan_folder}'."

        if not failed_items:
            full_standards = ""
            current_file = ""
            for filename, text in all_paragraphs:
                if filename != current_file:
                    current_file = filename
                    full_standards += f"\n--- {filename} ---\n"
                full_standards += text + "\n"
            return full_standards

        keywords = set()
        stopwords = {"the", "and", "for", "with", "that", "this", "from", "have", "were", "been", "none", "notes", "custom", "finding", "l1", "l2", "l3"}
        for item in failed_items:
            words = [w.lower().strip(".,()[]:;\"'-") for w in item.split()]
            meaningful = [w for w in words if len(w) > 2 and w not in stopwords]
            keywords.update(meaningful)

        relevant_blocks = []
        for filename, text in all_paragraphs:
            text_lower = text.lower()
            if any(kw in text_lower for kw in keywords) or "form" in text_lower or "log-" in text_lower:
                relevant_blocks.append(f"[{filename}] {text}")

        if not relevant_blocks:
            full_standards = ""
            current_file = ""
            for filename, text in all_paragraphs:
                if filename != current_file:
                    current_file = filename
                    full_standards += f"\n--- {filename} ---\n"
                full_standards += text + "\n"
            return full_standards

        return "\n".join(relevant_blocks)
            
    except Exception as e:
        return f"WARNING: Could not read standards folder. Error: {e}"

def generate_gemini_response(api_key, prompt_text):
    """Executes prompt via Gemini API, testing text models while skipping non-text audio/TTS endpoints."""
    if not api_key:
        raise Exception("GEMINI_API_KEY is missing from Streamlit secrets.")
    
    genai.configure(api_key=api_key)
    
    candidates = [
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-flash',
        'gemini-flash-latest'
    ]
    
    try:
        for model_item in genai.list_models():
            if 'generateContent' in model_item.supported_generation_methods:
                clean_name = model_item.name.replace('models/', '').strip()
                if not any(bad in clean_name.lower() for bad in ['tts', 'audio', 'imagen', 'embedding', 'realtime']):
                    if clean_name not in candidates:
                        candidates.append(clean_name)
    except Exception:
        pass

    last_error = None
    for model_name in candidates:
        try:
            m = genai.GenerativeModel(model_name)
            res = m.generate_content(prompt_text)
            if res and res.text:
                return res.text
        except Exception as err:
            last_error = err
            err_str = str(err)
            if any(k in err_str.lower() for k in ["404", "notfound", "not found", "400", "modality", "audio", "tts"]):
                continue
            raise err
            
    if last_error:
        raise last_error
    raise Exception("No active text-based Gemini model responded for this API key.")

def generate_ai_report(api_key, client_label, audit_date, final_score, deductions, failed_items_formatted, changelog_prompt, notes_prompt, company_standards, progress_context):
    """Generates executive summary using Gemini. Raises exception if API fails."""
    prompt = f"""
    You are an expert Lead Food Safety Compliance Officer (FSCO) for {client_label}. 
    I just finished an audit on {audit_date}. 
    The final score is {final_score:.2f}% ({deductions} points in deductions). 
    The specific violations found were: 
    {failed_items_formatted}
    
    CRITICAL RULEBOOK (PRPs & SOPs):
    You MUST base your Root Cause analysis and Preventive Actions EXACTLY on these company standards. 
    Do NOT invent generic solutions if a solution exists in these rules. 
    STRICT ANTI-HALLUCINATION RULES:
    - DO NOT invent, generate, or cite section numbers, clause numbers, or clause IDs.
    - Reference specific form codes cleanly as written in the standards (e.g., FORM LOG-DEV-01, FORM LOG-TEMP-01, FORM LOG-GHP-01, FORM LOG-BUF-01). NEVER leave the standalone word "Form" or "FORM" without its explicit log code.
    - Write all recommendations in clean, plain operational descriptions.
    ---
    {company_standards}
    ---
    
    Write a detailed, highly clinical Audit Executive Summary Report.
    
    CRITICAL FORMATTING RULES:
    - ONLY use **bold** text for section titles or headers.
    - DO NOT use inline bolding inside of paragraphs.
    - Use simple dashes (-) instead of em-dashes (-).
    - DO NOT include square brackets [like this] anywhere in your output.
    
    Format the report STRICTLY with these sections exactly as named:

    **1. Executive Summary**
    Objective:
    Summarize the surveillance audit purpose.
    Current Compliance Status:
    State the score.
    Administrative Breakdown:
    Hypothesize the root cause of the systemic failures based on our standards.
    Key Verdict:
    Give a strict directive for immediate next steps.

    **2. FSMS Administration: Changelog**
    {changelog_prompt}

    **3. Audit Scoring & Finding Summary**
    Write exactly: "See quantitative table below."

    **3.2 Detailed Finding & Resolution Plan**
    You MUST copy and paste the EXACT list of failed items provided below word-for-word. DO NOT summarize, rephrase, or alter them. YOU MUST retain all risk level tags like [L1], [L2], [L3] and checkpoint ID numbers:
    {failed_items_formatted}

    **4. Corrective and Preventive Action (CAPA) Summary**
    For every L1 and L2 violation, provide a recommended action plan. Number each violation sequentially (e.g., 1., 2., 3.). 
    Format EXACTLY like this:
    1. Issue: (State the violation)
    Immediate Correction:
    (What to do today)
    Root Cause:
    (Hypothesize why it happened)
    Preventive Action:
    (How to stop it happening again)

    **5. Mandatory Compliance Toolkit**
    List any physical safety equipment that must be procured based on the specific violations.

    **6. Historical Progress Summary**
    Data:
    [{progress_context}]
    Provide a portfolio-level 1-2 sentence commentary on the facility's compliance trajectory based on the provided data.

    **7. Auditor Notes & Recommendations**
    Direct observations and suggestions provided by the Lead Auditor:
    {notes_prompt}
    """
    raw_ai_text = generate_gemini_response(api_key, prompt)
    return sanitize_ai_output(raw_ai_text.replace('**', ''))

def generate_sop_guide(api_key, client_label, current_failures, company_standards):
    """Provides immediate physical action instructions for floor staff."""
    guide_prompt = f"""
    You are the FSCO for {client_label}. I am currently auditing the kitchen.
    Here are the items that just failed: {current_failures}
    
    Based STRICTLY on the following company SOPs, tell me what EXACT immediate physical action I need to instruct the staff to take right now to fix these specific issues.
    Do not give me root causes or long-term preventive actions. Just short, bulleted immediate instructions.
    
    SOPs:
    {company_standards}
    """
    raw_ai_text = generate_gemini_response(api_key, guide_prompt)
    return sanitize_ai_output(raw_ai_text)