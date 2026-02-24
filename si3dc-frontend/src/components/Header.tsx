import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Activity, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

export default function Header() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const navLinks = [
    { name: 'Solução', path: '/#solution' },
    { name: 'Funcionalidades', path: '/#features' },
    { name: 'Segurança', path: '/#security' },
    { name: 'Junte-se a Nós', path: '/join-us' },
  ];

  const handleScroll = (e: React.MouseEvent<HTMLAnchorElement>, targetId: string) => {
    if (location.pathname === '/' && targetId.startsWith('#')) {
      e.preventDefault();
      const id = targetId.substring(1);
      const targetElement = document.getElementById(id);
      if (targetElement) {
        targetElement.scrollIntoView({ behavior: 'smooth' });
      }
    } else if (targetId.startsWith('/#')) {
        e.preventDefault();
        navigate('/');
        setTimeout(() => {
            const id = targetId.substring(2);
            const targetElement = document.getElementById(id);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        }, 100);
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="bg-blue-600 p-2 rounded-lg group-hover:bg-blue-700 transition-colors">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <span className="font-bold text-xl text-slate-900 tracking-tight">SI3DC</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                onClick={(e) => handleScroll(e, link.path)}
                className={`text-sm font-medium transition-colors text-slate-600 hover:text-blue-600`}
              >
                {link.name}
              </Link>
            ))}
            <Link
              to="/login"
              className="px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors shadow-sm hover:shadow-md"
            >
              Acessar Plataforma
            </Link>
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 text-slate-600 hover:text-blue-600 transition-colors"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-white border-t border-slate-100 overflow-hidden"
          >
            <div className="px-4 py-4 space-y-4">
              {navLinks.map((link) => (
                <Link
                  key={link.name}
                  to={link.path}
                  onClick={(e) => { handleScroll(e, link.path); setIsOpen(false); }}
                  className={`block text-base font-medium text-slate-600 hover:text-blue-600`}
                >
                  {link.name}
                </Link>
              ))}
              <Link
                to="/login"
                onClick={() => setIsOpen(false)}
                className="block w-full text-center px-5 py-3 bg-blue-600 text-white text-base font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                Acessar Plataforma
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
