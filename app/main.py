import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import router as api_router
from app.middleware.logging import RequestLoggingMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    description="DareZone habit-building social application API",
    redirect_slashes=False,  # Prevent 307 redirects that lose JWT token
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Request Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# Include API routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring
    Returns service status and version info
    """
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "app_name": settings.APP_NAME,
    }


@app.get("/debug/env-check")
async def env_check():
    """
    Debug endpoint to check if environment variables are set
    WARNING: Remove this in production!
    """
    return {
        "supabase_url_set": bool(settings.SUPABASE_URL),
        "supabase_url_preview": settings.SUPABASE_URL[:40] + "..." if settings.SUPABASE_URL else "NOT_SET",
        "supabase_service_key_set": bool(settings.SUPABASE_SERVICE_ROLE_KEY),
        "supabase_anon_key_set": bool(settings.SUPABASE_ANON_KEY),
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "app_name": settings.APP_NAME,
    }


@app.get("/")
async def root():
    """
    Root endpoint - Welcome message and links
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api": "/api/v1",
    }


@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown"""
    logger.info(f"Shutting down {settings.APP_NAME}")
