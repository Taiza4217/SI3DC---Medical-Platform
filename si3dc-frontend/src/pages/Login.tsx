import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Activity, Lock, Shield, Building, ArrowLeft, AlertTriangle } from 'lucide-react';
import { authService } from '../services/api';

export default function Login() {
  const [professionalId, setProfessionalId] = useState('');
  const [password, setPassword] = useState('');
  const [healthNetwork, setHealthNetwork] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const healthNetworks = [
    { id: 'hc_sp', name: 'Hospital das Clínicas - SP' },
    { id: 'einstein', name: 'Hospital Israelita Albert Einstein' },
    { id: 'sirio', name: 'Hospital Sírio-Libanês' },
    { id: 'unimed', name: 'Rede Unimed' },
  ];

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      await authService.login(professionalId, password, healthNetwork);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full lg:grid lg:grid-cols-2 font-sans">
      {/* Left Panel - Visuals */}
      <div className="hidden lg:flex flex-col items-center justify-center bg-slate-900 text-white p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900 to-slate-900 opacity-50"></div>
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-800/20 rounded-full -translate-x-1/2 -translate-y-1/2 blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-sky-700/20 rounded-full translate-x-1/2 translate-y-1/2 blur-3xl"></div>

        <div className="relative z-10 text-center">
          <div className="bg-white/10 p-4 rounded-2xl inline-block mb-6 backdrop-blur-sm">
            <Activity className="h-12 w-12 text-white" />
          </div>
          <h1 className="font-bold text-4xl tracking-tight">Plataforma SI3DC</h1>
          <p className="text-slate-300 mt-4 max-w-md">
            A inteligência de dados que unifica a saúde e potencializa o cuidado clínico.
          </p>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="flex items-center justify-center p-8 sm:p-12 bg-slate-50 relative">
        <Link
          to="/"
          className="absolute top-6 left-6 inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors z-10"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar
        </Link>

        <div className="w-full max-w-md">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-slate-900">Acesso à Plataforma</h2>
            <p className="text-slate-500 mt-2">Entre com suas credenciais institucionais.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="healthNetwork" className="block text-sm font-medium text-slate-700 mb-1.5">Convênio / Rede de saúde</label>
              <div className="relative">
                <select
                  id="healthNetwork"
                  required
                  value={healthNetwork}
                  onChange={(e) => setHealthNetwork(e.target.value)}
                  className="w-full appearance-none px-4 py-3 pr-10 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all bg-white"
                >
                  <option value="" disabled>Selecione sua instituição</option>
                  {healthNetworks.map(network => (
                    <option key={network.id} value={network.id}>{network.name}</option>
                  ))}
                </select>
                <Building className="absolute right-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 pointer-events-none" />
              </div>
            </div>

            <div>
              <label htmlFor="professionalId" className="block text-sm font-medium text-slate-700 mb-1.5">Número profissional (CRM, CRP ou ID)</label>
              <div className="relative">
                <input
                  type="text"
                  id="professionalId"
                  required
                  value={professionalId}
                  onChange={(e) => setProfessionalId(e.target.value)}
                  className="w-full px-4 py-3 pl-11 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="Ex: 123456-SP"
                />
                <Shield className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label htmlFor="password" className="block text-sm font-medium text-slate-700">Senha</label>
                <a href="#" className="text-xs text-blue-600 hover:underline">Esqueceu a senha?</a>
              </div>
              <div className="relative">
                <input
                  type="password"
                  id="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 pl-11 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="••••••••"
                />
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-lg flex items-center">
                <AlertTriangle className="h-5 w-5 text-red-600 mr-3 flex-shrink-0" />
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 px-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Verificando...' : 'Entrar'}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-slate-200 text-center text-sm text-slate-500">
            Não tem acesso? <Link to="/join-us" className="text-blue-600 font-medium hover:underline">Solicite integração</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
