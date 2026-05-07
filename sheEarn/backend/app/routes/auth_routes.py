"""Authentication routes — register, login, refresh, logout"""
from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
import random
from datetime import datetime, timedelta

from app import db
from app.models.user import User
from app.models.payment import Wallet
from app.utils.responses import success, error

auth_bp = Blueprint("auth", __name__)

# Temporary in-memory OTP store (in production this should be in Redis)
# format: { phone: {"otp": "123456", "expires_at": datetime} }
OTP_STORE = {}


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form

    name     = (data.get("name")     or "").strip()
    username = (data.get("username") or "").strip() or None
    email    = (data.get("email")    or "").strip().lower() or None
    phone    = (data.get("phone")    or "").strip() or None
    password = data.get("password", "")
    role     = data.get("role", "customer")
    language = data.get("language", "en")
    security_question = data.get("security_question", "").strip()
    security_answer   = data.get("security_answer", "").strip()
    # Gender from form is only used for customers.
    # For providers it will be determined by Didit's document scan.
    gender   = data.get("gender", "female").lower()

    # ── Basic field validation ──────────────────────────────────────────────
    if not name:
        return error("Name is required")
    if not password or len(password) < 6:
        return error("Password must be at least 6 characters")
    if not username:
        return error("Username is required")
    if not email and not phone:
        return error("Email or phone number is required")
    if role not in ("provider", "customer"):
        return error("Role must be 'provider' or 'customer'")
    if not security_question or not security_answer:
        return error("Security question and answer are required for account recovery")

    if username and User.query.filter_by(username=username).first():
        return error("Username is already taken", 409)
    if email and User.query.filter_by(email=email).first():
        return error("Email already registered", 409)
    if phone and User.query.filter_by(phone=phone).first():
        return error("Phone number already registered", 409)

    # ── Provider: require ID document + KYC ────────────────────────────────
    if role == "provider":
        # Gender self-declaration is IGNORED for providers.
        # Gender is determined solely by OCR of the uploaded document.

        document_file = request.files.get("document")
        if not document_file:
            return error("A government-issued ID document is required for provider registration.")

        # ── Step 1: Local OCR — extract gender from document immediately ─
        from app.utils.didit_kyc import extract_gender_from_document, create_kyc_session

        ocr_gender, raw_text = extract_gender_from_document(document_file)
        print(f"[Register] OCR detected gender: {ocr_gender}")

        if ocr_gender == "male":
            return error(
                "Registration denied: Your ID document identifies you as male. "
                "Only women are permitted to register as service providers on SheEarn.",
                403,
            )

        if ocr_gender == "unknown":
            return error(
                f"Could not verify your gender from the uploaded document. "
                f"Please upload a clearer picture of your ID where your gender (Female) is clearly visible. "
                f"(OCR saw: {raw_text[:100]})",
                400,
            )

        # ── Step 2: Create user — strictly approved as female ────────────
        user = User(
            name=name, username=username, email=email, phone=phone,
            role=role, language=language,
            gender="female",
            kyc_status="approved",
            security_question=security_question
        )
        user.set_password(password)
        user.set_security_answer(security_answer)
        db.session.add(user)
        db.session.flush()   # assigns user.id without committing

        # Create wallet
        wallet = Wallet(user_id=user.id)
        db.session.add(wallet)
        db.session.commit()

        # ── Issue tokens immediately (OCR approved) ──────────────────────
        access_token  = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return success(
            {
                "access_token":  access_token,
                "refresh_token": refresh_token,
                "user":          user.to_dict(),
            },
            "Registration successful! Identity verified.",
            201,
        )

    # ── Customer registration — immediate login ─────────────────────────────
    user = User(
        name=name, username=username, email=email, phone=phone, 
        role=role, language=language, gender=gender,
        security_question=security_question
    )
    user.set_password(password)
    user.set_security_answer(security_answer)
    db.session.add(user)
    db.session.flush()

    wallet = Wallet(user_id=user.id)
    db.session.add(wallet)
    db.session.commit()

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success(
        {
            "user":          user.to_dict(),
            "access_token":  access_token,
            "refresh_token": refresh_token,
        },
        "Registration successful",
        201,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data       = request.get_json(silent=True) or {}
    identifier = (data.get("email") or data.get("phone") or "").strip()
    password   = data.get("password", "")

    if not identifier or not password:
        return error("Email/phone and password are required")

    user = User.query.filter(
        (User.email == identifier.lower()) | (User.phone == identifier) | (User.username == identifier)
    ).first()

    if not user or not user.check_password(password):
        return error("Invalid credentials", 401)
    if not user.is_active:
        return error("Account is deactivated. Contact support.", 403)

    # ── KYC gate for providers ──────────────────────────────────────────────
    if user.role == "provider":
        kyc_status = (user.kyc_status or "pending").lower()
        gender     = (user.gender     or "unverified").lower()

        if kyc_status == "pending":
            return error(
                "⏳ Your KYC verification is still in progress. "
                "Please wait — you will receive a notification once it is complete.",
                403,
            )

        if kyc_status == "declined":
            return error(
                "❌ KYC Verification Failed. Your document could not be verified as belonging to a woman. "
                "Only women are permitted to register as service providers on SheEarn.",
                403,
            )

        if kyc_status == "approved" and gender != "female":
            # Approved by Didit but gender was not female — safety check
            return error(
                "❌ Provider access denied: document does not confirm female identity.",
                403,
            )

        # kyc_status == "approved" AND gender == "female" — all good ✓

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success(
        {
            "user":          user.to_dict(),
            "access_token":  access_token,
            "refresh_token": refresh_token,
        },
        "Login successful",
    )


# ─────────────────────────────────────────────────────────────────────────────
# DIDIT KYC WEBHOOK
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/kyc-webhook", methods=["POST"])
def kyc_webhook():
    """
    Called by Didit.me when a KYC session status changes.

    Didit sends vendor_data = user.id (set during session creation).
    We use that to look up the user, then:
      - extract gender from the document scan
      - set kyc_status = "approved" if female, else "declined"
    """
    payload = request.get_json(silent=True) or {}
    print(f"[Didit Webhook] Received: {payload}")

    from app.utils.didit_kyc import extract_gender_from_webhook, extract_kyc_status

    # ── Locate user ─────────────────────────────────────────────────────────
    data_block = payload.get("data") or {}

    # Primary: vendor_data is the user.id we passed during session creation
    vendor_data = (
        payload.get("vendor_data")
        or data_block.get("vendor_data")
        or str(payload.get("user_id", ""))
        or str(data_block.get("user_id", ""))
    ).strip()

    # Secondary: session_id stored in user.kyc_session_id
    session_id = (
        payload.get("session_id")
        or payload.get("id")
        or data_block.get("session_id")
        or ""
    ).strip()

    # Tertiary: email / phone
    email = data_block.get("email") or payload.get("email") or ""
    phone = data_block.get("phone") or payload.get("phone") or ""

    user = None
    if vendor_data and vendor_data.isdigit():
        user = User.query.get(int(vendor_data))
    if not user and session_id:
        user = User.query.filter_by(kyc_session_id=session_id).first()
    if not user and email:
        user = User.query.filter_by(email=email).first()
    if not user and phone:
        user = User.query.filter_by(phone=phone).first()

    if not user:
        print("[Didit Webhook] WARNING: Could not match payload to any user.")
        return success(message="Webhook received (user not found)")

    # ── Extract KYC outcome ─────────────────────────────────────────────────
    didit_status = extract_kyc_status(payload)
    gender       = extract_gender_from_webhook(payload)

    print(f"[Didit Webhook] user={user.id} ({user.name}), didit_status={didit_status}, gender={gender}")

    if didit_status == "approved":
        if gender == "female":
            # ✅ Verified female — full provider access granted
            user.gender     = "female"
            user.kyc_status = "approved"
            print(f"[Didit Webhook] APPROVED & female -- user {user.id} can now log in.")
        elif gender in ("male", "other"):
            # ❌ Document scanned but not female
            user.gender     = gender
            user.kyc_status = "declined"
            print(f"[Didit Webhook] DECLINED: gender mismatch ({gender}) -- provider access denied.")
        else:
            # Gender not in payload yet — mark approved, gender stays unverified
            # (A follow-up webhook may provide gender)
            user.kyc_status = "approved"
            print(f"[Didit Webhook] WARNING: Approved but no gender data -- kyc_status=approved, gender stays unverified.")

    elif didit_status == "declined":
        user.kyc_status = "declined"
        if gender:
            user.gender = gender
        print(f"[Didit Webhook] DECLINED by Didit -- user {user.id}.")

    else:
        # Still pending or unknown
        user.kyc_status = didit_status
        print(f"[Didit Webhook] ℹ️  Status={didit_status} — no change to gender.")

    # Update session_id if not already stored
    if session_id and not user.kyc_session_id:
        user.kyc_session_id = session_id

    db.session.commit()
    return success(message="Webhook processed")


# ─────────────────────────────────────────────────────────────────────────────
# KYC STATUS CHECK  (frontend polls this after registration)
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/kyc-status", methods=["GET"])
def kyc_status_check():
    """
    Returns the current KYC status for a user identified by email or phone.
    The frontend can poll this every few seconds after provider registration.
    """
    email = request.args.get("email", "").strip().lower()
    phone = request.args.get("phone", "").strip()

    user = None
    if email:
        user = User.query.filter_by(email=email).first()
    if not user and phone:
        user = User.query.filter_by(phone=phone).first()

    if not user:
        return error("User not found", 404)

    return success(
        {
            "kyc_status": user.kyc_status,
            "gender":     user.gender,
            "can_login":  user.kyc_status == "approved" and user.gender == "female",
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# OTP LOGIN
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/request-otp", methods=["POST"])
def request_otp():
    data  = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()

    if not phone:
        return error("Phone number is required")

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return error("Phone number not registered", 404)

    otp_code = str(random.randint(100000, 999999))
    OTP_STORE[phone] = {
        "otp": otp_code,
        "expires_at": datetime.utcnow() + timedelta(minutes=5)
    }

    print(f"--- MOCK OTP FOR {phone}: {otp_code} ---")
    return success(message=f"OTP sent successfully (hint: it's {otp_code})")


@auth_bp.route("/login-otp", methods=["POST"])
def login_otp():
    data  = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    otp   = (data.get("otp")   or "").strip()

    if not phone or not otp:
        return error("Phone and OTP are required")
        
    record = OTP_STORE.get(phone)
    if not record:
        return error("No OTP requested for this phone", 400)
    if datetime.utcnow() > record["expires_at"]:
        del OTP_STORE[phone]
        return error("OTP expired", 400)
    if otp != record["otp"]:
        return error("Invalid OTP", 401)
        
    # Clear OTP after successful use
    del OTP_STORE[phone]

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return error("User not found", 404)
    if not user.is_active:
        return error("Account is deactivated. Contact support.", 403)

    # KYC gate for providers via OTP too
    if user.role == "provider":
        kyc_status = (user.kyc_status or "pending").lower()
        gender     = (user.gender     or "unverified").lower()
        if kyc_status == "pending":
            return error("⏳ KYC verification is still in progress. Please try again shortly.", 403)
        if kyc_status == "declined" or gender != "female":
            return error("❌ KYC failed. Provider access denied.", 403)

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success(
        {
            "user":          user.to_dict(),
            "access_token":  access_token,
            "refresh_token": refresh_token,
        },
        "OTP Login successful",
    )


# ─────────────────────────────────────────────────────────────────────────────
# STANDARD HELPERS
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id   = get_jwt_identity()
    new_token = create_access_token(identity=user_id)
    return success({"access_token": new_token}, "Token refreshed")


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    from app.utils.auth import get_current_user
    user = get_current_user()
    if not user:
        return error("User not found", 404)
    data = user.to_dict()
    if user.profile:
        data["profile"] = user.profile.to_dict()
    if user.wallet:
        data["wallet"] = user.wallet.to_dict()
    return success(data)


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    from app.utils.auth import get_current_user
    user   = get_current_user()
    data   = request.get_json(silent=True) or {}
    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "")

    if not user.check_password(old_pw):
        return error("Current password is incorrect", 401)
    if len(new_pw) < 6:
        return error("New password must be at least 6 characters")

    user.set_password(new_pw)
    db.session.commit()
    return success(message="Password changed successfully")


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD RECOVERY
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    identifier = (data.get("identifier") or "").strip()

    if not identifier:
        return error("Email or phone is required")

    user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()
    if not user:
        return error("No account found with this email/phone", 404)

    if not user.security_question:
        return error("This account does not have a security question set up. Please contact admin.", 400)

    return success({
        "message": "Security question retrieved",
        "security_question": user.security_question
    })


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    identifier = (data.get("identifier") or "").strip()
    answer = (data.get("security_answer") or "").strip()
    new_password = data.get("new_password", "")

    if not identifier or not answer or not new_password:
        return error("Identifier, security answer, and new password are required")

    if len(new_password) < 6:
        return error("Password must be at least 6 characters")

    user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()
    if not user:
        return error("No account found with this email/phone", 404)

    if not user.check_security_answer(answer):
        return error("Incorrect security answer", 401)

    user.set_password(new_password)
    db.session.commit()

    return success({"message": "Password has been successfully reset. You can now log in."})
