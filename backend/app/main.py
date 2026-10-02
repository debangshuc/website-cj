from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Returns service metadata and API version.",
)
def read_root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns the health status of the API service.",
)
def health_check():
    return {
        "status": "ok",
    }


# Include /api routes
app.include_router(api_router, prefix=settings.API_V1_STR)
