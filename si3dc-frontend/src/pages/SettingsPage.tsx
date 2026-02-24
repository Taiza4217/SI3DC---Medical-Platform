import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, User, Mail, Phone, Camera } from 'lucide-react';
import { getStoredUser, authService } from '../services/api';

export default function SettingsPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }
    setUser(getStoredUser());
  }, [navigate]);

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-blue-600 mb-8">
          <ArrowLeft className="h-4 w-4" />
          Voltar ao Painel
        </Link>

        <h1 className="text-3xl font-bold text-slate-900 mb-8">Configurações de Perfil</h1>

        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
          {/* Profile Picture */}
          <div className="flex items-center gap-6 mb-8">
            <div className="relative">
              <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center border-4 border-white shadow-md text-blue-600">
                <User className="h-10 w-10" />
              </div>
              <button className="absolute bottom-0 right-0 bg-blue-600 p-2 rounded-full text-white hover:bg-blue-700 transition-colors">
                <Camera className="h-4 w-4" />
              </button>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-800">{user.name || 'Profissional'}</h2>
              <p className="text-slate-500">{user.specialty || 'Especialidade'} {user.professionalId ? `| CRM: ${user.professionalId}` : ''}</p>
            </div>
          </div>

          {/* Form */}
          <form className="space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1">Nome Completo</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input type="text" id="name" defaultValue={user.name || ''} className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50" readOnly />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input type="email" id="email" defaultValue={user.email || 'email@não.cadastrado'} className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50" readOnly />
              </div>
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-slate-700 mb-1">Telefone</label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input type="tel" id="phone" defaultValue={user.phone || 'Não cadastrado'} className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50" readOnly />
              </div>
            </div>

            <div className="pt-4 text-right">
              <p className="text-sm text-slate-500">Para alterar seus dados, entre em contato com o administrador da sua instituição.</p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
