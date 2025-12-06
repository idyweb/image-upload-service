from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.routes.upload import router
from api.utils.config import settings
from api.utils.logger import logger
from api.db.database import engine
from api.db.base_model import Base

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

app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Upload Service...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    logger.info("Upload Service started successfully")

