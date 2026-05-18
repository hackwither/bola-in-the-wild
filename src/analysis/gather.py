import json
from pathlib import Path

# Folder containing individual report JSON files
RAW_REPORTS_DIR = Path("../data/raw_reports")

# Output file
OUTPUT_FILE = "../data/combined_reports.json"

combined_reports = []

# Iterate through all JSON files
for file_path in RAW_REPORTS_DIR.glob("*.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        combined_reports.append({
            "source_file": file_path.name,
            "content": data
        })

    except Exception as e:
        print(f"[!] Failed to process {file_path.name}: {e}")

# Write combined output
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(combined_reports, f, indent=2, ensure_ascii=False)

print(f"[+] Combined {len(combined_reports)} reports into {OUTPUT_FILE}")