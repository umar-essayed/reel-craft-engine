import os
import re
import json
from typing import Dict, Any, Optional

def extract_text_from_file(file_path: str) -> str:
    """Extracts raw text from PDF, TXT, MD, or JSON files locally without external tokens."""
    if not os.path.exists(file_path):
        return ""

    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            pages_text = []
            for page in doc:
                pages_text.append(page.get_text())
            text = "\n".join(pages_text)
        except Exception as e:
            # Fallback to pdfplumber if fitz fails
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            except Exception:
                text = ""

    elif ext == ".docx":
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(file_path) as z:
                xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            texts = [node.text for node in tree.iter() if node.text]
            text = "\n".join(texts)
        except Exception:
            text = ""

    elif ext in (".txt", ".md", ".json"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            text = ""

    return text.strip()

def analyze_company_profile(raw_text: str, brand_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Locally parses and structures company profile into key brand intelligence:
    - Company Name & Tagline
    - Core Services / Products
    - Target Audience
    - Competitive Advantages & Numbers
    - Brand Voice & Tone
    - Executive Summary for AI System Prompt
    """
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    cleaned_full = "\n".join(lines)

    # Detect emails, websites, phones
    website_match = re.search(r'(https?://[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6})', cleaned_full)
    website = website_match.group(0) if website_match else "brand.com"
    if " " in website or "@" in website:
        website = "brand.com"

    # Identify potential brand name if not provided
    name = brand_name
    if not name and lines:
        first_line = lines[0]
        if len(first_line) < 40 and not any(kw in first_line.lower() for kw in ["profile", "company", "بروفايل", "شركة"]):
            name = first_line
        else:
            name = "البراند"

    # Extract bullet points / services
    services = []
    advantages = []
    
    for line in lines:
        if any(marker in line for marker in ["-", "•", "*", "1.", "2.", "3.", "4."]) and len(line) < 120:
            clean_item = re.sub(r'^[-•*\d.]+\s*', '', line).strip()
            if any(w in clean_item for w in ["خدمة", "نظام", "إدارة", "برنامج", "تطبيق", "حلول", "مبيعات", "مخازن", "توصيل", "system", "service", "app"]):
                services.append(clean_item)
            elif any(w in clean_item for w in ["سريع", "أمان", "توفير", "دعم", "مجاني", "خصم", "ضمان", "سهل", "fast", "secure", "free"]):
                advantages.append(clean_item)

    if not services:
        services = [l for l in lines[1:6] if len(l) < 90]

    snippet = cleaned_full[:1800]

    profile_data = {
        "company_name": name,
        "website": website,
        "raw_text_length": len(raw_text),
        "detected_services": services[:6],
        "detected_advantages": advantages[:6],
        "executive_summary": snippet,
        "has_full_profile": len(raw_text) > 50
    }

    return profile_data

def ingest_company_profile(file_path: Optional[str] = None, text: str = "", project_dir: Optional[str] = None) -> Dict[str, Any]:
    """Ingests a company profile from file or raw text, analyzes it locally, and saves brand_profile.json."""
    raw = ""
    if file_path and os.path.exists(file_path):
        raw = extract_text_from_file(file_path)
    if not raw and text:
        raw = text

    analysis = analyze_company_profile(raw)

    profile = {
        "brand_name": analysis.get("company_name", ""),
        "services": analysis.get("detected_services", []),
        "unique_selling_points": analysis.get("detected_advantages", []),
        "target_audience": "أصحاب الأعمال والمهتمين بالحلول المبتكرة",
        "summary": analysis.get("executive_summary", "")[:1200],
        "contact": {
            "website": analysis.get("website", "")
        }
    }

    if project_dir and os.path.exists(project_dir):
        out_path = os.path.join(project_dir, "brand_profile.json")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return profile

