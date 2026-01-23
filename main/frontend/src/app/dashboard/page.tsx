'use client';

import React, { useState } from 'react';
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar, Collection } from "@/components/layout/Sidebar";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchFilters } from "@/components/search/SearchFilters";
import { Paper } from "@/types/models";
import { SearchResults } from "@/components/search/SearchResults";
import { Pagination } from "@/components/ui/pagination-custom";
import { SettingsModal } from "@/components/settings/SettingsModal";
import { BookOpen, Sparkles } from 'lucide-react';
import { useUploadStore } from "@/store/upload.store";

import { searchService } from '@/services/search.service';
import { settingsService } from '@/services/settings.service';
import { paperService } from '@/services/paper.service';
import { collectionService } from '@/services/collection.service';
import { toast } from 'sonner';
import { useAuthStore } from '@/store/use-auth-store';
import { logger } from '@/lib/logger';
import { SearchSettings as SearchSettingsType, SystemSettings } from '@/types/settings';

export default function DashboardPage() {
  const [hasSearched, setHasSearched] = useState(false);
  const [searchResults, setSearchResults] = useState<Paper[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  // Upload modal is now controlled globally
  const [isSearching, setIsSearching] = useState(false);
  const [activeCollection, setActiveCollection] = useState<Collection | null>(null);
  const [isAIEnabled, setIsAIEnabled] = useState(false);
  
  // Search Configuration State
  const [searchFilters, setSearchFilters] = useState({
    match_title: true,
    match_author: true,
    match_abstract: true,
    match_source: true,
    enable_web_search: false,
  });

  const [searchSettings, setSearchSettings] = useState<SearchSettingsType>({
    match_analysis_status: 'unprocessed',
    min_date: '',
    max_date: '',
    limit: 10,
  });

  // System Settings State
  const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);

  // Pagination State
  const [page, setPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const openUpload = useUploadStore((s) => s.open);
  const setUploadCollectionId = useUploadStore((s) => s.setCollectionId);
  const lastUploadTime = useUploadStore((s) => s.lastUploadTime);

  const loadCollections = React.useCallback(async () => {
    if (!isAuthenticated) {
        setCollections([]);
        return;
    }
    try {
      const list = await collectionService.getAll();
      const mapped = list.map(c => ({
        id: c.collection_id,
        label: c.name,
        count: c.total || 0
      }));
      setCollections(mapped);
    } catch (error: any) {
      logger.error("Failed to load collections", error, 'DashboardPage');
    }
  }, [isAuthenticated]);

  const loadRecentPapers = React.useCallback(async () => {
    try {
      setIsSearching(true);
      const papers = await paperService.getList(1, 10);
      setSearchResults(papers);
      setHasSearched(true); // Show results
      setHasMore(false); // Recent papers usually just list
    } catch (error: any) {
      logger.error("Failed to load papers", error, 'DashboardPage');
      toast.error(error.message || "加载失败");
    } finally {
      setIsSearching(false);
    }
  }, []);

  const loadCollectionPapers = React.useCallback(async (collectionId: string) => {
    try {
      setIsSearching(true);
      const detail = await collectionService.getById(collectionId);
      // Backend returns { items: [...] } for collection details
      const papers = detail.items ?? [];
      setSearchResults(papers);
      setIsAIEnabled(false);
      setHasSearched(true);
      setHasMore(false); // Collection view usually full list or need pagination impl
    } catch (error: any) {
      logger.error("Failed to load collection papers", error, 'DashboardPage');
      toast.error(error.message || "加载收藏夹论文失败");
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleUploadSuccess = React.useCallback(() => {
    loadCollections();
    if (activeCollection?.id) {
      loadCollectionPapers(activeCollection.id);
    }
  }, [activeCollection?.id, loadCollectionPapers, loadCollections]);

  React.useEffect(() => {
    setUploadCollectionId(activeCollection?.id ?? null);
  }, [activeCollection?.id, setUploadCollectionId]);

  React.useEffect(() => {
    return () => {
      setUploadCollectionId(null);
    };
  }, [setUploadCollectionId]);

  // Listen for upload success
  React.useEffect(() => {
    if (lastUploadTime > 0) {
        handleUploadSuccess();
    }
  }, [handleUploadSuccess, lastUploadTime]);

  const loadSystemSettings = React.useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const settings = await settingsService.getSystemSettings();
      setSystemSettings(settings);
      if (settings.system_colour === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    } catch (error) {
      logger.error("Failed to load system settings", error, 'DashboardPage');
    }
  }, [isAuthenticated]);

  const loadSearchSettings = React.useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const settings = await settingsService.getSearchSettings();
      // Update local state with fetched settings
      setSearchSettings(prev => ({
        ...prev,
        ...settings,
        // Ensure dates are strings if backend returns date objects, though JSON usually handles this
      }));
    } catch (error) {
      logger.error("Failed to load search settings", error, 'DashboardPage');
    }
  }, [isAuthenticated]);

  // Initial load & Auth change
  React.useEffect(() => {
    loadCollections();
    loadSystemSettings();
    loadSearchSettings();
  }, [loadCollections]);

  // Auto-select Default Collection
  React.useEffect(() => {
    if (collections.length > 0 && !activeCollection && !hasSearched) {
      // Find "默认收藏夹" or use the first one
      const defaultCol = collections.find(c => c.label === '默认收藏夹' || c.label.includes('默认')) || collections[0];
      if (defaultCol) {
        setActiveCollection(defaultCol);
        loadCollectionPapers(defaultCol.id);
      }
    }
  }, [collections, activeCollection, hasSearched, loadCollectionPapers]);



  const handleSearch = async (query: string, useAI: boolean) => {
    // If query is empty, fallback to collection view (pure local)
    if (!query || !query.trim()) {
        setCurrentQuery('');
        if (activeCollection) {
            loadCollectionPapers(activeCollection.id);
        } else {
             // Try to find default collection
             const defaultCol = collections.find(c => c.label === '默认收藏夹' || c.label.includes('默认')) || collections[0];
             if (defaultCol) {
                 setActiveCollection(defaultCol);
                 loadCollectionPapers(defaultCol.id);
             } else {
                 toast.info("暂无收藏夹可显示");
             }
        }
        return;
    }

    setIsSearching(true);
    setIsAIEnabled(useAI);
    setCurrentQuery(query);
    setPage(1);
    
    try {
        const response = await searchService.search({
            query,
            page: 1,
            limit: searchSettings.limit,
            // Only pass collection_id filter if we are NOT searching web (external)
            // If enable_web_search is true, we ignore collection context for the search itself
            filters: (!searchFilters.enable_web_search && activeCollection) ? { collection_id: activeCollection.id } : undefined,
            ...searchFilters,
            ...searchSettings
        });
        setHasSearched(true);
        setSearchResults(response.items || []);
        setTotalResults(response.total);
        setHasMore(response.total > response.items.length); // Assuming response.total exists
    } catch (error: any) {
        logger.error("Search failed", error, 'DashboardPage');
        toast.error(error.message || "搜索失败");
    } finally {
        setIsSearching(false);
    }
  };

  const handlePageChange = async (newPage: number) => {
    if (isLoadingMore) return;
    setIsLoadingMore(true);
    
    try {
        const response = await searchService.search({
            query: currentQuery,
            page: newPage,
            limit: searchSettings.limit,
            filters: (!searchFilters.enable_web_search && activeCollection) ? { collection_id: activeCollection.id } : undefined,
            ...searchFilters,
            ...searchSettings
        });
        setSearchResults(response.items);
        setPage(newPage);
        setTotalResults(response.total);
        setHasMore(response.total > response.items.length);
        
        // Scroll to top
        const mainContent = document.getElementById('main-content');
        if (mainContent) mainContent.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error: any) {
        logger.error("Page change failed", error, 'DashboardPage');
        toast.error("加载失败");
    } finally {
        setIsLoadingMore(false);
    }
  };

  const handleToggleBookmark = (paperId: string) => {
    setSearchResults(prev => prev.map(p => 
      p.paper_id === paperId ? { ...p, is_bookmarked: !p.is_bookmarked } : p
    ));
  };

  const handlePaperUpdate = () => {
    loadCollections();
    if (activeCollection) {
      loadCollectionPapers(activeCollection.id);
    } else if (hasSearched && currentQuery) {
      handleSearch(currentQuery, isAIEnabled);
    } else {
        // Fallback to default collection if available
        const defaultCol = collections.find(c => c.label === '默认收藏夹' || c.label.includes('默认')) || collections[0];
        if (defaultCol) {
            setActiveCollection(defaultCol);
            loadCollectionPapers(defaultCol.id);
        }
    }
  };

  const handleCollectionsClick = () => {
    if (collections.length > 0) {
        // Try to find "默认收藏夹" or use the first one
        const defaultCol = collections.find(c => c.label.includes('默认')) || collections[0];
        setActiveCollection(defaultCol);
        loadCollectionPapers(defaultCol.id);
    } else {
        toast.info("暂无收藏夹");
    }
  };

  return (
    <div className="h-screen bg-gray-50 dark:bg-gray-950 flex flex-col overflow-hidden transition-colors duration-300">
      <Navbar 
        onCollectionsClick={handleCollectionsClick}
      />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar 
          onSettingsClick={() => setIsSettingsOpen(true)} 
          onSelectCollection={(collection) => {
             if (collection?.id) {
               setActiveCollection(collection);
               loadCollectionPapers(collection.id);
               return;
             }
             // If collection is null (e.g. deleted), switch to default
             setHasSearched(false);
             const defaultCol = collections.find(c => c.label === '默认收藏夹' || c.label.includes('默认')) || collections[0];
             if (defaultCol) {
                 setActiveCollection(defaultCol);
                 loadCollectionPapers(defaultCol.id);
             } else {
                 setActiveCollection(null);
             }
          }}
          collections={collections}
          activeCollectionId={activeCollection?.id}
          onRefresh={loadCollections}
        />

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto relative p-6 md:p-12 flex flex-col items-center" id="main-content">
          
          {/* Header Status Bar */}
          <div className="w-full max-w-5xl flex justify-end mb-4 min-h-[32px]">
             {activeCollection && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg shadow-sm animate-in fade-in slide-in-from-top-2">
                   <span className="text-xs font-medium text-gray-400 dark:text-gray-500">当前查看</span>
                   <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400">{activeCollection.label}</span>
                </div>
             )}
          </div>

          {/* Top Search Area */}
          <div className={`w-full max-w-5xl flex flex-col items-center transition-all duration-500 ${hasSearched ? 'pt-2 pb-6' : 'pt-16 pb-10'}`}>
            <SearchBar 
              onSearch={handleSearch} 
              settings={searchSettings}
              onSettingsChange={setSearchSettings}
              onSettingsApply={async () => {
                try {
                  await settingsService.updateSearchSettings(searchSettings);
                  toast.success('搜索设置已保存');
                  // Optional: Trigger search immediately on apply if query exists
                  if (currentQuery) {
                    handleSearch(currentQuery, isAIEnabled);
                  }
                } catch (error) {
                  console.error('Failed to save search settings:', error);
                  toast.error('保存设置失败');
                }
              }}
            />
            <SearchFilters 
              className="mt-4" 
              onUploadClick={() => openUpload({ collectionId: activeCollection?.id ?? null })}
              filters={searchFilters}
              onChange={(newFilters) => {
                setSearchFilters(newFilters);
                // Optional: Trigger search immediately on filter change if query exists
                // if (currentQuery) handleSearch(currentQuery, isAIEnabled); // Need to pass updated filters, but handleSearch uses state. 
                // So better to let user click search, OR use useEffect to trigger.
                // For now, let user click search or just rely on manual search trigger.
              }}
            />
          </div>

          {/* Content Area */}
          <div className="flex-1 w-full max-w-5xl flex flex-col pb-10">
            {isSearching ? (
               <div className="flex-1 flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 dark:border-indigo-400 mb-4"></div>
                  <p>
                    {activeCollection ? `正在 ${activeCollection.label} 中检索...` : "正在深度检索..."}
                  </p>
               </div>
            ) : hasSearched ? (
              <>
                <SearchResults 
                  results={searchResults} 
                  onToggleBookmark={handleToggleBookmark} 
                  aiEnabled={isAIEnabled} 
                  collections={collections}
                  onPaperUpdate={handlePaperUpdate}
                />
                <div className="mt-8">
                  <Pagination 
                    currentPage={page}
                    total={totalResults}
                    pageSize={searchSettings.limit}
                    onPageChange={handlePageChange}
                    disabled={isLoadingMore}
                  />
                </div>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-400 dark:text-gray-500 mt-10">
                <div className="w-24 h-24 bg-gray-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-6">
                  {activeCollection ? (
                     <Sparkles className="w-10 h-10 text-indigo-300 dark:text-indigo-400" />
                  ) : (
                     <BookOpen className="w-10 h-10 text-gray-300 dark:text-gray-600" />
                  )}
                </div>
                <h2 className="text-xl font-semibold text-gray-600 dark:text-gray-300 mb-2">
                   {activeCollection ? `在 ${activeCollection.label} 中探索` : "开始探索知识"}
                </h2>
                <p className="max-w-md text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                  {activeCollection 
                    ? "仅搜索当前收藏夹内的论文。切换到全局搜索可查看更多结果。" 
                    : "输入关键词开始搜索，或上传您的 PDF 论文。开启 AI 模式可以获得更深度的见解和关联推荐。"
                  }
                </p>
              </div>
            )}
          </div>
          
        </main>
      </div>

      {/* Settings Modal */}
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
        onSettingsChanged={() => {
          loadSystemSettings();
          loadSearchSettings();
        }}
      />
      
    </div>
  );
}
