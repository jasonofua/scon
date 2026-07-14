"""
API routes for SCONIA application.
"""
from fastapi import APIRouter
from app.api.routes import (
    chat, search, judges, constitution, admin, fees, procedures, cases,
    websocket, monitoring, documents
)

api_router = APIRouter()

# Include route modules
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(judges.router, prefix="/judges", tags=["judges"])
api_router.include_router(constitution.router, prefix="/constitution", tags=["constitution"])
api_router.include_router(fees.router, prefix="/fees", tags=["fees"])
api_router.include_router(procedures.router, prefix="/procedures", tags=["procedures"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(websocket.router, prefix="/websocket", tags=["websocket"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
