import React, { useState, useEffect } from 'react';
import {
  ScaleIcon,
  MagnifyingGlassIcon,
  CalendarIcon,

  StarIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  InformationCircleIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { ApiService } from '../../services/api';
import { toast } from 'react-hot-toast';
import clsx from 'clsx';

interface SupremeCourtCase {
  id: number;
  case_number: string;
  case_title: string;
  judgment_date: string;
  case_summary: string;
  legal_principles: string[];
  case_status: string;
  judges_panel?: number[];
  constitutional_provisions_cited?: number[];
}

interface CaseFilters {
  year?: number;
  status?: string;
  search?: string;
}

const CasesPage: React.FC = () => {
  const [cases, setCases] = useState<SupremeCourtCase[]>([]);
  const [landmarkCases, setLandmarkCases] = useState<SupremeCourtCase[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<CaseFilters>({});
  const [expandedCases, setExpandedCases] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);
  const [_currentPage, setCurrentPage] = useState(0);

  const caseStatuses = [
    { value: 'decided', label: 'Decided', color: 'text-green-600' },
    { value: 'pending', label: 'Pending', color: 'text-yellow-600' },
    { value: 'dismissed', label: 'Dismissed', color: 'text-red-600' },
    { value: 'withdrawn', label: 'Withdrawn', color: 'text-neutral-600' },
  ];

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 30 }, (_, i) => currentYear - i);

  useEffect(() => {
    loadCasesData();
  }, []);

  const loadCasesData = async () => {
    setIsLoading(true);
    try {
      // Load real uploaded case data
      const casesData = await ApiService.getCases(filters.year, undefined, searchQuery, 100);

      setCases(casesData.cases || []);

      // Extract landmark cases (cases with significant legal principles)
      const landmarkCases = (casesData.cases || []).filter(
        (c: any) => c.legal_principles && c.legal_principles.length > 0
      );
      setLandmarkCases(landmarkCases);

      // Set stats
      setStats({
        total_cases: casesData.count || 0,
        cases_this_year: (casesData.cases || []).filter(
          (c: any) => c.year === new Date().getFullYear()
        ).length,
        decided_cases: casesData.count || 0,
        pending_cases: 0,
        available_years: [...new Set(
          (casesData.cases || []).map((c: any) => c.year).filter(Boolean)
        )].sort((a: any, b: any) => b - a),
        total_documents: casesData.total_documents || 0
      });
    } catch (error) {
      console.error('Error loading cases data:', error);
      toast.error('Failed to load cases data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() && !filters.year && !filters.status) {
      loadCasesData();
      return;
    }

    setIsLoading(true);
    try {
      const results = await ApiService.getCases(
        filters.year,
        filters.status,
        searchQuery.trim() || undefined,
        20,
        0
      );
      setCases(results.cases || []);
      setCurrentPage(0);
      toast.success(`Found ${results.cases?.length || 0} cases`);
    } catch (error) {
      console.error('Search error:', error);
      toast.error('Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCase = (caseId: string) => {
    const newExpanded = new Set(expandedCases);
    if (newExpanded.has(caseId)) {
      newExpanded.delete(caseId);
    } else {
      newExpanded.add(caseId);
    }
    setExpandedCases(newExpanded);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // const getStatusColor = (status: string) => {
  //   const statusInfo = caseStatuses.find(s => s.value === status.toLowerCase());
  //   return statusInfo?.color || 'text-neutral-600';
  // };

  const clearFilters = () => {
    setFilters({});
    setSearchQuery('');
    setCurrentPage(0);
    loadCasesData();
  };

  if (isLoading && cases.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-neutral-600">Loading Cases...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-neutral-50">
      {/* Header */}
      <div className="bg-white border-b border-neutral-200 px-6 py-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center space-x-3 mb-4">
            <div className="h-12 w-12 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center">
              <ScaleIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">Supreme Court Cases</h1>
              <p className="text-neutral-600">
                Explore landmark decisions and legal precedents from Nigeria's highest court
              </p>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="flex-1 relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-neutral-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search cases by title, case number, or legal principles..."
                  className="w-full pl-10 pr-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={clsx(
                  'px-4 py-3 border rounded-lg flex items-center space-x-2 transition-colors duration-200',
                  showFilters
                    ? 'bg-primary-50 border-primary-200 text-primary-700'
                    : 'bg-white border-neutral-300 text-neutral-700 hover:bg-neutral-50'
                )}
              >
                <FunnelIcon className="h-5 w-5" />
                <span>Filters</span>
              </button>
              <button
                onClick={handleSearch}
                disabled={isLoading}
                className="btn-primary px-6 py-3"
              >
                Search
              </button>
            </div>

            {/* Filters Panel */}
            {showFilters && (
              <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      Year
                    </label>
                    <select
                      value={filters.year || ''}
                      onChange={(e) => setFilters({ ...filters, year: e.target.value ? parseInt(e.target.value) : undefined })}
                      className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">All Years</option>
                      {years.map(year => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      Status
                    </label>
                    <select
                      value={filters.status || ''}
                      onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined })}
                      className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">All Statuses</option>
                      {caseStatuses.map(status => (
                        <option key={status.value} value={status.value}>{status.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-end">
                    <button
                      onClick={clearFilters}
                      className="w-full px-4 py-2 text-sm text-neutral-600 hover:text-neutral-900 border border-neutral-300 rounded-lg hover:bg-neutral-50 transition-colors duration-200"
                    >
                      Clear Filters
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="max-w-6xl mx-auto px-6 py-6 h-full">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
            {/* Sidebar */}
            <div className="lg:col-span-1">
              <div className="space-y-6">
                {/* Stats */}
                {stats && (
                  <div className="bg-white rounded-lg border border-neutral-200 p-6">
                    <h3 className="font-semibold text-neutral-900 mb-4">Case Statistics</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Total Cases:</span>
                        <span className="font-medium">{stats.total_cases}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">This Year:</span>
                        <span className="font-medium">{stats.cases_this_year}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Decided:</span>
                        <span className="font-medium text-green-600">{stats.decided_cases}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Pending:</span>
                        <span className="font-medium text-yellow-600">{stats.pending_cases}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Landmark Cases */}
                {landmarkCases.length > 0 && (
                  <div className="bg-white rounded-lg border border-neutral-200 p-6">
                    <h3 className="font-semibold text-neutral-900 mb-4 flex items-center space-x-2">
                      <StarIcon className="h-5 w-5 text-yellow-500" />
                      <span>Landmark Cases</span>
                    </h3>
                    <div className="space-y-3">
                      {landmarkCases.slice(0, 3).map((case_) => (
                        <div key={case_.id} className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <h4 className="font-medium text-sm text-yellow-900 mb-1">
                            {case_.case_title}
                          </h4>
                          <p className="text-xs text-yellow-700">
                            {case_.case_number}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3 h-full overflow-hidden">
              <div className="h-full overflow-y-auto space-y-6 pr-2">
                {cases.length > 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <InformationCircleIcon className="h-5 w-5 text-green-600" />
                      <p className="text-green-800 font-medium">
                        Showing {cases.length} case{cases.length !== 1 ? 's' : ''}
                        {searchQuery && ` matching "${searchQuery}"`}
                        {filters.year && ` from ${filters.year}`}
                        {filters.status && ` with status "${filters.status}"`}
                      </p>
                    </div>
                  </div>
                )}

                {cases.map((case_) => (
                  <div key={case_.id} className="bg-white rounded-lg border border-neutral-200 shadow-sm">
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                              {case_.case_number}
                            </span>
                            <span className={clsx(
                              'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
                              case_.case_status === 'decided' ? 'bg-green-100 text-green-800' :
                              case_.case_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-neutral-100 text-neutral-800'
                            )}>
                              {case_.case_status}
                            </span>
                            {case_.judgment_date && (
                              <span className="inline-flex items-center space-x-1 text-sm text-neutral-500">
                                <CalendarIcon className="h-4 w-4" />
                                <span>{formatDate(case_.judgment_date)}</span>
                              </span>
                            )}
                          </div>
                          <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                            {case_.case_title}
                          </h3>
                        </div>
                        
                        <button
                          onClick={() => toggleCase(case_.id.toString())}
                          className="p-2 hover:bg-neutral-100 rounded-lg transition-colors duration-200"
                        >
                          {expandedCases.has(case_.id.toString()) ? (
                            <ChevronDownIcon className="h-5 w-5 text-neutral-500" />
                          ) : (
                            <ChevronRightIcon className="h-5 w-5 text-neutral-500" />
                          )}
                        </button>
                      </div>

                      <div className="bg-neutral-50 rounded-lg p-4">
                        <div className="prose prose-sm max-w-none">
                          <div className="text-neutral-800 leading-relaxed">
                            {expandedCases.has(case_.id.toString()) 
                              ? case_.case_summary
                              : `${case_.case_summary?.substring(0, 200)}...`
                            }
                          </div>
                        </div>
                      </div>

                      {case_.legal_principles && case_.legal_principles.length > 0 && (
                        <div className="mt-4">
                          <h4 className="font-medium text-neutral-900 mb-2">Legal Principles:</h4>
                          <div className="flex flex-wrap gap-2">
                            {case_.legal_principles.slice(0, expandedCases.has(case_.id.toString()) ? undefined : 3).map((principle, index) => (
                              <span
                                key={index}
                                className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700"
                              >
                                {principle}
                              </span>
                            ))}
                            {!expandedCases.has(case_.id.toString()) && case_.legal_principles.length > 3 && (
                              <span className="text-xs text-neutral-500">
                                +{case_.legal_principles.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {cases.length === 0 && !isLoading && (
                  <div className="text-center py-16">
                    <ScaleIcon className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                    <h3 className="text-lg font-medium text-neutral-900 mb-2">No cases found</h3>
                    <p className="text-neutral-600 mb-6">
                      {searchQuery || filters.year || filters.status
                        ? 'No cases match your search criteria'
                        : 'No cases available at the moment'
                      }
                    </p>
                    {(searchQuery || filters.year || filters.status) && (
                      <button
                        onClick={clearFilters}
                        className="btn-primary"
                      >
                        Clear Filters
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CasesPage;
