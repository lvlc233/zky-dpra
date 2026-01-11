'use client';

import React, { useState } from 'react';
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar, Collection } from "@/components/layout/Sidebar";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchFilters } from "@/components/search/SearchFilters";
import { SearchResults, Paper } from "@/components/search/SearchResults";
import { SettingsModal } from "@/components/settings/SettingsModal";
import { UploadModal } from "@/components/upload/UploadModal";
import { BookOpen, Sparkles } from 'lucide-react';

export default function DashboardPage() {
  const [hasSearched, setHasSearched] = useState(false);
  const [searchResults, setSearchResults] = useState<Paper[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [activeCollection, setActiveCollection] = useState<Collection | null>(null);
  const [isAIEnabled, setIsAIEnabled] = useState(false);

  const handleSearch = (query: string, useAI: boolean) => {
    setIsSearching(true);
    setIsAIEnabled(useAI);
    
    // Simulate API call
    setTimeout(() => {
      setHasSearched(true);
      const mockResults: Paper[] = [
        {
          id: '1',
          title: 'Attention Is All You Need',
          authors: ['Ashish Vaswani', 'Noam Shazeer', 'Niki Parmar', 'Jakob Uszkoreit', 'Llion Jones', 'Aidan N. Gomez', 'Lukasz Kaiser', 'Illia Polosukhin'],
          year: 2017,
          source: 'NeurIPS',
          abstract: 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.',
          citations: 85000,
          isBookmarked: true
        },
        {
          id: '2',
          title: 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
          authors: ['Jacob Devlin', 'Ming-Wei Chang', 'Kenton Lee', 'Kristina Toutanova'],
          year: 2018,
          source: 'NAACL',
          abstract: 'We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.',
          citations: 62000,
          isBookmarked: false
        },
        {
          id: '3',
          title: 'GPT-3: Language Models are Few-Shot Learners',
          authors: ['Tom B. Brown', 'Benjamin Mann', 'Nick Ryder', 'Melanie Subbiah', 'Jared D. Kaplan', 'Prafulla Dhariwal', 'Arvind Neelakantan'],
          year: 2020,
          source: 'NeurIPS',
          abstract: 'Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task. While typically task-agnostic in architecture, this method still requires task-specific fine-tuning datasets of thousands or tens of thousands of examples. By contrast, humans can generally perform a new language task from only a few examples or from simple instructions.',
          citations: 18000,
          isBookmarked: false
        },
        {
          id: '4',
          title: 'Deep Residual Learning for Image Recognition',
          authors: ['Kaiming He', 'Xiangyu Zhang', 'Shaoqing Ren', 'Jian Sun'],
          year: 2016,
          source: 'CVPR',
          abstract: 'Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.',
          citations: 150000,
          isBookmarked: true
        }
      ];

      // Simulate filtering by collection
      let filtered = mockResults;
      if (activeCollection) {
        console.log(`Searching within collection: ${activeCollection.label}`);
        filtered = mockResults.slice(0, 2); 
      }
      
      // Simulate AI Enhancement
      if (useAI) {
         console.log("AI Search Enabled");
         filtered = filtered.map(p => ({
           ...p,
           aiScore: Math.floor(Math.random() * (99 - 85) + 85),
           aiReason: p.id === '1' ? "作为 Transformer 架构的开山之作，与您的研究方向「深度学习基础」高度相关。" :
                     p.id === '2' ? "BERT 模型在 NLP 领域的预训练范式对您的项目具有重要的参考价值。" :
                     "该论文提出了核心算法改进，在相关基准测试中表现优异，值得深入阅读。"
         }));
      }

      setSearchResults(filtered);
      setIsSearching(false);
    }, 1000);
  };

  const handleToggleBookmark = (id: string) => {
    setSearchResults(prev => prev.map(p => 
      p.id === id ? { ...p, isBookmarked: !p.isBookmarked } : p
    ));
  };

  return (
    <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
      <Navbar />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar 
          onSettingsClick={() => setIsSettingsOpen(true)} 
          onSelectCollection={(collection) => {
             setActiveCollection(collection);
             // Optional: reset search or auto-search when switching collections
             setHasSearched(false); 
          }}
        />

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto relative p-6 md:p-12 flex flex-col items-center">
          
          {/* Header Status Bar */}
          <div className="w-full max-w-5xl flex justify-end mb-4 min-h-[32px]">
             {activeCollection && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-200 rounded-lg shadow-sm animate-in fade-in slide-in-from-top-2">
                   <span className="text-xs font-medium text-gray-400">当前查看</span>
                   <span className="text-sm font-semibold text-indigo-600">{activeCollection.label}</span>
                </div>
             )}
          </div>

          {/* Top Search Area */}
          <div className={`w-full max-w-5xl flex flex-col items-center transition-all duration-500 ${hasSearched ? 'pt-2 pb-6' : 'pt-16 pb-10'}`}>
            <SearchBar onSearch={handleSearch} />
            <SearchFilters 
              className="mt-4" 
              onUploadClick={() => setIsUploadOpen(true)} 
            />
          </div>

          {/* Content Area */}
          <div className="flex-1 w-full max-w-5xl flex flex-col">
            {isSearching ? (
               <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-4"></div>
                  <p>
                    {activeCollection ? `正在 ${activeCollection.label} 中检索...` : "正在深度检索..."}
                  </p>
               </div>
            ) : hasSearched ? (
              <SearchResults results={searchResults} onToggleBookmark={handleToggleBookmark} aiEnabled={isAIEnabled} />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-400 mt-10">
                <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                  {activeCollection ? (
                     <Sparkles className="w-10 h-10 text-indigo-300" />
                  ) : (
                     <BookOpen className="w-10 h-10 text-gray-300" />
                  )}
                </div>
                <h2 className="text-xl font-semibold text-gray-600 mb-2">
                   {activeCollection ? `在 ${activeCollection.label} 中探索` : "开始探索知识"}
                </h2>
                <p className="max-w-md text-sm text-gray-500 leading-relaxed">
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
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      
      {/* Upload Modal */}
      <UploadModal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} />
    </div>
  );
}
