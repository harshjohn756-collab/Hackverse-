# -*- coding: utf-8 -*-
"""
Add/update government schemes with comprehensive multilingual data
(English, Hindi, Kannada) from the official myScheme portal.
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from app.models.scheme import GovernmentScheme

app = create_app()

# ─────────────────────────────────────────────────────────────────────
# SCHEME DATA
# ─────────────────────────────────────────────────────────────────────

SCHEMES = [
    # ── 1. Assistance for Daughter's Marriage (Rajasthan) ────────────
    {
        "name": "Assistance for Daughter's Marriage",
        "category": "safety_education",
        "eligibility": (
            "The applicant should be a native of Rajasthan. "
            "The applicant should be the widow of an ex-serviceman of the rank of Havildar or below. "
            "The assistance is available for a maximum of two daughters. "
            "The daughter should be at least 18 years of age at the time of marriage. "
            "The daughter's name should be recorded in the ex-serviceman's discharge book. "
            "The applicant should possess a valid Ex-Serviceman/Widow Identity Card. "
            "The application should be submitted within one year from the date of marriage."
        ),
        "eligibility_hi": (
            "आवेदक राजस्थान का मूल निवासी होना चाहिए। "
            "आवेदक हवलदार या उससे नीचे के पद के पूर्व सैनिक की विधवा होनी चाहिए। "
            "सहायता एक पूर्व सैनिक की विधवा की अधिकतम दो बेटियों के लिए उपलब्ध है। "
            "विवाह के समय बेटी की आयु कम से कम 18 वर्ष होनी चाहिए। "
            "आवेदन विवाह की तारीख से एक साल के भीतर प्रस्तुत किया जाना चाहिए।"
        ),
        "eligibility_kn": (
            "ಅರ್ಜಿದಾರರು ರಾಜಸ್ಥಾನದ ಸ್ಥಳೀಯರಾಗಿರಬೇಕು. "
            "ಅರ್ಜಿದಾರರು ಹವಿಲ್ದಾರ್ ಅಥವಾ ಅದಕ್ಕಿಂತ ಕಡಿಮೆ ಶ್ರೇಣಿಯ ಮಾಜಿ ಸೈನಿಕರ ವಿಧವೆಯಾಗಿರಬೇಕು. "
            "ಮಾಜಿ ಸೈನಿಕನೊಬ್ಬನ ವಿಧವೆಯ ಗರಿಷ್ಠ ಇಬ್ಬರು ಪುತ್ರಿಯರಿಗೆ ಈ ನೆರವು ಲಭ್ಯವಿದೆ. "
            "ಮದುವೆಯ ಸಮಯದಲ್ಲಿ ಮಗಳಿಗೆ ಕನಿಷ್ಠ 18 ವರ್ಷ ವಯಸ್ಸಾಗಿರಬೇಕು. "
            "ಅರ್ಜಿಯನ್ನು ಮದುವೆಯ ದಿನಾಂಕದಿಂದ ಒಂದು ವರ್ಷದೊಳಗೆ ಸಲ್ಲಿಸಬೇಕು."
        ),
        "benefits": "Financial assistance for daughter's marriage of ex-serviceman's widow",
        "scheme_url": "https://rajsainik.rajasthan.gov.in/",
        "application_steps": [
            "Visit the office of the District Sainik Welfare Officer",
            "Request the prescribed application form",
            "Fill in all mandatory fields and attach required documents",
            "Submit the signed application to the District Sainik Welfare Officer",
            "Request a receipt with submission date and ID number",
            "Await verification and committee review (every 6 months)",
            "If approved, financial assistance is transferred to bank account",
        ],
        "documents_required": [
            "Ex-Serviceman/Widow Identity Card",
            "Discharge Book or Part-2 Order",
            "Daughter's birth certificate",
            "Marriage certificate",
            "Bank account details",
            "Aadhaar card",
        ],
    },

    # ── 2. Janani Suraksha Yojana (JSY) ─────────────────────────────
    {
        "name": "Janani Suraksha Yojana (JSY)",
        "category": "health_maternity",
        "eligibility": (
            "For Institutional Delivery: Must deliver in a government health centre or accredited private institution. "
            "Low Performing States (LPS): All pregnant women eligible without BPL certification. "
            "High Performing States (HPS): Must be from BPL household and SC/ST woman. "
            "For Home Delivery (all states): Must be from BPL household with valid BPL certificate."
        ),
        "eligibility_hi": (
            "संस्थागत प्रसव के लिए: सरकारी स्वास्थ्य केंद्र या मान्यता प्राप्त निजी संस्थान में प्रसव कराना चाहिए। "
            "कम प्रदर्शन करने वाले राज्यों में: सभी गर्भवती महिलाएं बिना BPL प्रमाणन के पात्र हैं। "
            "उच्च प्रदर्शन करने वाले राज्यों में: BPL परिवार की SC/ST महिला होनी चाहिए। "
            "होम डिलीवरी के लिए: BPL परिवार से होना चाहिए और BPL प्रमाण पत्र होना चाहिए।"
        ),
        "eligibility_kn": (
            "ಸಂಸ್ಥಾಗತ ಹೆರಿಗೆಗೆ: ಸರ್ಕಾರಿ ಆರೋಗ್ಯ ಕೇಂದ್ರ ಅಥವಾ ಮಾನ್ಯತೆ ಪಡೆದ ಖಾಸಗಿ ಸಂಸ್ಥೆಯಲ್ಲಿ ಹೆರಿಗೆ ಮಾಡಬೇಕು. "
            "ಕಡಿಮೆ ಕಾರ್ಯಕ್ಷಮತೆ ರಾಜ್ಯಗಳಲ್ಲಿ: ಎಲ್ಲಾ ಗರ್ಭಿಣಿ ಮಹಿಳೆಯರು BPL ಪ್ರಮಾಣೀಕರಣವಿಲ್ಲದೆ ಅರ್ಹರು. "
            "ಉನ್ನತ ಕಾರ್ಯಕ್ಷಮತೆ ರಾಜ್ಯಗಳಲ್ಲಿ: BPL ಕುಟುಂಬದ SC/ST ಮಹಿಳೆ ಆಗಿರಬೇಕು."
        ),
        "benefits": "Cash assistance for institutional delivery: ₹1,400 (rural) / ₹1,000 (urban) in LPS; ₹700 (rural) / ₹600 (urban) in HPS",
        "scheme_url": "https://nhm.gov.in/index1.php?lang=1&level=3&sublinkid=841&lid=309",
        "application_steps": [
            "Register at the nearest government health centre or Anganwadi centre",
            "Get ASHA worker assistance for registration",
            "Carry MCH-JSY card and referral slip from ASHA/ANM",
            "Deliver at government or accredited private institution",
            "Receive cash assistance post-delivery",
        ],
        "documents_required": [
            "MCH-JSY card",
            "BPL certificate (for HPS/home delivery)",
            "SC/ST certificate (for HPS)",
            "Referral slip from ASHA/ANM/Medical Officer",
            "Aadhaar card",
            "Bank account details",
        ],
    },

    # ── 3. Mahila Samman Savings Certificate ─────────────────────────
    {
        "name": "Mahila Samman Savings Certificate",
        "category": "financial_inclusion",
        "eligibility": (
            "Indian citizen women and girl children. "
            "Any individual woman can apply. Minor account can be opened by guardian. "
            "No upper age limit. Single-holder type account. "
            "Minimum deposit ₹1,000, maximum ₹2,00,000. "
            "Matures after 2 years. Up to 40% withdrawal after 1 year."
        ),
        "eligibility_hi": (
            "आवेदक के पास भारतीय नागरिकता होनी चाहिए। "
            "यह योजना केवल महिलाओं और बालिकाओं के लिए है। "
            "कोई ऊपरी आयु सीमा नहीं है। "
            "न्यूनतम ₹1000/- और अधिकतम ₹2,00,000/- जमा। "
            "दो साल बाद परिपक्वता। एक साल बाद 40% तक निकासी।"
        ),
        "eligibility_kn": (
            "ಅರ್ಜಿದಾರರು ಭಾರತೀಯ ಪೌರತ್ವವನ್ನು ಹೊಂದಿರಬೇಕು. "
            "ಈ ಯೋಜನೆಯು ಮಹಿಳೆಯರು ಮತ್ತು ಹೆಣ್ಣು ಮಕ್ಕಳಿಗೆ ಮಾತ್ರ ಅನ್ವಯಿಸುತ್ತದೆ. "
            "ಯಾವುದೇ ಗರಿಷ್ಠ ವಯಸ್ಸಿನ ಮಿತಿಯಿಲ್ಲ. "
            "ಕನಿಷ್ಠ ₹1000/- ಮತ್ತು ಗರಿಷ್ಠ ₹2,00,000/- ಠೇವಣಿ. "
            "ಎರಡು ವರ್ಷಗಳ ನಂತರ ಪಕ್ವತೆ. ಒಂದು ವರ್ಷದ ನಂತರ 40% ವರೆಗೆ ಹಿಂಪಡೆಯುವಿಕೆ."
        ),
        "benefits": "7.5% interest rate p.a., quarterly compounding. Tax benefits under Section 80C.",
        "scheme_url": "https://www.indiapost.gov.in/",
        "application_steps": [
            "Visit the nearest Post Office Branch or designated bank",
            "Collect or download the application form",
            "Fill out the form and attach required documents",
            "Fill out declaration and nomination details",
            "Submit with initial deposit amount (min ₹1,000)",
            "Receive certificate as proof of investment",
        ],
        "documents_required": [
            "Aadhaar card",
            "PAN card",
            "Address proof",
            "Passport-size photograph",
            "Bank account details",
            "Guardian's ID (for minor accounts)",
        ],
    },

    # ── 4. New Swarnima Scheme for Women ─────────────────────────────
    {
        "name": "New Swarnima Scheme for Women",
        "category": "entrepreneurship",
        "eligibility": (
            "The applicant must be a Female. "
            "Age must be between 18 and 55 years. "
            "Must be an Entrepreneur. "
            "Total Annual Family Income must be less than ₹3 Lakh per annum."
        ),
        "eligibility_hi": (
            "आवेदक महिला होनी चाहिए। "
            "आवेदक की आयु 18 से 55 वर्ष के बीच होनी चाहिए। "
            "आवेदक को उद्यमी होना चाहिए। "
            "कुल वार्षिक पारिवारिक आय ₹3 लाख प्रति वर्ष से कम होनी चाहिए।"
        ),
        "eligibility_kn": (
            "ಅರ್ಜಿದಾರರು ಮಹಿಳೆಯಾಗಿರಬೇಕು. "
            "ಅರ್ಜಿದಾರರ ವಯಸ್ಸು 18 ರಿಂದ 55 ವರ್ಷದೊಳಗಿನವರಾಗಿರಬೇಕು. "
            "ಅರ್ಜಿದಾರರು ಉದ್ಯಮಿಯಾಗಿರಬೇಕು. "
            "ಒಟ್ಟು ವಾರ್ಷಿಕ ಕುಟುಂಬ ಆದಾಯವು ವರ್ಷಕ್ಕೆ ₹3 ಲಕ್ಷಕ್ಕಿಂತ ಕಡಿಮೆಯಿರಬೇಕು."
        ),
        "benefits": "Loan up to ₹2 Lakh at concessional interest rate (5% p.a.) for women entrepreneurs from SC category",
        "scheme_url": "https://nsfdc.nic.in/",
        "application_steps": [
            "Visit the nearest SCA (State Channelizing Agency) office",
            "Apply on the prescribed form for Swarnima Scheme for Women",
            "Enter necessary details and mention vocation/training requirements",
            "Submit application form and required documents to SCA office",
            "Await loan sanction by SCA after review",
        ],
        "documents_required": [
            "Identity proof (Aadhaar/Voter ID)",
            "SC/ST caste certificate",
            "Income certificate (annual family income < ₹3 Lakh)",
            "Business plan/proposal",
            "Address proof",
            "Bank account details",
            "Passport-size photographs",
        ],
    },

    # ── 5. PM Vidyalaxmi ────────────────────────────────────────────
    {
        "name": "PM Vidyalaxmi",
        "category": "safety_education",
        "eligibility": (
            "Indian citizen students with merit-based admission to one of 860 designated QHEIs. "
            "Not admitted through management quota. "
            "Annual family income up to ₹8,00,000 for 3% interest subvention. "
            "Must not receive any other Central/State scholarship or interest subvention. "
            "Must maintain satisfactory academic performance from 2nd year. "
            "Can avail benefits only once (UG or PG or integrated course)."
        ),
        "eligibility_hi": (
            "आवेदक को भारतीय नागरिक होना चाहिए। "
            "860 नामित गुणवत्तापूर्ण उच्च शैक्षणिक संस्थानों में योग्यता-आधारित प्रवेश। "
            "प्रबंधन कोटा से प्रवेश नहीं। "
            "3% ब्याज अनुदान के लिए वार्षिक पारिवारिक आय ₹8,00,000 तक। "
            "कोई अन्य छात्रवृत्ति या ब्याज अनुदान प्राप्त नहीं होनी चाहिए। "
            "केवल एक बार लाभ (स्नातक या स्नातकोत्तर)।"
        ),
        "eligibility_kn": (
            "ಅರ್ಜಿದಾರರು ಭಾರತೀಯ ಪ್ರಜೆಯಾಗಿರಬೇಕು. "
            "860 ಗೊತ್ತುಪಡಿಸಿದ ಗುಣಮಟ್ಟದ ಉನ್ನತ ಶಿಕ್ಷಣ ಸಂಸ್ಥೆಗಳಲ್ಲಿ ಅರ್ಹತೆ ಆಧಾರಿತ ಪ್ರವೇಶ. "
            "ನಿರ್ವಹಣಾ ಕೋಟಾದ ಮೂಲಕ ಪ್ರವೇಶಿಸಬಾರದು. "
            "3% ಬಡ್ಡಿ ಸಹಾಯಧನಕ್ಕೆ ಕುಟುಂಬದ ವಾರ್ಷಿಕ ಆದಾಯ ₹8,00,000 ವರೆಗೆ. "
            "ಬೇರೆ ಯಾವುದೇ ವಿದ್ಯಾರ್ಥಿವೇತನ ಪಡೆಯಬಾರದು. "
            "ಒಮ್ಮೆ ಮಾತ್ರ ಪ್ರಯೋಜನ (ಪದವಿಪೂರ್ವ ಅಥವಾ ಸ್ನಾತಕೋತ್ತರ)."
        ),
        "benefits": "3% interest subvention on education loans for students from families with annual income up to ₹8 Lakh. Full interest subvention for economically weaker sections.",
        "scheme_url": "https://pmvidyalaxmi.co.in/Index.aspx",
        "application_steps": [
            "Visit the PM Vidyalaxmi portal (pmvidyalaxmi.co.in)",
            "Register with Aadhaar and academic details",
            "Apply for education loan through the portal",
            "Select the bank and loan amount",
            "Upload required documents",
            "Await bank verification and loan approval",
        ],
        "documents_required": [
            "Aadhaar card",
            "Admission letter from QHEI",
            "Academic mark sheets/certificates",
            "Family income certificate",
            "Bank account details",
            "Fee structure from institution",
            "Co-borrower documents (if required)",
        ],
    },
]


def main():
    with app.app_context():
        added = 0
        updated = 0

        for data in SCHEMES:
            name = data["name"]
            existing = GovernmentScheme.query.filter_by(name=name).first()

            if existing:
                s = existing
                updated += 1
                print(f"  [UPDATE] {name}")
            else:
                s = GovernmentScheme(name=name, category=data["category"])
                db.session.add(s)
                added += 1
                print(f"  [NEW]    {name}")

            s.category = data["category"]
            s.eligibility = data.get("eligibility")
            s.eligibility_hi = data.get("eligibility_hi")
            s.eligibility_kn = data.get("eligibility_kn")
            s.benefits = data.get("benefits")
            s.scheme_url = data.get("scheme_url")

            if data.get("application_steps"):
                s.application_steps = data["application_steps"]
            if data.get("documents_required"):
                s.documents_required = data["documents_required"]
            if data.get("documents_required_hi"):
                s.documents_required_hi = data["documents_required_hi"]
            if data.get("documents_required_kn"):
                s.documents_required_kn = data["documents_required_kn"]

        db.session.commit()
        print(f"\nDone! Added {added} new schemes, updated {updated} existing.")

        # Show all schemes
        all_schemes = GovernmentScheme.query.all()
        print(f"\nTotal schemes in DB: {len(all_schemes)}")
        for s in all_schemes:
            docs = len(s.documents_required) if s.documents_required else 0
            print(f"  [{s.id}] {s.name} | docs={docs} | hi={'Y' if s.eligibility_hi else 'N'} | kn={'Y' if s.eligibility_kn else 'N'}")


if __name__ == "__main__":
    main()
