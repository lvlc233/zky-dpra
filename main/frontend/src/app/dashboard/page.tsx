'use client';

import React, { useState } from 'react';
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar, Collection } from "@/components/layout/Sidebar";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchFilters } from "@/components/search/SearchFilters";
import { Paper } from "@/types/models";
import { SearchResults } from "@/components/search/SearchResults";
import { SettingsModal } from "@/components/settings/SettingsModal";
import { UploadModal } from "@/components/upload/UploadModal";
import { BookOpen, Sparkles, Loader2 } from 'lucide-react';
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
    match_summary: true,
    match_full_text: true,
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
        collection_id: c.collection_id,
        label: c.name,
        count: c.count || 0
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
      const papers = (detail as any)?.papers ?? [];
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
    if (activeCollection?.collection_id) {
      loadCollectionPapers(activeCollection.collection_id);
      return;
    }
    loadRecentPapers();
  }, [activeCollection?.collection_id, loadCollectionPapers, loadRecentPapers]);

  React.useEffect(() => {
    setUploadCollectionId(activeCollection?.collection_id ?? null);
  }, [activeCollection?.collection_id, setUploadCollectionId]);

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
    
    // Inject Mock Data for detail page testing
    const MOCK_DATA: Paper = {
        paper_id: 'mock-id-001',
        title: 'DeepPaper: A Deep Learning Approach for Academic Paper Research',
        url: 'https://arxiv.org/pdf/2601.14047',
        file_url: 'https://arxiv.org/pdf/2601.14047',
        authors: ['Frontend Agent', 'User'],
        summary: '这是一个用于测试详情页面的模拟数据。点击此处进入详情页面查看效果。',
        published_at: '2026-01-21',
        source: 'Mock System',
        tags: ['Mock', 'Test', 'Agent'],
        status: 'success'
    } as any;

    setSearchResults([MOCK_DATA]);
    setHasSearched(true);
  }, [loadCollections]);


  const handleSearch = async (query: string, useAI: boolean) => {
    if (!query || !query.trim()) {
        toast.error("请输入搜索内容");
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
            filters: activeCollection ? { collection_id: activeCollection.id } : undefined,
            ...searchFilters,
            ...searchSettings
        });
        setHasSearched(true);
        setSearchResults(response.items || []);
        setHasMore(response.total > response.items.length); // Assuming response.total exists
    } catch (error: any) {
        logger.error("Search failed", error, 'DashboardPage');
        toast.error(error.message || "搜索失败");
    } finally {
        setIsSearching(false);
    }
  };

  const handleLoadMore = async () => {
    if (isLoadingMore || !hasMore) return;
    setIsLoadingMore(true);
    const nextPage = page + 1;
    
    try {
        const response = await searchService.search({
            query: currentQuery,
            page: nextPage,
            limit: searchSettings.limit,
            filters: activeCollection ? { collection_id: activeCollection.id } : undefined,
            ...searchFilters,
            ...searchSettings
        });
        setSearchResults(prev => [...prev, ...response.items]);
        setPage(nextPage);
        setHasMore(searchResults.length + response.items.length < response.total);
    } catch (error: any) {
        logger.error("Load more failed", error, 'DashboardPage');
        toast.error("加载更多失败");
    } finally {
        setIsLoadingMore(false);
    }
  };

  const handleToggleBookmark = (id: string) => {
    setSearchResults(prev => prev.map(p => 
      p.id === id ? { ...p, is_bookmarked: !p.is_bookmarked } : p
    ));
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
             setActiveCollection(collection);
             if (collection?.id) {
               loadCollectionPapers(collection.id);
               return;
             }
             setHasSearched(false);
             loadRecentPapers();
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
              onSettingsApply={() => {
                // Optional: Trigger search immediately on apply if query exists
                if (currentQuery) {
                  handleSearch(currentQuery, isAIEnabled);
                }
              }}
            />
            <SearchFilters 
              className="mt-4" 
              onUploadClick={() => openUpload({ collectionId: activeCollection?.collection_id ?? null })}
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
                <SearchResults results={searchResults} onToggleBookmark={handleToggleBookmark} aiEnabled={isAIEnabled} />
                {hasMore && (
                  <div className="mt-8 flex justify-center">
                    <button 
                      onClick={handleLoadMore}
                      disabled={isLoadingMore}
                      className="flex items-center gap-2 px-6 py-2.5 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-gray-300 font-medium rounded-full shadow-sm hover:bg-gray-50 dark:hover:bg-slate-700 hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoadingMore && <Loader2 className="w-4 h-4 animate-spin" />}
                      {isLoadingMore ? '加载中...' : '加载更多'}
                    </button>
                  </div>
                )}
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
