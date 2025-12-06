from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.routes import router
from api.utils.config import settings
from api.utils.logger import logger
from api.db.database import init_db



app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION
)


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting up Upload Service...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    logger.info("Upload Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Upload Service...")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}