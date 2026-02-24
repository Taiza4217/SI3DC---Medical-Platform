import React from 'react';
import { Mail, Phone, MapPin, Linkedin, Twitter, Globe } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 py-12 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <h3 className="text-white text-xl font-bold mb-4">SI3DC</h3>
            <p className="text-slate-400 mb-6 max-w-sm leading-relaxed">
              Sistema Inteligente de Integração, Interpretação e Apoio à Decisão Clínica.
              Transformando dados em segurança para o paciente.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-slate-400 hover:text-white transition-colors">
                <Linkedin className="h-5 w-5" />
              </a>
              <a href="#" className="text-slate-400 hover:text-white transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="#" className="text-slate-400 hover:text-white transition-colors">
                <Globe className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Institucional</h4>
            <ul className="space-y-2">
              <li><a href="#" className="hover:text-blue-400 transition-colors">Sobre Nós</a></li>
              <li><a href="#" className="hover:text-blue-400 transition-colors">Tecnologia HAI-DEF</a></li>
              <li><a href="#" className="hover:text-blue-400 transition-colors">Parceiros</a></li>
              <li><a href="#" className="hover:text-blue-400 transition-colors">Carreiras</a></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-white font-semibold mb-4">Contato</h4>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <MapPin className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" />
                <span>Av. Paulista, 1000 - Bela Vista<br />São Paulo - SP</span>
              </li>
              <li className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-blue-500 shrink-0" />
                <span>+55 (11) 3000-0000</span>
              </li>
              <li className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-blue-500 shrink-0" />
                <span>contato@si3dc.med.br</span>
              </li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-slate-800 mt-12 pt-8 text-center text-sm text-slate-500">
          &copy; {new Date().getFullYear()} SI3DC - Todos os direitos reservados.
        </div>
      </div>
    </footer>
  );
}
