import easyocr
import sys

image_path = sys.argv[1]

print(f"Reading image: {image_path}")
reader = easyocr.Reader(["en", "kn"], gpu=False, verbose=False)
results = reader.readtext(image_path, detail=0)

raw_text = " ".join(results).lower()
print(f"Raw text extracted: {raw_text}")

fragments = [r.strip().lower() for r in results]
print(f"Fragments:")
for f in fragments:
    print(f"  - '{f}'")
