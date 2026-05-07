"""
Full end-to-end test: Provider registration with MALE vs FEMALE ID documents.
Tests the complete flow: upload -> OCR -> accept/reject -> login gate.
"""
import sys, io, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
os.environ['FLASK_ENV'] = 'development'

import requests
from PIL import Image, ImageDraw, ImageFont

BASE = "http://localhost:5000"

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def make_id_image(name, gender_text):
    """Create a fake Aadhaar-like ID image with gender text."""
    img = Image.new('RGB', (600, 300), color='white')
    d = ImageDraw.Draw(img)
    # Use larger text for better OCR
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    d.text((30, 30), f"Government of India", fill='black', font=font)
    d.text((30, 70), f"Name: {name}", fill='black', font=font)
    d.text((30, 110), f"DOB: 01/01/1990", fill='black', font=font)
    d.text((30, 150), f"Gender / {gender_text}", fill='black', font=font)
    d.text((30, 190), f"Aadhaar: 1234 5678 9012", fill='black', font=font)
    
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=95)
    buf.seek(0)
    return buf

# =====================================================================
#  TEST 1: MALE ID Document -> Should be REJECTED
# =====================================================================
section("TEST 1: Register as Provider with MALE ID")

male_doc = make_id_image("Harsha A", "MALE")

resp = requests.post(f"{BASE}/api/auth/register", data={
    'name': 'Test Male User',
    'phone': '1111111111',
    'password': 'Test@123',
    'role': 'provider',
    'language': 'en',
}, files={
    'document': ('male_aadhaar.jpg', male_doc, 'image/jpeg')
})

print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Success: {data.get('success')}")
print(f"Message: {data.get('error') or data.get('message')}")

if resp.status_code == 403:
    print("\n>>> PASS: Male ID correctly REJECTED!")
else:
    print(f"\n>>> FAIL: Expected 403, got {resp.status_code}")

# =====================================================================
#  TEST 2: FEMALE ID Document -> Should be ACCEPTED
# =====================================================================
section("TEST 2: Register as Provider with FEMALE ID")

female_doc = make_id_image("Kavitha Devi", "FEMALE")

resp2 = requests.post(f"{BASE}/api/auth/register", data={
    'name': 'Test Female User',
    'phone': '2222222222',
    'password': 'Test@123',
    'role': 'provider',
    'language': 'en',
}, files={
    'document': ('female_aadhaar.jpg', female_doc, 'image/jpeg')
})

print(f"Status: {resp2.status_code}")
data2 = resp2.json()
print(f"Success: {data2.get('success')}")
print(f"Message: {data2.get('message')}")
has_token2 = bool(data2.get('data', {}).get('access_token'))
print(f"Has token: {has_token2}")
print(f"User: {data2.get('data', {}).get('user', {}).get('kyc_status')}")

if resp2.status_code in (200, 201) and has_token2:
    print("\n>>> PASS: Female ID auto-approved with immediate login!")
else:
    print(f"\n>>> FAIL: Expected 201 with token, got {resp2.status_code}")

# =====================================================================
#  TEST 3: Login the auto-approved female provider (should WORK)
# =====================================================================
section("TEST 3: Login auto-approved female provider")

resp3 = requests.post(f"{BASE}/api/auth/login", json={
    'phone': '2222222222',
    'password': 'Test@123',
})

print(f"Status: {resp3.status_code}")
data3 = resp3.json()
has_token3 = bool(data3.get('data', {}).get('access_token'))
print(f"Has token: {has_token3}")
print(f"Message: {data3.get('message')}")

if resp3.status_code == 200 and has_token3:
    print("\n>>> PASS: Auto-approved female provider can LOGIN!")
else:
    print(f"\n>>> FAIL: Expected 200 with token, got {resp3.status_code}")

# =====================================================================
#  TEST 4: Male provider tries to login (should not exist)
# =====================================================================
section("TEST 4: Male provider login attempt (user not created)")

resp4 = requests.post(f"{BASE}/api/auth/login", json={
    'phone': '1111111111',
    'password': 'Test@123',
})

print(f"Status: {resp4.status_code}")
data4 = resp4.json()
print(f"Message: {data4.get('error') or data4.get('message')}")

if resp4.status_code == 401:
    print("\n>>> PASS: Male user was never created — login denied!")
else:
    print(f"\n>>> FAIL: Expected 401, got {resp4.status_code}")

# =====================================================================
#  SUMMARY
# =====================================================================
section("RESULTS SUMMARY")
print("Test 1 (Male ID rejected):           ", "PASS" if resp.status_code == 403 else "FAIL")
print("Test 2 (Female ID auto-approved):     ", "PASS" if resp2.status_code in (200,201) and has_token2 else "FAIL")
print("Test 3 (Approved female can login):   ", "PASS" if resp3.status_code == 200 and has_token3 else "FAIL")
print("Test 4 (Male user never created):     ", "PASS" if resp4.status_code == 401 else "FAIL")
