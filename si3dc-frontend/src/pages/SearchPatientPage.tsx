import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Clock, FileText, Brain, Shield, Stethoscope, HeartPulse, Siren, User, LogOut, Settings, ArrowLeft, Upload, MessageSquarePlus } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import UploadModal from '../components/UploadModal';
import NoteModal from '../components/NoteModal';
import { patientService, dashboardService, clinicalService } from '../services/api';

const historyButtons = [
  { icon: Clock, label: 'Histórico de saúde', color: 'blue', type: 'saude' },
  { icon: FileText, label: 'Histórico de exames', color: 'indigo', type: 'exames' },
  { icon: Shield, label: 'Medicamentoso e alérgico', color: 'emerald', type: 'medicamentoso' },
  { icon: Brain, label: 'Saúde mental', color: 'purple', type: 'mental' },
  { icon: Stethoscope, label: 'Odontológico', color: 'sky', type: 'odontologico' },
  { icon: HeartPulse, label: 'Tratamentos e cirurgias', color: 'rose', type: 'tratamentos' },
];

const colorMap = {
  blue: { border: 'hover:border-blue-500', bg: 'bg-blue-100', text: 'text-blue-600' },
  indigo: { border: 'hover:border-indigo-500', bg: 'bg-indigo-100', text: 'text-indigo-600' },
  emerald: { border: 'hover:border-emerald-500', bg: 'bg-emerald-100', text: 'text-emerald-600' },
  purple: { border: 'hover:border-purple-500', bg: 'bg-purple-100', text: 'text-purple-600' },
  sky: { border: 'hover:border-sky-500', bg: 'bg-sky-100', text: 'text-sky-600' },
  rose: { border: 'hover:border-rose-500', bg: 'bg-rose-100', text: 'text-rose-600' },
};

function PatientViewHeader({ onNewSearch, onEndAppointment }: { onNewSearch: () => void, onEndAppointment: () => void }) {
  return (
    <header className="bg-white/80 backdrop-blur-md fixed top-0 left-0 right-0 z-40 border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-8">
        <div className="flex justify-between items-center h-20">
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">
              <ArrowLeft className="h-4 w-4" />
              Voltar
            </Link>
            <button onClick={onEndAppointment} className="ml-6 text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">Encerrar Atendimento</button>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/emergency" className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-red-50 hover:bg-red-100 text-red-700 transition-colors">
              <Siren className="h-4 w-4" />
              Modo Emergência
            </Link>
            <Link to="/settings" className="p-2 text-slate-500 hover:text-slate-800">
              <Settings className="h-5 w-5" />
            </Link>
            <Link to="/login" className="p-2 text-slate-500 hover:text-slate-800">
              <LogOut className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}

function PatientView({ patient, onNewSearch, onEndAppointment }: { patient: any, onNewSearch: () => void, onEndAppointment: () => void }) {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isNoteModalOpen, setIsNoteModalOpen] = useState(false);

  // We should ideally fetch notes to show reminders, but for now we'll just mock it or omit it
  // if not available.
  const [reminders, setReminders] = useState<any[]>([]);
  React.useEffect(() => {
    // Optionally fetch notes here to show reminders if needed
    fetch(`/api/clinical/notes/${patient?.name}?type=reminder`)
      .then(r => r.json())
      .then(d => {
        if (d.notes && d.notes.length > 0) setReminders(d.notes);
      })
      .catch(console.error);
  }, [patient?.name]);

  if (!patient) return <div>Carregando paciente...</div>;

  return (
    <>
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        patientName={patient.name}
      />
      <NoteModal
        isOpen={isNoteModalOpen}
        onClose={() => setIsNoteModalOpen(false)}
        patientName={patient.name}
      />
      <PatientViewHeader onNewSearch={onNewSearch} onEndAppointment={onEndAppointment} />
      <div className="max-w-4xl mx-auto px-8 pt-28 pb-16">
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">{patient.name}</h1>
            <p className="text-slate-500">CPF: {patient.cpf} | Idade: {patient.age} anos</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-300 text-slate-700 font-semibold rounded-lg transition-colors shadow-sm hover:bg-slate-50"
            >
              <Upload className="h-4 w-4" />
              Adicionar Documentos
            </button>
            <button
              onClick={() => setIsNoteModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors shadow-sm"
            >
              <MessageSquarePlus className="h-4 w-4" />
              Adicionar Nota
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 mb-12">
          <div className="lg:col-span-3 bg-white p-6 rounded-xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-3">Resumo Clínico (IA)</h3>
            <p className="text-slate-600 leading-relaxed">{patient.summary}</p>
          </div>
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-amber-50 border-l-4 border-amber-400 p-6 rounded-md">
              <h3 className="text-lg font-bold text-amber-900 mb-4">Alertas Críticos</h3>
              <ul className="space-y-3">
                {patient.alerts?.map((alert: any, index: number) => (
                  <li key={index} className="text-sm text-amber-800">• <strong>{alert.type}:</strong> {alert.text}</li>
                ))}
              </ul>
            </div>
            {reminders.length > 0 && (
              <div className="bg-blue-50 border-l-4 border-blue-400 p-6 rounded-md">
                <h3 className="text-lg font-bold text-blue-900 mb-4">Lembretes Pessoais</h3>
                {reminders.map((rem: any, i: number) => (
                  <p key={i} className="text-sm text-blue-800 mb-2">• {rem.content}</p>
                ))}
              </div>
            )}
          </div>
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900 mb-6">Explorar Histórico do Paciente</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {historyButtons.map((button, index) => (
              <Link to={`/history?type=${button.type}&from=/search-patient`} key={index}>
                <motion.div
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.98 }}
                  className={`group p-6 rounded-xl text-left bg-white border border-slate-200 hover:shadow-lg ${colorMap[button.color as keyof typeof colorMap].border} transition-all h-full`}
                >
                  <div className={`mb-4 p-3 rounded-lg w-min ${colorMap[button.color as keyof typeof colorMap].bg}`}>
                    <button.icon className={`h-6 w-6 ${colorMap[button.color as keyof typeof colorMap].text}`} />
                  </div>
                  <h3 className="font-bold text-slate-900">{button.label}</h3>
                  <p className="text-sm text-slate-500 mt-1">Visualizar detalhes</p>
                </motion.div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

export default function SearchPatientPage() {
  const [patientFound, setPatientFound] = useState(() => {
    return sessionStorage.getItem('currentPatientFound') === 'true';
  });
  const [patientId, setPatientId] = useState(sessionStorage.getItem('currentPatientId') || '');
  const [patientData, setPatientData] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    sessionStorage.setItem('currentPatientFound', patientFound.toString());
  }, [patientFound]);

  React.useEffect(() => {
    if (patientFound && patientId && !patientData) {
      patientService.getById(patientId).then(setPatientData).catch(console.error);
    }
  }, [patientFound, patientId, patientData]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery) return;
    setLoading(true);
    try {
      const patients = await patientService.search(searchQuery);
      if (patients && patients.length > 0) {
        setPatientData(patients[0]);
        setPatientId(patients[0].id);
        sessionStorage.setItem('currentPatientId', patients[0].id);
        setPatientFound(true);
      } else {
        alert('Nenhum paciente encontrado com esse CPF/RG.');
      }
    } catch (err: any) {
      alert(err.message || 'Erro na busca.');
    } finally {
      setLoading(false);
    }
  };

  const handleEndAppointment = async () => {
    try {
      await dashboardService.endCurrent();
    } catch (e) {
      console.log('Atendimento atual finalizado (ou não havia prioridade local).');
    }
    setPatientFound(false);
    setPatientData(null);
    setPatientId('');
    sessionStorage.removeItem('currentPatientFound');
    sessionStorage.removeItem('currentPatientId');
    // Using window.location.href instead of navigate here to force router refresh or we can use normal Link
    window.location.href = '/dashboard';
  };

  return (
    <div className="min-h-screen w-full bg-slate-100 font-sans">
      <AnimatePresence mode="wait">
        {!patientFound ? (
          <motion.div
            key="search"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex flex-col items-center justify-center h-screen p-8 text-center"
          >
            <div className="max-w-lg">
              <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-blue-600 mb-8">
                <ArrowLeft className="h-4 w-4" />
                Voltar ao Painel
              </Link>
              <h1 className="text-3xl font-bold text-slate-900 mb-4">Acesse o Prontuário Inteligente</h1>
              <p className="text-slate-600 mb-8">Insira o CPF, RG ou ID do paciente para carregar o histórico clínico completo, consolidado e analisado pela IA da SI3DC.</p>
              <form onSubmit={handleSearch} className="flex items-center max-w-sm mx-auto shadow-lg shadow-blue-500/10 rounded-lg">
                <input
                  type="text"
                  placeholder="Digite o CPF, RG ou ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-4 rounded-l-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  disabled={loading}
                />
                <button type="submit" disabled={loading} className="px-6 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-r-lg transition-colors">
                  <Search className="h-5 w-5" />
                </button>
              </form>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="patient-view"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <PatientView patient={patientData} onNewSearch={() => { setPatientFound(false); setPatientData(null); }} onEndAppointment={handleEndAppointment} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
