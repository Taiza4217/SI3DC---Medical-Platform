import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X } from 'lucide-react';
import { clinicalService } from '../services/api';

interface ObservationModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientName: string;
}

export default function ObservationModal({ isOpen, onClose, patientName }: ObservationModalProps) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!content.trim()) return;
    setLoading(true);
    try {
      await clinicalService.saveNote(patientName, 'observation', content);
      alert('Observação salva com sucesso!');
      setContent('');
      onClose();
    } catch (e: any) {
      alert(e.message || 'Erro ao salvar observação.');
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
              <h2 className="text-2xl font-bold">Registrar Observação</h2>
              <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100">
                <X className="h-5 w-5 text-slate-500" />
              </button>
            </div>
            <p className="text-sm text-slate-500 mb-4">As observações adicionadas aqui serão anexadas ao prontuário de <strong className='font-semibold'>{patientName}</strong>.</p>
            <textarea
              placeholder='Digite suas observações clínicas...'
              value={content}
              onChange={(e) => setContent(e.target.value)}
              disabled={loading}
              className='w-full h-40 p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none'
            />
            <div className="mt-6 flex justify-end">
              <button onClick={handleSave} disabled={loading} className="px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors">
                {loading ? 'Salvando...' : 'Salvar Observação'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
