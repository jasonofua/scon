"""
Procedures API endpoints for SCONIA.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional, Dict, Any
import logging

from app.database import get_async_db
from app.models.legal import Procedure, RequiredForm

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_procedures(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in procedure names"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of procedures"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get court procedures with optional filtering.
    """
    try:
        query_obj = select(Procedure).where(Procedure.is_active == True)
        
        if category:
            query_obj = query_obj.where(Procedure.category.ilike(f'%{category}%'))
        
        if search:
            query_obj = query_obj.where(
                or_(
                    Procedure.procedure_name.ilike(f'%{search}%'),
                    Procedure.category.ilike(f'%{search}%')
                )
            )
        
        query_obj = query_obj.order_by(Procedure.category, Procedure.procedure_name).limit(limit)
        
        result = await db.execute(query_obj)
        procedures = result.scalars().all()
        
        procedures_data = []
        for procedure in procedures:
            procedures_data.append({
                "id": procedure.id,
                "procedure_name": procedure.procedure_name,
                "category": procedure.category,
                "step_by_step_guide": procedure.step_by_step_guide,
                "required_documents": procedure.required_documents,
                "estimated_timeline": procedure.estimated_timeline,
                "associated_fees": procedure.associated_fees,
                "contact_departments": procedure.contact_departments
            })
        
        return {
            "procedures": procedures_data,
            "count": len(procedures_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting procedures: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve procedures")


@router.get("/categories")
async def get_procedure_categories(db: AsyncSession = Depends(get_async_db)):
    """
    Get list of procedure categories.
    """
    try:
        result = await db.execute(
            select(Procedure.category)
            .where(
                and_(
                    Procedure.is_active == True,
                    Procedure.category.isnot(None)
                )
            )
            .distinct()
            .order_by(Procedure.category)
        )
        categories = [row[0] for row in result.fetchall()]
        
        return {
            "categories": categories,
            "count": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting procedure categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")


@router.get("/{procedure_id}")
async def get_procedure(
    procedure_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get specific procedure by ID with detailed information.
    """
    try:
        result = await db.execute(
            select(Procedure).where(
                and_(
                    Procedure.id == procedure_id,
                    Procedure.is_active == True
                )
            )
        )
        procedure = result.scalar_one_or_none()
        
        if not procedure:
            raise HTTPException(status_code=404, detail="Procedure not found")
        
        # Get associated forms if any
        forms = []
        if procedure.required_documents:
            for doc_name in procedure.required_documents:
                form_result = await db.execute(
                    select(RequiredForm).where(
                        and_(
                            RequiredForm.form_name.ilike(f'%{doc_name}%'),
                            RequiredForm.is_active == True
                        )
                    )
                )
                form = form_result.scalar_one_or_none()
                if form:
                    forms.append({
                        "id": form.id,
                        "form_name": form.form_name,
                        "form_type": form.form_type,
                        "description": form.description,
                        "file_url": form.file_url,
                        "completion_guide": form.completion_guide
                    })
        
        return {
            "id": procedure.id,
            "procedure_name": procedure.procedure_name,
            "category": procedure.category,
            "step_by_step_guide": procedure.step_by_step_guide,
            "required_documents": procedure.required_documents,
            "estimated_timeline": procedure.estimated_timeline,
            "associated_fees": procedure.associated_fees,
            "contact_departments": procedure.contact_departments,
            "related_forms": forms
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting procedure {procedure_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve procedure")


@router.get("/search/by-name")
async def search_procedures_by_name(
    name: str = Query(..., description="Procedure name to search"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search procedures by name.
    """
    try:
        result = await db.execute(
            select(Procedure)
            .where(
                and_(
                    Procedure.procedure_name.ilike(f'%{name}%'),
                    Procedure.is_active == True
                )
            )
            .limit(limit)
        )
        procedures = result.scalars().all()
        
        search_results = []
        for procedure in procedures:
            search_results.append({
                "id": procedure.id,
                "procedure_name": procedure.procedure_name,
                "category": procedure.category,
                "estimated_timeline": procedure.estimated_timeline,
                "required_documents_count": len(procedure.required_documents) if procedure.required_documents else 0
            })
        
        return {
            "search_term": name,
            "results": search_results,
            "count": len(search_results)
        }
        
    except Exception as e:
        logger.error(f"Error searching procedures: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/guide/{procedure_name}")
async def get_procedure_guide(
    procedure_name: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get step-by-step guide for a specific procedure.
    """
    try:
        result = await db.execute(
            select(Procedure).where(
                and_(
                    Procedure.procedure_name.ilike(f'%{procedure_name}%'),
                    Procedure.is_active == True
                )
            )
        )
        procedure = result.scalar_one_or_none()
        
        if not procedure:
            raise HTTPException(status_code=404, detail=f"Procedure '{procedure_name}' not found")
        
        # Format the guide for better readability
        guide = procedure.step_by_step_guide or {}
        
        if isinstance(guide, dict):
            formatted_steps = []
            for key, value in guide.items():
                if key.startswith('step'):
                    step_number = key.replace('step_', '').replace('step', '')
                    formatted_steps.append({
                        "step_number": step_number,
                        "description": value,
                        "order": int(step_number) if step_number.isdigit() else 999
                    })
            
            # Sort steps by order
            formatted_steps.sort(key=lambda x: x["order"])
        else:
            formatted_steps = [{"step_number": "1", "description": str(guide), "order": 1}]
        
        return {
            "procedure_name": procedure.procedure_name,
            "category": procedure.category,
            "steps": formatted_steps,
            "required_documents": procedure.required_documents,
            "estimated_timeline": procedure.estimated_timeline,
            "contact_departments": procedure.contact_departments
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting procedure guide: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve procedure guide")


@router.get("/forms/")
async def get_required_forms(
    form_type: Optional[str] = Query(None, description="Filter by form type"),
    search: Optional[str] = Query(None, description="Search in form names"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of forms"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get required forms with optional filtering.
    """
    try:
        query_obj = select(RequiredForm).where(RequiredForm.is_active == True)
        
        if form_type:
            query_obj = query_obj.where(RequiredForm.form_type.ilike(f'%{form_type}%'))
        
        if search:
            query_obj = query_obj.where(
                or_(
                    RequiredForm.form_name.ilike(f'%{search}%'),
                    RequiredForm.description.ilike(f'%{search}%')
                )
            )
        
        query_obj = query_obj.order_by(RequiredForm.form_type, RequiredForm.form_name).limit(limit)
        
        result = await db.execute(query_obj)
        forms = result.scalars().all()
        
        forms_data = []
        for form in forms:
            forms_data.append({
                "id": form.id,
                "form_name": form.form_name,
                "form_type": form.form_type,
                "description": form.description,
                "requirements": form.requirements,
                "file_url": form.file_url,
                "completion_guide": form.completion_guide,
                "related_procedures": form.related_procedures
            })
        
        return {
            "forms": forms_data,
            "count": len(forms_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting forms: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve forms")


@router.get("/forms/{form_id}")
async def get_form(
    form_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get specific form by ID with detailed information.
    """
    try:
        result = await db.execute(
            select(RequiredForm).where(
                and_(
                    RequiredForm.id == form_id,
                    RequiredForm.is_active == True
                )
            )
        )
        form = result.scalar_one_or_none()
        
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        return {
            "id": form.id,
            "form_name": form.form_name,
            "form_type": form.form_type,
            "description": form.description,
            "requirements": form.requirements,
            "file_url": form.file_url,
            "completion_guide": form.completion_guide,
            "related_procedures": form.related_procedures
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting form {form_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve form")


@router.get("/stats/summary")
async def get_procedures_stats(db: AsyncSession = Depends(get_async_db)):
    """
    Get statistics about procedures and forms.
    """
    try:
        # Get procedures stats
        procedures_result = await db.execute(
            select(Procedure).where(Procedure.is_active == True)
        )
        procedures = procedures_result.scalars().all()
        
        # Get forms stats
        forms_result = await db.execute(
            select(RequiredForm).where(RequiredForm.is_active == True)
        )
        forms = forms_result.scalars().all()
        
        # Calculate statistics
        procedure_categories = set(p.category for p in procedures if p.category)
        form_types = set(f.form_type for f in forms if f.form_type)
        
        return {
            "procedures": {
                "total": len(procedures),
                "categories": list(procedure_categories),
                "categories_count": len(procedure_categories)
            },
            "forms": {
                "total": len(forms),
                "types": list(form_types),
                "types_count": len(form_types)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting procedures stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")
