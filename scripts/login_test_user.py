
import os
import sys
import httpx
from dotenv import load_dotenv

# Load env
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: Missing env vars")
    sys.exit(1)

auth_url = f"{url}/auth/v1/token?grant_type=password"
headers = {
    "apikey": key,
    "Content-Type": "application/json"
}
data = {
    "email": "test1@example.com",
    "password": "12345678"
}

try:
    response = httpx.post(auth_url, headers=headers, json=data)
    if response.status_code == 200:
        print(response.json()["access_token"])
    else:
        print(f"Error: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
