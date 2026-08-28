from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router

app = FastAPI(
    title = settings.PROJECT_NAME,
    openapi_url = f"{settings.API_PREFIX}/openapi.json",
    docs_url = "/docs",
    redoc_url = "/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# Register API Router
app.include_router(api_router, prefix = settings.API_PREFIX)

@app.get("/")
async def root():
    return {"message": "FSRA API is running. Navigate to /docs for Swagger UI."}