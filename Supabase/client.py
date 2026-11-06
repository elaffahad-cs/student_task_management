"""
Supabase client initialization.
Fails fast with a clear error if env vars are missing.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_url = os.environ.get("SUPABASE_URL")
_key = os.environ.get("SUPABASE_KEY")

if not _url or not _url.startswith("https://"):
    raise RuntimeError(
        f"SUPABASE_URL missing or invalid. Got: {_url!r}. Check your .env file."
    )
if not _key:
    raise RuntimeError("SUPABASE_KEY missing. Check your .env file.")

supabase: Client = create_client(_url, _key)