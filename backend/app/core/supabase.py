from supabase import create_client, Client
from backend.app.core.config import settings

def get_supabase_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE.KEY)

supabase: Client = get_supabase_client()