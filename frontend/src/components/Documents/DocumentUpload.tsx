import React, { useState, useCallback, useRef } from 'react';
import {
  XMarkIcon,
  CloudArrowUpIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { ApiService } from '../../services/api';

interface DocumentUploadProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess?: (result: any) => void;
}

interface UploadFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  result?: any;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [documentType, setDocumentType] = useState('general');
  const [processImmediately, setProcessImmediately] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const documentTypes = [
    { value: 'constitution', label: 'Constitution' },
    { value: 'case', label: 'Legal Case' },
    { value: 'procedure', label: 'Court Procedure' },
    { value: 'form', label: 'Legal Form' },
    { value: 'general', label: 'General Legal Document' },
  ];

  const allowedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain',
  ];

  const maxFileSize = 10 * 1024 * 1024; // 10MB

  const validateFile = (file: File): string | null => {
    if (!allowedTypes.includes(file.type)) {
      return 'File type not supported. Please upload PDF, Word, or text files.';
    }
    if (file.size > maxFileSize) {
      return 'File size exceeds 10MB limit.';
    }
    return null;
  };

  const generateFileId = () => Math.random().toString(36).substring(2, 15);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    const validFiles: UploadFile[] = [];

    fileArray.forEach((file) => {
      const error = validateFile(file);
      validFiles.push({
        file,
        id: generateFileId(),
        status: error ? 'error' : 'pending',
        progress: 0,
        error: error || undefined,
      });
    });

    setFiles((prev) => [...prev, ...validFiles]);
  }, []);

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const uploadFile = async (uploadFile: UploadFile) => {
    setFiles((prev) =>
      prev.map((f) =>
        f.id === uploadFile.id ? { ...f, status: 'uploading', progress: 0 } : f
      )
    );

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === uploadFile.id && f.progress < 90
              ? { ...f, progress: f.progress + 10 }
              : f
          )
        );
      }, 200);

      const result = await ApiService.uploadDocument(
        uploadFile.file,
        documentType,
        processImmediately
      );

      clearInterval(progressInterval);

      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? { ...f, status: 'success', progress: 100, result }
            : f
        )
      );

      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (error: any) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? {
                ...f,
                status: 'error',
                progress: 0,
                error: error.message || 'Upload failed',
              }
            : f
        )
      );
    }
  };

  const uploadAllFiles = async () => {
    const pendingFiles = files.filter((f) => f.status === 'pending');
    for (const file of pendingFiles) {
      await uploadFile(file);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      addFiles(droppedFiles);
    }
  }, [addFiles]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      addFiles(selectedFiles);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading':
        return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <DocumentTextIcon className="h-5 w-5 text-neutral-500" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-200">
          <h2 className="text-xl font-semibold text-neutral-900">Upload Documents</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
          >
            <XMarkIcon className="h-5 w-5 text-neutral-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[calc(90vh-140px)] overflow-y-auto">
          {/* Upload Settings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Document Type
              </label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="w-full border border-neutral-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {documentTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={processImmediately}
                  onChange={(e) => setProcessImmediately(e.target.checked)}
                  className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-neutral-700">Process immediately</span>
              </label>
            </div>
          </div>

          {/* Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={clsx(
              'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
              isDragOver
                ? 'border-primary-500 bg-primary-50'
                : 'border-neutral-300 hover:border-neutral-400'
            )}
          >
            <CloudArrowUpIcon className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
            <p className="text-lg font-medium text-neutral-900 mb-2">
              Drop files here or click to browse
            </p>
            <p className="text-sm text-neutral-500 mb-4">
              Supports PDF, Word documents, and text files up to 10MB
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn-primary"
            >
              Select Files
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-neutral-900">
                Files ({files.length})
              </h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {files.map((uploadFile) => (
                  <div
                    key={uploadFile.id}
                    className="flex items-center space-x-3 p-3 bg-neutral-50 rounded-lg"
                  >
                    <div className="flex-shrink-0">
                      {getStatusIcon(uploadFile.status)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-900 truncate">
                        {uploadFile.file.name}
                      </p>
                      <p className="text-xs text-neutral-500">
                        {formatFileSize(uploadFile.file.size)}
                      </p>
                      {uploadFile.status === 'uploading' && (
                        <div className="mt-1">
                          <div className="bg-neutral-200 rounded-full h-1">
                            <div
                              className="bg-primary-500 h-1 rounded-full transition-all duration-300"
                              style={{ width: `${uploadFile.progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                      {uploadFile.error && (
                        <p className="text-xs text-red-600 mt-1">{uploadFile.error}</p>
                      )}
                    </div>
                    <button
                      onClick={() => removeFile(uploadFile.id)}
                      className="p-1 hover:bg-neutral-200 rounded transition-colors"
                    >
                      <XMarkIcon className="h-4 w-4 text-neutral-500" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-neutral-200">
          <div className="text-sm text-neutral-500">
            {files.filter((f) => f.status === 'success').length} of {files.length} uploaded
          </div>
          <div className="flex items-center space-x-3">
            <button onClick={onClose} className="btn-ghost">
              Cancel
            </button>
            <button
              onClick={uploadAllFiles}
              disabled={files.filter((f) => f.status === 'pending').length === 0}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Upload Files
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;
