import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, MessageSquareText, Bell } from 'lucide-react';
import { clinicalService } from '../services/api';

interface NoteModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientName: string;
}

export default function NoteModal({ isOpen, onClose, patientName }: NoteModalProps) {
  const [noteType, setNoteType] = useState<'observation' | 'reminder'>('observation');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!content.trim()) return;
    setLoading(true);
    try {
      await clinicalService.saveNote(patientName, noteType, content);
      alert('Nota salva com sucesso!');
      setContent('');
      onClose();
    } catch (e: any) {
      alert(e.message || 'Erro ao salvar nota.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-8 text-slate-900"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Adicionar Nota</h2>
              <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100">
                <X className="h-5 w-5 text-slate-500" />
              </button>
            </div>

            {/* Type Selector */}
            <div className="flex border border-slate-200 rounded-lg p-1 mb-6 bg-slate-100">
              <button
                onClick={() => setNoteType('observation')}
                className={`w-1/2 py-2 rounded-md text-sm font-semibold transition-colors ${noteType === 'observation' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-600'}`}
              >
                <MessageSquareText className="h-4 w-4 inline-block mr-2" />
                Observação Clínica
              </button>
              <button
                onClick={() => setNoteType('reminder')}
                className={`w-1/2 py-2 rounded-md text-sm font-semibold transition-colors ${noteType === 'reminder' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-600'}`}
              >
                <Bell className="h-4 w-4 inline-block mr-2" />
                Lembrete Pessoal
              </button>
            </div>

            {noteType === 'observation' ? (
              <p className="text-sm text-slate-500 mb-4">A observação será visível para outros profissionais e expirará em 2 anos.</p>
            ) : (
              <p className="text-sm text-slate-500 mb-4">Este lembrete será visível <strong>apenas para você</strong> no próximo atendimento deste paciente.</p>
            )}

            <textarea
              placeholder={`Digite sua ${noteType === 'observation' ? 'observação' : 'lembrete'}...`}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              disabled={loading}
              className='w-full h-40 p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none'
            />
            <div className="mt-6 flex justify-end">
              <button onClick={handleSave} disabled={loading} className="px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors">
                {loading ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
