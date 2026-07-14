"""
Admin API endpoints for SCONIA.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import logging

from app.database import get_async_db
from app.services.auth import get_current_superuser
from app.services.document_processor import document_processor
from app.services.vector_db import vector_db_service
from app.models.admin import User
from app.models.embeddings import ProcessedDocument, SearchQuery, UserSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    process_immediately: bool = Form(True),
    use_gemini: bool = Form(True),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Upload and optionally process a legal document.
    """
    from app.services.file_upload import file_upload_service

    try:
        # Validate and save upload
        upload_result = await file_upload_service.save_upload(
            file=file,
            document_type=document_type,
            user_id=current_user.id
        )

        if not upload_result["success"]:
            raise HTTPException(status_code=400, detail="File upload failed")

        response = {
            "message": "Document uploaded successfully",
            "upload_info": upload_result
        }

        # Process immediately if requested
        if process_immediately:
            try:
                document_id = await file_upload_service.process_uploaded_file(
                    file_path=upload_result["file_path"],
                    document_type=document_type,
                    db=db,
                    user_id=current_user.id,
                    use_gemini=use_gemini
                )

                response.update({
                    "document_id": document_id,
                    "processing_status": "completed",
                    "message": "Document uploaded and processed successfully"
                })

            except Exception as processing_error:
                logger.error(f"Error processing document: {processing_error}")
                response.update({
                    "processing_status": "failed",
                    "processing_error": str(processing_error),
                    "message": "Document uploaded but processing failed"
                })
        else:
            response["processing_status"] = "pending"

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.post("/documents/validate")
async def validate_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: User = Depends(get_current_superuser)
):
    """
    Validate a document without uploading it.
    """
    from app.services.file_upload import file_upload_service

    try:
        validation_result = await file_upload_service.validate_upload(
            file=file,
            document_type=document_type,
            user_id=current_user.id
        )

        return {
            "validation_result": validation_result,
            "file_info": validation_result.get("file_info", {})
        }

    except Exception as e:
        logger.error(f"Error validating document: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate document")


@router.get("/documents/upload-status/{filename}")
async def get_upload_status(
    filename: str,
    current_user: User = Depends(get_current_superuser)
):
    """
    Get status of an uploaded file.
    """
    from app.services.file_upload import file_upload_service

    try:
        status = await file_upload_service.get_upload_status(filename)
        return status

    except Exception as e:
        logger.error(f"Error getting upload status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get upload status")


@router.get("/documents")
async def get_processed_documents(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get list of processed documents.
    """
    try:
        documents = await document_processor.get_processed_documents(db)
        return {
            "documents": documents,
            "count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a processed document and its embeddings.
    """
    try:
        # Delete from vector database
        success = await vector_db_service.delete_document_embeddings(document_id)
        
        if success:
            # Update database record
            result = await db.execute(
                select(ProcessedDocument).where(ProcessedDocument.document_id == document_id)
            )
            doc = result.scalar_one_or_none()
            
            if doc:
                doc.is_active = False
                await db.commit()
            
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.get("/analytics/queries")
async def get_query_analytics(
    days: int = 7,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get query analytics for the specified number of days.
    """
    try:
        # Get query statistics
        result = await db.execute(
            select(
                func.count(SearchQuery.id).label('total_queries'),
                func.avg(SearchQuery.response_time).label('avg_response_time'),
                func.count(SearchQuery.satisfaction_rating).label('rated_queries'),
                func.avg(SearchQuery.satisfaction_rating).label('avg_rating')
            ).where(
                SearchQuery.created_at >= func.now() - func.interval(f'{days} days')
            )
        )
        stats = result.first()
        
        # Get query types breakdown
        result = await db.execute(
            select(
                SearchQuery.intent_classification,
                func.count(SearchQuery.id).label('count')
            ).where(
                SearchQuery.created_at >= func.now() - func.interval(f'{days} days')
            ).group_by(SearchQuery.intent_classification)
        )
        query_types = {row.intent_classification: row.count for row in result.fetchall()}
        
        return {
            "period_days": days,
            "total_queries": stats.total_queries or 0,
            "average_response_time": float(stats.avg_response_time or 0),
            "rated_queries": stats.rated_queries or 0,
            "average_rating": float(stats.avg_rating or 0),
            "query_types_breakdown": query_types
        }
        
    except Exception as e:
        logger.error(f"Error getting query analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.get("/analytics/sessions")
async def get_session_analytics(
    days: int = 7,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get session analytics for the specified number of days.
    """
    try:
        # Get session statistics
        result = await db.execute(
            select(
                func.count(UserSession.id).label('total_sessions'),
                func.avg(UserSession.query_count).label('avg_queries_per_session'),
                func.sum(UserSession.query_count).label('total_queries')
            ).where(
                UserSession.created_at >= func.now() - func.interval(f'{days} days')
            )
        )
        stats = result.first()
        
        # Get device type breakdown
        result = await db.execute(
            select(
                UserSession.device_type,
                func.count(UserSession.id).label('count')
            ).where(
                UserSession.created_at >= func.now() - func.interval(f'{days} days')
            ).group_by(UserSession.device_type)
        )
        device_types = {row.device_type: row.count for row in result.fetchall()}
        
        return {
            "period_days": days,
            "total_sessions": stats.total_sessions or 0,
            "total_queries": stats.total_queries or 0,
            "average_queries_per_session": float(stats.avg_queries_per_session or 0),
            "device_types_breakdown": device_types
        }
        
    except Exception as e:
        logger.error(f"Error getting session analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.get("/system/status")
async def get_system_status(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get system status and health information.
    """
    try:
        # Get vector database status
        vector_info = await vector_db_service.get_collection_info()
        
        # Get database counts
        result = await db.execute(select(func.count(ProcessedDocument.id)))
        total_documents = result.scalar()
        
        result = await db.execute(
            select(func.count(ProcessedDocument.id))
            .where(ProcessedDocument.processing_status == 'completed')
        )
        processed_documents = result.scalar()
        
        result = await db.execute(select(func.count(UserSession.id)))
        total_sessions = result.scalar()
        
        return {
            "status": "operational",
            "vector_database": vector_info,
            "documents": {
                "total": total_documents,
                "processed": processed_documents,
                "processing_rate": (processed_documents / total_documents * 100) if total_documents > 0 else 0
            },
            "sessions": {
                "total": total_sessions
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.post("/vector-db/initialize")
async def initialize_vector_database(
    current_user: User = Depends(get_current_superuser)
):
    """
    Initialize vector database collections.
    """
    try:
        await vector_db_service.initialize_collections()
        return {"message": "Vector database initialized successfully"}
        
    except Exception as e:
        logger.error(f"Error initializing vector database: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize vector database")
