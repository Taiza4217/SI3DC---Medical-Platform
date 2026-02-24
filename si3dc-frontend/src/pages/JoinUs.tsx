import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle, Activity, Hospital, Users, Stethoscope } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

const FeatureCard = ({ icon: Icon, title, children }: { icon: React.ElementType, title: string, children: React.ReactNode }) => (
  <div className="flex items-start gap-4">
    <div className="bg-white/10 p-2 rounded-lg">
      <Icon className="h-6 w-6 text-sky-300" />
    </div>
    <div>
      <h3 className="font-semibold text-white">{title}</h3>
      <p className="text-slate-400 text-sm mt-1">{children}</p>
    </div>
  </div>
);

export default function JoinUs() {
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitted(true);
  };

  return (
    <div className="min-h-screen w-full lg:grid lg:grid-cols-2 font-sans">
      {/* Left Panel - Visuals & Info */}
      <div className="hidden lg:flex flex-col justify-between bg-slate-900 text-white p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900 to-slate-900 opacity-50"></div>
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-800/20 rounded-full -translate-x-1/2 -translate-y-1/2 blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-sky-700/20 rounded-full translate-x-1/2 translate-y-1/2 blur-3xl"></div>
        
        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center gap-3 group mb-8">
            <div className="bg-white/10 p-2 rounded-lg group-hover:bg-white/20 transition-colors">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <span className="font-bold text-xl tracking-tight">SI3DC</span>
          </Link>
          <h1 className="font-bold text-4xl tracking-tight leading-snug">Leve a inteligência clínica para sua rede de saúde.</h1>
          <p className="text-slate-300 mt-4 max-w-lg">
            Integre históricos, reduza a fragmentação de dados e apoie decisões médicas com a segurança e a eficiência da nossa plataforma de IA.
          </p>
        </div>

        <div className="relative z-10 space-y-6">
            <FeatureCard icon={Hospital} title="Hospitais e Clínicas">Unifique prontuários e otimize o fluxo de trabalho clínico.</FeatureCard>
            <FeatureCard icon={Users} title="Convênios e Redes de Saúde">Obtenha uma visão 360° da saúde dos seus beneficiários.</FeatureCard>
            <FeatureCard icon={Stethoscope} title="Sistemas Hospitalares (HIS/ERP)">Integre-se de forma transparente aos seus sistemas existentes.</FeatureCard>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="flex items-center justify-center p-8 sm:p-12 bg-slate-50 relative">
        <Link 
          to="/" 
          className="absolute top-6 left-6 inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors z-20 lg:hidden"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar
        </Link>

        <div className="w-full max-w-lg">
          <AnimatePresence mode="wait">
            {isSubmitted ? (
              <motion.div
                key="success"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center bg-white p-12 rounded-2xl border border-slate-200 shadow-sm"
              >
                <CheckCircle className="h-16 w-16 text-emerald-500 mx-auto mb-6" />
                <h2 className="text-2xl font-bold text-slate-900 mb-4">Solicitação Enviada!</h2>
                <p className="text-slate-600 max-w-md mx-auto">
                  Nossa equipe entrará em contato para iniciar o processo de integração segura com a plataforma SI3DC.
                </p>
              </motion.div>
            ) : (
              <motion.div
                key="form"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-white p-8 sm:p-12 rounded-2xl border border-slate-200 shadow-sm"
              >
                <div className="text-center lg:text-left mb-8">
                  <h2 className="text-3xl font-bold text-slate-900">Solicite a Integração</h2>
                  <p className="text-slate-500 mt-2">Preencha o formulário para iniciar a parceria.</p>
                </div>
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div>
                    <label htmlFor="organizationName" className="block text-sm font-medium text-slate-700 mb-1.5">Nome da instituição</label>
                    <input type="text" id="organizationName" required className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="Hospital Central" />
                  </div>
                  <div>
                    <label htmlFor="responsibleName" className="block text-sm font-medium text-slate-700 mb-1.5">Nome do responsável</label>
                    <input type="text" id="responsibleName" required className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="Dr. João Silva" />
                  </div>
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1.5">Email institucional</label>
                    <input type="email" id="email" required className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="contato@hospital.com.br" />
                  </div>
                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-slate-700 mb-1.5">Telefone</label>
                    <input type="tel" id="phone" required className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="(11) 99999-9999" />
                  </div>
                  <button type="submit" className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors shadow-sm hover:shadow-md">
                    Enviar Solicitação
                  </button>
                </form>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
