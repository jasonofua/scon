import React, { useState } from 'react';
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  CalendarIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';

interface SearchFilters {
  query: string;
  documentTypes: string[];
  dateRange: {
    start: string;
    end: string;
  };
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  tags: string[];
  minRelevance: number;
}

interface AdvancedSearchProps {
  onSearch: (filters: SearchFilters) => void;
  isLoading?: boolean;
  className?: string;
}

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({
  onSearch,
  isLoading = false,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    documentTypes: [],
    dateRange: { start: '', end: '' },
    sortBy: 'relevance',
    sortOrder: 'desc',
    tags: [],
    minRelevance: 0.5,
  });

  const documentTypes = [
    { value: 'constitution', label: 'Constitution', color: 'bg-blue-100 text-blue-800' },
    { value: 'case', label: 'Legal Cases', color: 'bg-green-100 text-green-800' },
    { value: 'procedure', label: 'Procedures', color: 'bg-purple-100 text-purple-800' },
    { value: 'form', label: 'Forms', color: 'bg-orange-100 text-orange-800' },
    { value: 'general', label: 'General', color: 'bg-gray-100 text-gray-800' },
  ];

  const sortOptions = [
    { value: 'relevance', label: 'Relevance' },
    { value: 'date', label: 'Date' },
    { value: 'title', label: 'Title' },
    { value: 'type', label: 'Document Type' },
  ];

  const commonTags = [
    'fundamental rights',
    'constitutional law',
    'supreme court',
    'appeal process',
    'civil procedure',
    'criminal law',
    'electoral law',
    'judicial review',
  ];

  const updateFilter = <K extends keyof SearchFilters>(
    key: K,
    value: SearchFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const toggleDocumentType = (type: string) => {
    const newTypes = filters.documentTypes.includes(type)
      ? filters.documentTypes.filter((t) => t !== type)
      : [...filters.documentTypes, type];
    updateFilter('documentTypes', newTypes);
  };

  const toggleTag = (tag: string) => {
    const newTags = filters.tags.includes(tag)
      ? filters.tags.filter((t) => t !== tag)
      : [...filters.tags, tag];
    updateFilter('tags', newTags);
  };

  const clearFilters = () => {
    setFilters({
      query: '',
      documentTypes: [],
      dateRange: { start: '', end: '' },
      sortBy: 'relevance',
      sortOrder: 'desc',
      tags: [],
      minRelevance: 0.5,
    });
  };

  const handleSearch = () => {
    onSearch(filters);
  };

  const hasActiveFilters = 
    filters.documentTypes.length > 0 ||
    filters.dateRange.start ||
    filters.dateRange.end ||
    filters.tags.length > 0 ||
    filters.minRelevance !== 0.5;

  return (
    <div className={clsx('bg-white rounded-lg border border-neutral-200', className)}>
      {/* Main Search Bar */}
      <div className="p-4">
        <div className="flex items-center space-x-3">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-neutral-400" />
            <input
              type="text"
              value={filters.query}
              onChange={(e) => updateFilter('query', e.target.value)}
              placeholder="Search legal documents, cases, procedures..."
              className="w-full pl-10 pr-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={clsx(
              'p-3 rounded-lg border transition-colors',
              isExpanded || hasActiveFilters
                ? 'border-primary-500 bg-primary-50 text-primary-600'
                : 'border-neutral-300 hover:border-neutral-400 text-neutral-600'
            )}
          >
            <AdjustmentsHorizontalIcon className="h-5 w-5" />
          </button>
          <button
            onClick={handleSearch}
            disabled={isLoading}
            className="btn-primary px-6 py-3 disabled:opacity-50"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="mt-3 flex items-center space-x-2 flex-wrap">
            <span className="text-sm text-neutral-600">Active filters:</span>
            {filters.documentTypes.map((type) => {
              const typeInfo = documentTypes.find((t) => t.value === type);
              return (
                <span
                  key={type}
                  className={clsx(
                    'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                    typeInfo?.color || 'bg-gray-100 text-gray-800'
                  )}
                >
                  {typeInfo?.label}
                  <button
                    onClick={() => toggleDocumentType(type)}
                    className="ml-1 hover:bg-black hover:bg-opacity-10 rounded-full p-0.5"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </span>
              );
            })}
            {filters.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-accent-100 text-accent-800"
              >
                {tag}
                <button
                  onClick={() => toggleTag(tag)}
                  className="ml-1 hover:bg-black hover:bg-opacity-10 rounded-full p-0.5"
                >
                  <XMarkIcon className="h-3 w-3" />
                </button>
              </span>
            ))}
            <button
              onClick={clearFilters}
              className="text-xs text-neutral-500 hover:text-neutral-700 underline"
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Advanced Filters */}
      {isExpanded && (
        <div className="border-t border-neutral-200 p-4 space-y-6">
          {/* Document Types */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-3">
              Document Types
            </label>
            <div className="flex flex-wrap gap-2">
              {documentTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => toggleDocumentType(type.value)}
                  className={clsx(
                    'px-3 py-2 rounded-lg border text-sm font-medium transition-colors',
                    filters.documentTypes.includes(type.value)
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-neutral-300 hover:border-neutral-400 text-neutral-700'
                  )}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                From Date
              </label>
              <div className="relative">
                <CalendarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-neutral-400" />
                <input
                  type="date"
                  value={filters.dateRange.start}
                  onChange={(e) =>
                    updateFilter('dateRange', { ...filters.dateRange, start: e.target.value })
                  }
                  className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                To Date
              </label>
              <div className="relative">
                <CalendarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-neutral-400" />
                <input
                  type="date"
                  value={filters.dateRange.end}
                  onChange={(e) =>
                    updateFilter('dateRange', { ...filters.dateRange, end: e.target.value })
                  }
                  className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Sort Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Sort By
              </label>
              <select
                value={filters.sortBy}
                onChange={(e) => updateFilter('sortBy', e.target.value)}
                className="w-full border border-neutral-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Order
              </label>
              <select
                value={filters.sortOrder}
                onChange={(e) => updateFilter('sortOrder', e.target.value as 'asc' | 'desc')}
                className="w-full border border-neutral-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>

          {/* Common Tags */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-3">
              Common Topics
            </label>
            <div className="flex flex-wrap gap-2">
              {commonTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={clsx(
                    'px-3 py-1 rounded-full text-sm transition-colors',
                    filters.tags.includes(tag)
                      ? 'bg-accent-500 text-white'
                      : 'bg-neutral-100 hover:bg-neutral-200 text-neutral-700'
                  )}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          {/* Relevance Threshold */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Minimum Relevance: {Math.round(filters.minRelevance * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={filters.minRelevance}
              onChange={(e) => updateFilter('minRelevance', parseFloat(e.target.value))}
              className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-neutral-500 mt-1">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedSearch;
