from supabase import Client, create_client
from app.core.config import settings
from functools import lru_cache


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get Supabase client singleton
    Uses service role key for backend operations
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
