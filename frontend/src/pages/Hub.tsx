import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const SECTIONS = [
  {
    to: '/aulas',
    title: 'Aulas',
    description: 'Trilhas, módulos e aulas gravadas da escola. Continue de onde parou.',
    tag: 'Escola',
  },
  {
    to: '/lives',
    title: 'Lives',
    description: 'Salas de mercado em tempo real e replays das últimas transmissões.',
    tag: 'Ao vivo',
  },
  {
    to: '/ferramenta',
    title: 'Ferramenta de Trading',
    description: 'Watchlist, radar de ativos, copiloto de decisão e mesa técnica.',
    tag: 'Ferramenta',
  },
  {
    to: '/perfil',
    title: 'Perfil & Assinatura',
    description: 'Dados da conta, plano atual e preferências.',
    tag: 'Conta',
  },
];

export function Hub() {
  const { user } = useAuth();

  return (
    <div className="container dashboard-container">
      <div className="page-header">
        <div>
          <p className="eyebrow">OneB · Escola de Investimentos</p>
          <h1>Olá, {user?.username}</h1>
          <p className="muted">Escolha uma seção para continuar.</p>
        </div>
      </div>

      <section className="hub-grid">
        {SECTIONS.map((section) => (
          <Link key={section.to} to={section.to} className="hub-card">
            <span className="hub-card-tag">{section.tag}</span>
            <h2>{section.title}</h2>
            <p className="muted">{section.description}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}
