import json
import os

with open("Data/Main-JSON.json", "r", encoding="utf-8") as f_main:
    main = json.load(f_main)

with open("Data/Add-JSON.json", "r", encoding="utf-8") as f_add:
    add = json.load(f_add)

# Set for fast duplicate checking
existing_sources = {item["source"] for item in main}

# Append only new entries
new_entries = 0
for item in add:
    if item["source"] not in existing_sources:
        main.append(item)
        new_entries += 1

# Save back the updated JSON
if new_entries > 0:
    with open("Data/Main-JSON.json", "w", encoding="utf-8") as f_main:
        json.dump(main, f_main, indent=2, ensure_ascii=False)
    print(f"[INFO] Added {new_entries} new items to Main-JSON.json")
else:
    print("[INFO] No new items to add.")