import React, { useState } from 'react';
import {
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ScaleIcon,
  BookOpenIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline';
import type { SearchResult, SearchResponse } from '../../types';
import { ApiService } from '../../services/api';
import { toast } from 'react-hot-toast';
import clsx from 'clsx';
import AdvancedSearch from './AdvancedSearch';

const SearchPage: React.FC = () => {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [totalFound, setTotalFound] = useState(0);
  const [lastQuery, setLastQuery] = useState('');

  const documentTypes = [
    { id: 'constitution', name: 'Constitution', icon: BookOpenIcon, color: 'text-blue-600' },
    { id: 'case', name: 'Cases', icon: ScaleIcon, color: 'text-green-600' },
    { id: 'procedure', name: 'Procedures', icon: DocumentTextIcon, color: 'text-purple-600' },
    { id: 'court_info', name: 'Court Info', icon: UserGroupIcon, color: 'text-orange-600' },
  ];

  const handleAdvancedSearch = async (filters: any) => {
    if (!filters.query.trim()) return;

    setIsLoading(true);
    setLastQuery(filters.query);

    try {
      const response: SearchResponse = await ApiService.semanticSearch(
        filters.query,
        20,
        filters.documentTypes.length > 0 ? filters.documentTypes : undefined
      );

      setResults(response.results);
      setTotalFound(response.total_found);

      toast.success(`Found ${response.total_found} results`);
    } catch (error: any) {
      console.error('Search error:', error);
      toast.error('Search failed. Please try again.');
      setResults([]);
      setTotalFound(0);
    } finally {
      setIsLoading(false);
    }
  };

  const getDocumentTypeInfo = (type: string) => {
    return documentTypes.find(dt => dt.id === type) || documentTypes[0];
  };

  return (
    <div className="h-full flex flex-col bg-neutral-50">
      {/* Search Header */}
      <div className="bg-white border-b border-neutral-200 px-6 py-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-neutral-900 mb-2">Legal Document Search</h1>
          <p className="text-neutral-600 mb-6">
            Search through constitutional documents, court cases, procedures, and legal information
          </p>

          {/* Advanced Search Component */}
          <AdvancedSearch
            onSearch={handleAdvancedSearch}
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="max-w-4xl mx-auto px-6 py-6">
          {totalFound > 0 && (
            <div className="mb-8">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <p className="text-green-800 font-medium">
                    Found {totalFound} legal document{totalFound !== 1 ? 's' : ''} related to "{lastQuery}"
                  </p>
                </div>
                <p className="text-green-700 text-sm mt-1">
                  Results are sorted by relevance to help you find the most useful information first.
                </p>
              </div>
            </div>
          )}

          <div className="space-y-6">
            {results.map((result) => {
              const typeInfo = getDocumentTypeInfo(result.document_type);

              // Helper function to format and improve text readability
              const formatResultText = (text: string, documentType: string) => {
                // Clean up the text
                let cleanText = text.trim();

                // Add better formatting for constitutional text
                if (documentType === 'constitution') {
                  // Add line breaks for sections and subsections
                  cleanText = cleanText
                    .replace(/Section (\d+):/g, '\n\nSection $1:')
                    .replace(/\((\d+)\)/g, '\n($1)')
                    .replace(/\([a-z]\)/g, '\n($&)')
                    .trim();
                }

                return cleanText;
              };

              // Helper function to create user-friendly titles
              const getResultTitle = (result: SearchResult) => {
                if (result.metadata?.title) {
                  return result.metadata.title;
                }

                // Generate titles based on document type and content
                switch (result.document_type) {
                  case 'constitution':
                    if (result.text.includes('Section')) {
                      const sectionMatch = result.text.match(/Section (\d+):/);
                      if (sectionMatch) {
                        return `Constitutional Rights - Section ${sectionMatch[1]}`;
                      }
                    }
                    if (result.text.toLowerCase().includes('right to life')) {
                      return 'Right to Life - Constitutional Protection';
                    }
                    if (result.text.toLowerCase().includes('fundamental rights')) {
                      return 'Fundamental Rights - Constitutional Provisions';
                    }
                    return 'Constitutional Provision';
                  case 'case':
                    return 'Court Case';
                  case 'procedure':
                    return 'Legal Procedure';
                  default:
                    return typeInfo.name;
                }
              };

              // Helper function to create user-friendly summaries
              const getResultSummary = (result: SearchResult) => {
                const text = result.text.toLowerCase();

                if (result.document_type === 'constitution') {
                  if (text.includes('right to life')) {
                    return 'This section explains your constitutional right to life and the legal protections that ensure no one can unlawfully take your life.';
                  }
                  if (text.includes('fundamental rights')) {
                    return 'This section outlines the fundamental rights guaranteed to all citizens under the Nigerian Constitution.';
                  }
                  if (text.includes('right to')) {
                    return 'This section describes important constitutional rights and protections available to citizens.';
                  }
                }

                return 'Legal information relevant to your search.';
              };

              const resultTitle = getResultTitle(result);
              const resultSummary = getResultSummary(result);
              const formattedText = formatResultText(result.text, result.document_type);

              return (
                <div key={result.id} className="bg-white rounded-lg border border-neutral-200 shadow-sm hover:shadow-md transition-shadow duration-200">
                  <div className="p-6">
                    {/* Header with icon and type */}
                    <div className="flex items-start space-x-4 mb-4">
                      <div className="flex-shrink-0">
                        <div className="h-12 w-12 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg flex items-center justify-center">
                          <typeInfo.icon className={clsx('h-6 w-6', typeInfo.color)} />
                        </div>
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-lg font-semibold text-neutral-900 leading-tight">
                            {resultTitle}
                          </h3>
                          <span className={clsx(
                            'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
                            'bg-blue-50 text-blue-700 border border-blue-200'
                          )}>
                            {typeInfo.name}
                          </span>
                        </div>

                        <p className="text-sm text-neutral-600 mb-3">
                          {resultSummary}
                        </p>
                      </div>
                    </div>

                    {/* Main content */}
                    <div className="bg-neutral-50 rounded-lg p-4 mb-4">
                      <div className="prose prose-sm max-w-none">
                        <div className="text-neutral-800 leading-relaxed whitespace-pre-line">
                          {formattedText.length > 400
                            ? `${formattedText.substring(0, 400)}...`
                            : formattedText
                          }
                        </div>
                      </div>
                    </div>

                    {/* Footer with relevance and source info */}
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center space-x-1">
                          <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                          <span className="text-neutral-600">
                            {(result.score * 100).toFixed(0)}% relevant to your search
                          </span>
                        </div>
                        {result.metadata?.title && (
                          <span className="text-neutral-500">
                            Source: {result.metadata.title}
                          </span>
                        )}
                      </div>

                      <button className="text-blue-600 hover:text-blue-700 font-medium">
                        View Full Document →
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Empty State */}
          {!isLoading && results.length === 0 && lastQuery && (
            <div className="text-center py-16">
              <div className="bg-neutral-100 rounded-full h-16 w-16 mx-auto mb-4 flex items-center justify-center">
                <MagnifyingGlassIcon className="h-8 w-8 text-neutral-400" />
              </div>
              <h3 className="text-lg font-medium text-neutral-900 mb-2">No results found</h3>
              <p className="text-neutral-600 mb-6 max-w-md mx-auto">
                We couldn't find any legal documents matching "{lastQuery}". Try using different keywords or check the suggestions below.
              </p>

              <div className="bg-blue-50 rounded-lg p-6 max-w-2xl mx-auto">
                <h4 className="font-medium text-blue-900 mb-3">Search Tips:</h4>
                <ul className="text-sm text-blue-800 space-y-2 text-left">
                  <li>• Try broader terms like "rights", "court procedures", or "constitution"</li>
                  <li>• Use simple language instead of legal jargon</li>
                  <li>• Check your spelling and try alternative words</li>
                  <li>• Remove filters to see more results</li>
                </ul>
              </div>
            </div>
          )}

          {/* Initial State - No search performed yet */}
          {!isLoading && results.length === 0 && !lastQuery && (
            <div className="text-center py-16">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-full h-20 w-20 mx-auto mb-6 flex items-center justify-center">
                <BookOpenIcon className="h-10 w-10 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-3">Search Legal Documents</h3>
              <p className="text-neutral-600 mb-8 max-w-lg mx-auto">
                Find information about your rights, court procedures, legal cases, and constitutional provisions.
                Start by typing your question or legal topic above.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                <div className="bg-white border border-neutral-200 rounded-lg p-4 text-left">
                  <h4 className="font-medium text-neutral-900 mb-2">Popular Searches:</h4>
                  <ul className="text-sm text-neutral-600 space-y-1">
                    <li>• Right to life</li>
                    <li>• Court procedures</li>
                    <li>• Filing a case</li>
                    <li>• Constitutional rights</li>
                  </ul>
                </div>

                <div className="bg-white border border-neutral-200 rounded-lg p-4 text-left">
                  <h4 className="font-medium text-neutral-900 mb-2">Document Types:</h4>
                  <ul className="text-sm text-neutral-600 space-y-1">
                    <li>• Constitution</li>
                    <li>• Court cases</li>
                    <li>• Legal procedures</li>
                    <li>• Court information</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Initial State */}
          {!lastQuery && (
            <div className="text-center py-12">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-neutral-400" />
              <h3 className="mt-2 text-sm font-medium text-neutral-900">Search Legal Documents</h3>
              <p className="mt-1 text-sm text-neutral-500">
                Enter your search query above to find relevant legal documents and cases.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchPage;
