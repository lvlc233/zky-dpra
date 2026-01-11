'use client';

import React, { useState } from 'react';
import { ReaderNavbar } from '@/components/reader/ReaderNavbar';
import { ReaderSidebar } from '@/components/reader/ReaderSidebar';
import { ReaderRightPanel } from '@/components/reader/ReaderRightPanel';
import { PDFViewer } from '@/components/reader/PDFViewer';
import { Layer, Annotation } from '@/types/reader';

interface ReaderPageProps {
  params: {
    id: string;
  };
}

export default function ReaderPage({ params }: ReaderPageProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  
  // Layers State
  const [layers, setLayers] = useState<Layer[]>([
    { id: 'system-base', name: '原文 (Base)', type: 'system', visible: true, annotations: [], color: 'bg-gray-500' },
    { id: 'user-notes', name: '我的笔记', type: 'user', visible: true, annotations: [], color: 'bg-yellow-500' },
  ]);
  const [activeLayerId, setActiveLayerId] = useState<string>('user-notes');

  // Layer Handlers
  const handleAddLayer = () => {
    const newLayer: Layer = {
      id: Date.now().toString(),
      name: `新视图 ${layers.length}`,
      type: 'user',
      visible: true,
      annotations: [],
      color: 'bg-green-500'
    };
    setLayers([...layers, newLayer]);
    setActiveLayerId(newLayer.id);
  };

  const handleDeleteLayer = (id: string) => {
    setLayers(layers.filter(l => l.id !== id));
    if (activeLayerId === id) {
      setActiveLayerId('system-base');
    }
  };

  const handleToggleLayerVisibility = (id: string) => {
    setLayers(layers.map(l => l.id === id ? { ...l, visible: !l.visible } : l));
  };

  const handleSetActiveLayer = (id: string) => {
    setActiveLayerId(id);
  };

  const handleAddAnnotation = (annotation: Annotation) => {
    setLayers(layers.map(l => {
      if (l.id === activeLayerId) {
        return { ...l, annotations: [...l.annotations, annotation] };
      }
      return l;
    }));
  };

  const handleUpdateAnnotation = (annotation: Annotation) => {
    setLayers(layers.map(l => {
      // Find which layer contains this annotation
      if (l.annotations.some(a => a.id === annotation.id)) {
        return {
          ...l,
          annotations: l.annotations.map(a => a.id === annotation.id ? annotation : a)
        };
      }
      return l;
    }));
  };

  const handleDeleteAnnotation = (annotationId: string) => {
    setLayers(layers.map(l => ({
      ...l,
      annotations: l.annotations.filter(a => a.id !== annotationId)
    })));
  };
  
  // Mock data - In real app, fetch by params.id
  // Using a sample PDF for demonstration
  const pdfUrl = "https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf"; 

  return (
    <div className="h-screen w-full flex flex-col bg-white overflow-hidden">
      {/* 1. Top Navbar */}
      <ReaderNavbar 
        title={`Paper ID: ${params.id} - Trace-based Just-in-Time Type Specialization for Dynamic Languages`}
        isBookmarked={true}
        onViewManage={() => console.log('View Manage')}
        onSearch={setSearchQuery}
      />

      {/* 2. Main Workspace (Flex Row) */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* Left Sidebar (Outline/Views) */}
        <ReaderSidebar 
          isCollapsed={isSidebarCollapsed} 
          className="flex-shrink-0 z-20"
          onNavigate={setCurrentPage}
          // Layer Props
          layers={layers}
          activeLayerId={activeLayerId}
          onAddLayer={handleAddLayer}
          onDeleteLayer={handleDeleteLayer}
          onToggleLayerVisibility={handleToggleLayerVisibility}
          onSetActiveLayer={handleSetActiveLayer}
        />

        {/* Center Main Content (PDF) */}
        <main className="flex-1 flex flex-col relative min-w-0">
          <PDFViewer 
            url={pdfUrl} 
            className="w-full h-full"
            initialPage={currentPage}
            onPageChange={setCurrentPage}
            searchQuery={searchQuery}
            // Layer Props
            layers={layers}
            activeLayerId={activeLayerId}
            onAddAnnotation={handleAddAnnotation}
            onUpdateAnnotation={handleUpdateAnnotation}
            onDeleteAnnotation={handleDeleteAnnotation}
          />
        </main>

        {/* Right Sidebar (AI Assistant/Tabs) */}
        <ReaderRightPanel 
          className="flex-shrink-0 z-20 shadow-xl"
        />
        
      </div>
    </div>
  );
}
