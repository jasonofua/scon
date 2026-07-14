import React, { useState, useEffect } from 'react';
import {
  BookOpenIcon,
  MagnifyingGlassIcon,
  ScaleIcon,
  DocumentTextIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  StarIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import { ApiService } from '../../services/api';
import { toast } from 'react-hot-toast';
import clsx from 'clsx';

interface ConstitutionalProvision {
  id: number;
  chapter: string;
  section: string;
  subsection?: string;
  title: string;
  content: string;
  keywords?: string[];
  related_sections?: string[];
}

interface Chapter {
  name: string;
  count: number;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

const ConstitutionPage: React.FC = () => {
  const [provisions, setProvisions] = useState<ConstitutionalProvision[]>([]);
  const [_chapters, setChapters] = useState<string[]>([]);
  const [_fundamentalRights, setFundamentalRights] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedChapter, setSelectedChapter] = useState<string>('');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const chapterInfo: Record<string, Chapter> = {
    'Chapter I': {
      name: 'General Provisions',
      count: 0,
      description: 'Federal Republic of Nigeria, supremacy of constitution, and basic structure',
      icon: BookOpenIcon,
      color: 'text-blue-600'
    },
    'Chapter II': {
      name: 'Fundamental Objectives',
      count: 0,
      description: 'Directive principles of state policy and fundamental objectives',
      icon: DocumentTextIcon,
      color: 'text-green-600'
    },
    'Chapter III': {
      name: 'Citizenship',
      count: 0,
      description: 'Nigerian citizenship, acquisition, and deprivation',
      icon: StarIcon,
      color: 'text-purple-600'
    },
    'Chapter IV': {
      name: 'Fundamental Rights',
      count: 0,
      description: 'Constitutional rights and freedoms of Nigerian citizens',
      icon: ScaleIcon,
      color: 'text-red-600'
    },
  };

  useEffect(() => {
    loadConstitutionData();
  }, []);

  const loadConstitutionData = async () => {
    setIsLoading(true);
    try {
      // Load real uploaded constitution data
      const provisionsData = await ApiService.getConstitutionalProvisions(undefined, undefined, undefined, 100);

      setProvisions(provisionsData.provisions || []);

      // Extract chapters from provisions
      const uniqueChapters = [...new Set(
        (provisionsData.provisions || []).map((p: any) => p.chapter).filter(Boolean)
      )];
      setChapters(uniqueChapters as string[]);

      // Extract fundamental rights (Chapter IV)
      const fundamentalRights = (provisionsData.provisions || []).filter(
        (p: any) => p.chapter && p.chapter.toLowerCase().includes('iv')
      );
      setFundamentalRights(fundamentalRights);

      // Set stats
      setStats({
        total_provisions: provisionsData.count || 0,
        total_chapters: uniqueChapters.length,
        fundamental_rights_count: fundamentalRights.length,
        total_documents: provisionsData.total_documents || 0
      });
    } catch (error) {
      console.error('Error loading constitution data:', error);
      toast.error('Failed to load constitution data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    try {
      const results = await ApiService.searchConstitution(searchQuery, 20);
      setProvisions(results.results || []);
      toast.success(`Found ${results.results?.length || 0} results`);
    } catch (error) {
      console.error('Search error:', error);
      toast.error('Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChapterFilter = async (chapter: string) => {
    if (selectedChapter === chapter) {
      setSelectedChapter('');
      loadConstitutionData();
      return;
    }

    setSelectedChapter(chapter);
    setIsLoading(true);
    try {
      const results = await ApiService.getConstitutionalProvisions(chapter);
      setProvisions(results.provisions || []);
    } catch (error) {
      console.error('Filter error:', error);
      toast.error('Failed to filter by chapter');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const formatContent = (content: string) => {
    return content
      .replace(/\n\n/g, '\n')
      .replace(/Section (\d+):/g, '\n\nSection $1:')
      .replace(/\((\d+)\)/g, '\n($1)')
      .trim();
  };

  if (isLoading && provisions.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-neutral-600">Loading Constitution...</p>
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
            <div className="h-12 w-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
              <BookOpenIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">Nigerian Constitution</h1>
              <p className="text-neutral-600">
                Explore the Constitution of the Federal Republic of Nigeria 1999
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
                placeholder="Search constitutional provisions, sections, rights..."
                className="w-full pl-10 pr-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={!searchQuery.trim() || isLoading}
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
              <div className="bg-white rounded-lg border border-neutral-200 p-6 sticky top-6">
                <h3 className="font-semibold text-neutral-900 mb-4">Chapters</h3>
                
                {/* Quick Stats */}
                {stats && (
                  <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                    <div className="text-sm text-blue-800">
                      <div className="flex justify-between mb-1">
                        <span>Total Provisions:</span>
                        <span className="font-medium">{stats.total_provisions}</span>
                      </div>
                      <div className="flex justify-between mb-1">
                        <span>Chapters:</span>
                        <span className="font-medium">{stats.total_chapters}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Sections:</span>
                        <span className="font-medium">{stats.total_sections}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Chapter Filters */}
                <div className="space-y-2">
                  {Object.entries(chapterInfo).map(([key, chapter]) => (
                    <button
                      key={key}
                      onClick={() => handleChapterFilter(key)}
                      className={clsx(
                        'w-full text-left p-3 rounded-lg border transition-colors duration-200',
                        selectedChapter === key
                          ? 'bg-primary-50 border-primary-200 text-primary-700'
                          : 'bg-white border-neutral-200 hover:bg-neutral-50'
                      )}
                    >
                      <div className="flex items-center space-x-3">
                        <chapter.icon className={clsx('h-5 w-5', chapter.color)} />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm">{chapter.name}</div>
                          <div className="text-xs text-neutral-500 truncate">
                            {chapter.description}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>

                {/* Fundamental Rights Quick Access */}
                <div className="mt-6 pt-6 border-t border-neutral-200">
                  <h4 className="font-medium text-neutral-900 mb-3">Quick Access</h4>
                  <button
                    onClick={() => handleChapterFilter('Chapter IV')}
                    className="w-full p-3 bg-red-50 border border-red-200 rounded-lg text-left hover:bg-red-100 transition-colors duration-200"
                  >
                    <div className="flex items-center space-x-2">
                      <ScaleIcon className="h-5 w-5 text-red-600" />
                      <span className="font-medium text-red-700">Fundamental Rights</span>
                    </div>
                    <p className="text-xs text-red-600 mt-1">
                      Your constitutional rights and freedoms
                    </p>
                  </button>
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3 h-full overflow-hidden">
              <div className="h-full overflow-y-auto space-y-6 pr-2">
                {provisions.length > 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <InformationCircleIcon className="h-5 w-5 text-green-600" />
                      <p className="text-green-800 font-medium">
                        Showing {provisions.length} constitutional provision{provisions.length !== 1 ? 's' : ''}
                        {selectedChapter && ` from ${selectedChapter}`}
                        {searchQuery && ` matching "${searchQuery}"`}
                      </p>
                    </div>
                  </div>
                )}

                {provisions.map((provision) => (
                  <div key={provision.id} className="bg-white rounded-lg border border-neutral-200 shadow-sm">
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                              {provision.chapter}
                            </span>
                            {provision.section && (
                              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-neutral-100 text-neutral-800">
                                Section {provision.section}
                              </span>
                            )}
                          </div>
                          <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                            {provision.title || `Section ${provision.section}`}
                          </h3>
                        </div>
                        
                        <button
                          onClick={() => toggleSection(provision.id.toString())}
                          className="p-2 hover:bg-neutral-100 rounded-lg transition-colors duration-200"
                        >
                          {expandedSections.has(provision.id.toString()) ? (
                            <ChevronDownIcon className="h-5 w-5 text-neutral-500" />
                          ) : (
                            <ChevronRightIcon className="h-5 w-5 text-neutral-500" />
                          )}
                        </button>
                      </div>

                      <div className="bg-neutral-50 rounded-lg p-4">
                        <div className="prose prose-sm max-w-none">
                          <div className="text-neutral-800 leading-relaxed whitespace-pre-line">
                            {expandedSections.has(provision.id.toString()) 
                              ? formatContent(provision.content)
                              : `${formatContent(provision.content).substring(0, 300)}...`
                            }
                          </div>
                        </div>
                      </div>

                      {provision.keywords && provision.keywords.length > 0 && (
                        <div className="mt-4 flex flex-wrap gap-2">
                          {provision.keywords.map((keyword, index) => (
                            <span
                              key={index}
                              className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-neutral-100 text-neutral-700"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {provisions.length === 0 && !isLoading && (
                  <div className="text-center py-16">
                    <BookOpenIcon className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                    <h3 className="text-lg font-medium text-neutral-900 mb-2">No provisions found</h3>
                    <p className="text-neutral-600 mb-6">
                      {searchQuery 
                        ? `No constitutional provisions match "${searchQuery}"`
                        : 'Select a chapter or search to view constitutional provisions'
                      }
                    </p>
                    <button
                      onClick={() => {
                        setSearchQuery('');
                        setSelectedChapter('');
                        loadConstitutionData();
                      }}
                      className="btn-primary"
                    >
                      View All Provisions
                    </button>
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

export default ConstitutionPage;
