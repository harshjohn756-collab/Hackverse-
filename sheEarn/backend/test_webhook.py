"""
Test the full Didit.me KYC webhook → gender update → login gate flow.

Run while the backend is live:
  python test_webhook.py
"""
import sys, sqlite3, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "http://localhost:5000"
DB   = "instance/sheEarn.db"

# ── helpers ───────────────────────────────────────────────────────────────────
def db_user(phone):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, name, phone, gender, kyc_status, kyc_session_id FROM users WHERE phone=?", (phone,))
    row = c.fetchone()
    conn.close()
    return row

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print('─'*60)

# ── 1. Check state before ─────────────────────────────────────────────────────
PHONE = "9876543210"

section("1. User state BEFORE webhook")
print(db_user(PHONE))

# ── 2. Simulate Didit webhook: approved + female ──────────────────────────────
section("2. Sending webhook: status=approved, gender=F")
payload_female = {
    "vendor_data": "",        # will be resolved via phone fallback
    "session_id": "test-session-001",
    "status": "approved",
    "data": {
        "phone":  PHONE,
        "status": "approved",
    },
    "document": {
        "gender": "F",        # Didit returns F/M/X
        "name":   "Test User",
    },
}
res = requests.post(f"{BASE}/api/auth/kyc-webhook", json=payload_female)
print("Status Code:", res.status_code)
print("Response   :", res.json())

section("3. User state AFTER webhook (expect gender=female, kyc_status=approved)")
print(db_user(PHONE))

# ── 3. KYC status poll endpoint ────────────────────────────────────────────────
section("4. Polling /api/auth/kyc-status")
r = requests.get(f"{BASE}/api/auth/kyc-status", params={"phone": PHONE})
print("Status Code:", r.status_code)
print("Response   :", r.json())

# ── 4. Login should now succeed ────────────────────────────────────────────────
section("5. Login attempt (should SUCCEED for approved female provider)")
r = requests.post(f"{BASE}/api/auth/login", json={"phone": PHONE, "password": "test1234"})
print("Status Code:", r.status_code)
data = r.json()
print("Message    :", data.get("message"))
print("Has token  :", bool(data.get("data", {}).get("access_token")))

# ── 5. Test declined (non-female) ──────────────────────────────────────────────
section("6. Sending webhook: status=approved, gender=M (should DECLINE)")
PHONE2 = "9999999999"
# Only run if this user exists
u = db_user(PHONE2)
if u:
    payload_male = {
        "data": {"phone": PHONE2, "status": "approved"},
        "document": {"gender": "M"},
        "status": "approved",
    }
    res2 = requests.post(f"{BASE}/api/auth/kyc-webhook", json=payload_male)
    print("Webhook response:", res2.json())
    print("DB state:", db_user(PHONE2))

    r2 = requests.post(f"{BASE}/api/auth/login", json={"phone": PHONE2, "password": "test1234"})
    print("Login (should FAIL):", r2.status_code, r2.json().get("message"))
else:
    print(f"(User {PHONE2} not in DB — skipping male-decline test)")
