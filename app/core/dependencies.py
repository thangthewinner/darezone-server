from supabase import Client, create_client, ClientOptions
from app.core.config import settings
from functools import lru_cache


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get Supabase client singleton
    Uses service role key for backend operations with RLS bypass
    """
    options = ClientOptions(
        schema="public",
        auto_refresh_token=False,
        persist_session=False,
    )
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
        options=options
    )
