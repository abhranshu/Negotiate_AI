from datasets import load_dataset

SAVE_PATH = r"C:\Users\Lenovo\OneDrive\Desktop\MSME Major project\data"

# Option 1 — Full dataset (~38 GB) — skip unless you have storage
# ds = load_dataset("aharley/rvl_cdip", cache_dir=SAVE_PATH)

# Option 2 — Invoice-only subset (~2-5 GB) ✅ RECOMMENDED for MSME project
ds = load_dataset("chainyo/rvl-cdip-invoice", cache_dir=SAVE_PATH)

# Option 3 — With OCR text pre-extracted (~5-10 GB)
# ds = load_dataset("jordyvl/rvl_cdip_easyocr", cache_dir=SAVE_PATH)

print("Download complete!")
print(ds)
print("\nFirst sample:", ds["train"][0])
