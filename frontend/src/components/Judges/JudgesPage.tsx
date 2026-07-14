import React, { useState, useEffect } from 'react';
import {
  UserGroupIcon,
  StarIcon,
  AcademicCapIcon,
  BuildingLibraryIcon,
  CalendarIcon,
  InformationCircleIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import { ApiService } from '../../services/api';
import { toast } from 'react-hot-toast';
import clsx from 'clsx';

interface Judge {
  id: number;
  full_name: string;
  title: string;
  appointment_date: string;
  background_summary: string;
  education: any;
  previous_positions: string[];
  current_status: string;
  image_url?: string;
  is_chief_justice: boolean;
}

interface CourtLevel {
  name: string;
  description: string;
  jurisdiction: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

const JudgesPage: React.FC = () => {
  const [judges, setJudges] = useState<Judge[]>([]);
  const [chiefJustice, setChiefJustice] = useState<Judge | null>(null);
  const [courtHierarchy, setCourtHierarchy] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [expandedJudges, setExpandedJudges] = useState<Set<string>>(new Set());

  const courtLevels: CourtLevel[] = [
    {
      name: 'Supreme Court',
      description: 'Highest court in Nigeria with final appellate jurisdiction',
      jurisdiction: 'Constitutional matters, appeals from Court of Appeal',
      icon: StarIcon,
      color: 'text-red-600'
    },
    {
      name: 'Court of Appeal',
      description: 'Intermediate appellate court',
      jurisdiction: 'Appeals from High Courts, Sharia Courts, Customary Courts',
      icon: BuildingLibraryIcon,
      color: 'text-blue-600'
    },
    {
      name: 'Federal High Court',
      description: 'Federal matters and specialized jurisdiction',
      jurisdiction: 'Federal revenue, banking, immigration, maritime law',
      icon: AcademicCapIcon,
      color: 'text-green-600'
    },
    {
      name: 'State High Court',
      description: 'General jurisdiction at state level',
      jurisdiction: 'Civil and criminal matters within state jurisdiction',
      icon: UserGroupIcon,
      color: 'text-purple-600'
    },
  ];

  const statusOptions = [
    { value: 'active', label: 'Active' },
    { value: 'retired', label: 'Retired' },
    { value: 'suspended', label: 'Suspended' },
  ];

  useEffect(() => {
    loadJudgesData();
  }, []);

  const loadJudgesData = async () => {
    setIsLoading(true);
    try {
      // Load real uploaded judges data
      const judgesData = await ApiService.getJudges(selectedStatus, 100);

      setJudges(judgesData.judges || []);

      // Find Chief Justice from the judges data
      const chiefJustice = (judgesData.judges || []).find(
        (judge: any) => judge.is_chief_justice
      );
      setChiefJustice(chiefJustice);

      // Use static court hierarchy for now
      setCourtHierarchy({
        levels: [
          {
            name: "Supreme Court of Nigeria",
            description: "Highest court in Nigeria",
            judges_count: (judgesData.judges || []).length
          }
        ]
      });
    } catch (error) {
      console.error('Error loading judges data:', error);
      toast.error('Failed to load judges data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() && !selectedStatus) {
      loadJudgesData();
      return;
    }

    setIsLoading(true);
    try {
      const results = await ApiService.getJudges(selectedStatus || undefined);
      let filteredJudges = results.judges || [];
      
      if (searchQuery.trim()) {
        filteredJudges = filteredJudges.filter((judge: Judge) =>
          judge.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          judge.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          judge.background_summary?.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }
      
      setJudges(filteredJudges);
      toast.success(`Found ${filteredJudges.length} judges`);
    } catch (error) {
      console.error('Search error:', error);
      toast.error('Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleJudge = (judgeId: string) => {
    const newExpanded = new Set(expandedJudges);
    if (newExpanded.has(judgeId)) {
      newExpanded.delete(judgeId);
    } else {
      newExpanded.add(judgeId);
    }
    setExpandedJudges(newExpanded);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedStatus('');
    loadJudgesData();
  };

  if (isLoading && judges.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-neutral-600">Loading Judges...</p>
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
            <div className="h-12 w-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
              <UserGroupIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">Judges & Court Structure</h1>
              <p className="text-neutral-600">
                Learn about Nigeria's judicial system and the judges who serve
              </p>
            </div>
          </div>

          {/* Search Bar */}
          <div className="flex items-center space-x-3">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-neutral-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search judges by name, title, or background..."
                className="w-full pl-10 pr-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Statuses</option>
              {statusOptions.map(status => (
                <option key={status.value} value={status.value}>{status.label}</option>
              ))}
            </select>
            <button
              onClick={handleSearch}
              disabled={isLoading}
              className="btn-primary px-6 py-3"
            >
              Search
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="max-w-6xl mx-auto px-6 py-6 h-full">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
            {/* Sidebar */}
            <div className="lg:col-span-1">
              <div className="space-y-6">
                {/* Chief Justice */}
                {chiefJustice && (
                  <div className="bg-white rounded-lg border border-neutral-200 p-6">
                    <h3 className="font-semibold text-neutral-900 mb-4 flex items-center space-x-2">
                      <StarIcon className="h-5 w-5 text-yellow-500" />
                      <span>Chief Justice</span>
                    </h3>
                    <div className="text-center">
                      {chiefJustice.image_url ? (
                        <img
                          src={chiefJustice.image_url}
                          alt={chiefJustice.full_name}
                          className="w-16 h-16 rounded-full mx-auto mb-3 object-cover"
                        />
                      ) : (
                        <div className="w-16 h-16 bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-full mx-auto mb-3 flex items-center justify-center">
                          <span className="text-white font-bold text-lg">
                            {chiefJustice.full_name.split(' ').map(n => n[0]).join('')}
                          </span>
                        </div>
                      )}
                      <h4 className="font-medium text-neutral-900">{chiefJustice.full_name}</h4>
                      <p className="text-sm text-neutral-600">{chiefJustice.title}</p>
                      {chiefJustice.appointment_date && (
                        <p className="text-xs text-neutral-500 mt-1">
                          Since {formatDate(chiefJustice.appointment_date)}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Court Hierarchy */}
                <div className="bg-white rounded-lg border border-neutral-200 p-6">
                  <h3 className="font-semibold text-neutral-900 mb-4">Court Hierarchy</h3>
                  {courtHierarchy ? (
                    <div className="space-y-3">
                      {courtHierarchy.levels?.map((court: any, index: number) => (
                        <div key={court.name} className="relative">
                          {index > 0 && (
                            <div className="absolute -top-3 left-6 w-px h-3 bg-neutral-300"></div>
                          )}
                          <div className="flex items-start space-x-3 p-3 bg-neutral-50 rounded-lg">
                            <BuildingLibraryIcon className="h-5 w-5 mt-0.5 text-blue-600" />
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-sm text-neutral-900">{court.name}</h4>
                              <p className="text-xs text-neutral-600 mt-1">{court.description}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {courtLevels.map((court, index) => (
                        <div key={court.name} className="relative">
                          {index > 0 && (
                            <div className="absolute -top-3 left-6 w-px h-3 bg-neutral-300"></div>
                          )}
                          <div className="flex items-start space-x-3 p-3 bg-neutral-50 rounded-lg">
                            <court.icon className={clsx('h-5 w-5 mt-0.5', court.color)} />
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-sm text-neutral-900">{court.name}</h4>
                              <p className="text-xs text-neutral-600 mt-1">{court.description}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-xs text-blue-700">
                          📄 Comprehensive court hierarchy data has been compiled and saved to nigeria_court_hierarchy_and_judges.txt for system integration.
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Quick Stats */}
                <div className="bg-white rounded-lg border border-neutral-200 p-6">
                  <h3 className="font-semibold text-neutral-900 mb-4">Statistics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-neutral-600">Total Judges:</span>
                      <span className="font-medium">{judges.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-600">Active:</span>
                      <span className="font-medium text-green-600">
                        {judges.filter(j => j.current_status === 'active').length}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-600">Retired:</span>
                      <span className="font-medium text-neutral-600">
                        {judges.filter(j => j.current_status === 'retired').length}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3 h-full overflow-hidden">
              <div className="h-full overflow-y-auto space-y-6 pr-2">
                {judges.length > 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <InformationCircleIcon className="h-5 w-5 text-green-600" />
                        <p className="text-green-800 font-medium">
                          Showing {judges.length} judge{judges.length !== 1 ? 's' : ''}
                          {searchQuery && ` matching "${searchQuery}"`}
                          {selectedStatus && ` with status "${selectedStatus}"`}
                        </p>
                      </div>
                      {(searchQuery || selectedStatus) && (
                        <button
                          onClick={clearFilters}
                          className="text-sm text-green-700 hover:text-green-900 font-medium"
                        >
                          Clear Filters
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {judges.map((judge) => (
                  <div key={judge.id} className="bg-white rounded-lg border border-neutral-200 shadow-sm">
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-start space-x-4 flex-1">
                          {judge.image_url ? (
                            <img
                              src={judge.image_url}
                              alt={judge.full_name}
                              className="w-12 h-12 rounded-full object-cover"
                            />
                          ) : (
                            <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-500 rounded-full flex items-center justify-center">
                              <span className="text-white font-bold">
                                {judge.full_name.split(' ').map(n => n[0]).join('')}
                              </span>
                            </div>
                          )}
                          
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <h3 className="text-lg font-semibold text-neutral-900">
                                {judge.full_name}
                              </h3>
                              {judge.is_chief_justice && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                  <StarIcon className="h-3 w-3 mr-1" />
                                  Chief Justice
                                </span>
                              )}
                              <span className={clsx(
                                'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                                judge.current_status === 'active' ? 'bg-green-100 text-green-800' :
                                judge.current_status === 'retired' ? 'bg-neutral-100 text-neutral-800' :
                                'bg-red-100 text-red-800'
                              )}>
                                {judge.current_status}
                              </span>
                            </div>
                            <p className="text-neutral-600 mb-2">{judge.title}</p>
                            {judge.appointment_date && (
                              <div className="flex items-center space-x-1 text-sm text-neutral-500">
                                <CalendarIcon className="h-4 w-4" />
                                <span>Appointed {formatDate(judge.appointment_date)}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        
                        <button
                          onClick={() => toggleJudge(judge.id.toString())}
                          className="p-2 hover:bg-neutral-100 rounded-lg transition-colors duration-200"
                        >
                          {expandedJudges.has(judge.id.toString()) ? (
                            <ChevronDownIcon className="h-5 w-5 text-neutral-500" />
                          ) : (
                            <ChevronRightIcon className="h-5 w-5 text-neutral-500" />
                          )}
                        </button>
                      </div>

                      {expandedJudges.has(judge.id.toString()) && (
                        <div className="space-y-4 pt-4 border-t border-neutral-200">
                          {judge.background_summary && (
                            <div>
                              <h4 className="font-medium text-neutral-900 mb-2">Background</h4>
                              <p className="text-neutral-700 text-sm leading-relaxed">
                                {judge.background_summary}
                              </p>
                            </div>
                          )}

                          {judge.education && (
                            <div>
                              <h4 className="font-medium text-neutral-900 mb-2">Education</h4>
                              <div className="bg-neutral-50 rounded-lg p-3">
                                <pre className="text-sm text-neutral-700 whitespace-pre-wrap">
                                  {JSON.stringify(judge.education, null, 2)}
                                </pre>
                              </div>
                            </div>
                          )}

                          {judge.previous_positions && judge.previous_positions.length > 0 && (
                            <div>
                              <h4 className="font-medium text-neutral-900 mb-2">Previous Positions</h4>
                              <ul className="space-y-1">
                                {judge.previous_positions.map((position, index) => (
                                  <li key={index} className="text-sm text-neutral-700 flex items-start space-x-2">
                                    <span className="text-neutral-400">•</span>
                                    <span>{position}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {judges.length === 0 && !isLoading && (
                  <div className="text-center py-16">
                    <UserGroupIcon className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                    <h3 className="text-lg font-medium text-neutral-900 mb-2">No judges found</h3>
                    <p className="text-neutral-600 mb-6">
                      {searchQuery || selectedStatus
                        ? 'No judges match your search criteria'
                        : 'No judges available at the moment'
                      }
                    </p>
                    {(searchQuery || selectedStatus) && (
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

export default JudgesPage;
