"""Test resume upload API"""
import requests
import json
import os

url = 'http://localhost:9091/api/resume/upload'

# Get file from CV directory using short name
cv_dir = r'C:\Users\Administrator\Desktop\职引未来\CV'

# List files in CV directory
print(f"Files in CV directory:")
for f in os.listdir(cv_dir):
    print(f"  - {f}")

# Get the docx file
docx_files = [f for f in os.listdir(cv_dir) if f.endswith('.docx')]
if not docx_files:
    print("No DOCX files found!")
    exit(1)

docx_path = os.path.join(cv_dir, docx_files[0])
print(f"\nTesting upload: {docx_files[0]}")
print("-" * 50)

with open(docx_path, 'rb') as f:
    files = {'file': ('resume.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
    data = {'save_raw': 'true'}
    response = requests.post(url, files=files, data=data)
    print(f'Status Code: {response.status_code}')

    if response.status_code == 200:
        result = response.json()
        print("\nParsed Resume Data:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f'Error: {response.text}')
