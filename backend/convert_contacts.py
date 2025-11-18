import openpyxl
import json
import re

# Read Excel file
wb = openpyxl.load_workbook(r"C:\Users\lenovo\Desktop\smartii\Contacts backup [02.13.17 am] [11-18-2025].xlsx")
ws = wb.active

contacts = []

# Skip header row, start from row 2
for row in ws.iter_rows(min_row=2, values_only=True):
    # Try to extract name and phone from first few columns
    name = None
    phone = None
    
    for cell in row:
        if cell and isinstance(cell, str):
            # Check if it looks like a phone number
            if re.search(r'[\d+\-\s()]{8,}', cell):
                # Clean phone number
                phone = re.sub(r'[^\d+]', '', cell)
                if not phone.startswith('+'):
                    phone = '+91' + phone  # Assume India if no country code
            elif not name and len(cell.strip()) > 0:
                # First non-phone text is likely the name
                name = cell.strip()
    
    if name and phone:
        contacts.append({"name": name, "phone": phone})

# Save to JSON
with open(r"C:\Users\lenovo\Desktop\smartii\backend\integrations\contacts.json", 'w', encoding='utf-8') as f:
    json.dump(contacts, f, indent=2, ensure_ascii=False)

print(f"✅ Converted {len(contacts)} contacts!")
for i, c in enumerate(contacts[:5]):  # Show first 5
    print(f"  {c['name']}: {c['phone']}")
if len(contacts) > 5:
    print(f"  ... and {len(contacts)-5} more")
