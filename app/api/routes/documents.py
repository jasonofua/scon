"""
Documents API endpoints for SCONIA - serves real uploaded document data.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
import logging
import json
import re
from datetime import datetime

from app.database import get_async_db
from app.models.embeddings import ProcessedDocument
from app.services.vector_db import vector_db_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/debug")
async def debug_documents(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Debug endpoint to see raw document content.
    """
    try:
        # Get a sample constitution document
        result = await db.execute(
            select(ProcessedDocument).where(
                and_(
                    ProcessedDocument.document_type == 'constitution',
                    ProcessedDocument.processing_status == 'completed',
                    ProcessedDocument.is_active == True
                )
            ).limit(1)
        )
        document = result.scalars().first()

        if not document:
            return {"message": "No constitution documents found"}

        # Get sample chunks from vector database
        try:
            search_results = await vector_db_service.search_by_document_id(
                document.document_id, limit=3
            )
            search_error = None
        except Exception as e:
            search_results = []
            search_error = str(e)

        # Also test direct Qdrant query
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            scroll_result = vector_db_service.client.scroll(
                collection_name=vector_db_service.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document.document_id)
                        )
                    ]
                ),
                limit=3,
                with_payload=True
            )

            direct_results = []
            for point in scroll_result[0]:
                payload = point.payload
                direct_results.append({
                    "id": point.id,
                    "text": payload.get("text", "")[:200] + "...",
                    "document_id": payload.get("document_id"),
                    "chunk_index": payload.get("chunk_index", 0)
                })
            direct_error = None
        except Exception as direct_error:
            direct_results = []
            direct_error = str(direct_error)

        return {
            "document_info": {
                "id": document.document_id,
                "name": document.document_name,
                "type": document.document_type,
                "status": document.processing_status
            },
            "search_results": search_results,
            "search_error": search_error,
            "direct_results": direct_results,
            "direct_error": direct_error,
            "sample_chunks": [
                {
                    "chunk_index": result.get("chunk_index", 0),
                    "text_preview": result.get("text", "")[:500] + "..." if len(result.get("text", "")) > 500 else result.get("text", "")
                }
                for result in search_results[:3]
            ]
        }

    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return {"error": str(e)}


@router.post("/sync")
async def sync_databases(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Synchronize document IDs between PostgreSQL and Qdrant databases.
    """
    try:
        from datetime import datetime

        # Get Qdrant documents
        response = vector_db_service.client.scroll(
            collection_name=vector_db_service.collection_name,
            limit=1000,
            with_payload=True
        )

        qdrant_docs = {}
        for point in response[0]:
            payload = point.payload
            doc_id = payload.get('document_id')
            if doc_id and doc_id not in qdrant_docs:
                qdrant_docs[doc_id] = {
                    'document_type': payload.get('document_type', 'unknown'),
                    'file_path': payload.get('file_path', ''),
                    'chunk_count': 0
                }
            if doc_id:
                qdrant_docs[doc_id]['chunk_count'] += 1

        # Get PostgreSQL documents
        result = await db.execute(select(ProcessedDocument.document_id))
        postgres_ids = {row[0] for row in result.fetchall()}

        # Find missing documents
        missing_in_postgres = set(qdrant_docs.keys()) - postgres_ids
        orphaned_in_postgres = postgres_ids - set(qdrant_docs.keys())

        # Create missing PostgreSQL records
        missing_docs = []
        for doc_id in missing_in_postgres:
            info = qdrant_docs[doc_id]
            doc_name = 'constitution.txt' if 'constitution' in doc_id else f'{doc_id}.txt'

            processed_doc = ProcessedDocument(
                document_id=doc_id,
                document_name=doc_name,
                document_type=info['document_type'],
                file_path=info['file_path'] or f'/app/{doc_name}',
                file_size=1000,
                processing_status='completed',
                chunk_count=info['chunk_count'],
                processed_at=datetime.utcnow()
            )
            missing_docs.append(processed_doc)

        if missing_docs:
            db.add_all(missing_docs)
            await db.commit()

        # Mark orphaned records as failed
        orphaned_count = 0
        if orphaned_in_postgres:
            result = await db.execute(
                select(ProcessedDocument).where(
                    ProcessedDocument.document_id.in_(orphaned_in_postgres)
                )
            )
            orphaned_docs = result.scalars().all()

            for doc in orphaned_docs:
                doc.processing_status = 'failed'
                doc.error_message = 'No corresponding vector embeddings found'

            await db.commit()
            orphaned_count = len(orphaned_docs)

        return {
            "message": "Database synchronization complete",
            "qdrant_documents": len(qdrant_docs),
            "postgres_documents_before": len(postgres_ids),
            "created_postgres_records": len(missing_docs),
            "marked_as_failed": orphaned_count,
            "missing_documents": list(missing_in_postgres),
            "orphaned_documents": list(orphaned_in_postgres)
        }

    except Exception as e:
        logger.error(f"Error in sync endpoint: {e}")
        return {"error": str(e)}


@router.get("/constitution")
async def get_constitution_documents(
    chapter: Optional[str] = Query(None, description="Filter by chapter"),
    section: Optional[str] = Query(None, description="Filter by section"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of provisions"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get constitutional provisions from uploaded constitution documents.
    """
    try:
        # Get constitution documents
        result = await db.execute(
            select(ProcessedDocument).where(
                and_(
                    ProcessedDocument.document_type == 'constitution',
                    ProcessedDocument.processing_status == 'completed',
                    ProcessedDocument.is_active == True
                )
            )
        )
        documents = result.scalars().all()
        
        if not documents:
            return {
                "provisions": [],
                "count": 0,
                "message": "No constitution documents found"
            }
        
        # Parse constitutional provisions from document content
        provisions = []
        for doc in documents:
            try:
                # Get document chunks from vector database
                search_results = await vector_db_service.search_by_document_id(
                    doc.document_id, limit=100
                )
                
                for result in search_results:
                    text = result.get("text", "")
                    if not text:
                        continue
                    
                    # Extract constitutional sections
                    section_matches = re.findall(
                        r'Section\s+(\d+)(?:\((\d+)\))?\s*[:\-]?\s*([^\n]+)', 
                        text, re.IGNORECASE
                    )
                    
                    for match in section_matches:
                        section_num = match[0]
                        subsection = match[1] if match[1] else None
                        title = match[2].strip()
                        
                        # Skip if filtering by section and doesn't match
                        if section and section_num != section:
                            continue
                        
                        # Extract chapter information
                        chapter_match = re.search(
                            r'Chapter\s+([IVX]+|[0-9]+)', text, re.IGNORECASE
                        )
                        chapter_name = chapter_match.group(1) if chapter_match else "Unknown"
                        
                        # Skip if filtering by chapter and doesn't match
                        if chapter and chapter.upper() not in chapter_name.upper():
                            continue
                        
                        # Extract content around the section
                        section_pattern = rf'Section\s+{section_num}.*?(?=Section\s+\d+|$)'
                        content_match = re.search(section_pattern, text, re.IGNORECASE | re.DOTALL)
                        content = content_match.group(0) if content_match else text[:500]
                        
                        provision = {
                            "id": f"section_{section_num}_{subsection or '1'}",
                            "chapter": f"Chapter {chapter_name}",
                            "section": section_num,
                            "subsection": subsection,
                            "title": title,
                            "content": content.strip(),
                            "document_id": doc.document_id,
                            "document_name": doc.document_name,
                            "keywords": _extract_keywords(content),
                            "created_at": doc.created_at.isoformat() if doc.created_at else None
                        }
                        provisions.append(provision)
                        
                        if len(provisions) >= limit:
                            break
                    
                    if len(provisions) >= limit:
                        break
                        
            except Exception as e:
                logger.error(f"Error parsing document {doc.document_id}: {e}")
                continue
        
        # Remove duplicates and sort
        unique_provisions = {}
        for prov in provisions:
            key = f"{prov['section']}_{prov['subsection'] or '1'}"
            if key not in unique_provisions:
                unique_provisions[key] = prov
        
        sorted_provisions = sorted(
            unique_provisions.values(), 
            key=lambda x: (int(x['section']), int(x['subsection'] or '1'))
        )
        
        return {
            "provisions": sorted_provisions[:limit],
            "count": len(sorted_provisions),
            "total_documents": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error getting constitution documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve constitution documents")


@router.get("/cases")
async def get_case_documents(
    year: Optional[int] = Query(None, description="Filter by year"),
    search: Optional[str] = Query(None, description="Search in case titles"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of cases"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get Supreme Court cases from uploaded case documents.
    """
    try:
        # Get case documents
        result = await db.execute(
            select(ProcessedDocument).where(
                and_(
                    ProcessedDocument.document_type == 'case',
                    ProcessedDocument.processing_status == 'completed',
                    ProcessedDocument.is_active == True
                )
            )
        )
        documents = result.scalars().all()
        
        if not documents:
            return {
                "cases": [],
                "count": 0,
                "message": "No case documents found"
            }
        
        # Parse cases from document content
        cases = []
        for doc in documents:
            try:
                # Get document chunks from vector database
                search_results = await vector_db_service.search_by_document_id(
                    doc.document_id, limit=100
                )
                
                for result in search_results:
                    text = result.get("text", "")
                    if not text:
                        continue
                    
                    # Extract case information
                    case_patterns = [
                        r'(\d+)\.\s*([A-Z\s&]+(?:v\.?|vs\.?)\s*[A-Z\s&]+)\s*\((\d{4})\)',
                        r'([A-Z\s&]+(?:v\.?|vs\.?)\s*[A-Z\s&]+)\s*\((\d{4})\)',
                        r'Case:\s*([A-Z\s&]+(?:v\.?|vs\.?)\s*[A-Z\s&]+)',
                    ]
                    
                    for pattern in case_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            if len(match) == 3:  # Pattern with number
                                case_number, case_title, case_year = match
                            elif len(match) == 2:  # Pattern without number
                                case_title, case_year = match
                                case_number = None
                            else:  # Pattern with just title
                                case_title = match[0]
                                case_year = None
                                case_number = None
                            
                            # Skip if filtering by year and doesn't match
                            if year and case_year and int(case_year) != year:
                                continue
                            
                            # Skip if searching and doesn't match
                            if search and search.lower() not in case_title.lower():
                                continue
                            
                            # Extract case summary
                            case_start = text.find(case_title)
                            if case_start != -1:
                                summary_text = text[case_start:case_start + 1000]
                            else:
                                summary_text = text[:500]
                            
                            case = {
                                "id": f"case_{len(cases) + 1}",
                                "case_number": case_number,
                                "case_title": case_title.strip(),
                                "judgment_date": f"{case_year}-01-01" if case_year else None,
                                "year": int(case_year) if case_year else None,
                                "case_summary": summary_text.strip(),
                                "document_id": doc.document_id,
                                "document_name": doc.document_name,
                                "legal_principles": _extract_legal_principles(summary_text),
                                "created_at": doc.created_at.isoformat() if doc.created_at else None
                            }
                            cases.append(case)
                            
                            if len(cases) >= limit:
                                break
                        
                        if len(cases) >= limit:
                            break
                    
                    if len(cases) >= limit:
                        break
                        
            except Exception as e:
                logger.error(f"Error parsing case document {doc.document_id}: {e}")
                continue
        
        # Remove duplicates and sort
        unique_cases = {}
        for case in cases:
            key = case['case_title'].lower().strip()
            if key not in unique_cases:
                unique_cases[key] = case
        
        sorted_cases = sorted(
            unique_cases.values(),
            key=lambda x: x['year'] or 0,
            reverse=True
        )
        
        return {
            "cases": sorted_cases[:limit],
            "count": len(sorted_cases),
            "total_documents": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error getting case documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve case documents")


@router.get("/judges")
async def get_judge_documents(
    status: Optional[str] = Query(None, description="Filter by status (active/retired)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of judges"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get judges information from uploaded judge documents.
    """
    try:
        # Get judge documents
        result = await db.execute(
            select(ProcessedDocument).where(
                and_(
                    ProcessedDocument.document_type.in_(['judge', 'general']),
                    ProcessedDocument.processing_status == 'completed',
                    ProcessedDocument.is_active == True
                )
            )
        )
        documents = result.scalars().all()
        
        if not documents:
            return {
                "judges": [],
                "count": 0,
                "message": "No judge documents found"
            }
        
        # Parse judges from document content
        judges = []
        for doc in documents:
            try:
                # Get document chunks from vector database
                search_results = await vector_db_service.search_by_document_id(
                    doc.document_id, limit=100
                )
                
                for result in search_results:
                    text = result.get("text", "")
                    if not text:
                        continue
                    
                    # Extract judge information
                    judge_patterns = [
                        r'(?:Hon\.?\s*)?Justice\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)*)',
                        r'Chief Justice\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*(?:CJN|Chief Justice)',
                    ]
                    
                    for pattern in judge_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            judge_name = match.strip()
                            
                            # Skip common false positives
                            if len(judge_name.split()) < 2 or judge_name.lower() in ['of nigeria', 'of the', 'supreme court']:
                                continue
                            
                            # Extract judge details
                            judge_start = text.lower().find(judge_name.lower())
                            if judge_start != -1:
                                context = text[max(0, judge_start - 200):judge_start + 800]
                            else:
                                context = text[:500]
                            
                            # Determine if Chief Justice
                            is_chief = any(term in context.lower() for term in ['chief justice', 'cjn'])
                            
                            # Extract appointment date
                            date_match = re.search(r'appointed?\s+(?:in\s+)?(\d{4})', context, re.IGNORECASE)
                            appointment_year = date_match.group(1) if date_match else None
                            
                            # Determine status
                            judge_status = "Active"
                            if any(term in context.lower() for term in ['retired', 'former', 'late']):
                                judge_status = "Retired"
                            
                            # Skip if filtering by status and doesn't match
                            if status and status.lower() != judge_status.lower():
                                continue
                            
                            judge = {
                                "id": f"judge_{len(judges) + 1}",
                                "full_name": f"Hon. Justice {judge_name}",
                                "title": "Chief Justice of Nigeria" if is_chief else "Justice of the Supreme Court",
                                "appointment_date": f"{appointment_year}-01-01" if appointment_year else None,
                                "appointment_year": int(appointment_year) if appointment_year else None,
                                "background_summary": context.strip()[:300] + "..." if len(context) > 300 else context.strip(),
                                "current_status": judge_status,
                                "is_chief_justice": is_chief,
                                "is_active": judge_status.lower() == "active",
                                "document_id": doc.document_id,
                                "document_name": doc.document_name,
                                "created_at": doc.created_at.isoformat() if doc.created_at else None
                            }
                            judges.append(judge)
                            
                            if len(judges) >= limit:
                                break
                        
                        if len(judges) >= limit:
                            break
                    
                    if len(judges) >= limit:
                        break
                        
            except Exception as e:
                logger.error(f"Error parsing judge document {doc.document_id}: {e}")
                continue
        
        # Remove duplicates and sort
        unique_judges = {}
        for judge in judges:
            key = judge['full_name'].lower().strip()
            if key not in unique_judges:
                unique_judges[key] = judge
        
        sorted_judges = sorted(
            unique_judges.values(),
            key=lambda x: (not x['is_chief_justice'], x['appointment_year'] or 0),
            reverse=True
        )
        
        return {
            "judges": sorted_judges[:limit],
            "count": len(sorted_judges),
            "total_documents": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error getting judge documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve judge documents")


def _extract_keywords(text: str) -> List[str]:
    """Extract keywords from text."""
    # Simple keyword extraction
    keywords = []
    common_legal_terms = [
        'constitution', 'fundamental rights', 'supreme court', 'appeal', 'judgment',
        'legal', 'law', 'section', 'provision', 'article', 'clause'
    ]
    
    text_lower = text.lower()
    for term in common_legal_terms:
        if term in text_lower:
            keywords.append(term)
    
    return keywords[:5]


def _extract_legal_principles(text: str) -> List[str]:
    """Extract legal principles from case text."""
    principles = []
    
    # Look for common legal principle indicators
    principle_patterns = [
        r'held that\s+([^.]+)',
        r'principle\s+(?:is|that)\s+([^.]+)',
        r'established\s+that\s+([^.]+)',
        r'rule\s+(?:is|that)\s+([^.]+)'
    ]
    
    for pattern in principle_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            principle = match.strip()
            if len(principle) > 20 and len(principle) < 200:
                principles.append(principle)
    
    return principles[:3]
