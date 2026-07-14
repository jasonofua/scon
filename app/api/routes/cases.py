"""
Cases API endpoints for SCONIA.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import logging

from app.database import get_async_db
from app.models.legal import SupremeCourtCase, Judge

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_cases(
    year: Optional[int] = Query(None, description="Filter by judgment year"),
    status: Optional[str] = Query(None, description="Filter by case status"),
    search: Optional[str] = Query(None, description="Search in case titles"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of cases"),
    offset: int = Query(0, ge=0, description="Number of cases to skip"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get Supreme Court cases with optional filtering and pagination.
    """
    try:
        query_obj = select(SupremeCourtCase).where(SupremeCourtCase.is_active == True)
        
        if year:
            query_obj = query_obj.where(func.extract('year', SupremeCourtCase.judgment_date) == year)
        
        if status:
            query_obj = query_obj.where(SupremeCourtCase.case_status.ilike(f'%{status}%'))
        
        if search:
            query_obj = query_obj.where(
                or_(
                    SupremeCourtCase.case_title.ilike(f'%{search}%'),
                    SupremeCourtCase.case_number.ilike(f'%{search}%'),
                    SupremeCourtCase.case_summary.ilike(f'%{search}%')
                )
            )
        
        # Order by judgment date (most recent first)
        query_obj = query_obj.order_by(SupremeCourtCase.judgment_date.desc()).offset(offset).limit(limit)
        
        result = await db.execute(query_obj)
        cases = result.scalars().all()
        
        cases_data = []
        for case in cases:
            # Get judge names for the panel
            judge_names = []
            if case.judges_panel:
                judges_result = await db.execute(
                    select(Judge.full_name).where(Judge.id.in_(case.judges_panel))
                )
                judge_names = [row[0] for row in judges_result.fetchall()]
            
            cases_data.append({
                "id": case.id,
                "case_number": case.case_number,
                "case_title": case.case_title,
                "judgment_date": case.judgment_date.isoformat() if case.judgment_date else None,
                "judges_panel": judge_names,
                "case_summary": case.case_summary,
                "legal_principles": case.legal_principles,
                "case_status": case.case_status,
                "full_judgment_url": case.full_judgment_url
            })
        
        # Get total count for pagination
        count_result = await db.execute(
            select(func.count(SupremeCourtCase.id)).where(SupremeCourtCase.is_active == True)
        )
        total_count = count_result.scalar()
        
        return {
            "cases": cases_data,
            "count": len(cases_data),
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error getting cases: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cases")


@router.get("/{case_id}")
async def get_case(
    case_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get specific case by ID with full details.
    """
    try:
        result = await db.execute(
            select(SupremeCourtCase).where(
                and_(
                    SupremeCourtCase.id == case_id,
                    SupremeCourtCase.is_active == True
                )
            )
        )
        case = result.scalar_one_or_none()
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Get detailed judge information
        judges_info = []
        if case.judges_panel:
            judges_result = await db.execute(
                select(Judge).where(Judge.id.in_(case.judges_panel))
            )
            judges = judges_result.scalars().all()
            
            for judge in judges:
                judges_info.append({
                    "id": judge.id,
                    "full_name": judge.full_name,
                    "title": judge.title,
                    "is_chief_justice": judge.is_chief_justice
                })
        
        return {
            "id": case.id,
            "case_number": case.case_number,
            "case_title": case.case_title,
            "judgment_date": case.judgment_date.isoformat() if case.judgment_date else None,
            "judges_panel": judges_info,
            "case_summary": case.case_summary,
            "legal_principles": case.legal_principles,
            "constitutional_provisions_cited": case.constitutional_provisions_cited,
            "case_status": case.case_status,
            "full_judgment_url": case.full_judgment_url,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting case {case_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve case")


@router.get("/search/by-number")
async def search_by_case_number(
    case_number: str = Query(..., description="Case number to search"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search for a case by its case number.
    """
    try:
        result = await db.execute(
            select(SupremeCourtCase).where(
                and_(
                    SupremeCourtCase.case_number.ilike(f'%{case_number}%'),
                    SupremeCourtCase.is_active == True
                )
            )
        )
        case = result.scalar_one_or_none()
        
        if not case:
            return {
                "case_number": case_number,
                "found": False,
                "message": "Case not found"
            }
        
        return {
            "case_number": case_number,
            "found": True,
            "case": {
                "id": case.id,
                "case_number": case.case_number,
                "case_title": case.case_title,
                "judgment_date": case.judgment_date.isoformat() if case.judgment_date else None,
                "case_status": case.case_status
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching case by number: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/landmark/cases")
async def get_landmark_cases(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of cases"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get landmark Supreme Court cases.
    """
    try:
        # For now, we'll consider cases with legal principles as landmark cases
        # This can be enhanced with a specific landmark flag in the future
        result = await db.execute(
            select(SupremeCourtCase)
            .where(
                and_(
                    SupremeCourtCase.is_active == True,
                    SupremeCourtCase.legal_principles.isnot(None),
                    func.array_length(SupremeCourtCase.legal_principles, 1) > 0
                )
            )
            .order_by(SupremeCourtCase.judgment_date.desc())
            .limit(limit)
        )
        cases = result.scalars().all()
        
        landmark_cases = []
        for case in cases:
            landmark_cases.append({
                "id": case.id,
                "case_number": case.case_number,
                "case_title": case.case_title,
                "judgment_date": case.judgment_date.isoformat() if case.judgment_date else None,
                "legal_principles": case.legal_principles,
                "case_summary": case.case_summary[:300] + "..." if case.case_summary and len(case.case_summary) > 300 else case.case_summary
            })
        
        return {
            "landmark_cases": landmark_cases,
            "count": len(landmark_cases)
        }
        
    except Exception as e:
        logger.error(f"Error getting landmark cases: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve landmark cases")


@router.get("/recent/judgments")
async def get_recent_judgments(
    days: int = Query(365, ge=1, le=3650, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of cases"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get recent Supreme Court judgments.
    """
    try:
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        result = await db.execute(
            select(SupremeCourtCase)
            .where(
                and_(
                    SupremeCourtCase.is_active == True,
                    SupremeCourtCase.judgment_date >= cutoff_date
                )
            )
            .order_by(SupremeCourtCase.judgment_date.desc())
            .limit(limit)
        )
        cases = result.scalars().all()
        
        recent_cases = []
        for case in cases:
            recent_cases.append({
                "id": case.id,
                "case_number": case.case_number,
                "case_title": case.case_title,
                "judgment_date": case.judgment_date.isoformat(),
                "case_status": case.case_status,
                "case_summary": case.case_summary[:200] + "..." if case.case_summary and len(case.case_summary) > 200 else case.case_summary
            })
        
        return {
            "recent_judgments": recent_cases,
            "count": len(recent_cases),
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Error getting recent judgments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent judgments")


@router.get("/years/available")
async def get_available_years(db: AsyncSession = Depends(get_async_db)):
    """
    Get list of years with available judgments.
    """
    try:
        result = await db.execute(
            select(func.extract('year', SupremeCourtCase.judgment_date).label('year'))
            .where(
                and_(
                    SupremeCourtCase.is_active == True,
                    SupremeCourtCase.judgment_date.isnot(None)
                )
            )
            .distinct()
            .order_by('year')
        )
        years = [int(row[0]) for row in result.fetchall()]
        
        return {
            "available_years": years,
            "count": len(years),
            "earliest_year": min(years) if years else None,
            "latest_year": max(years) if years else None
        }
        
    except Exception as e:
        logger.error(f"Error getting available years: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve available years")


@router.get("/stats/summary")
async def get_cases_stats(db: AsyncSession = Depends(get_async_db)):
    """
    Get statistics about Supreme Court cases.
    """
    try:
        # Get all active cases
        result = await db.execute(
            select(SupremeCourtCase).where(SupremeCourtCase.is_active == True)
        )
        cases = result.scalars().all()
        
        # Calculate statistics
        total_cases = len(cases)
        cases_with_judgments = sum(1 for case in cases if case.judgment_date)
        cases_with_principles = sum(1 for case in cases if case.legal_principles)
        
        # Status breakdown
        status_counts = {}
        for case in cases:
            status = case.case_status or "Unknown"
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Year breakdown (last 5 years)
        current_year = datetime.now().year
        year_counts = {}
        for case in cases:
            if case.judgment_date:
                year = case.judgment_date.year
                if year >= current_year - 5:
                    year_counts[year] = year_counts.get(year, 0) + 1
        
        return {
            "total_cases": total_cases,
            "cases_with_judgments": cases_with_judgments,
            "landmark_cases": cases_with_principles,
            "status_breakdown": status_counts,
            "recent_years_breakdown": year_counts
        }
        
    except Exception as e:
        logger.error(f"Error getting cases stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")
