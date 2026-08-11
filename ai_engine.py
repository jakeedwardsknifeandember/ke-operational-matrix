import os
import re
import docx
import google.generativeai as genai
import streamlit as st

@st.cache_resource(show_spinner=False)
def _get_semantic_model():
    """Loads and caches the SentenceTransformer model in memory via Streamlit resource caching."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('all-MiniLM-L6-v2')
    except Exception:
        return None

def extract_concept_only(name):
    """Strips store establishment name and extracts concept in parentheses."""
    if not name:
        return ""
    if '(' in name and ')' in name:
        return name[name.find('(') + 1:name.rfind(')')].strip()
    return name.strip()

def sanitize_ai_output(text):
    """Strips fake section numbers, replaces 'deg' with '°', and auto-fills missing log form codes."""
    if not text:
        return ""
    text = re.sub(r'\bSection\s+\d+(?:\.\d+)*\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bClause\s+\d+(?:\.\d+)*\b', '', text, flags=re.IGNORECASE)
    
    # Auto-convert 'deg F' / 'deg C' / 'deg' to standard degree symbols '°F' / '°C' / '°'
    text = re.sub(r'\bdeg\s*([FC])\b', r'°\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdeg\b', '°', text, flags=re.IGNORECASE)
    
    # Replace isolated 'Form' or 'FORM' references without codes with explicit default log codes
    text = re.sub(r'\b(using|in|on)\s+Form\b(?!\s+LOG-)', r'\1 FORM LOG-DEV-01', text, flags=re.IGNORECASE)
    text = re.sub(r'\bForm\.\b', 'FORM LOG-DEV-01.', text)
    
    # Clean horizontal spaces without stripping newlines (\n)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'[ \t]+([.,;:!\?])', r'\1', text)
    return text.strip()

def read_company_standards(concept_folder, failed_items=None):
    """
    Recursively scans standards/<concept_folder>/ (handling both flat and nested structures),
    excludes non-SOP folders like 'Audit Reports', and performs fuzzy/stemmed relevance ranking.
    """
    target_path = os.path.join("standards", concept_folder)
    
    if os.path.exists(target_path) and os.path.isdir(target_path):
        scan_folder = target_path
    elif os.path.exists("standards") and os.path.isdir("standards"):
        scan_folder = "standards"
    else:
        return "WARNING: No standards directory found for this establishment."

    # Directories to ignore during RAG scanning
    EXCLUDED_DIRS = {"audit reports", "audit_reports", "temp", "tmp", "old"}

    try:
        found_docs = False
        all_paragraphs = []

        for root, dirs, files in os.walk(scan_folder):
            # Exclude non-standard directories dynamically
            dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED_DIRS]
            
            for filename in files:
                if filename.endswith(".docx") and not filename.startswith("~$"):
                    found_docs = True
                    doc_path = os.path.join(root, filename)
                    try:
                        doc = docx.Document(doc_path)
                        for p in doc.paragraphs:
                            text = p.text.strip()
                            if len(text) > 10:  # Skip empty or trivial lines
                                all_paragraphs.append((filename, text))
                    except Exception:
                        continue
        
        if not found_docs:
            return f"WARNING: No active .docx SOP files found in '{scan_folder}'."

        if not failed_items:
            # Full dump if no failures are provided (capped at 25,000 chars)
            full_standards = []
            current_file = ""
            total_chars = 0
            for filename, text in all_paragraphs:
                clean_fn = filename.replace('.docx', '').replace('.doc', '')
                if clean_fn != current_file:
                    current_file = clean_fn
                    full_standards.append(f"\n--- {clean_fn} ---")
                full_standards.append(text)
                total_chars += len(text)
                if total_chars > 25000:
                    break
            return "\n".join(full_standards)

        # Build stem/keyword dictionary for robust searching
        keywords = set()
        stopwords = {
            "the", "and", "for", "with", "that", "this", "from", "have", "were", "been", 
            "none", "notes", "custom", "finding", "l1", "l2", "l3", "item", "failed", "check"
        }
        
        for item in failed_items:
            words = [w.lower().strip(".,()[]:;\"'-") for w in item.split()]
            for w in words:
                if len(w) > 2 and w not in stopwords:
                    keywords.add(w)
                    # Add partial stems for custom findings (e.g., 'flooring' -> 'floor')
                    if len(w) > 4:
                        keywords.add(w[:4])

        scored_blocks = []

        # 1. ATTEMPT SEMANTIC SEARCH WITH CACHED MODEL
        try:
            import torch
            from sentence_transformers import util
            
            semantic_model = _get_semantic_model()
            if semantic_model is not None:
                corpus = [text for _, text in all_paragraphs]
                corpus_embeddings = semantic_model.encode(corpus, convert_to_tensor=True)
                query_embeddings = semantic_model.encode(failed_items, convert_to_tensor=True)
                
                cos_scores = util.cos_sim(query_embeddings, corpus_embeddings)
                top_k = min(5, len(corpus))
                
                for i in range(len(failed_items)):
                    top_results = torch.topk(cos_scores[i], k=top_k)
                    for idx in top_results[1]:
                        filename, text = all_paragraphs[idx.item()]
                        clean_fn = filename.replace('.docx', '').replace('.doc', '')
                        scored_blocks.append((10, f"[{clean_fn}] {text}")) # Assign high base semantic score
                    
        except Exception:
            pass # Silently fallback to lexical keyword scoring if library is missing or fails

        # 2. LEXICAL KEYWORD & FORM CODE SCORING
        for filename, text in all_paragraphs:
            clean_fn = filename.replace('.docx', '').replace('.doc', '')
            text_lower = text.lower()
            score = 0
            
            # Score matches based on keyword presence
            for kw in keywords:
                if kw in text_lower:
                    score += 1
            
            # Boost score for structural form codes and mandatory log definitions
            if "log-" in text_lower or "form" in text_lower:
                score += 2
            if "prp" in text_lower or "sop" in text_lower:
                score += 1

            if score > 0:
                scored_blocks.append((score, f"[{clean_fn}] {text}"))

        # Remove duplicates while preserving highest score
        unique_blocks = {}
        for score, block in scored_blocks:
            if block not in unique_blocks or score > unique_blocks[block]:
                unique_blocks[block] = score

        # Sort blocks by relevance score in descending order
        final_scored_blocks = [(score, block) for block, score in unique_blocks.items()]
        final_scored_blocks.sort(key=lambda x: x[0], reverse=True)

        if not final_scored_blocks:
            # Fallback: Top 50 general SOP paragraphs if keywords yield no hits
            fallback_blocks = [f"[{fn.replace('.docx', '').replace('.doc', '')}] {txt}" for fn, txt in all_paragraphs[:50]]
            return "\n".join(fallback_blocks)

        # Accumulate relevant blocks up to a strict 20,000 character limit
        selected_blocks = []
        char_count = 0
        for score, block in final_scored_blocks:
            selected_blocks.append(block)
            char_count += len(block)
            if char_count >= 20000:
                break

        return "\n".join(selected_blocks)
            
    except Exception as e:
        return f"WARNING: Could not read standards folder. Error: {e}"

def generate_gemini_response(api_key_input, prompt_text):
    """
    Executes prompt via Gemini API with Multi-Key Failover.
    Iterates through a pool of backup API keys if a key hits quota limits or 429 rate errors.
    """
    if not api_key_input:
        raise Exception("GEMINI_API_KEY is missing from Streamlit secrets.")
    
    # Standardize input into a list of key strings
    if isinstance(api_key_input, list):
        api_keys = [str(k).strip() for k in api_key_input if str(k).strip()]
    else:
        api_keys = [k.strip() for k in str(api_key_input).split(',') if k.strip()]

    if not api_keys:
        raise Exception("No valid Gemini API key found in configuration.")

    last_error = None

    for key_idx, current_key in enumerate(api_keys):
        try:
            genai.configure(api_key=current_key)
            
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

            # Try candidate models with the current active API key
            for model_name in candidates:
                try:
                    m = genai.GenerativeModel(model_name)
                    res = m.generate_content(prompt_text)
                    if res and res.text:
                        return res.text
                except Exception as err:
                    last_error = err
                    err_str = str(err).lower()
                    
                    # 404/modality issues: try next model under the SAME API key
                    if any(k in err_str for k in ["404", "notfound", "not found", "400", "modality", "audio", "tts"]):
                        continue
                    
                    # Quota exhaustion or Rate Limit (429): break model loop to trigger key failover
                    if any(k in err_str for k in ["429", "quota", "resourceexhausted", "exhausted", "limit"]):
                        break
                    
                    # Unrecognized error: break model loop to switch key
                    break

        except Exception as key_err:
            last_error = key_err
            continue

    if last_error:
        raise last_error
    raise Exception("All provided Gemini API keys and candidate models were exhausted or failed.")

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
    - You may cite exact section or clause numbers (e.g., Section 5.3.1) ONLY IF they explicitly appear in the provided company standards. DO NOT invent, guess, or hallucinate fake section numbers.
    - Reference specific form codes cleanly as written in the standards (e.g., FORM LOG-DEV-01, FORM LOG-TEMP-01, FORM LOG-GHP-01, FORM LOG-BUF-01). NEVER leave the standalone word "Form" or "FORM" without its explicit log code.
    - When citing a document, SOP, or PRP, you must include its descriptive title in parentheses if available (e.g., PRP 1.0 (Personal Hygiene)).
    - Write all recommendations in clean, plain operational descriptions.
    ---
    {company_standards}
    ---
    
    Write a detailed, highly clinical Audit Executive Summary Report.
    
    CRITICAL FORMATTING RULES:
    - ONLY use **bold** text for section titles or headers.
    - DO NOT use inline bolding inside of paragraphs.
    - Use simple dashes (-) instead of em-dashes (-).
    - DO NOT include square brackets anywhere in your output, EXCEPT for the risk level tags [L1], [L2], and [L3] strictly inside the 3.2 Detailed Finding list. DO NOT use bracketed risk tags inside standard paragraphs (like the Administrative Breakdown).
    
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
    Provide a portfolio-level 1-2 sentence commentary on the facility's compliance trajectory based on the provided data. You MUST refer to the store strictly by its full label "{client_label}" (e.g. "Tata's Chicks - Makati") instead of shorthand phrases like "the facility" or "the branch".

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