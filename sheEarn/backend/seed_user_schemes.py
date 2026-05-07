import json
from app import create_app, db
from app.models.scheme import GovernmentScheme

def seed_schemes():
    app = create_app()
    with app.app_context():
        db.session.query(GovernmentScheme).delete()
        
        schemes = [
            {
                "name": "New Swarnima Scheme for Women",
                "category": GovernmentScheme.CATEGORY_ENTREPRENEURSHIP,
                "scheme_url": "http://www.nbcfdc.gov.in/new-swarnima-for-women",
                "application_steps": [
                    "Step 1: The applicant should approach the State Channelizing Agency (SCA) / bank / NBCFDC partner office in her district.",
                    "Step 2: Collect the prescribed application form from the concerned agency and fill in personal, income, and business details.",
                    "Step 3: Clearly mention the proposed self-employment activity / business plan in the application.",
                    "Step 4: Attach required documents such as Caste certificate (OBC), Income certificate (≤ ₹3 lakh), Identity proof, Address proof",
                    "Step 5: Submit the completed application form to the district office / channel partner.",
                    "Step 6: The concerned authority verifies eligibility and forwards the application for approval.",
                    "Step 7: Upon approval, the loan is sanctioned and disbursed through the bank/channel partner."
                ],
                "documents_required": [
                    "Caste certificate (OBC)",
                    "Income certificate (≤ ₹3 lakh)",
                    "Identity proof",
                    "Address proof"
                ]
            },
            {
                "name": "WISE PhD Fellowship",
                "category": GovernmentScheme.CATEGORY_SAFETY,
                "scheme_url": "https://dst.gov.in/scientific-programmes/wise-kiran",
                "application_steps": [
                    "Step 1: The applicant must visit the official Department of Science & Technology (DST) portal.",
                    "Step 2: Register/login and access the fellowship application form.",
                    "Step 3: Fill in academic, research, and personal details.",
                    "Step 4: Upload required documents (PhD admission proof, certificates, proposal).",
                    "Step 5: Submit the application online.",
                    "Step 6: Selection is done based on eligibility and evaluation."
                ],
                "documents_required": ["PhD admission proof", "Certificates", "Research proposal"]
            },
            {
                "name": "SERB-POWER Fellowship",
                "category": GovernmentScheme.CATEGORY_SAFETY,
                "scheme_url": "https://serb.gov.in/page/english/power_fellowship",
                "application_steps": [
                    "Step 1: The applicant must visit the official SERB portal and register/login.",
                    "Step 2: Fill out the online application form with research and personal details.",
                    "Step 3: Upload required documents (CV, research proposal, academic certificates).",
                    "Step 4: Submit the application online before the deadline.",
                    "Step 5: Applications are reviewed by an expert committee.",
                    "Step 6: Selected candidates receive fellowship approval."
                ],
                "documents_required": ["CV", "Research proposal", "Academic certificates"]
            },
            {
                "name": "Scholarship Scheme for Girls (General)",
                "category": GovernmentScheme.CATEGORY_SAFETY,
                "scheme_url": "https://dce.karnataka.gov.in/30/Student%20Scholarships/en",
                "application_steps": [
                    "Step 1: The applicant must visit the official scholarship portal.",
                    "Step 2: Register using basic details (name, mobile number, email).",
                    "Step 3: Log in and fill out the online application form.",
                    "Step 4: Upload required documents (ID proof, academic records, income certificate).",
                    "Step 5: Submit the application form online.",
                    "Step 6: Track application status through the portal."
                ],
                "documents_required": ["ID proof", "Academic records", "Income certificate"]
            },
            {
                "name": "Vikasa Medical check up",
                "category": GovernmentScheme.CATEGORY_HEALTH,
                "scheme_url": "",
                "application_steps": [
                    "Step 1: The beneficiary must visit the nearest government health centre / camp location.",
                    "Step 2: Register at the facility with basic personal details.",
                    "Step 3: Submit required identification (if applicable).",
                    "Step 4: Undergo medical examination and tests.",
                    "Step 5: Receive treatment/services as per eligibility."
                ],
                "documents_required": ["Identification proof (if applicable)"]
            },
            {
                "name": "Swami Vivekanand single girl",
                "category": GovernmentScheme.CATEGORY_SAFETY,
                "scheme_url": "https://svsgc.ugc.ac.in/",
                "application_steps": [
                    "Step 1: The applicant must visit the official UGC scholarship portal and register online when applications are open.",
                    "Step 2: Log in using credentials and fill out the online application form with personal, academic, and research details.",
                    "Step 3: Upload required documents such as Proof of being a single girl child (affidavit), Admission proof for Ph.D. in Social Sciences, Identity and academic certificates.",
                    "Step 4: Submit the completed application form online before the deadline.",
                    "Step 5: Applications are evaluated by an expert committee, and selection is made based on eligibility and merit.",
                    "Step 6: Selected candidates receive fellowship approval, and benefits are provided as per guidelines."
                ],
                "documents_required": [
                    "Proof of being a single girl child (affidavit)",
                    "Admission proof for Ph.D. in Social Sciences",
                    "Identity and academic certificates"
                ]
            },
            {
                "name": "Pm vidhyalaksmi",
                "category": GovernmentScheme.CATEGORY_SAFETY,
                "scheme_url": "https://pmvidyalaxmi.co.in/",
                "application_steps": [
                    "Step 1: The applicant must visit the official scholarship portal.",
                    "Step 2: Register/login using required credentials.",
                    "Step 3: Fill out the application form.",
                    "Step 4: Upload necessary documents (academic records, ID proof, income proof).",
                    "Step 5: Submit the application and track status online."
                ],
                "documents_required": ["Academic records", "ID proof", "Income proof"]
            },
            {
                "name": "Pradhan Mantri Surakshit Matritva Abhiyan (PMSMA)",
                "category": GovernmentScheme.CATEGORY_HEALTH,
                "scheme_url": "Offline application",
                "application_steps": [
                    "Step 1: The pregnant woman can visit a government health facility on the 9th of every month.",
                    "Step 2: Register for antenatal check-up.",
                    "Step 3: Undergo necessary medical tests and examination.",
                    "Step 4: Receive medical advice and treatment from doctors."
                ],
                "documents_required": []
            },
            {
                "name": "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
                "category": GovernmentScheme.CATEGORY_HEALTH,
                "scheme_url": "https://www.pmuy.gov.in/index.aspx",
                "application_steps": [
                    "Step 1: The applicant must register at the nearest Anganwadi Centre or approved health facility.",
                    "Step 2: Fill out the prescribed application form.",
                    "Step 3: Submit required documents (Aadhaar card, bank details, pregnancy registration proof).",
                    "Step 4: The application is verified by the concerned authority.",
                    "Step 5: The benefit amount is transferred to the beneficiary’s bank account through DBT."
                ],
                "documents_required": ["Aadhaar card", "Bank details", "Pregnancy registration proof"]
            },
            {
                "name": "Mahila Samman Savings Certificate",
                "category": GovernmentScheme.CATEGORY_FINANCIAL,
                "scheme_url": "",
                "application_steps": [
                    "Step 1: The applicant can visit the nearest Post Office or authorized bank branch to collect the application form or download it from the official website.",
                    "Step 2: Fill out the application form and attach required KYC documents.",
                    "Step 3: Fill out the declaration and nomination details.",
                    "Step 4: Submit the application form along with the initial deposit amount.",
                    "Step 5: Receive the certificate as proof of investment."
                ],
                "documents_required": ["KYC documents"]
            },
            {
                "name": "Pradhan Mantri Mudra Yojana (PMMY)",
                "category": GovernmentScheme.CATEGORY_ENTREPRENEURSHIP,
                "scheme_url": "",
                "application_steps": [
                    "Step 1: The applicant can visit a bank, NBFC, or microfinance institution offering Mudra loans.",
                    "Step 2: Collect and fill out the loan application form.",
                    "Step 3: Submit required documents (identity proof, address proof, business details, and plan).",
                    "Step 4: The bank verifies the application and assesses eligibility.",
                    "Step 5: Upon approval, the loan amount is sanctioned and credited to the applicant’s account."
                ],
                "documents_required": ["Identity proof", "Address proof", "Business details and plan"]
            },
            {
                "name": "Sukanya Samriddhi Yojana (SSY)",
                "category": GovernmentScheme.CATEGORY_FINANCIAL,
                "scheme_url": "https://www.nsiindia.gov.in/(S(sk0o2m45vlbkym45rwhf0055))/InternalPage.aspx?Id_Pk=89",
                "application_steps": [
                    "Step 1: The applicant can visit the nearest Post Office or authorized bank branch to collect the application form or download it from the official website.",
                    "Step 2: Fill out the application form and attach required documents (birth certificate of the girl child, identity proof, address proof).",
                    "Step 3: Provide guardian details and nomination information.",
                    "Step 4: Submit the application form along with the initial deposit amount.",
                    "Step 5: The account will be opened and a passbook will be issued as proof."
                ],
                "documents_required": ["Birth certificate of the girl child", "Identity proof", "Address proof"]
            }
        ]
        
        for sd in schemes:
            s = GovernmentScheme(
                name=sd["name"],
                category=sd["category"],
                application_steps=sd["application_steps"],
                documents_required=sd["documents_required"],
                scheme_url=sd.get("scheme_url", ""),
                is_active=True
            )
            db.session.add(s)
        
        db.session.commit()
        print(f"Successfully seeded {len(schemes)} schemes.")

if __name__ == '__main__':
    seed_schemes()
