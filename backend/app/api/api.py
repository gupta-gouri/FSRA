from fastapi import APIRouter
from app.api.endpoints import clients, projects, files, pipeline, verification, analytics, reports

api_router = APIRouter()

@api_router.get("/health", tags = ["Health"])
async def health_check():
    return {"status": "ok", "service": "FSRA API"}

api_router.include_router(clients.router, prefix = "/clients", tags = ["Clients"])
api_router.include_router(projects.router, prefix = "/projects", tags = ["Projects"])
api_router.include_router(files.router, prefix = "/files", tags = ["Files"])
api_router.include_router(pipeline.router, prefix = "/AuditService", tags = ["Audit Service"])
api_router.include_router(verification.router, prefix = "/verification", tags = ["Verification"])
api_router.include_router(analytics.router, prefix = "/analytics", tags = ["Analytics & Forensics"])
api_router.include_router(reports.router, prefix = "/reports", tags = ["Reports & Deliverables"])