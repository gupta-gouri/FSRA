from fastapi import APIRouter
from app.api.endpoints import clients, projects

api_router = APIRouter()

@api_router.get("/health", tags = ["Health"])
async def health_check():
    return {"status": "ok", "service": "FSRA API"}

api_router.include_router(clients.router, prefix = "/clients", tags = ["Clients"])
api_router.include_router(projects.router, prefix = "/projects", tags = ["Projects"])
