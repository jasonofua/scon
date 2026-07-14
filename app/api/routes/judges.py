"""
Judges API endpoints for SCONIA.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import logging

from app.database import get_async_db
from app.models.legal import Judge
from app.schemas.legal import JudgeResponse, JudgeListResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=JudgeListResponse)
async def get_judges(
    active_only: bool = Query(True, description="Return only active judges"),
    include_chief: bool = Query(True, description="Include Chief Justice"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of judges"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get list of Supreme Court judges.
    """
    try:
        query_obj = select(Judge)
        
        if active_only:
            query_obj = query_obj.where(Judge.is_active == True)
        
        # Order by Chief Justice first, then by appointment date
        query_obj = query_obj.order_by(
            Judge.is_chief_justice.desc(),
            Judge.appointment_date.desc()
        ).limit(limit)
        
        result = await db.execute(query_obj)
        judges = result.scalars().all()
        
        judges_data = []
        for judge in judges:
            judges_data.append({
                "id": judge.id,
                "full_name": judge.full_name,
                "title": judge.title,
                "appointment_date": judge.appointment_date.isoformat() if judge.appointment_date else None,
                "background_summary": judge.background_summary,
                "education": judge.education,
                "previous_positions": judge.previous_positions,
                "current_status": judge.current_status,
                "image_url": judge.image_url,
                "is_chief_justice": judge.is_chief_justice,
                "is_active": judge.is_active
            })
        
        return JudgeListResponse(
            judges=judges_data,
            total_count=len(judges_data),
            active_count=sum(1 for j in judges_data if j["is_active"]),
            chief_justice_included=any(j["is_chief_justice"] for j in judges_data)
        )
        
    except Exception as e:
        logger.error(f"Error getting judges: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve judges")


@router.get("/chief-justice", response_model=JudgeResponse)
async def get_chief_justice(db: AsyncSession = Depends(get_async_db)):
    """
    Get current Chief Justice of Nigeria.
    """
    try:
        result = await db.execute(
            select(Judge).where(
                and_(
                    Judge.is_chief_justice == True,
                    Judge.is_active == True
                )
            )
        )
        chief_justice = result.scalar_one_or_none()
        
        if not chief_justice:
            raise HTTPException(status_code=404, detail="Chief Justice not found")
        
        return JudgeResponse(
            id=chief_justice.id,
            full_name=chief_justice.full_name,
            title=chief_justice.title,
            appointment_date=chief_justice.appointment_date.isoformat() if chief_justice.appointment_date else None,
            background_summary=chief_justice.background_summary,
            education=chief_justice.education,
            previous_positions=chief_justice.previous_positions,
            current_status=chief_justice.current_status,
            image_url=chief_justice.image_url,
            is_chief_justice=chief_justice.is_chief_justice,
            is_active=chief_justice.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Chief Justice: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Chief Justice")


@router.get("/{judge_id}", response_model=JudgeResponse)
async def get_judge(
    judge_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get specific judge by ID.
    """
    try:
        result = await db.execute(
            select(Judge).where(Judge.id == judge_id)
        )
        judge = result.scalar_one_or_none()
        
        if not judge:
            raise HTTPException(status_code=404, detail="Judge not found")
        
        return JudgeResponse(
            id=judge.id,
            full_name=judge.full_name,
            title=judge.title,
            appointment_date=judge.appointment_date.isoformat() if judge.appointment_date else None,
            background_summary=judge.background_summary,
            education=judge.education,
            previous_positions=judge.previous_positions,
            current_status=judge.current_status,
            image_url=judge.image_url,
            is_chief_justice=judge.is_chief_justice,
            is_active=judge.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting judge {judge_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve judge")


@router.get("/search/{name}")
async def search_judges(
    name: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search judges by name.
    """
    try:
        result = await db.execute(
            select(Judge).where(
                and_(
                    Judge.full_name.ilike(f'%{name}%'),
                    Judge.is_active == True
                )
            ).limit(10)
        )
        judges = result.scalars().all()
        
        judges_data = []
        for judge in judges:
            judges_data.append({
                "id": judge.id,
                "full_name": judge.full_name,
                "title": judge.title,
                "is_chief_justice": judge.is_chief_justice,
                "appointment_date": judge.appointment_date.isoformat() if judge.appointment_date else None
            })
        
        return {
            "search_term": name,
            "results": judges_data,
            "count": len(judges_data)
        }
        
    except Exception as e:
        logger.error(f"Error searching judges: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/stats/summary")
async def get_judges_stats(db: AsyncSession = Depends(get_async_db)):
    """
    Get statistics about judges.
    """
    try:
        # Get all judges
        result = await db.execute(select(Judge))
        all_judges = result.scalars().all()
        
        # Calculate statistics
        total_judges = len(all_judges)
        active_judges = sum(1 for j in all_judges if j.is_active)
        inactive_judges = total_judges - active_judges
        
        # Get Chief Justice
        chief_justice = next((j for j in all_judges if j.is_chief_justice and j.is_active), None)
        
        return {
            "total_judges": total_judges,
            "active_judges": active_judges,
            "inactive_judges": inactive_judges,
            "chief_justice": {
                "name": chief_justice.full_name if chief_justice else None,
                "appointment_date": chief_justice.appointment_date.isoformat() if chief_justice and chief_justice.appointment_date else None
            } if chief_justice else None
        }
        
    except Exception as e:
        logger.error(f"Error getting judges stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")
