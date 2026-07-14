"""
Constitution API endpoints for SCONIA.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
import logging

from app.database import get_async_db
from app.models.legal import ConstitutionalProvision
from app.schemas.legal import ConstitutionalProvisionResponse, ConstitutionalProvisionListResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=ConstitutionalProvisionListResponse)
async def get_constitutional_provisions(
    chapter: Optional[str] = Query(None, description="Filter by chapter"),
    section: Optional[str] = Query(None, description="Filter by section"),
    keyword: Optional[str] = Query(None, description="Search by keyword"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of provisions"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get constitutional provisions with optional filtering.
    """
    try:
        query_obj = select(ConstitutionalProvision).where(ConstitutionalProvision.is_active == True)
        
        # Apply filters
        if chapter:
            query_obj = query_obj.where(ConstitutionalProvision.chapter.ilike(f'%{chapter}%'))
        
        if section:
            query_obj = query_obj.where(ConstitutionalProvision.section == section)
        
        if keyword:
            query_obj = query_obj.where(
                or_(
                    ConstitutionalProvision.title.ilike(f'%{keyword}%'),
                    ConstitutionalProvision.content.ilike(f'%{keyword}%'),
                    ConstitutionalProvision.keywords.any(keyword.lower())
                )
            )
        
        # Order by chapter and section
        query_obj = query_obj.order_by(
            ConstitutionalProvision.chapter,
            ConstitutionalProvision.section
        ).limit(limit)
        
        result = await db.execute(query_obj)
        provisions = result.scalars().all()
        
        provisions_data = []
        chapters_included = set()
        
        for provision in provisions:
            provisions_data.append(ConstitutionalProvisionResponse(
                id=provision.id,
                chapter=provision.chapter,
                section=provision.section,
                subsection=provision.subsection,
                title=provision.title,
                content=provision.content,
                keywords=provision.keywords,
                related_sections=provision.related_sections
            ))
            
            if provision.chapter:
                chapters_included.add(provision.chapter)
        
        return ConstitutionalProvisionListResponse(
            provisions=provisions_data,
            total_count=len(provisions_data),
            chapters_included=list(chapters_included)
        )
        
    except Exception as e:
        logger.error(f"Error getting constitutional provisions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve constitutional provisions")


@router.get("/chapters")
async def get_chapters(db: AsyncSession = Depends(get_async_db)):
    """
    Get list of all constitutional chapters.
    """
    try:
        result = await db.execute(
            select(ConstitutionalProvision.chapter)
            .where(ConstitutionalProvision.is_active == True)
            .distinct()
            .order_by(ConstitutionalProvision.chapter)
        )
        chapters = [row[0] for row in result.fetchall() if row[0]]
        
        return {
            "chapters": chapters,
            "count": len(chapters)
        }
        
    except Exception as e:
        logger.error(f"Error getting chapters: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chapters")


@router.get("/section/{section_number}", response_model=ConstitutionalProvisionResponse)
async def get_section(
    section_number: str,
    subsection: Optional[str] = Query(None, description="Specific subsection"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get specific constitutional section.
    """
    try:
        query_obj = select(ConstitutionalProvision).where(
            and_(
                ConstitutionalProvision.section == section_number,
                ConstitutionalProvision.is_active == True
            )
        )
        
        if subsection:
            query_obj = query_obj.where(ConstitutionalProvision.subsection == subsection)
        
        result = await db.execute(query_obj)
        provision = result.scalar_one_or_none()
        
        if not provision:
            raise HTTPException(status_code=404, detail=f"Section {section_number} not found")
        
        return ConstitutionalProvisionResponse(
            id=provision.id,
            chapter=provision.chapter,
            section=provision.section,
            subsection=provision.subsection,
            title=provision.title,
            content=provision.content,
            keywords=provision.keywords,
            related_sections=provision.related_sections
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting section {section_number}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve section")


@router.get("/fundamental-rights")
async def get_fundamental_rights(db: AsyncSession = Depends(get_async_db)):
    """
    Get fundamental rights provisions (Chapter IV).
    """
    try:
        result = await db.execute(
            select(ConstitutionalProvision)
            .where(
                and_(
                    ConstitutionalProvision.chapter.ilike('%IV%'),
                    ConstitutionalProvision.is_active == True
                )
            )
            .order_by(ConstitutionalProvision.section)
        )
        provisions = result.scalars().all()
        
        rights_data = []
        for provision in provisions:
            rights_data.append({
                "section": provision.section,
                "title": provision.title,
                "content": provision.content[:200] + "..." if len(provision.content) > 200 else provision.content,
                "keywords": provision.keywords
            })
        
        return {
            "chapter": "Chapter IV - Fundamental Rights",
            "rights": rights_data,
            "count": len(rights_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting fundamental rights: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fundamental rights")


@router.get("/search")
async def search_constitution(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search constitutional provisions by text.
    """
    try:
        result = await db.execute(
            select(ConstitutionalProvision)
            .where(
                and_(
                    or_(
                        ConstitutionalProvision.title.ilike(f'%{query}%'),
                        ConstitutionalProvision.content.ilike(f'%{query}%')
                    ),
                    ConstitutionalProvision.is_active == True
                )
            )
            .limit(limit)
        )
        provisions = result.scalars().all()
        
        search_results = []
        for provision in provisions:
            # Highlight matching text (simple implementation)
            content_snippet = provision.content
            if len(content_snippet) > 300:
                # Find query in content and create snippet around it
                query_pos = content_snippet.lower().find(query.lower())
                if query_pos != -1:
                    start = max(0, query_pos - 100)
                    end = min(len(content_snippet), query_pos + 200)
                    content_snippet = "..." + content_snippet[start:end] + "..."
                else:
                    content_snippet = content_snippet[:300] + "..."
            
            search_results.append({
                "id": provision.id,
                "chapter": provision.chapter,
                "section": provision.section,
                "title": provision.title,
                "content_snippet": content_snippet,
                "keywords": provision.keywords
            })
        
        return {
            "query": query,
            "results": search_results,
            "count": len(search_results)
        }
        
    except Exception as e:
        logger.error(f"Error searching constitution: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/stats")
async def get_constitution_stats(db: AsyncSession = Depends(get_async_db)):
    """
    Get statistics about constitutional provisions.
    """
    try:
        # Get all provisions
        result = await db.execute(
            select(ConstitutionalProvision)
            .where(ConstitutionalProvision.is_active == True)
        )
        provisions = result.scalars().all()
        
        # Calculate statistics
        total_provisions = len(provisions)
        chapters = set(p.chapter for p in provisions if p.chapter)
        sections = set(p.section for p in provisions if p.section)
        
        # Count by chapter
        chapter_counts = {}
        for provision in provisions:
            if provision.chapter:
                chapter_counts[provision.chapter] = chapter_counts.get(provision.chapter, 0) + 1
        
        return {
            "total_provisions": total_provisions,
            "total_chapters": len(chapters),
            "total_sections": len(sections),
            "chapter_breakdown": chapter_counts,
            "fundamental_rights_count": chapter_counts.get("Chapter IV", 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting constitution stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")
