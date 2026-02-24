import React from 'react';
import { motion } from 'motion/react';
import { Link } from 'react-router-dom';
import { ArrowRight, Brain, Database, ShieldCheck, Network, FileText, Activity } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <section id="solution" className="relative pt-32 pb-20 lg:pt-40 lg:pb-32 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
            
            {/* Text Content */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="max-w-2xl"
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold uppercase tracking-wide mb-6">
                <Brain className="h-3 w-3" />
                Inteligência Clínica Avançada
              </div>
              
              <h1 className="text-4xl lg:text-5xl xl:text-6xl font-bold text-slate-900 leading-tight mb-6">
                Transformando dados de saúde em <span className="text-blue-600">decisões clínicas seguras</span>
              </h1>
              
              <p className="text-lg text-slate-600 mb-6 leading-relaxed">
                Sistemas de saúde modernos não sofrem pela falta de dados, mas pela incapacidade de transformá-los em conhecimento acionável. Clínicos enfrentam históricos fragmentados, notas extensas e pouco tempo. Como resultado, informações críticas são frequentemente perdidas, contribuindo para atrasos, erros e exaustão profissional.
              </p>

              <div className="bg-white p-6 rounded-xl border-l-4 border-blue-500 shadow-sm mb-8">
                <h3 className="font-semibold text-slate-900 mb-2 flex items-center gap-2">
                  <Database className="h-5 w-5 text-blue-500" />
                  Tecnologia HAI-DEF
                </h3>
                <p className="text-slate-600 text-sm">
                  Modelos médicos de linguagem oferecem uma solução única: eles conseguem compreender linguagem clínica, sintetizar informações complexas e estruturar dados automaticamente. Nossa aplicação usa modelos <strong>HAI-DEF</strong> para transformar textos clínicos não estruturados em resumos claros, organizados e clinicamente relevantes.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/join-us"
                  className="inline-flex justify-center items-center px-8 py-4 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-all shadow-lg hover:shadow-blue-500/25 group"
                >
                  Solicitar Integração
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <a
                  href="#features"
                  className="inline-flex justify-center items-center px-8 py-4 bg-white text-slate-700 font-semibold rounded-xl border border-slate-200 hover:bg-slate-50 transition-all hover:border-slate-300"
                >
                  Saiba mais
                </a>
              </div>
            </motion.div>

            {/* Visual Content */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="relative lg:h-[600px] flex items-center justify-center"
            >
              {/* Abstract Network Visualization */}
              <div className="relative w-full max-w-lg aspect-square">
                {/* Central Hub */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
                  <div className="w-32 h-32 bg-blue-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-500/30 animate-pulse-slow">
                    <Brain className="h-16 w-16 text-white" />
                  </div>
                  <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 whitespace-nowrap bg-white px-4 py-1 rounded-full shadow-md border border-slate-100 text-sm font-semibold text-blue-900">
                    Núcleo HAI-DEF
                  </div>
                </div>

                {/* Orbiting Nodes */}
                {[
                  { icon: FileText, label: "Prontuários", pos: "top-0 left-1/2 -translate-x-1/2", delay: "0s" },
                  { icon: Database, label: "Histórico", pos: "bottom-0 left-1/2 -translate-x-1/2", delay: "1s" },
                  { icon: Activity, label: "Sinais Vitais", pos: "top-1/2 right-0 translate-x-1/2 -translate-y-1/2", delay: "2s" },
                  { icon: Network, label: "Integração", pos: "top-1/2 left-0 -translate-x-1/2 -translate-y-1/2", delay: "3s" },
                ].map((node, i) => (
                  <motion.div
                    key={i}
                    className={`absolute ${node.pos} z-10 flex flex-col items-center gap-2`}
                    animate={{ y: [0, -10, 0] }}
                    transition={{ duration: 4, repeat: Infinity, delay: i * 0.5, ease: "easeInOut" }}
                  >
                    <div className="w-16 h-16 bg-white rounded-xl border border-slate-200 shadow-lg flex items-center justify-center text-slate-600">
                      <node.icon className="h-8 w-8 text-blue-500" />
                    </div>
                    <span className="text-xs font-medium text-slate-500 bg-white/80 px-2 py-0.5 rounded-md backdrop-blur-sm">
                      {node.label}
                    </span>
                  </motion.div>
                ))}

                {/* Connecting Lines (SVG) */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none z-0 opacity-30">
                  <line x1="50%" y1="50%" x2="50%" y2="10%" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 4" />
                  <line x1="50%" y1="50%" x2="50%" y2="90%" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 4" />
                  <line x1="50%" y1="50%" x2="10%" y2="50%" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 4" />
                  <line x1="50%" y1="50%" x2="90%" y2="50%" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 4" />
                  <circle cx="50%" cy="50%" r="180" fill="none" stroke="#e2e8f0" strokeWidth="1" />
                  <circle cx="50%" cy="50%" r="280" fill="none" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="8 8" />
                </svg>

                {/* Floating Shield Badge */}
                <div className="absolute top-10 right-10 bg-emerald-50 border border-emerald-100 p-3 rounded-lg shadow-sm flex items-center gap-3 animate-bounce-slow">
                  <div className="bg-emerald-100 p-1.5 rounded-md">
                    <ShieldCheck className="h-5 w-5 text-emerald-600" />
                  </div>
                  <div>
                    <div className="text-xs text-emerald-800 font-bold">Segurança Clínica</div>
                    <div className="text-[10px] text-emerald-600">Validado por especialistas</div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
        
        {/* Background Decorative Elements */}
        <div className="absolute top-0 right-0 -z-10 w-1/2 h-full bg-gradient-to-l from-blue-50 to-transparent opacity-60" />
        <div className="absolute bottom-0 left-0 -z-10 w-1/3 h-1/3 bg-blue-100 rounded-full blur-3xl opacity-30 translate-y-1/2 -translate-x-1/2" />
      </section>

      {/* Features Grid (Optional but good for "Credibility") */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Por que escolher o SI3DC?</h2>
            <p className="text-slate-600">
              Nossa plataforma integra o que há de mais avançado em IA com protocolos clínicos rigorosos.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                title: "Redução de Carga Cognitiva",
                desc: "Resumos estruturados que permitem ao médico focar no paciente, não na tela.",
                icon: Brain
              },
              {
                title: "Segurança do Paciente",
                desc: "Identificação automática de riscos e inconsistências em históricos complexos.",
                icon: ShieldCheck
              },
              {
                title: "Integração Total",
                desc: "Conecta-se aos principais prontuários eletrônicos sem fricção.",
                icon: Network
              }
            ].map((feature, i) => (
              <div key={i} className="p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:border-blue-200 hover:shadow-lg transition-all group">
                <div className="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center mb-6 group-hover:bg-blue-600 transition-colors">
                  <feature.icon className="h-6 w-6 text-blue-600 group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-3">{feature.title}</h3>
                <p className="text-slate-600 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security Section */}
      <section id="security" className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Segurança e Conformidade em Primeiro Lugar</h2>
            <p className="text-slate-600 leading-relaxed mb-6">
              Nossa arquitetura foi desenhada com base nos mais rigorosos padrões de segurança e conformidade com a LGPD. O acesso aos dados é temporário, auditado e restrito ao profissional responsável pelo atendimento ativo, garantindo a máxima proteção às informações sensíveis do paciente.
            </p>
            <ul className="space-y-4 inline-block text-left">
              <li className="flex items-center gap-3">
                <ShieldCheck className="h-6 w-6 text-emerald-500 flex-shrink-0" />
                <span>Acesso temporário e auditado por consulta.</span>
              </li>
              <li className="flex items-center gap-3">
                <ShieldCheck className="h-6 w-6 text-emerald-500 flex-shrink-0" />
                <span>Criptografia de ponta a ponta para dados em repouso e em trânsito.</span>
              </li>
              <li className="flex items-center gap-3">
                <ShieldCheck className="h-6 w-6 text-emerald-500 flex-shrink-0" />
                <span>Controle de permissões baseado no nível profissional.</span>
              </li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
