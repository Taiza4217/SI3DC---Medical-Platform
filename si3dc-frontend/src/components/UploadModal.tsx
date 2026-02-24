import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, UploadCloud, FileText, Loader, CheckCircle } from 'lucide-react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientName: string;
}

export default function UploadModal({ isOpen, onClose, patientName }: UploadModalProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const handleFileChange = (newFiles: FileList | null) => {
    if (newFiles) {
      setFiles(prevFiles => [...prevFiles, ...Array.from(newFiles)]);
    }
  };

  const onDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    handleFileChange(event.dataTransfer.files);
  }, []);

  const onDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleUpload = () => {
    if (files.length === 0) return;

    setIsUploading(true);
    setTimeout(() => {
      setIsUploading(false);
      setIsProcessing(true);
      // Simulate AI processing
      setTimeout(() => {
        setIsProcessing(false);
        setIsComplete(true);
      }, 3000);
    }, 1500);
  };

  const resetAndClose = () => {
    setFiles([]);
    setIsComplete(false);
    onClose();
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          onClick={resetAndClose}
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            className="bg-white rounded-2xl shadow-xl w-full max-w-2xl p-8 text-slate-900"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Adicionar Documentos</h2>
              <button onClick={resetAndClose} className="p-2 rounded-full hover:bg-slate-100">
                <X className="h-5 w-5 text-slate-500" />
              </button>
            </div>

            <AnimatePresence mode="wait">
              {isComplete ? (
                <motion.div key="success" initial={{opacity: 0}} animate={{opacity: 1}} className="text-center py-12">
                  <CheckCircle className="h-16 w-16 text-emerald-500 mx-auto mb-4" />
                  <h3 className="text-xl font-bold">Documentos enviados</h3>
                  <p className="text-slate-500 mt-2">A IA está processando os arquivos e atualizará o prontuário em instantes.</p>
                  <button onClick={resetAndClose} className="mt-6 px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg">Fechar</button>
                </motion.div>
              ) : isUploading || isProcessing ? (
                 <motion.div key="progress" initial={{opacity: 0}} animate={{opacity: 1}} className="text-center py-12">
                    <Loader className="h-16 w-16 text-blue-600 mx-auto mb-4 animate-spin" />
                    <h3 className="text-xl font-bold">{isUploading ? 'Enviando...' : 'Processando com IA...'}</h3>
                    <p className="text-slate-500 mt-2">{isProcessing && 'Interpretando, extraindo dados e atualizando o prontuário.'}</p>
                </motion.div>
              ) : (
                <motion.div key="form" initial={{opacity: 0}} animate={{opacity: 1}}>
                  <p className="mb-4">Anexe laudos, exames e relatórios para <strong className="font-semibold">{patientName}</strong>. A IA irá processar e integrar os dados ao prontuário.</p>
                  <div 
                    className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center cursor-pointer hover:bg-slate-50 transition-colors"
                    onDrop={onDrop}
                    onDragOver={onDragOver}
                  >
                    <input
                      type="file"
                      multiple
                      onChange={(e) => handleFileChange(e.target.files)}
                      className="hidden"
                      id="file-upload"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <UploadCloud className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                      <p className="font-semibold text-slate-700">Arraste e solte ou clique para selecionar</p>
                      <p className="text-sm text-slate-500 mt-1">PDF, JPG, PNG, DOCX (máx 10MB por arquivo)</p>
                    </label>
                  </div>

                  {files.length > 0 && (
                    <div className="mt-6">
                      <h4 className="font-semibold mb-2">Arquivos selecionados:</h4>
                      <ul className="space-y-2">
                        {files.map((file, index) => (
                          <li key={index} className="flex items-center justify-between bg-slate-50 p-2 rounded-lg">
                            <div className="flex items-center gap-3">
                              <FileText className="h-5 w-5 text-slate-500" />
                              <span className="text-sm font-medium">{file.name}</span>
                            </div>
                            <button onClick={() => setFiles(files.filter(f => f !== file))} className="p-1 rounded-full hover:bg-slate-200">
                              <X className="h-4 w-4 text-slate-500" />
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="mt-8 flex justify-end">
                    <button 
                      onClick={handleUpload}
                      disabled={files.length === 0}
                      className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
                    >
                      Enviar Documentos
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
