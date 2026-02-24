import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const historyData: { [key: string]: { title: string, content: React.ReactNode } } = {
  'saude': {
    title: 'Histórico de Saúde Geral',
    content: (
      <div className="prose max-w-none">
        <h4>Doenças Diagnosticadas</h4>
        <ul>
          <li>Hipertensão Arterial Sistêmica (HAS) - CID I10</li>
          <li>Diabetes Mellitus Tipo 2 (DM2) - CID E11</li>
          <li>Dislipidemia - CID E78</li>
        </ul>
        <h4>Histórico Familiar</h4>
        <p>Pai com histórico de Infarto Agudo do Miocárdio aos 55 anos. Mãe com DM2.</p>
        <h4>Evolução Clínica</h4>
        <p>Paciente segue em acompanhamento regular com cardiologista e endocrinologista, com bom controle pressórico e glicêmico em uso das medicações prescritas.</p>
      </div>
    )
  },
  'exames': {
    title: 'Histórico de Exames',
    content: (
      <div className="prose max-w-none">
        <h4>Exames Laboratoriais Recentes (15/01/2026)</h4>
        <ul>
          <li>Hemoglobina Glicada (HbA1c): <strong>7.2%</strong> (Meta: &lt;7.0%) - <span className='text-red-600'>Levemente alterado</span></li>
          <li>Colesterol LDL: <strong>95 mg/dL</strong> (Meta: &lt;100 mg/dL)</li>
          <li>Creatinina: <strong>1.1 mg/dL</strong> (Função renal preservada)</li>
        </ul>
        <h4>Exames de Imagem</h4>
        <p><strong>Ecocardiograma (05/11/2025):</strong> Fração de ejeção de 60%, sem alterações segmentares.</p>
        <p><strong>Raio-X de Tórax (05/11/2025):</strong> Sem sinais de congestão pulmonar.</p>
      </div>
    )
  },
  'medicamentoso': {
    title: 'Histórico Medicamentoso e Alérgico',
    content: (
      <div className="prose max-w-none">
        <h4>Medicamentos em Uso Contínuo</h4>
        <ul>
          <li>Losartana 50mg - 1x ao dia</li>
          <li>Metformina 850mg - 2x ao dia</li>
          <li>AAS 100mg - 1x ao dia</li>
          <li>Sinvastatina 20mg - 1x à noite</li>
        </ul>
        <h4>Alergias Conhecidas</h4>
        <p className='text-red-700 font-bold'>Alergia grave a Penicilina, com relato de anafilaxia.</p>
      </div>
    )
  },
  'mental': {
    title: 'Histórico de Saúde Mental',
    content: <p>Nenhum diagnóstico psiquiátrico ou tratamento psicológico registrado no sistema.</p>
  },
  'odontologico': {
    title: 'Histórico Odontológico',
    content: <p>Acompanhamento odontológico regular, sem registros de procedimentos cirúrgicos ou infecções relevantes.</p>
  },
  'tratamentos': {
    title: 'Histórico de Tratamentos e Cirurgias',
    content: (
      <div className="prose max-w-none">
        <h4>Cirurgias Realizadas</h4>
        <ul>
          <li><strong>Revascularização do Miocárdio (Ponte de Safena)</strong> - 2021</li>
          <li>Apendicectomia - 2005</li>
        </ul>
        <h4>Internações</h4>
        <p>Nenhuma internação nos últimos 5 anos, exceto pela cirurgia cardíaca.</p>
      </div>
    )
  }
};

export default function HistoryPage() {
  const [searchParams] = useSearchParams();
  const type = searchParams.get('type') || 'saude';
  const from = searchParams.get('from') || '/search-patient';
  const data = historyData[type];

  return (
    <div className="min-h-screen bg-slate-100 p-8">
      <div className="max-w-4xl mx-auto">
        <Link to={from} className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-blue-600 mb-6">
          <ArrowLeft className="h-4 w-4" />
          Voltar para o prontuário
        </Link>
        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
          <h1 className="text-3xl font-bold text-slate-900 mb-6">{data.title}</h1>
          <div>{data.content}</div>
        </div>
      </div>
    </div>
  );
}
