
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load env
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: Missing env vars")
    sys.exit(1)

supabase = create_client(url, key)

# Try get existing habit
response = supabase.table("habits").select("id").limit(1).execute()

if response.data:
    print(response.data[0]["id"])
    sys.exit(0)

# Create new habit
habit_data = {
    "name": "Daily Parsing",
    "description": "Read something every day",
    "icon": "book",
    "category": "learning",
    "is_system": True
}

response = supabase.table("habits").insert(habit_data).execute()

if response.data:
    print(response.data[0]["id"])
else:
    print("Error: Failed to create habit")
    sys.exit(1)
