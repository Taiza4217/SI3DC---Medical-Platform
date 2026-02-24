import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, LogOut, Settings, CheckCircle, Clock, Search, Siren, Upload, PlusCircle, Activity, Users, BarChart3, ShieldCheck } from 'lucide-react';
import { motion } from 'motion/react';
import { getStoredUser, authService, dashboardService, patientService } from '../services/api';

const statusStyles = {
  completed: { icon: CheckCircle, text: 'Atendido', color: 'text-emerald-500', bg: 'bg-emerald-50' },
  current: { icon: Clock, text: 'Em atendimento', color: 'text-blue-500', bg: 'bg-blue-50' },
  upcoming: { icon: Clock, text: 'Aguardando', color: 'text-slate-500', bg: 'bg-slate-50' },
};

const actionButtons = [
  {
    label: 'Buscar Prontuário',
    description: 'Acesse o prontuário inteligente do paciente',
    icon: Search,
    path: '/search-patient',
    color: 'from-blue-600 to-blue-700',
    shadow: 'shadow-blue-500/25',
  },
  {
    label: 'Modo Emergência',
    description: 'Resumo emergencial em até 5 segundos',
    icon: Siren,
    path: '/emergency',
    color: 'from-red-600 to-red-700',
    shadow: 'shadow-red-500/25',
  },
  {
    label: 'Upload de Documentos',
    description: 'Envie exames, laudos e relatórios',
    icon: Upload,
    path: '/upload',
    color: 'from-emerald-600 to-emerald-700',
    shadow: 'shadow-emerald-500/25',
  },
  {
    label: 'Novo Atendimento',
    description: 'Iniciar um novo atendimento clínico',
    icon: PlusCircle,
    path: '/search-patient',
    color: 'from-violet-600 to-violet-700',
    shadow: 'shadow-violet-500/25',
  },
];

function DashboardHeader() {
  const user = getStoredUser();
  const navigate = useNavigate();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  return (
    <header className="bg-white/80 backdrop-blur-md fixed top-0 left-0 right-0 z-40 border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-8">
        <div className="flex justify-between items-center h-20">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 p-2.5 rounded-full">
              <User className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">{user?.name || 'Profissional'}</p>
              <p className="text-xs text-slate-500">{user?.specialty || 'Especialidade'} | {user?.institution || 'Instituição'} | CRM: {user?.professionalId || 'N/A'}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/settings" className="p-2 text-slate-500 hover:text-slate-800 transition-colors">
              <Settings className="h-5 w-5" />
            </Link>
            <button onClick={handleLogout} className="p-2 text-slate-500 hover:text-slate-800 transition-colors">
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default function DashboardPage() {
  const user = getStoredUser();
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
    } else {
      fetchDashboard();
    }
  }, [navigate]);

  const fetchDashboard = async () => {
    try {
      const data = await dashboardService.getStats();
      setDashboardData(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const currentAppointment = dashboardData?.appointments?.find((a: any) => a.status === 'current');

  const handleStartNextAppointment = async () => {
    if (currentAppointment) {
      alert("Você deve encerrar o atendimento atual antes de iniciar um novo.");
      return;
    }

    try {
      await dashboardService.startNext();
      await fetchDashboard();
    } catch (error: any) {
      alert(error.message || "Erro ao iniciar próximo atendimento");
    }
  };

  const handleAccessRecord = (patientId: string) => {
    sessionStorage.setItem('currentPatientId', patientId);
    sessionStorage.setItem('currentPatientFound', 'true');
    navigate('/search-patient');
  };

  if (loading) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center">Carregando...</div>;
  }

  const appointments = dashboardData?.appointments || [];
  const completedCount = appointments.filter((a: any) => a.status === 'completed').length;
  const currentCount = appointments.filter((a: any) => a.status === 'current').length;
  const upcomingCount = appointments.filter((a: any) => a.status === 'upcoming').length;

  return (
    <div className="min-h-screen w-full bg-slate-50 font-sans">
      <DashboardHeader />
      <main className="max-w-7xl mx-auto px-8 pt-28 pb-16">
        {/* Welcome Section */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-slate-900">
            Olá, {user?.name?.split(' ').slice(0, 2).join(' ') || 'Profissional'} 👋
          </h1>
          <p className="text-slate-500 mt-1">Veja o resumo do seu dia e acesse as ferramentas clínicas.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0 }}
            className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-slate-500">Total Hoje</span>
              <Users className="h-5 w-5 text-blue-500" />
            </div>
            <p className="text-3xl font-bold text-slate-900">{appointments.length}</p>
            <p className="text-xs text-slate-400 mt-1">pacientes agendados</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-slate-500">Atendidos</span>
              <CheckCircle className="h-5 w-5 text-emerald-500" />
            </div>
            <p className="text-3xl font-bold text-emerald-600">{completedCount}</p>
            <p className="text-xs text-slate-400 mt-1">consultas finalizadas</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-slate-500">Em Atendimento</span>
              <Activity className="h-5 w-5 text-blue-500" />
            </div>
            <p className="text-3xl font-bold text-blue-600">{currentCount}</p>
            <p className="text-xs text-slate-400 mt-1">consulta ativa agora</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-slate-500">Aguardando</span>
              <Clock className="h-5 w-5 text-amber-500" />
            </div>
            <p className="text-3xl font-bold text-amber-600">{upcomingCount}</p>
            <p className="text-xs text-slate-400 mt-1">pacientes na fila</p>
          </motion.div>
        </div>

        {/* Action Buttons */}
        <div className="mb-10">
          <h2 className="text-xl font-bold text-slate-900 mb-6">Ações Rápidas</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {actionButtons.map((btn, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + index * 0.05 }}
                whileHover={{ scale: 1.03, y: -4 }}
                whileTap={{ scale: 0.98 }}
              >
                {btn.label === 'Novo Atendimento' ? (
                  <button
                    onClick={handleStartNextAppointment}
                    className={`group w-full text-left block p-6 rounded-2xl bg-gradient-to-br ${btn.color} text-white shadow-lg ${btn.shadow} hover:shadow-xl transition-all h-full`}
                  >
                    <div className="bg-white/20 p-3 rounded-xl w-max mb-4 backdrop-blur-sm">
                      <btn.icon className="h-7 w-7" />
                    </div>
                    <h3 className="text-lg font-bold mb-1">{btn.label}</h3>
                    <p className="text-sm text-white/80">{btn.description}</p>
                  </button>
                ) : (
                  <Link
                    to={btn.path}
                    className={`group block p-6 rounded-2xl bg-gradient-to-br ${btn.color} text-white shadow-lg ${btn.shadow} hover:shadow-xl transition-all h-full`}
                  >
                    <div className="bg-white/20 p-3 rounded-xl w-max mb-4 backdrop-blur-sm">
                      <btn.icon className="h-7 w-7" />
                    </div>
                    <h3 className="text-lg font-bold mb-1">{btn.label}</h3>
                    <p className="text-sm text-white/80">{btn.description}</p>
                  </Link>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* System Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="bg-emerald-100 p-3 rounded-xl">
              <ShieldCheck className="h-6 w-6 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">LGPD Compliance</p>
              <p className="text-xs text-slate-500">Auditoria ativa • Criptografia ativada</p>
            </div>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="bg-blue-100 p-3 rounded-xl">
              <Activity className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">IA Operacional</p>
              <p className="text-xs text-slate-500">MedGemma • HAI-DEF ativo</p>
            </div>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="bg-violet-100 p-3 rounded-xl">
              <BarChart3 className="h-6 w-6 text-violet-600" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">Última Sincronização</p>
              <p className="text-xs text-slate-500">{new Date().toLocaleTimeString('pt-BR')} • Todos os sistemas</p>
            </div>
          </div>
        </div>

        {/* Today's Appointments */}
        <div>
          <h2 className="text-xl font-bold text-slate-900 mb-6">Agenda do Dia</h2>
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <ul className="divide-y divide-slate-100">
              {appointments.map((appt: any, index: number) => {
                const StatusIcon = statusStyles[appt.status as keyof typeof statusStyles].icon;
                const statusText = statusStyles[appt.status as keyof typeof statusStyles].text;
                const statusColor = statusStyles[appt.status as keyof typeof statusStyles].color;
                const statusBg = statusStyles[appt.status as keyof typeof statusStyles].bg;
                return (
                  <li key={index} className="p-4 grid grid-cols-3 items-center hover:bg-slate-50 transition-colors">
                    <div className="col-span-1 flex items-center">
                      <div className="font-bold text-slate-800 w-20">{appt.time}</div>
                      <div className="text-slate-600">{appt.name}</div>
                    </div>
                    <div className={`col-span-1 px-3 py-1 rounded-full text-xs font-medium flex items-center justify-center gap-2 ${statusBg} ${statusColor} w-max`}>
                      <StatusIcon className="h-3.5 w-3.5" />
                      {statusText}
                    </div>
                    <div className="col-span-1 text-right">
                      {appt.status === 'upcoming' && currentCount === 0 && (
                        <button onClick={handleStartNextAppointment} className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg text-sm hover:bg-blue-700 transition-colors">
                          Novo Atendimento
                        </button>
                      )}
                      {appt.status === 'current' && (
                        <button onClick={() => handleAccessRecord(appt.patientId)} className="px-4 py-2 bg-emerald-600 text-white font-semibold rounded-lg text-sm hover:bg-emerald-700 transition-colors">
                          Acessar Prontuário
                        </button>
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
