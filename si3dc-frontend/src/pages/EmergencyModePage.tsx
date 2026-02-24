import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Siren, ShieldCheck, ShieldAlert, Activity, Database, ArrowLeft, Loader, Upload, MessageSquarePlus, Clock, FileText, Brain, Stethoscope, HeartPulse } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import UploadModal from '../components/UploadModal';
import ObservationModal from '../components/ObservationModal';
import { emergencyService } from '../services/api';

const historyButtons = [
  { icon: Clock, label: 'Saúde', color: 'blue', type: 'saude' },
  { icon: FileText, label: 'Exames', color: 'indigo', type: 'exames' },
  { icon: ShieldAlert, label: 'Medicamentos', color: 'emerald', type: 'medicamentoso' },
  { icon: Brain, label: 'Saúde Mental', color: 'purple', type: 'mental' },
  { icon: Stethoscope, label: 'Odontológico', color: 'sky', type: 'odontologico' },
  { icon: HeartPulse, label: 'Tratamentos', color: 'rose', type: 'tratamentos' },
];

const colorMap = {
  blue: { border: 'border-blue-500', bg: 'bg-blue-100', text: 'text-blue-600' },
  indigo: { border: 'border-indigo-500', bg: 'bg-indigo-100', text: 'text-indigo-600' },
  emerald: { border: 'border-emerald-500', bg: 'bg-emerald-100', text: 'text-emerald-600' },
  purple: { border: 'border-purple-500', bg: 'bg-purple-100', text: 'text-purple-600' },
  sky: { border: 'border-sky-500', bg: 'bg-sky-100', text: 'text-sky-600' },
  rose: { border: 'border-rose-500', bg: 'bg-rose-100', text: 'text-rose-600' },
};

interface EmergencyData {
  patientName: string;
  criticalInfo: Record<string, string>;
  governance: {
    consistency: string;
    confidence: string;
    sources: string[];
  };
}

export default function EmergencyModePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [summary, setSummary] = useState<EmergencyData | null>(() => {
    const saved = sessionStorage.getItem('emergencySummary');
    return saved ? JSON.parse(saved) : null;
  });
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isObservationModalOpen, setIsObservationModalOpen] = useState(false);

  React.useEffect(() => {
    if (summary) {
      sessionStorage.setItem('emergencySummary', JSON.stringify(summary));
    } else {
      sessionStorage.removeItem('emergencySummary');
    }
  }, [summary]);

  const handleSearch = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setSummary(null);

    try {
      const data = await emergencyService.getSummary(searchQuery);
      setSummary(data);
    } catch (error) {
      console.error('Emergency search failed:', error);
      // Fallback to mock data if backend is unavailable
      setSummary({
        patientName: 'José da Silva',
        criticalInfo: {
          'Alergias Críticas': 'Penicilina (Anafilaxia)',
          'Medicamentos Atuais': 'Warfarina (Anticoagulante), Losartana (Anti-hipertensivo)',
          'Doenças Crônicas': 'Hipertensão, Diabetes Mellitus Tipo 2, Doença Arterial Coronariana',
          'Cirurgias Relevantes': 'Revascularização do miocárdio (2019)',
          'Riscos Médicos': 'Alto risco de sangramento (uso de anticoagulante)',
          'Alertas de Interação': 'Evitar AINEs (risco de sangramento com Warfarina)',
        },
        governance: {
          consistency: '99.8%',
          confidence: 'Elevada',
          sources: ['Prontuário HC-SP', 'Dispensação Farmacêutica', 'Resultados Laboratoriais'],
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col items-center justify-center p-4 font-sans relative">
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        patientName={summary?.patientName || ''}
      />
      <ObservationModal
        isOpen={isObservationModalOpen}
        onClose={() => setIsObservationModalOpen(false)}
        patientName={summary?.patientName || ''}
      />

      <div className="relative z-10 w-full">
        <Link
          to="/dashboard"
          onClick={() => sessionStorage.removeItem('emergencySummary')}
          className="absolute top-6 left-6 inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar ao Dashboard
        </Link>

        <div className="w-full max-w-3xl text-center mx-auto">
          <Siren className="h-16 w-16 text-red-600 mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-slate-900">Modo Emergência</h1>
          <p className="text-slate-600 mt-2 mb-8">Acesso rápido a informações críticas para decisões imediatas.</p>

          {!summary && (
            <form onSubmit={handleSearch} className="flex items-center max-w-md mx-auto mb-8 shadow-lg shadow-red-500/10 rounded-lg">
              <input
                type="text"
                placeholder="Digite o CPF ou RG do paciente..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-5 py-4 rounded-l-lg border border-slate-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all"
                disabled={isLoading}
              />
              <button type="submit" className="px-6 py-4 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-r-lg transition-colors disabled:bg-red-400" disabled={isLoading}>
                {isLoading ? <Loader className="h-6 w-6 animate-spin" /> : <Search className="h-6 w-6" />}
              </button>
            </form>
          )}

          <AnimatePresence>
            {summary && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-2xl shadow-lg p-8 border border-red-200 text-left mt-8"
              >
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900 mb-1">Resumo Emergencial (IA)</h2>
                    <p className="text-slate-500">Paciente: {summary.patientName}</p>
                  </div>
                  <div className='flex items-center gap-2'>
                    <button onClick={() => setIsUploadModalOpen(true)} className='flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 font-semibold rounded-lg text-sm hover:bg-blue-100'>
                      <Upload className='h-4 w-4' /> Adicionar Documentos
                    </button>
                    <button onClick={() => setIsObservationModalOpen(true)} className='flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 font-semibold rounded-lg text-sm hover:bg-slate-200'>
                      <MessageSquarePlus className='h-4 w-4' /> Registrar Observação
                    </button>
                  </div>
                </div>

                <div className="space-y-4 mb-8">
                  {Object.entries(summary.criticalInfo).map(([key, value]) => (
                    <div key={key} className="grid grid-cols-1 md:grid-cols-3 gap-x-4 gap-y-1 py-3 border-b border-slate-100">
                      <strong className="md:col-span-1 text-slate-700">{key}</strong>
                      <p className={`md:col-span-2 ${key === 'Alergias Críticas' ? 'text-red-600 font-bold' : 'text-slate-800'}`}>{value}</p>
                    </div>
                  ))}
                </div>

                <div className="mb-8">
                  <h3 className="text-lg font-bold text-slate-900 mb-4">Acesso Rápido ao Histórico</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {historyButtons.map((button, index) => (
                      <Link to={`/history?type=${button.type}&from=/emergency`} key={index} className={`flex items-center gap-3 p-3 rounded-lg bg-white border border-slate-200 hover:shadow-md transition-all`}>
                        <div className={`p-2 rounded-lg ${colorMap[button.color as keyof typeof colorMap].bg}`}>
                          <button.icon className={`h-5 w-5 ${colorMap[button.color as keyof typeof colorMap].text}`} />
                        </div>
                        <span className="font-semibold text-sm text-slate-800">{button.label}</span>
                      </Link>
                    ))}
                  </div>
                </div>

                {/* AI Governance Layer */}
                <div className="bg-sky-50 border border-sky-200 p-4 rounded-xl">
                  <h3 className="text-lg font-bold text-sky-900 mb-3 flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5" /> AI Governance Layer
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4 text-sky-700" />
                      <div>
                        <p className="font-semibold text-sky-800">Consistência Clínica</p>
                        <p className="text-sky-600">{summary.governance.consistency}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4 text-sky-700" />
                      <div>
                        <p className="font-semibold text-sky-800">Confiança do Modelo</p>
                        <p className="text-sky-600">{summary.governance.confidence}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4 text-sky-700" />
                      <div>
                        <p className="font-semibold text-sky-800">Fontes de Dados</p>
                        <p className="text-sky-600">{summary.governance.sources.join(', ')}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
