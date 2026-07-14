"""
Fees API endpoints for SCONIA.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
import logging
from decimal import Decimal

from app.database import get_async_db
from app.models.legal import FeeSchedule
from app.schemas.legal import FeeScheduleResponse, FeeCalculationRequest, FeeCalculationResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[FeeScheduleResponse])
async def get_fee_schedules(
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    case_category: Optional[str] = Query(None, description="Filter by case category"),
    active_only: bool = Query(True, description="Return only active fees"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get court fee schedules with optional filtering.
    """
    try:
        query_obj = select(FeeSchedule)
        
        if active_only:
            query_obj = query_obj.where(FeeSchedule.is_active == True)
        
        if service_type:
            query_obj = query_obj.where(FeeSchedule.service_type.ilike(f'%{service_type}%'))
        
        if case_category:
            query_obj = query_obj.where(FeeSchedule.case_category.ilike(f'%{case_category}%'))
        
        query_obj = query_obj.order_by(FeeSchedule.service_type, FeeSchedule.case_category)
        
        result = await db.execute(query_obj)
        fees = result.scalars().all()
        
        return [
            FeeScheduleResponse(
                id=fee.id,
                service_type=fee.service_type,
                case_category=fee.case_category,
                fee_amount=float(fee.fee_amount) if fee.fee_amount else None,
                payment_methods=fee.payment_methods,
                effective_date=fee.effective_date.isoformat() if fee.effective_date else None,
                description=fee.description,
                is_active=fee.is_active
            )
            for fee in fees
        ]
        
    except Exception as e:
        logger.error(f"Error getting fee schedules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fee schedules")


@router.get("/service-types")
async def get_service_types(db: AsyncSession = Depends(get_async_db)):
    """
    Get list of available service types.
    """
    try:
        result = await db.execute(
            select(FeeSchedule.service_type)
            .where(FeeSchedule.is_active == True)
            .distinct()
            .order_by(FeeSchedule.service_type)
        )
        service_types = [row[0] for row in result.fetchall()]
        
        return {
            "service_types": service_types,
            "count": len(service_types)
        }
        
    except Exception as e:
        logger.error(f"Error getting service types: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve service types")


@router.get("/case-categories")
async def get_case_categories(db: AsyncSession = Depends(get_async_db)):
    """
    Get list of available case categories.
    """
    try:
        result = await db.execute(
            select(FeeSchedule.case_category)
            .where(
                and_(
                    FeeSchedule.is_active == True,
                    FeeSchedule.case_category.isnot(None)
                )
            )
            .distinct()
            .order_by(FeeSchedule.case_category)
        )
        categories = [row[0] for row in result.fetchall()]
        
        return {
            "case_categories": categories,
            "count": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting case categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve case categories")


@router.post("/calculate", response_model=FeeCalculationResponse)
async def calculate_fees(
    request: FeeCalculationRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Calculate total fees for a service request.
    """
    try:
        # Get base fee
        query_obj = select(FeeSchedule).where(
            and_(
                FeeSchedule.service_type.ilike(f'%{request.service_type}%'),
                FeeSchedule.is_active == True
            )
        )
        
        if request.case_category:
            query_obj = query_obj.where(
                FeeSchedule.case_category.ilike(f'%{request.case_category}%')
            )
        
        result = await db.execute(query_obj)
        base_fee_record = result.scalar_one_or_none()
        
        if not base_fee_record:
            raise HTTPException(
                status_code=404, 
                detail=f"Fee not found for service type: {request.service_type}"
            )
        
        base_fee = float(base_fee_record.fee_amount or 0)
        additional_fees = []
        total_additional = 0.0
        
        # Calculate additional service fees
        if request.additional_services:
            for service in request.additional_services:
                result = await db.execute(
                    select(FeeSchedule).where(
                        and_(
                            FeeSchedule.service_type.ilike(f'%{service}%'),
                            FeeSchedule.is_active == True
                        )
                    )
                )
                additional_fee_record = result.scalar_one_or_none()
                
                if additional_fee_record:
                    fee_amount = float(additional_fee_record.fee_amount or 0)
                    additional_fees.append({
                        "service": service,
                        "amount": fee_amount,
                        "description": additional_fee_record.description
                    })
                    total_additional += fee_amount
        
        total_fee = base_fee + total_additional
        
        # Create breakdown
        breakdown = [
            {
                "item": f"{base_fee_record.service_type} - {base_fee_record.case_category or 'General'}",
                "amount": base_fee,
                "type": "base_fee"
            }
        ]
        
        for additional in additional_fees:
            breakdown.append({
                "item": additional["service"],
                "amount": additional["amount"],
                "type": "additional_service"
            })
        
        return FeeCalculationResponse(
            service_type=request.service_type,
            case_category=request.case_category,
            base_fee=base_fee,
            additional_fees=additional_fees,
            total_fee=total_fee,
            payment_methods=base_fee_record.payment_methods or [],
            breakdown=breakdown
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating fees: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate fees")


@router.get("/payment-methods")
async def get_payment_methods(db: AsyncSession = Depends(get_async_db)):
    """
    Get list of available payment methods.
    """
    try:
        result = await db.execute(
            select(FeeSchedule.payment_methods)
            .where(
                and_(
                    FeeSchedule.is_active == True,
                    FeeSchedule.payment_methods.isnot(None)
                )
            )
        )
        
        all_methods = set()
        for row in result.fetchall():
            if row[0]:  # payment_methods is not None
                all_methods.update(row[0])
        
        return {
            "payment_methods": sorted(list(all_methods)),
            "count": len(all_methods)
        }
        
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment methods")


@router.get("/search")
async def search_fees(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search fee schedules by service type or description.
    """
    try:
        result = await db.execute(
            select(FeeSchedule)
            .where(
                and_(
                    FeeSchedule.is_active == True,
                    FeeSchedule.service_type.ilike(f'%{query}%') |
                    FeeSchedule.description.ilike(f'%{query}%') |
                    FeeSchedule.case_category.ilike(f'%{query}%')
                )
            )
            .limit(limit)
        )
        fees = result.scalars().all()
        
        search_results = []
        for fee in fees:
            search_results.append({
                "id": fee.id,
                "service_type": fee.service_type,
                "case_category": fee.case_category,
                "fee_amount": float(fee.fee_amount) if fee.fee_amount else None,
                "description": fee.description,
                "payment_methods": fee.payment_methods
            })
        
        return {
            "query": query,
            "results": search_results,
            "count": len(search_results)
        }
        
    except Exception as e:
        logger.error(f"Error searching fees: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/stats")
async def get_fee_stats(db: AsyncSession = Depends(get_async_db)):
    """
    Get statistics about fee schedules.
    """
    try:
        # Get all active fees
        result = await db.execute(
            select(FeeSchedule).where(FeeSchedule.is_active == True)
        )
        fees = result.scalars().all()
        
        # Calculate statistics
        total_fees = len(fees)
        service_types = set(fee.service_type for fee in fees)
        case_categories = set(fee.case_category for fee in fees if fee.case_category)
        
        # Fee ranges
        amounts = [float(fee.fee_amount) for fee in fees if fee.fee_amount]
        min_fee = min(amounts) if amounts else 0
        max_fee = max(amounts) if amounts else 0
        avg_fee = sum(amounts) / len(amounts) if amounts else 0
        
        return {
            "total_fee_schedules": total_fees,
            "service_types_count": len(service_types),
            "case_categories_count": len(case_categories),
            "fee_range": {
                "minimum": min_fee,
                "maximum": max_fee,
                "average": round(avg_fee, 2)
            },
            "service_types": list(service_types),
            "case_categories": list(case_categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting fee stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")
