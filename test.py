# test_supabase.py
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()  # reads .env

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BUCKET = os.getenv("BUCKET_NAME", "images")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    # Try to list objects in the bucket (safe read)
    res = supabase.storage.from_(BUCKET).list()
    print("Storage list response:", res)
except Exception as e:
    print("Connection test failed:", e)
