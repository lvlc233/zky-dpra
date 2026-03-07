import React, { useState, useRef, useEffect } from 'react';
import { Layer, Annotation, Rect as AnnotationRect } from '@/types/reader';
import { Highlighter, MessageSquare, Languages, X, Check, Trash2, Palette, Edit2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface PDFPageOverlayProps {
  pageIndex: number; // 0-based
  scale: number;
  layers: Layer[];
  activeViewId: string;
  onAddAnnotation?: (annotation: Annotation) => void;
  onUpdateAnnotation?: (annotation: Annotation) => void;
  onDeleteAnnotation?: (annotationId: string) => void;
}

const HIGHLIGHT_COLORS = [
  { name: 'Yellow', value: 'bg-yellow-300', hex: '#fde047' },
  { name: 'Green', value: 'bg-green-300', hex: '#86efac' },
  { name: 'Blue', value: 'bg-blue-300', hex: '#93c5fd' },
  { name: 'Red', value: 'bg-red-300', hex: '#fca5a5' },
  { name: 'Purple', value: 'bg-purple-300', hex: '#d8b4fe' },
];

// Mock Translation Service
const translateTextMock = async (text: string): Promise<string> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(`[译] ${text.substring(0, 100)}${text.length > 100 ? '...' : ''} (这里是模拟的翻译结果，实际应接入后端 API)`);
    }, 800);
  });
};

export const PDFPageOverlay: React.FC<PDFPageOverlayProps> = ({
  pageIndex,
  scale,
  layers,
  activeViewId,
  onAddAnnotation,
  onUpdateAnnotation,
  onDeleteAnnotation
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const editPopupRef = useRef<HTMLDivElement>(null);
  const [selectedRects, setSelectedRects] = useState<AnnotationRect[]>([]);
  const [showToolbar, setShowToolbar] = useState(false);
  const [toolbarPosition, setToolbarPosition] = useState<{ top: number; left: number } | null>(null);
  const [selectedText, setSelectedText] = useState('');

  const [translationModal, setTranslationModal] = useState<{
    isOpen: boolean;
    text: string;
    result: string;
    loading: boolean;
    position: { top: number; left: number } | null;
  }>({
    isOpen: false,
    text: '',
    result: '',
    loading: false,
    position: null
  });

  // State for editing existing annotation
  const [activeAnnotationId, setActiveAnnotationId] = useState<string | null>(null);
  const [editPosition, setEditPosition] = useState<{ top: number; left: number } | null>(null);
  const [noteContent, setNoteContent] = useState('');
  const [translationResult, setTranslationResult] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  
  // Draft annotation state (not yet saved to backend)
  const [draftAnnotation, setDraftAnnotation] = useState<Annotation | null>(null);

  // Filter visible layers and their annotations for this page
  const visibleAnnotations = layers
    .filter(l => l.visible)
    .flatMap(l => l.annotations.map(a => ({ ...a, layerColor: l.color })))
    .filter(a => (a.rects || []).some(r => Number(r.pageIndex) === pageIndex));

  // Handle click outside to close popup
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (activeAnnotationId) {
        // If popup is not rendered (ref is null) but we think we are editing, 
        // it means the annotation is not found in layers (ghost state).
        // We should clear active state to unblock user.
        if (!editPopupRef.current) {
             setActiveAnnotationId(null);
        } else if (!editPopupRef.current.contains(event.target as Node)) {
            // Clicked outside the popup
            setActiveAnnotationId(null);
        }
      }
    };

    if (activeAnnotationId) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [activeAnnotationId]);

  const handleDelete = React.useCallback(() => {
    if (!activeAnnotationId) return;
    
    // If it's a draft, just clear it
    if (draftAnnotation && draftAnnotation.annotation_id === activeAnnotationId) {
        setDraftAnnotation(null);
        setActiveAnnotationId(null);
        return;
    }

    if (onDeleteAnnotation) {
      onDeleteAnnotation(activeAnnotationId);
    }
    setActiveAnnotationId(null);
  }, [activeAnnotationId, draftAnnotation, onDeleteAnnotation]);

  // Handle Delete Key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!activeAnnotationId) return;
      
      if (e.key === 'Delete' || (e.key === 'Backspace' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName))) {
        handleDelete();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeAnnotationId, handleDelete]);


  // Handle Text Selection
  useEffect(() => {
    const handleSelection = () => {
      // If we are editing an annotation, don't trigger new selection logic easily
      if (activeAnnotationId) return;

      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
        setShowToolbar(false);
        return;
      }

      const range = selection.getRangeAt(0);
      const container = containerRef.current;
      
      if (!container || !container.parentElement?.contains(range.commonAncestorContainer)) {
        return;
      }

      const text = selection.toString();
      setSelectedText(text);

      // We are inside this page
      const pageRect = container.getBoundingClientRect();
      const clientRects = range.getClientRects();
      
      const newRects: AnnotationRect[] = [];
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

      for (let i = 0; i < clientRects.length; i++) {
        const rect = clientRects[i];
        
        // Convert to percentage relative to page
        const x = ((rect.left - pageRect.left) / pageRect.width) * 100;
        const y = ((rect.top - pageRect.top) / pageRect.height) * 100;
        const width = (rect.width / pageRect.width) * 100;
        const height = (rect.height / pageRect.height) * 100;

        newRects.push({ x, y, width, height, pageIndex });

        // Update bounds for toolbar position
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x + width);
        maxY = Math.max(maxY, y + height);
      }

      if (newRects.length > 0) {
        setSelectedRects(newRects);
        setToolbarPosition({
          top: minY, 
          left: (minX + maxX) / 2
        });
        setShowToolbar(true);
      }
    };

    document.addEventListener('mouseup', handleSelection);
    return () => {
      document.removeEventListener('mouseup', handleSelection);
    };
  }, [pageIndex, activeAnnotationId]);

  const handleCreateAnnotation = async (type: 'highlight' | 'note' | 'translate', color?: string) => {
    if (selectedRects.length === 0) return;

    // Special handling for Translation: Transient Mode
    if (type === 'translate') {
      // Calculate position (reusing toolbar or similar logic)
      let pos = toolbarPosition;
      if (!pos) {
         // Fallback center
         pos = { top: 50, left: 50 };
      }

      setTranslationModal({
        isOpen: true,
        text: selectedText,
        result: '',
        loading: true,
        position: { top: pos.top + 5, left: pos.left }
      });
      
      // Clear selection UI
      setShowToolbar(false);
      window.getSelection()?.removeAllRanges();

      // Fetch translation
      try {
        const translated = await translateTextMock(selectedText);
        setTranslationModal(prev => ({ ...prev, result: translated, loading: false }));
      } catch (e) {
        setTranslationModal(prev => ({ ...prev, result: '翻译失败', loading: false }));
      }
      return;
    }

    if (!onAddAnnotation) return;

    let content = '';
    // Use crypto.randomUUID() if available, otherwise use a random UUID generator
    const generateUUID = () => {
        if (typeof crypto !== 'undefined' && crypto.randomUUID) {
            return crypto.randomUUID();
        }
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    };
     const newId = generateUUID();
     
     // Determine initial content
     if (type === 'note') {
       content = '';
       setNoteContent('');
     }
 
     const newAnnotation: Annotation = {
       annotation_id: newId,
       type,
       rects: selectedRects,
       createdAt: Date.now(),
       content,
       color: color || 'bg-yellow-300'
     };
 
     // If it's a note, enter draft mode first (don't save yet)
     if (type === 'note') {
        setDraftAnnotation(newAnnotation);
     } else {
        // For highlights/others, save immediately
        onAddAnnotation(newAnnotation);
     }
     
     // Clear selection UI but keep internal state for popup positioning
    window.getSelection()?.removeAllRanges();
    setShowToolbar(false);

    // Calculate position for the popup immediately
    if (toolbarPosition) {
       // We can adjust slightly
       setEditPosition({
         top: toolbarPosition.top + 5, // Slightly lower than toolbar was
         left: toolbarPosition.left
       });
    }

    // Auto-open logic
    if (type === 'note') {
      setActiveAnnotationId(newId);
    }
  };

  const handleAnnotationClick = (e: React.MouseEvent, annotation: Annotation) => {
    e.stopPropagation();
    e.preventDefault();
    
    setActiveAnnotationId(annotation.annotation_id);
    setNoteContent(annotation.content || '');
    setTranslationResult(annotation.type === 'translate' ? (annotation.content || '') : '');
    
    // Position popup near the first rect of the annotation on this page
    const firstRect = annotation.rects.find(r => Number(r.pageIndex) === pageIndex);
    if (firstRect) {
      setEditPosition({
        top: firstRect.y + firstRect.height,
        left: firstRect.x + firstRect.width / 2
      });
    }
  };

  const handleUpdateColor = (color: string) => {
    if (!activeAnnotationId || !onUpdateAnnotation) return;
    const annotation = visibleAnnotations.find(a => a.annotation_id === activeAnnotationId);
    if (annotation) {
      onUpdateAnnotation({ ...annotation, color });
    }
  };

  const handleSaveNote = () => {
    if (!activeAnnotationId) return;

    // Check if we are saving a draft
    if (draftAnnotation && draftAnnotation.annotation_id === activeAnnotationId) {
        if (onAddAnnotation) {
             onAddAnnotation({ ...draftAnnotation, content: noteContent });
        }
        setDraftAnnotation(null);
        setActiveAnnotationId(null);
        return;
    }

    if (!onUpdateAnnotation) return;
    const annotation = visibleAnnotations.find(a => a.annotation_id === activeAnnotationId);
    if (annotation) {
      onUpdateAnnotation({ ...annotation, content: noteContent });
      setActiveAnnotationId(null);
    }
  };

  const handleSaveTranslationAsNote = () => {
     if (!onAddAnnotation) return;
     
     const generateUUID = () => {
        if (typeof crypto !== 'undefined' && crypto.randomUUID) {
            return crypto.randomUUID();
        }
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    };
     const newId = generateUUID();
     const newAnnotation: Annotation = {
        annotation_id: newId,
        type: 'note', // Save as Note for better editability and tooltip support
        rects: selectedRects, 
        createdAt: Date.now(),
        content: `[原文] ${translationModal.text}\n\n[译文] ${translationModal.result}`,
        color: 'bg-green-300' // Green color to distinguish translation notes
      };
      
      onAddAnnotation(newAnnotation);
      setTranslationModal(prev => ({ ...prev, isOpen: false }));
  };



  const activeAnnotation = visibleAnnotations.find(a => a.annotation_id === activeAnnotationId) 
    || (draftAnnotation?.annotation_id === activeAnnotationId ? draftAnnotation : undefined);

  // Combine visibleAnnotations with draftAnnotation for rendering
  const allAnnotationsToRender = [...visibleAnnotations];
  if (draftAnnotation && !visibleAnnotations.some(a => a.annotation_id === draftAnnotation.annotation_id)) {
     allAnnotationsToRender.push(draftAnnotation);
  }

  return (
    <TooltipProvider delayDuration={100}>
      <div ref={containerRef} className="absolute inset-0 z-[100] pointer-events-none">
        {/* Existing Annotations */}
        {allAnnotationsToRender.map(annotation => (
          <React.Fragment key={annotation.annotation_id}>
            {annotation.rects.filter(r => r.pageIndex === pageIndex).map((rect, idx) => {
              const annotationElement = (
                <div
                  key={`${annotation.annotation_id}-${idx}`}
                  className={cn(
                    "absolute transition-all mix-blend-multiply cursor-pointer pointer-events-auto rounded-[2px]",
                    annotation.color || annotation.layerColor || "bg-yellow-300",
                    activeAnnotationId === annotation.annotation_id && "ring-2 ring-indigo-500 ring-offset-1 z-10",
                    annotation.type === 'note' && "border-b-[3px] border-red-500 border-dashed !bg-transparent rounded-none", // Notes keep underline style
                    annotation.type === 'translate' && "border-b-2 border-green-500 border-dashed !bg-transparent rounded-none"
                  )}
                  title="点击编辑或删除"
                  style={{
                    left: `${rect.x}%`,
                    top: `${rect.y}%`,
                    width: `${rect.width}%`,
                    height: `${rect.height}%`,
                    opacity: 0.4
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveAnnotationId(annotation.annotation_id);
                    setNoteContent(annotation.content || '');
                    setTranslationResult(annotation.type === 'translate' ? (annotation.content || '') : '');
                    setEditPosition({
                      top: rect.y + rect.height,
                      left: rect.x + rect.width / 2
                    });
                  }}
                />
              );

              // Wrap notes (and legacy translations) with Tooltip
              if ((annotation.type === 'note' || annotation.type === 'translate') && annotation.content && !activeAnnotationId) {
                return (
                  <Tooltip key={`${annotation.annotation_id}-${idx}`}>
                    <TooltipTrigger asChild>
                      {annotationElement}
                    </TooltipTrigger>
                    <TooltipContent 
                      side="top" 
                      align="center"
                      className="max-w-[280px] break-words"
                    >
                       <div className="flex justify-between items-center gap-2 mb-1 pb-1 border-b border-gray-100 dark:border-slate-700">
                        <div className="flex items-center gap-1">
                          {annotation.type === 'translate' || (annotation.content && annotation.content.includes('[译文]')) ? (
                             <Languages className="w-3 h-3 text-green-500" />
                          ) : (
                             <MessageSquare className="w-3 h-3 text-indigo-500" />
                          )}
                          <span className="text-[10px] font-semibold text-gray-500 uppercase">
                            {annotation.type === 'translate' || (annotation.content && annotation.content.includes('[译文]')) ? '翻译' : '备注'}
                          </span>
                        </div>
                        <button 
                          className="p-1 hover:bg-red-100 dark:hover:bg-red-900/40 text-gray-400 hover:text-red-500 rounded transition-colors"
                          title="删除备注"
                          onClick={(e) => {
                             e.stopPropagation();
                             onDeleteAnnotation?.(annotation.annotation_id);
                          }}
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                      <div className="text-sm">
                        {annotation.content}
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              }

              return annotationElement;
            })}
          </React.Fragment>
        ))}

        {/* Creation Toolbar */}
      {showToolbar && toolbarPosition && !activeAnnotationId && (
        <div 
          className="absolute z-50 pointer-events-auto flex items-center gap-2 bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-200 p-2 rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.15)] border border-gray-100 dark:border-slate-700 transform -translate-x-1/2 -translate-y-full"
          style={{
            left: `${toolbarPosition.left}%`,
            top: `${toolbarPosition.top}%`,
            marginTop: '-12px'
          }}
        >
          {/* Color Picker for immediate highlight */}
          <div className="flex gap-1.5 mr-1">
             {HIGHLIGHT_COLORS.map(c => (
               <button
                 key={c.name}
                 onClick={(e) => { e.stopPropagation(); handleCreateAnnotation('highlight', c.value); }}
                 className={cn("w-5 h-5 rounded-full border border-gray-200 dark:border-slate-600 hover:scale-110 hover:shadow-sm transition-all", c.value)}
                 title={`高亮 ${c.name}`}
               />
             ))}
          </div>
          <div className="w-[1px] h-5 bg-gray-200 dark:bg-slate-700 mx-1" />
          
          <button 
            onClick={(e) => { e.stopPropagation(); handleCreateAnnotation('note'); }}
            className="flex items-center gap-1 px-2 py-1 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-md transition-colors text-xs font-medium"
            title="添加备注"
          >
            <MessageSquare className="w-4 h-4" />
          </button>
          
          <button 
            onClick={(e) => { e.stopPropagation(); handleCreateAnnotation('translate'); }}
            className="flex items-center gap-1 px-2 py-1 hover:bg-green-50 dark:hover:bg-green-900/30 text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 rounded-md transition-colors text-xs font-medium"
            title="翻译选中内容"
          >
            <Languages className="w-4 h-4" />
          </button>
          
          <div className="w-[1px] h-5 bg-gray-200 dark:bg-slate-700 mx-1" />
          
          <button 
            onClick={() => { setShowToolbar(false); window.getSelection()?.removeAllRanges(); }}
            className="p-1 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-md transition-colors text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Edit/View Popup */}
      {activeAnnotationId && activeAnnotation && editPosition && (
        <div 
          ref={editPopupRef}
          className="absolute z-50 pointer-events-auto bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 p-3 rounded-lg shadow-xl border border-gray-200 dark:border-slate-700 w-64 transform -translate-x-1/2"
          style={{
            left: `${editPosition.left}%`,
            top: `${editPosition.top}%`,
            marginTop: '8px'
          }}
        >
          {/* Header */}
          <div className="flex justify-between items-center mb-2 pb-2 border-b border-gray-100 dark:border-slate-700">
            <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
              {activeAnnotation.type === 'highlight' ? '高亮样式' : 
               activeAnnotation.type === 'note' ? '备注内容' : '翻译结果'}
            </span>
            <div className="flex gap-1">
               <button 
                 onClick={handleDelete}
                 className="flex items-center gap-1 px-2 py-1 bg-red-100 dark:bg-red-900/40 hover:bg-red-200 dark:hover:bg-red-900/60 text-red-700 dark:text-red-300 rounded-md transition-colors text-xs font-medium border border-red-200 dark:border-red-800 shadow-sm"
                 title="删除此标记 (Delete)"
               >
                 <Trash2 className="w-3 h-3" />
                 <span>删除</span>
               </button>
               <button 
                 onClick={() => setActiveAnnotationId(null)}
                 className="p-1 hover:bg-gray-100 dark:hover:bg-slate-700 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded transition-colors"
               >
                 <X className="w-3.5 h-3.5" />
               </button>
            </div>
          </div>

          {/* Content */}
          {activeAnnotation.type === 'highlight' && (
            <div className="flex justify-center gap-2 p-1">
              {HIGHLIGHT_COLORS.map(c => (
                <button
                  key={c.name}
                  onClick={() => handleUpdateColor(c.value)}
                  className={cn(
                    "w-6 h-6 rounded-full border-2 transition-transform hover:scale-110", 
                    c.value,
                    activeAnnotation.color === c.value ? "border-gray-900 dark:border-gray-100" : "border-transparent"
                  )}
                  title={c.name}
                />
              ))}
            </div>
          )}

          {activeAnnotation.type === 'note' && (
            <div className="space-y-2">
              <textarea
                autoFocus
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSaveNote();
                  }
                }}
                className="w-full text-sm p-2 border border-gray-200 dark:border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 min-h-[80px] bg-gray-50 dark:bg-slate-900 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500"
                placeholder="输入备注... (按 Enter 保存)"
              />
              <button
                onClick={handleSaveNote}
                className="w-full flex items-center justify-center gap-1 bg-indigo-600 text-white py-1.5 rounded-md text-xs font-medium hover:bg-indigo-700"
              >
                <Check className="w-3 h-3" />
                保存备注
              </button>
            </div>
          )}

          {activeAnnotation.type === 'translate' && (
            <div className="space-y-2">
              <div className="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-slate-900 p-3 rounded-md min-h-[60px] max-h-[200px] overflow-y-auto leading-relaxed border border-gray-100 dark:border-slate-700">
                {isTranslating ? (
                  <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 py-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="font-medium">正在翻译中...</span>
                  </div>
                ) : (
                  translationResult || '暂无翻译结果'
                )}
              </div>
            </div>
          )}
        </div>
      )}
      {/* Translation Modal (Transient) */}
      {translationModal.isOpen && translationModal.position && (
         <div 
           className="absolute z-50 pointer-events-auto bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 p-0 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-gray-100 dark:border-slate-700 w-72 transform -translate-x-1/2"
           style={{
             left: `${translationModal.position.left}%`,
             top: `${translationModal.position.top}%`,
             marginTop: '12px'
           }}
           onClick={(e) => e.stopPropagation()}
         >
           {/* Header */}
           <div className="flex justify-between items-center px-4 py-3 border-b border-gray-100 dark:border-slate-700 bg-gray-50/50 dark:bg-slate-900/50 rounded-t-xl">
             <div className="flex items-center gap-2">
               <Languages className="w-4 h-4 text-indigo-500 dark:text-indigo-400" />
               <span className="text-sm font-semibold text-gray-700 dark:text-gray-200">翻译助手</span>
             </div>
             <button 
               onClick={() => setTranslationModal(prev => ({ ...prev, isOpen: false }))}
               className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
             >
               <X className="w-4 h-4" />
             </button>
           </div>
           
           {/* Body */}
           <div className="p-4 space-y-4">
             {/* Source */}
             <div className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 italic border-l-2 border-gray-200 dark:border-slate-600 pl-2">
               {translationModal.text}
             </div>
             
             {/* Result */}
             <div className="min-h-[80px]">
               {translationModal.loading ? (
                  <div className="flex flex-col items-center justify-center h-full gap-2 text-indigo-500 dark:text-indigo-400 py-4">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-xs font-medium">正在翻译...</span>
                  </div>
               ) : (
                  <div className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed font-medium">
                    {translationModal.result}
                  </div>
               )}
             </div>
           </div>
           
           {/* Footer */}
           <div className="px-4 py-3 border-t border-gray-100 dark:border-slate-700 flex gap-2">
             <button
               onClick={handleSaveTranslationAsNote}
               disabled={translationModal.loading}
               className="flex-1 flex items-center justify-center gap-1.5 bg-indigo-600 text-white py-1.5 rounded-lg text-xs font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
             >
               <MessageSquare className="w-3.5 h-3.5" />
               保存为备注
             </button>
           </div>
         </div>
      )}
    </div>
    </TooltipProvider>
  );
};
