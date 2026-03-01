"""Test resume upload API - PDF version"""
import requests
import json
import os

url = 'http://localhost:9091/api/resume/upload'

cv_dir = r'C:\Users\Administrator\Desktop\职引未来\CV'

# Get the PDF file
pdf_files = [f for f in os.listdir(cv_dir) if f.endswith('.pdf')]
if not pdf_files:
    print("No PDF files found!")
    exit(1)

pdf_path = os.path.join(cv_dir, pdf_files[0])
print(f"Testing PDF upload: {pdf_files[0]}")
print("-" * 50)

with open(pdf_path, 'rb') as f:
    files = {'file': ('resume.pdf', f, 'application/pdf')}
    data = {'save_raw': 'true'}
    response = requests.post(url, files=files, data=data)
    print(f'Status Code: {response.status_code}')

    if response.status_code == 200:
        result = response.json()
        print("\nParsed Resume Data:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f'Error: {response.text}')
