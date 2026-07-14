import React, { useState } from 'react';
import {
  DocumentTextIcon,
  BookOpenIcon,
  ScaleIcon,
  UserGroupIcon,
  PlusIcon,
  FunnelIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  CalendarIcon,
  TagIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import type { Document } from '../../types';
import DocumentUpload from './DocumentUpload';

const DocumentsPage: React.FC = () => {
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Mock documents data
  const documents: Document[] = [
    {
      id: '1',
      title: 'Chapter IV - Fundamental Rights',
      type: 'constitution',
      content: 'Constitutional provisions on fundamental rights...',
      uploadedAt: new Date('2024-01-15'),
      status: 'completed',
      metadata: { pages: 45, size: '2.3 MB' }
    },
    {
      id: '2',
      title: 'Marwa v. Nyako (2012)',
      type: 'case',
      content: 'Electoral law case...',
      uploadedAt: new Date('2024-01-10'),
      status: 'completed',
      metadata: { pages: 23, size: '1.8 MB' }
    },
    {
      id: '3',
      title: 'Supreme Court Filing Procedures',
      type: 'procedure',
      content: 'Court procedures and requirements...',
      uploadedAt: new Date('2024-01-08'),
      status: 'processing',
      metadata: { pages: 12, size: '0.9 MB' }
    },
    {
      id: '4',
      title: 'Chief Justice Profile',
      type: 'court_info',
      content: 'Information about the Chief Justice...',
      uploadedAt: new Date('2024-01-05'),
      status: 'completed',
      metadata: { pages: 8, size: '0.5 MB' }
    },
  ];

  const documentTypes = [
    { id: 'all', name: 'All Documents', icon: DocumentTextIcon, count: documents.length },
    { id: 'constitution', name: 'Constitution', icon: BookOpenIcon, count: documents.filter(d => d.type === 'constitution').length },
    { id: 'case', name: 'Cases', icon: ScaleIcon, count: documents.filter(d => d.type === 'case').length },
    { id: 'procedure', name: 'Procedures', icon: DocumentTextIcon, count: documents.filter(d => d.type === 'procedure').length },
    { id: 'court_info', name: 'Court Info', icon: UserGroupIcon, count: documents.filter(d => d.type === 'court_info').length },
  ];

  const filteredDocuments = documents.filter(doc => {
    const matchesType = selectedType === 'all' || doc.type === selectedType;
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-accent-100 text-accent-800';
      case 'processing':
        return 'bg-secondary-100 text-secondary-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-neutral-100 text-neutral-800';
    }
  };

  const getTypeIcon = (type: string) => {
    const typeInfo = documentTypes.find(t => t.id === type);
    return typeInfo?.icon || DocumentTextIcon;
  };

  return (
    <div className="h-full flex flex-col bg-neutral-50">
      {/* Header */}
      <div className="bg-white border-b border-neutral-200 px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Legal Documents</h1>
            <p className="text-neutral-600">
              Manage and browse constitutional documents, cases, and legal resources
            </p>
          </div>
          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="btn-primary flex items-center space-x-2"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Upload Document</span>
          </button>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents..."
              className="w-full input-primary"
            />
          </div>
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-neutral-500" />
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="border border-neutral-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              {documentTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name} ({type.count})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Document Types Grid */}
      <div className="px-6 py-4 bg-white border-b border-neutral-200">
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          {documentTypes.map((type) => (
            <button
              key={type.id}
              onClick={() => setSelectedType(type.id)}
              className={clsx(
                'p-4 rounded-lg border-2 transition-all duration-200 text-left',
                selectedType === type.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-neutral-200 bg-white hover:border-neutral-300'
              )}
            >
              <type.icon className={clsx(
                'h-6 w-6 mb-2',
                selectedType === type.id ? 'text-primary-600' : 'text-neutral-500'
              )} />
              <div className="text-sm font-medium text-neutral-900">{type.name}</div>
              <div className="text-xs text-neutral-500">{type.count} documents</div>
            </button>
          ))}
        </div>
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="px-6 py-6">
          <div className="grid gap-4">
            {filteredDocuments.map((document) => {
              const TypeIcon = getTypeIcon(document.type);
              return (
                <div key={document.id} className="card p-6 hover:shadow-medium transition-shadow duration-200">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className="h-12 w-12 bg-neutral-100 rounded-lg flex items-center justify-center">
                        <TypeIcon className="h-6 w-6 text-neutral-600" />
                      </div>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-medium text-neutral-900 truncate">
                          {document.title}
                        </h3>
                        <span className={clsx(
                          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                          getStatusColor(document.status)
                        )}>
                          {document.status}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-4 text-sm text-neutral-500 mb-3">
                        <div className="flex items-center space-x-1">
                          <TagIcon className="h-4 w-4" />
                          <span className="capitalize">{document.type.replace('_', ' ')}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <CalendarIcon className="h-4 w-4" />
                          <span>{document.uploadedAt.toLocaleDateString()}</span>
                        </div>
                        {document.metadata?.pages && (
                          <span>{document.metadata.pages} pages</span>
                        )}
                        {document.metadata?.size && (
                          <span>{document.metadata.size}</span>
                        )}
                      </div>
                      
                      <p className="text-neutral-600 text-sm mb-4 line-clamp-2">
                        {document.content}
                      </p>
                      
                      <div className="flex items-center space-x-3">
                        <button className="btn-ghost text-sm flex items-center space-x-1">
                          <EyeIcon className="h-4 w-4" />
                          <span>View</span>
                        </button>
                        <button className="btn-ghost text-sm flex items-center space-x-1">
                          <ArrowDownTrayIcon className="h-4 w-4" />
                          <span>Download</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Empty State */}
          {filteredDocuments.length === 0 && (
            <div className="text-center py-12">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-neutral-400" />
              <h3 className="mt-2 text-sm font-medium text-neutral-900">No documents found</h3>
              <p className="mt-1 text-sm text-neutral-500">
                {searchQuery 
                  ? "Try adjusting your search terms or filters."
                  : "Get started by uploading your first document."
                }
              </p>
              {!searchQuery && (
                <div className="mt-6">
                  <button
                    onClick={() => setIsUploadModalOpen(true)}
                    className="btn-primary"
                  >
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Upload Document
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      <DocumentUpload
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={(result) => {
          console.log('Upload successful:', result);
          // TODO: Refresh documents list
          setIsUploadModalOpen(false);
        }}
      />
    </div>
  );
};

export default DocumentsPage;
