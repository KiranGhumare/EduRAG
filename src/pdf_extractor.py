import fitz
import json
import re
from pathlib import Path

TEXT_LEN_THRESHOLD = 150

raw_pdfs_path = "../data/raw_pdfs"
extracted_pages_path = "../data/extracted_pages/pdf_pages.json"

meta_data_list = []


directory = Path(raw_pdfs_path)
files = directory.glob("*.pdf")

for file in files:
    doc = fitz.open(file)
    page_no = 0
    for page in doc:
        page_no+=1
        meta_data = {}
        text = page.get_text()
        if (len(text)<TEXT_LEN_THRESHOLD):
            meta_data["source_data"] = "ocr"
            meta_data["ocr_text"] = text
        else:
            meta_data["source_data"] = "digital_text"
            meta_data["text"] = text

        meta_data["page"] = page_no
        meta_data["pdf_title"] = file.name
        meta_data_list.append(meta_data)

with open(extracted_pages_path, "w", encoding="utf-8") as f:
    json.dump(meta_data_list, f)

print(f"Saved JSON to: {extracted_pages_path}")