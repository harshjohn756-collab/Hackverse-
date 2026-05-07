"""
Didit.me KYC Integration + Local OCR Gender Extraction
-------------------------------------------------------
- create_kyc_session(): sends doc to Didit.me for async verification
- extract_gender_from_document(): uses EasyOCR to read gender from ID doc locally
- extract_gender_from_webhook(): parses Didit webhook for gender
- extract_kyc_status(): normalises Didit status strings
"""
import base64
import io
import os
import re

import requests
from flask import current_app
from PIL import Image

# ── Lazy-loaded EasyOCR readers ──────────────────────────────────────────────
# EasyOCR can't mix all Indic scripts in one reader, so we use
# English+Kannada as primary (Aadhaar always prints MALE/FEMALE in English).
_ocr_reader_en_kn = None


def _get_ocr_reader():
    global _ocr_reader_en_kn
    if _ocr_reader_en_kn is None:
        import easyocr
        _ocr_reader_en_kn = easyocr.Reader(["en", "kn"], gpu=False, verbose=False)
    return _ocr_reader_en_kn


# ── Gender keyword maps (multilingual) ──────────────────────────────────────
_MALE_KEYWORDS = [
    # English + common OCR misreads
    "male", "/male", "/ male",
    "ilale", "iale", "ma1e", "nale", "mala", "maie",
    # Hindi transliteration
    "purush",
    # Kannada transliteration
    "purusha",
    # Unicode script
    "\u0aaa\u0ac1\u0ab0\u0ac1\u0ab7",     # Gujarati
]

_MALE_UNICODE = [
    "\u0c2a\u0c41\u0c30\u0c41\u0c37\u0c41\u0c21\u0c41",  # Telugu
    "\u0baa\u0bc1\u0bb0\u0bc1\u0bb7\u0ba9\u0bcd",          # Tamil
    "\u0d2a\u0d41\u0d30\u0d41\u0d37\u0d28\u0d4d",          # Malayalam
    "\u092a\u0941\u0930\u0941\u0937",                        # Hindi (Devanagari)
    "\u0caa\u0cc1\u0cb0\u0cc1\u0cb7",                        # Kannada
]

_FEMALE_KEYWORDS = [
    "female", "/female", "/ female",
    "mahila",
    "stree",
]

_FEMALE_UNICODE = [
    "\u0c38\u0c4d\u0c24\u0c4d\u0c30\u0c40",  # Telugu
    "\u0baa\u0bc6\u0ba3\u0bcd",                # Tamil
    "\u0d38\u0d4d\u0d24\u0d4d\u0d30\u0d40",    # Malayalam
    "\u092e\u0939\u093f\u0932\u093e",            # Hindi
    "\u0cae\u0cb9\u0cbf\u0cb3\u0cc6",            # Kannada
]


def _get_api_key():
    key = current_app.config.get("DIDIT_API_KEY") or os.environ.get("DIDIT_API_KEY")
    if not key:
        raise RuntimeError("DIDIT_API_KEY is not configured.")
    return key


def _get_callback_url():
    url = current_app.config.get("DIDIT_CALLBACK_URL") or os.environ.get("DIDIT_CALLBACK_URL")
    return url or ""


# ─────────────────────────────────────────────────────────────────────────────
# LOCAL OCR — extract gender from uploaded document image
# ─────────────────────────────────────────────────────────────────────────────
def extract_gender_from_document(file_obj) -> str:
    """
    Reads the uploaded ID document image with EasyOCR and scans the
    extracted text for gender keywords in English, Hindi, Kannada, etc.

    Returns: 'female', 'male', or 'unknown'
    """
    try:
        # Read file bytes and reset pointer
        file_bytes = file_obj.read()
        file_obj.seek(0)  # reset so Didit can still read it later

        # ── Pass image directly to OCR ───────────────────────────────
        print("[OCR] Running EasyOCR on document...")
        reader = _get_ocr_reader()
        
        # reader.readtext accepts bytes directly
        results = reader.readtext(file_bytes, detail=0)  # list of strings
        raw_text = " ".join(results).lower()
        
        # Safely print without crashing Windows console on Unicode
        safe_print_text = raw_text.encode('ascii', 'ignore').decode()
        print(f"[OCR] Extracted text ({len(raw_text)} chars): {safe_print_text[:300]}")

        # Also check each OCR fragment individually (better for short words)
        fragments = [r.strip().lower() for r in results]

        # ── Regex patterns for common OCR misreads ───────────────────────
        # OCR often misreads M as lI, A as 4, E as 3, etc.
        male_patterns = [
            r'\bmale\b', r'\b[mi1lnr][a4o][l1i][e3c]\b',    # male, ilale, ma1e, rnale, nole, rnalc
            r'/\s*male\b', r'gender.*male',
            r'\bm\s*a\s*l\s*e\b', r'\bm\s*a\s*1\s*e\b'      # spaced out m a l e
        ]
        female_patterns = [
            r'\bfemale\b', r'\bf[e3][mi1l][a4][l1][e3]\b',
            r'/\s*female\b', r'gender.*female',
        ]

        # ── Check for MALE ───────────────────────────────────────────────
        for pat in male_patterns:
            if re.search(pat, raw_text):
                # But make sure "female" isn't what matched
                if not re.search(r'female', raw_text):
                    print(f"[OCR] MALE regex matched: {pat}")
                    return "male", raw_text

        for kw in _MALE_KEYWORDS:
            if kw in raw_text:
                if "female" not in raw_text and "fe" + kw not in raw_text:
                    print(f"[OCR] MALE keyword matched: '{kw}'")
                    return "male", raw_text

        for kw in _MALE_UNICODE:
            if kw in raw_text:
                print(f"[OCR] MALE unicode matched")
                return "male", raw_text

        # ── Check for FEMALE ─────────────────────────────────────────────
        for pat in female_patterns:
            if re.search(pat, raw_text):
                print(f"[OCR] FEMALE regex matched: {pat}")
                return "female", raw_text

        for kw in _FEMALE_KEYWORDS:
            if kw in raw_text:
                print(f"[OCR] FEMALE keyword matched: '{kw}'")
                return "female", raw_text

        for kw in _FEMALE_UNICODE:
            if kw in raw_text:
                print(f"[OCR] FEMALE unicode matched")
                return "female", raw_text

        # ── Per-fragment check (catches single-word OCR results) ─────────
        for frag in fragments:
            if re.search(r'^[mi1l][a4][l1][e3]$', frag):
                print(f"[OCR] MALE fragment matched: '{frag}'")
                return "male", raw_text
            if re.search(r'^f[e3][mi1l][a4][l1][e3]$', frag):
                print(f"[OCR] FEMALE fragment matched: '{frag}'")
                return "female", raw_text

        print("[OCR] No gender keywords found in document text.")
        return "unknown", raw_text

    except Exception as e:
        print(f"[OCR] EasyOCR Error: {e}")
        return "unknown", ""


# ─────────────────────────────────────────────────────────────────────────────
# DIDIT SESSION
# ─────────────────────────────────────────────────────────────────────────────
def create_kyc_session(file_obj, user_id, user_data=None):
    """
    Creates a KYC verification session on Didit.me and submits the document.

    Returns: (session_id | None, error_msg | None)
    """
    api_key = _get_api_key()
    callback_url = _get_callback_url()

    file_content = file_obj.read()
    b64_doc = base64.b64encode(file_content).decode("utf-8")
    filename = getattr(file_obj, "filename", "document.jpg")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "vendor_data": str(user_id),
        "callback": callback_url,
        "document": {
            "document_base64": b64_doc,
            "filename": filename,
        },
        "user": user_data or {},
    }

    try:
        print(f"[Didit] Creating KYC session for user {user_id}, file={filename}")
        resp = requests.post(
            "https://apx.didit.me/v1/kyc/session",
            json=payload,
            headers=headers,
            timeout=15,
        )
        print(f"[Didit] Session response {resp.status_code}: {resp.text[:300]}")

        if resp.status_code in (200, 201):
            data = resp.json()
            session_id = data.get("session_id") or data.get("id")
            return str(session_id) if session_id else "pending", None

        return None, f"Didit API error {resp.status_code}: {resp.text[:200]}"

    except Exception as exc:
        print(f"[Didit] Session creation exception: {exc}")
        return "pending", None


# ─────────────────────────────────────────────────────────────────────────────
# WEBHOOK HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def extract_gender_from_webhook(payload: dict):
    """
    Parses a Didit webhook payload and returns 'female', 'male', or None.
    """
    def _find(d, *keys):
        for k in keys:
            if isinstance(d, dict) and k in d:
                return d[k]
        return None

    data_block   = payload.get("data") or {}
    doc_block    = payload.get("document") or data_block.get("document") or {}
    person_block = data_block.get("person") or {}

    raw = (
        _find(doc_block,    "gender", "sex")
        or _find(person_block, "gender", "sex")
        or _find(data_block,   "gender", "sex")
        or _find(payload,      "gender", "sex")
    )

    if raw is None:
        return None

    raw = str(raw).strip().upper()
    if raw in ("F", "FEMALE", "WOMAN"):
        return "female"
    if raw in ("M", "MALE", "MAN"):
        return "male"
    return "other"


def extract_kyc_status(payload: dict) -> str:
    """Returns normalised KYC status: 'approved', 'declined', or 'pending'."""
    data_block = payload.get("data") or {}
    raw = (
        payload.get("status")
        or data_block.get("status")
        or payload.get("verification_status")
        or "pending"
    )
    raw = str(raw).strip().lower()
    if raw in ("approved", "verified", "completed", "success"):
        return "approved"
    if raw in ("declined", "rejected", "failed"):
        return "declined"
    return "pending"
