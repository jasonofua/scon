"""
Enhanced file upload service for SCONIA.
Handles file validation, processing queue, and document management.
"""
from typing import List, Dict, Any, Optional, BinaryIO
import logging
import os
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime
import asyncio
from fastapi import UploadFile, HTTPException
import aiofiles

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import settings
from app.models.embeddings import ProcessedDocument
from app.services.document_processor import document_processor
from app.services.websocket_manager import connection_manager

logger = logging.getLogger(__name__)


class FileUploadService:
    """Enhanced file upload service with validation and processing."""
    
    def __init__(self):
        """Initialize file upload service."""
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.upload_dir / "pending").mkdir(exist_ok=True)
        (self.upload_dir / "processing").mkdir(exist_ok=True)
        (self.upload_dir / "completed").mkdir(exist_ok=True)
        (self.upload_dir / "failed").mkdir(exist_ok=True)
        
        self.max_file_size = settings.max_file_size
        self.allowed_extensions = settings.allowed_file_types
        
        # MIME type mapping
        self.mime_types = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'text/plain': 'txt',
            'text/html': 'html',
            'application/msword': 'doc'
        }
    
    def _validate_file_type(self, filename: str, content_type: str) -> bool:
        """Validate file type based on extension and MIME type."""
        try:
            # Check extension
            file_ext = Path(filename).suffix.lower().lstrip('.')
            if file_ext not in self.allowed_extensions:
                return False
            
            # Check MIME type
            if content_type in self.mime_types:
                expected_ext = self.mime_types[content_type]
                return expected_ext == file_ext or file_ext in ['doc', 'docx']
            
            # Fallback to extension check
            return file_ext in self.allowed_extensions
            
        except Exception as e:
            logger.error(f"Error validating file type: {e}")
            return False
    
    def _validate_file_size(self, file_size: int) -> bool:
        """Validate file size."""
        return file_size <= self.max_file_size
    
    def _generate_file_hash(self, content: bytes) -> str:
        """Generate SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path components
        filename = Path(filename).name
        
        # Replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename
    
    async def validate_upload(
        self,
        file: UploadFile,
        document_type: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate uploaded file before processing.
        
        Args:
            file: Uploaded file
            document_type: Type of legal document
            user_id: ID of uploading user
            
        Returns:
            Validation result with details
        """
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "file_info": {}
            }
            
            # Check if file is provided
            if not file or not file.filename:
                validation_result["valid"] = False
                validation_result["errors"].append("No file provided")
                return validation_result
            
            # Read file content for validation
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            file_size = len(content)
            file_hash = self._generate_file_hash(content)
            
            # Store file info
            validation_result["file_info"] = {
                "filename": file.filename,
                "size": file_size,
                "content_type": file.content_type,
                "hash": file_hash
            }
            
            # Validate file size
            if not self._validate_file_size(file_size):
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"File size ({file_size:,} bytes) exceeds maximum allowed size ({self.max_file_size:,} bytes)"
                )
            
            # Validate file type
            if not self._validate_file_type(file.filename, file.content_type or ""):
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"File type not allowed. Supported types: {', '.join(self.allowed_extensions)}"
                )
            
            # Check for empty file
            if file_size == 0:
                validation_result["valid"] = False
                validation_result["errors"].append("File is empty")
            
            # Check for duplicate files (by hash)
            # This would require database check in a real implementation
            
            # Validate document type
            valid_doc_types = ["constitution", "case", "procedure", "form", "general"]
            if document_type not in valid_doc_types:
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"Invalid document type. Allowed types: {', '.join(valid_doc_types)}"
                )
            
            # Add warnings for large files
            if file_size > self.max_file_size * 0.8:
                validation_result["warnings"].append("Large file may take longer to process")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating upload: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "file_info": {}
            }
    
    async def save_upload(
        self,
        file: UploadFile,
        document_type: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save uploaded file and prepare for processing.
        
        Args:
            file: Uploaded file
            document_type: Type of legal document
            user_id: ID of uploading user
            session_id: WebSocket session ID for progress updates
            
        Returns:
            Upload result with file path and metadata
        """
        try:
            # Validate upload first
            validation = await self.validate_upload(file, document_type, user_id)
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=validation["errors"])
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sanitized_name = self._sanitize_filename(file.filename)
            file_hash = validation["file_info"]["hash"][:8]
            unique_filename = f"{timestamp}_{file_hash}_{sanitized_name}"
            
            # Save to pending directory
            file_path = self.upload_dir / "pending" / unique_filename
            
            # Save file
            content = await file.read()
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Send progress update if session provided
            if session_id:
                await connection_manager.send_system_notification(
                    session_id, "file_uploaded", f"File '{file.filename}' uploaded successfully"
                )
            
            upload_result = {
                "success": True,
                "file_path": str(file_path),
                "filename": unique_filename,
                "original_filename": file.filename,
                "file_size": len(content),
                "document_type": document_type,
                "upload_time": datetime.utcnow().isoformat(),
                "status": "pending"
            }
            
            logger.info(f"File uploaded successfully: {unique_filename}")
            return upload_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving upload: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    async def process_uploaded_file(
        self,
        file_path: str,
        document_type: str,
        db: AsyncSession,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        use_gemini: bool = True
    ) -> str:
        """
        Process uploaded file through the document processing pipeline.
        
        Args:
            file_path: Path to uploaded file
            document_type: Type of legal document
            db: Database session
            user_id: ID of uploading user
            session_id: WebSocket session ID for progress updates
            use_gemini: Whether to use Gemini for embeddings
            
        Returns:
            Document ID of processed document
        """
        try:
            file_path_obj = Path(file_path)
            
            # Move file to processing directory
            processing_path = self.upload_dir / "processing" / file_path_obj.name
            file_path_obj.rename(processing_path)
            
            # Send progress update
            if session_id:
                await connection_manager.send_query_progress(
                    session_id, "processing", 0.2, "Starting document processing..."
                )
            
            # Process document
            document_id = await document_processor.process_document(
                file_path=str(processing_path),
                document_type=document_type,
                db=db,
                use_gemini=use_gemini
            )
            
            # Move to completed directory
            completed_path = self.upload_dir / "completed" / file_path_obj.name
            processing_path.rename(completed_path)
            
            # Send completion notification
            if session_id:
                await connection_manager.send_system_notification(
                    session_id, "processing_complete", 
                    f"Document processed successfully. Document ID: {document_id}"
                )
            
            logger.info(f"Document processed successfully: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            
            # Move to failed directory
            try:
                failed_path = self.upload_dir / "failed" / file_path_obj.name
                if file_path_obj.exists():
                    file_path_obj.rename(failed_path)
                elif processing_path.exists():
                    processing_path.rename(failed_path)
            except:
                pass
            
            # Send error notification
            if session_id:
                await connection_manager.send_system_notification(
                    session_id, "processing_error", 
                    f"Failed to process document: {str(e)}"
                )
            
            raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
    
    async def get_upload_status(self, filename: str) -> Dict[str, Any]:
        """Get status of an uploaded file."""
        try:
            # Check in different directories
            directories = ["pending", "processing", "completed", "failed"]
            
            for directory in directories:
                file_path = self.upload_dir / directory / filename
                if file_path.exists():
                    stat = file_path.stat()
                    return {
                        "filename": filename,
                        "status": directory,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": str(file_path)
                    }
            
            return {
                "filename": filename,
                "status": "not_found",
                "error": "File not found in any directory"
            }
            
        except Exception as e:
            logger.error(f"Error getting upload status: {e}")
            return {
                "filename": filename,
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup_old_files(self, days_old: int = 7):
        """Clean up old files from upload directories."""
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            # Clean up completed and failed files older than specified days
            for directory in ["completed", "failed"]:
                dir_path = self.upload_dir / directory
                
                for file_path in dir_path.iterdir():
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to delete {file_path}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            return 0


# Global file upload service instance
file_upload_service = FileUploadService()
