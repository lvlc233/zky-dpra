import React, { useState, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Plus, 
  Trash2, 
  Edit2, 
  ChevronUp, 
  ChevronDown, 
  Eye, 
  EyeOff
} from 'lucide-react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import { readerService } from '@/services/reader.service';
import { NoteMeta } from '@/types/models';
import { toast } from 'sonner';

interface NotesTabProps {
  paperId: string;
}

export const NotesTab: React.FC<NotesTabProps> = ({ paperId }) => {
  const [notes, setNotes] = useState<NoteMeta[]>([]);
  const [loading, setLoading] = useState(false);
  const [newNote, setNewNote] = useState('');
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);

  // Load notes on mount
  useEffect(() => {
    if (!paperId) return;
    loadNotes();
  }, [paperId]);

  const loadNotes = async () => {
    try {
      setLoading(true);
      const res = await readerService.getNotes(paperId);
      // Sort by created_at desc
      const sorted = (res.items || []).sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setNotes(sorted);
    } catch (e) {
      console.error("Failed to load notes", e);
      toast.error("加载笔记失败");
    } finally {
      setLoading(false);
    }
  };

  const handleAddOrUpdateNote = async () => {
    if (!newNote.trim()) return;
    
    if (editingNoteId) {
        // Update Logic
        try {
            const updated = await readerService.updateNote(paperId, editingNoteId, {
                content: newNote
            });
            
            // Update list
            setNotes(notes.map(n => n.id === editingNoteId ? {
                ...n,
                content: updated.content,
                // updated_at could be updated if interface supports it
            } : n));
            
            setNewNote('');
            setEditingNoteId(null);
            setIsPreviewMode(false);
            toast.success("笔记更新成功");
        } catch (e) {
            console.error("Failed to update note", e);
            toast.error("更新笔记失败");
        }
        return;
    }

    // Create Logic
    try {
      const created = await readerService.createNote(paperId, {
        title: "笔记", // Default title
        content: newNote,
        page: 1 // TODO: Get current page from context if possible, or leave undefined
      });
      
      // Add to list (optimistic or re-fetch)
      // Since created returns NoteResponse which matches NoteMeta structure (mostly)
      // We'll re-fetch to be safe or construct logic
      const newNoteItem: NoteMeta = {
        id: created.id,
        title: created.title || "笔记",
        page: created.page,
        created_at: created.created_at,
        content: created.content
      };
      
      setNotes([newNoteItem, ...notes]);
      setNewNote('');
      setIsPreviewMode(false);
      toast.success("笔记添加成功");
    } catch (e) {
      console.error("Failed to add note", e);
      toast.error("添加笔记失败");
    }
  };

  const startEdit = (note: NoteMeta) => {
    setEditingNoteId(note.id);
    setNewNote(note.content || '');
    setIsPreviewMode(false);
    // Optionally scroll to editor?
  };

  const cancelEdit = () => {
    setEditingNoteId(null);
    setNewNote('');
    setIsPreviewMode(false);
  };

  const handleDeleteNote = async (noteId: string) => {
    try {
      await readerService.deleteNote(paperId, noteId);
      setNotes(notes.filter(n => n.id !== noteId));
      if (editingNoteId === noteId) {
          cancelEdit();
      }
      toast.success("笔记已删除");
    } catch (e) {
      console.error("Failed to delete note", e);
      toast.error("删除失败");
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50/30 dark:bg-slate-800/30">
      {/* 1. Header & History Section */}
      <div className="flex-shrink-0 bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 shadow-sm z-10">
        <button 
          onClick={() => setIsHistoryOpen(!isHistoryOpen)}
          className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
        >
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">我的笔记</h3>
            <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">
              {notes.length} 条笔记
            </span>
          </div>
          {isHistoryOpen ? (
            <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          )}
        </button>

        <div className={cn(
          "grid transition-all duration-300 ease-in-out",
          isHistoryOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        )}>
          <div className="overflow-hidden">
             <ScrollArea className="h-[200px] border-t border-gray-100 dark:border-slate-800">
               <div className="p-4 space-y-3">
                 {loading && <div className="text-center text-xs text-gray-400">加载中...</div>}
                 {!loading && notes.length === 0 && (
                   <div className="text-center text-xs text-gray-400 py-4">暂无笔记</div>
                 )}
                 {notes.map(note => (
                   <div key={note.id} className="group relative bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 p-3 rounded-lg hover:border-indigo-300 dark:hover:border-indigo-500 transition-all shadow-sm">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/50 px-2 py-0.5 rounded">
                          Page {note.page || '-'}
                        </span>
                        <span className="text-[10px] text-gray-400 dark:text-gray-500">
                          {new Date(note.created_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-300 leading-snug prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown>{note.content || ''}</ReactMarkdown>
                      </div>
                      
                      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1 bg-white/80 dark:bg-slate-800/80 backdrop-blur rounded p-1">
                        <button 
                          onClick={() => startEdit(note)}
                          className="p-1 text-gray-400 dark:text-gray-500 hover:text-indigo-600 dark:hover:text-indigo-400 rounded"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                        <button 
                          onClick={() => handleDeleteNote(note.id)}
                          className="p-1 text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 rounded"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                   </div>
                 ))}
               </div>
             </ScrollArea>
          </div>
        </div>
      </div>

      {/* 2. Editor Section */}
      <div className="flex-1 flex flex-col min-h-0 bg-white dark:bg-slate-900">
        <div className="p-2 border-b border-gray-100 dark:border-slate-800 flex justify-between items-center bg-gray-50/50 dark:bg-slate-800/50">
          <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider pl-2">
                {editingNoteId ? '编辑笔记' : '新建笔记'}
              </span>
              {editingNoteId && (
                  <button 
                    onClick={cancelEdit}
                    className="p-1 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-full transition-colors text-indigo-600 dark:text-indigo-400"
                    title="切换回新建模式"
                  >
                      <Plus className="w-3.5 h-3.5 rotate-45" />
                  </button>
              )}
          </div>
          <button 
            onClick={() => setIsPreviewMode(!isPreviewMode)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors",
              isPreviewMode 
                ? "bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300" 
                : "bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700"
            )}
          >
            {isPreviewMode ? (
              <>
                <EyeOff className="w-3.5 h-3.5" />
                <span>退出预览</span>
              </>
            ) : (
              <>
                <Eye className="w-3.5 h-3.5" />
                <span>预览效果</span>
              </>
            )}
          </button>
        </div>

        <div className="flex-1 relative">
          {isPreviewMode ? (
            <div className="absolute inset-0 p-4 overflow-y-auto prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300">
               {newNote ? (
                 <ReactMarkdown>{newNote}</ReactMarkdown>
               ) : (
                 <span className="text-gray-400 dark:text-gray-500 italic">暂无内容预览...</span>
               )}
            </div>
          ) : (
            <textarea 
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="记录想法... (支持 Markdown)"
              className="w-full h-full p-4 resize-none focus:outline-none text-sm text-gray-800 dark:text-gray-200 bg-transparent leading-relaxed placeholder:text-gray-400 dark:placeholder:text-gray-600"
            />
          )}
        </div>

        <div className="p-4 border-t border-gray-100 dark:border-slate-800 bg-gray-50/30 dark:bg-slate-800/30">
          <button 
            onClick={handleAddOrUpdateNote}
            disabled={!newNote.trim()}
            className={cn(
                "w-full flex items-center justify-center gap-2 text-white py-2.5 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md",
                editingNoteId 
                    ? "bg-emerald-600 dark:bg-emerald-500 hover:bg-emerald-700 dark:hover:bg-emerald-600"
                    : "bg-indigo-600 dark:bg-indigo-500 hover:bg-indigo-700 dark:hover:bg-indigo-600"
            )}
          >
            {editingNoteId ? (
                <>
                    <Edit2 className="w-4 h-4" />
                    <span>更新笔记</span>
                </>
            ) : (
                <>
                    <Plus className="w-4 h-4" />
                    <span>添加笔记</span>
                </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};