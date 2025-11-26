import requests
import time
import sys
import os

# Configuration
API_URL = "http://localhost:8000"
PDF_PATH = "docs/dwr-25-40-2.pdf"

def verify_pipeline():
    if not os.path.exists(PDF_PATH):
        print(f"Error: File {PDF_PATH} not found.")
        return

    print(f"Uploading {PDF_PATH}...")
    with open(PDF_PATH, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{API_URL}/documents/", files=files)
    
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return

    doc_data = response.json()
    doc_id = doc_data["document_id"]
    print(f"Document uploaded. ID: {doc_id}, Status: {doc_data['status']}")

    # Poll for status
    print("Waiting for processing...")
    for _ in range(60):  # Wait up to 60 seconds
        time.sleep(2)
        response = requests.get(f"{API_URL}/documents/{doc_id}")
        if response.status_code != 200:
            print(f"Error fetching status: {response.text}")
            continue
        
        status = response.json()["status"]
        print(f"Status: {status}")
        
        if status == "SUCCESS":
            break
        elif status == "FAILED":
            print("Processing failed.")
            return

    if status != "SUCCESS":
        print("Timeout waiting for processing.")
        return

    # Fetch blocks
    print("Fetching blocks...")
    response = requests.get(f"{API_URL}/documents/{doc_id}/blocks")
    if response.status_code != 200:
        print(f"Error fetching blocks: {response.text}")
        return

    blocks = response.json()
    print(f"Total blocks: {len(blocks)}")
    
    # Analyze structure
    roles = {}
    for b in blocks:
        role = b.get("semantic_role") or "unknown" # API response might not include semantic_role if schema not updated in response model?
        # Wait, get_blocks in document.py returns a simplified dict.
        # I need to check if I updated get_blocks to return semantic_role.
        # I suspect I didn't update the response model or the route.
        # Let's check the route code I restored.
        pass

    # Print sample
    print("Sample blocks:")
    for b in blocks[:5]:
        print(b)

if __name__ == "__main__":
    verify_pipeline()
