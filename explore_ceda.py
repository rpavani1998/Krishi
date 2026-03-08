import requests
import re

URL = "https://api.ceda.ashoka.edu.in/documentation/"

def find_swagger_json():
    try:
        resp = requests.get(URL)
        print(f"Status: {resp.status_code}")
        content = resp.text
        # Look for .json or swagger config
        json_links = re.findall(r'url\s*:\s*["\']([^"\']+\.json)["\']', content)
        if json_links:
            print(f"Found JSON links: {json_links}")
        else:
            print("No JSON links found in HTML.")
            print(content[:500]) # Print first 500 chars to debug
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_swagger_json()
