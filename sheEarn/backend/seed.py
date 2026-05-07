"""
Seed script — populate the database with initial demo data.
Run: python seed.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.profile import Profile
from app.models.service import Service
from app.models.booking import Booking
from app.models.payment import Wallet
from app.models.scheme import GovernmentScheme
from datetime import datetime, timedelta

app = create_app("development")


def seed():
    with app.app_context():
        print("Dropping and recreating all tables...")
        db.drop_all()
        db.create_all()

        # ── Admin ──────────────────────────────────────────────────────────────
        admin = User(name="SheEarn Admin", email="admin@sheEarn.com", role="admin", language="en")
        admin.set_password("Admin@123")
        db.session.add(admin)
        db.session.flush()
        db.session.add(Wallet(user_id=admin.id))

        # ── Providers ──────────────────────────────────────────────────────────
        providers_data = [
            dict(name="Kavitha Reddy",   phone="9876543210", lang="kn", loc="Bengaluru", lat=12.9716, lon=77.5946, skills=["stitching","embroidery"]),
            dict(name="Sunita Devi",     phone="9876543211", lang="hi", loc="Mysuru",    lat=12.2958, lon=76.6394, skills=["cooking","tiffin"]),
            dict(name="Lakshmi Nair",    phone="9876543212", lang="kn", loc="Bengaluru", lat=12.9352, lon=77.6245, skills=["tutoring","math"]),
            dict(name="Priya Sharma",    phone="9876543213", lang="hi", loc="Hubballi",  lat=15.3647, lon=75.1240, skills=["beauty","mehendi"]),
            dict(name="Anjali Kumari",   phone="9876543214", lang="en", loc="Bengaluru", lat=13.0297, lon=77.5502, skills=["handmade_crafts"]),
        ]
        providers = []
        for p in providers_data:
            u = User(name=p["name"], phone=p["phone"], role="provider", language=p["lang"])
            u.set_password("Provider@123")
            db.session.add(u)
            db.session.flush()
            db.session.add(Wallet(user_id=u.id))
            profile = Profile(user_id=u.id, location=p["loc"], latitude=p["lat"], longitude=p["lon"])
            profile.skills = p["skills"]
            db.session.add(profile)
            providers.append(u)

        # ── Customers ─────────────────────────────────────────────────────────
        customers_data = [
            dict(name="Ravi Kumar",   phone="9123456780", lang="kn"),
            dict(name="Meera Pillai", phone="9123456781", lang="en"),
            dict(name="Arjun Singh",  phone="9123456782", lang="hi"),
        ]
        customers = []
        for c in customers_data:
            u = User(name=c["name"], phone=c["phone"], role="customer", language=c["lang"])
            u.set_password("Customer@123")
            db.session.add(u)
            db.session.flush()
            db.session.add(Wallet(user_id=u.id))
            customers.append(u)

        # ── Services ──────────────────────────────────────────────────────────
        services_data = [
            dict(provider=0, title="Custom Blouse Stitching",    category="stitching",      price=350),
            dict(provider=1, title="Home-cooked Tiffin Service",  category="cooking",        price=120),
            dict(provider=2, title="Mathematics Tuition (1-10)",  category="tutoring",       price=500),
            dict(provider=3, title="Bridal Mehendi Design",       category="beauty",         price=800),
            dict(provider=4, title="Handmade Jute Bags",          category="handmade_crafts",price=250),
            dict(provider=0, title="Embroidery Work on Sarees",   category="stitching",      price=600),
            dict(provider=1, title="Special Occasion Cooking",    category="cooking",        price=1500),
        ]
        services = []
        for sd in services_data:
            s = Service(
                provider_id=providers[sd["provider"]].id,
                title=sd["title"],
                category=sd["category"],
                price=sd["price"],
                description=f"Professional {sd['category']} service offered by a skilled woman entrepreneur.",
                is_approved=True,
            )
            db.session.add(s)
            services.append(s)

        db.session.flush()

        # ── Bookings ──────────────────────────────────────────────────────────
        booking1 = Booking(
            service_id=services[0].id,
            customer_id=customers[0].id,
            provider_id=providers[0].id,
            scheduled_at=datetime.utcnow() + timedelta(days=2),
            status=Booking.STATUS_ACCEPTED,
            address="123 MG Road, Bengaluru",
        )
        booking2 = Booking(
            service_id=services[1].id,
            customer_id=customers[1].id,
            provider_id=providers[1].id,
            scheduled_at=datetime.utcnow() - timedelta(days=1),
            status=Booking.STATUS_COMPLETED,
            address="45 Lal Bagh Road, Mysuru",
        )
        db.session.add_all([booking1, booking2])

        # ── Government Schemes ────────────────────────────────────────────────
        schemes = [
            GovernmentScheme(
                name="PM Vishwakarma Yojana",
                category=GovernmentScheme.CATEGORY_ENTREPRENEURSHIP,
                eligibility="Women artisans and craftspeople aged 18+",
                benefits="Skill training, ₹15,000 toolkit, collateral-free loan up to ₹3 lakh at 5% interest",
                scheme_url="https://pmvishwakarma.gov.in/",
            ),
            GovernmentScheme(
                name="Stand Up India",
                category=GovernmentScheme.CATEGORY_FINANCIAL,
                eligibility="Women entrepreneurs for greenfield enterprises",
                benefits="Bank loans between ₹10 lakh – ₹1 crore for SC/ST/Women",
                scheme_url="https://www.standupmitra.in/",
            ),
            GovernmentScheme(
                name="Pradhan Mantri Matru Vandana Yojana (PMMVY)",
                category=GovernmentScheme.CATEGORY_HEALTH,
                eligibility=(
                    "Women whose net family income is less than \u20b98 Lakh per annum; "
                    "Women holding MGNREGA Job Card; "
                    "Women farmers under Kisan Samman Nidhi; "
                    "Women holding e-Shram card; "
                    "Women under PMJAY (Ayushman Bharat); "
                    "Women holding BPL ration card; "
                    "Women partially (40%) or fully disabled (Divyang Jan); "
                    "SC/ST Women; "
                    "Pregnant and Lactating AWWS/AWHS/ASHAS; "
                    "Women holding ration card under NFSA 2013."
                ),
                eligibility_hi=(
                    "\u091c\u093f\u0928 \u092e\u0939\u093f\u0932\u093e\u0913\u0902 \u0915\u0940 \u0915\u0941\u0932 \u092a\u093e\u0930\u093f\u0935\u093e\u0930\u093f\u0915 \u0906\u092f \u20b98 \u0932\u093e\u0916 \u092a\u094d\u0930\u0924\u093f \u0935\u0930\u094d\u0937 \u0938\u0947 \u0915\u092e \u0939\u0948; "
                    "\u092e\u0928\u0930\u0947\u0917\u093e \u091c\u0949\u092c \u0915\u093e\u0930\u094d\u0921 \u0927\u093e\u0930\u0915 \u092e\u0939\u093f\u0932\u093e\u090f\u0901; "
                    "\u0915\u093f\u0938\u093e\u0928 \u0938\u092e\u094d\u092e\u093e\u0928 \u0928\u093f\u0927\u093f \u0915\u0947 \u0924\u0939\u0924 \u0932\u093e\u092d\u093e\u0930\u094d\u0925\u0940 \u092e\u0939\u093f\u0932\u093e \u0915\u093f\u0938\u093e\u0928; "
                    "\u0908-\u0936\u094d\u0930\u092e \u0915\u093e\u0930\u094d\u0921 \u0930\u0916\u0928\u0947 \u0935\u093e\u0932\u0940 \u092e\u0939\u093f\u0932\u093e\u090f\u0902; "
                    "\u092c\u0940.\u092a\u0940.\u090f\u0932. \u0930\u093e\u0936\u0928 \u0915\u093e\u0930\u094d\u0921 \u0927\u093e\u0930\u0915 \u092e\u0939\u093f\u0932\u093e\u090f\u0901; "
                    "\u0906\u0902\u0936\u093f\u0915 \u0930\u0942\u092a \u0938\u0947 (40%) \u092f\u093e \u092a\u0942\u0930\u0940 \u0924\u0930\u0939 \u0938\u0947 \u0935\u093f\u0915\u0932\u093e\u0902\u0917 \u092e\u0939\u093f\u0932\u093e\u090f\u0902; "
                    "\u090f\u0938\u0938\u0940/\u090f\u0938\u091f\u0940 \u092e\u0939\u093f\u0932\u093e\u090f\u0901; "
                    "\u0917\u0930\u094d\u092d\u0935\u0924\u0940 \u0914\u0930 \u0938\u094d\u0924\u0928\u092a\u093e\u0928 \u0915\u0930\u093e\u0928\u0947 \u0935\u093e\u0932\u0940 \u092e\u0939\u093f\u0932\u093e\u090f\u0901."
                ),
                eligibility_kn=(
                    "\u0c95\u0cc1\u0c9f\u0cc1\u0c82\u0cac\u0ca6 \u0ca8\u0cbf\u0cb5\u0ccd\u0cb5\u0cb3 \u0c86\u0ca6\u0cbe\u0caf \u0cb5\u0cbe\u0cb0\u0ccd\u0cb7\u0cbf\u0c95 \u20b98 \u0cb2\u0c95\u0ccd\u0cb7\u0c95\u0ccd\u0c95\u0cbf\u0c82\u0ca4 \u0c95\u0ca1\u0cbf\u0cae\u0cc6 \u0c87\u0cb0\u0cc1\u0cb5 \u0cae\u0cb9\u0cbf\u0cb3\u0cc6\u0caf\u0cb0\u0cc1; "
                    "\u0c8e\u0c82\u0c9c\u0cbf\u0c8e\u0ca8\u0ccd\u0c86\u0cb0\u0ccd\u0c87\u0c9c\u0cbf\u0c8e \u0c9c\u0cbe\u0cac\u0ccd \u0c95\u0cbe\u0cb0\u0ccd\u0ca1\u0ccd \u0cb9\u0cca\u0c82\u0ca6\u0cbf\u0cb0\u0cc1\u0cb5 \u0cae\u0cb9\u0cbf\u0cb3\u0cc6\u0caf\u0cb0\u0cc1; "
                    "\u0c87-\u0cb6\u0ccd\u0cb0\u0cae \u0c95\u0cbe\u0cb0\u0ccd\u0ca1\u0ccd \u0cb9\u0cca\u0c82\u0ca6\u0cbf\u0cb0\u0cc1\u0cb5 \u0cae\u0cb9\u0cbf\u0cb3\u0cc6\u0caf\u0cb0\u0cc1; "
                    "\u0cac\u0cbf\u0caa\u0cbf\u0c8e\u0cb2\u0ccd \u0caa\u0ca1\u0cbf\u0ca4\u0cb0 \u0c9a\u0cc0\u0c9f\u0cbf \u0cb9\u0cca\u0c82\u0ca6\u0cbf\u0cb0\u0cc1\u0cb5 \u0cae\u0cb9\u0cbf\u0cb3\u0cc6\u0caf\u0cb0\u0cc1; "
                    "\u0c8e\u0cb8\u0ccd\u0cb8\u0cbf/\u0c8e\u0cb8\u0ccd.\u0c9f\u0cbf. \u0cae\u0cb9\u0cbf\u0cb3\u0cc6\u0caf\u0cb0\u0cc1; "
                    "\u0c97\u0cb0\u0ccd\u0cad\u0cbf\u0ca3\u0cbf \u0cae\u0ca4\u0ccd\u0ca4\u0cc1 \u0cb9\u0cbe\u0cb2\u0cc1\u0ca3\u0cbf\u0cb8\u0cc1\u0cb5 \u0cae\u0cb9\u0cbf\u0cb3\u0cc6\u0caf\u0cb0\u0cc1."
                ),
                benefits="\u20b95,000 cash incentive in instalments for first live birth",
                scheme_url="https://pmmvy.wcd.gov.in/",
            ),
            GovernmentScheme(
                name="Mahila Shakti Kendra (MSK)",
                category=GovernmentScheme.CATEGORY_SAFETY,
                eligibility="Rural women in 115 aspirational districts",
                benefits="Community engagement, skill development, digital literacy",
                scheme_url="https://wcd.nic.in/",
            ),
            GovernmentScheme(
                name="Udyogini Scheme",
                category=GovernmentScheme.CATEGORY_ENTREPRENEURSHIP,
                eligibility="Women below poverty line aged 18-55",
                benefits="Subsidy up to ₹10,000 for starting a small business",
                scheme_url="https://www.pfc.gov.in/",
            ),
        ]
        for s in schemes:
            s.application_steps = ["Visit the nearest bank/CSC", "Fill application form", "Submit KYC documents", "Await approval"]

        # ── PMMVY: detailed documents required (multilingual) ─────────
        pmmvy = schemes[2]  # index 2 = PMMVY
        pmmvy.documents_required = [
            "Aadhaar card",
            "Aadhaar mapped bank/post office account",
            "Bank account details",
            "Eligibility proof (any one): MGNREGA Job Card / e-Shram card / BPL ration card / NFSA ration card",
            "MCP/RCHI card",
            "LMP date",
            "ANC date",
            "Child birth certificate",
            "Child immunization details",
            "Mobile number (mandatory)",
        ]
        pmmvy.documents_required_hi = (
            "\u0906\u0927\u093e\u0930 \u0915\u093e\u0930\u094d\u0921; "
            "\u0906\u0927\u093e\u0930 \u092e\u093e\u0928\u091a\u093f\u0924\u094d\u0930\u093f\u0924 \u092c\u0948\u0902\u0915/\u0921\u093e\u0915\u0918\u0930; "
            "\u092c\u0948\u0902\u0915 \u0916\u093e\u0924\u0947 \u0915\u093e \u0935\u093f\u0935\u0930\u0923; "
            "\u092a\u093e\u0924\u094d\u0930\u0924\u093e \u092a\u094d\u0930\u092e\u093e\u0923; "
            "\u090f\u092e\u0938\u0940\u092a\u0940/\u0906\u0930\u0938\u0940\u090f\u091a\u0906\u0908 \u0915\u093e\u0930\u094d\u0921; "
            "\u090f\u0932\u090f\u092e\u092a\u0940 \u0924\u093f\u0925\u093f; "
            "\u090f\u090f\u0928\u0938\u0940 \u0924\u093f\u0925\u093f; "
            "\u092c\u093e\u0932 \u091c\u0928\u094d\u092e \u092a\u094d\u0930\u092e\u093e\u0923 \u092a\u0924\u094d\u0930; "
            "\u092c\u093e\u0932 \u091f\u0940\u0915\u093e\u0915\u0930\u0923 \u0935\u093f\u0935\u0930\u0923; "
            "\u092e\u094b\u092c\u093e\u0907\u0932 \u0928\u0902\u092c\u0930 (\u0905\u0928\u093f\u0935\u093e\u0930\u094d\u092f)"
        )
        pmmvy.documents_required_kn = (
            "\u0c86\u0ca7\u0cbe\u0cb0\u0ccd \u0c95\u0cbe\u0cb0\u0ccd\u0ca1\u0ccd; "
            "\u0c86\u0ca7\u0cbe\u0cb0\u0ccd \u0cae\u0ccd\u0caf\u0cbe\u0caa\u0ccd \u0cae\u0cbe\u0ca1\u0cb2\u0cbe\u0ca6 \u0cac\u0ccd\u0caf\u0cbe\u0c82\u0c95\u0ccd/\u0c85\u0c82\u0c9a\u0cc6 \u0c95\u0c9a\u0cc7\u0cb0\u0cbf; "
            "\u0cac\u0ccd\u0caf\u0cbe\u0c82\u0c95\u0ccd \u0c96\u0cbe\u0ca4\u0cc6 \u0cb5\u0cbf\u0cb5\u0cb0\u0c97\u0cb3\u0cc1; "
            "\u0c85\u0cb0\u0ccd\u0cb9\u0ca4\u0cbe \u0caa\u0cc1\u0cb0\u0cbe\u0cb5\u0cc6; "
            "\u0c8e\u0c82.\u0cb8\u0cbf.\u0caa\u0cbf/\u0c86\u0cb0\u0ccd.\u0cb8\u0cbf.\u0c8e\u0c9a\u0ccd.\u0c90. \u0c95\u0cbe\u0cb0\u0ccd\u0ca1\u0ccd; "
            "\u0c8e\u0cb2\u0ccd.\u0c8e\u0c82.\u0caa\u0cbf \u0ca6\u0cbf\u0ca8\u0cbe\u0c82\u0c95; "
            "\u0c8e\u0c8e\u0ca8\u0ccd\u0cb8\u0cbf \u0ca6\u0cbf\u0ca8\u0cbe\u0c82\u0c95; "
            "\u0cae\u0c95\u0ccd\u0c95\u0cb3 \u0c9c\u0ca8\u0ca8 \u0caa\u0ccd\u0cb0\u0cae\u0cbe\u0ca3\u0caa\u0ca4\u0ccd\u0cb0; "
            "\u0cae\u0c95\u0ccd\u0c95\u0cb3 \u0cb0\u0ccb\u0c97\u0ca8\u0cbf\u0cb0\u0ccb\u0ca7\u0c95 \u0cb5\u0cbf\u0cb5\u0cb0\u0c97\u0cb3\u0cc1; "
            "\u0cae\u0cca\u0cac\u0cc8\u0cb2\u0ccd \u0cb8\u0c82\u0c96\u0ccd\u0caf\u0cc6 (\u0c95\u0ca1\u0ccd\u0ca1\u0cbe\u0caf)"
        )
        pmmvy.application_steps = [
            "Register via PMMVY Mobile App or visit nearest Anganwadi Centre/Health Facility",
            "Submit Aadhaar and bank details",
            "Upload eligibility proof document",
            "Submit MCP card and ANC/LMP dates",
            "Await verification and fund disbursement",
        ]

        db.session.add_all(schemes)

        db.session.commit()
        print("\n[DONE] Database seeded successfully!")
        print(f"   Admin     : admin@sheEarn.com  / Admin@123")
        print(f"   Providers : phone 987654321X   / Provider@123  (X = 0–4)")
        print(f"   Customers : phone 912345678X   / Customer@123  (X = 0–2)")


if __name__ == "__main__":
    seed()
