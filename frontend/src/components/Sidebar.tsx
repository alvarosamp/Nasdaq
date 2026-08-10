import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const GROUPS: { label: string; items: { to: string; label: string }[] }[] = [
  {
    label: 'Visão geral',
    items: [
      { to: '/ferramenta', label: 'Dashboard' },
      { to: '/resumo-diario', label: 'Resumo Diário' },
      { to: '/analise-matinal', label: 'Análise Matinal' },
    ],
  },
  {
    label: 'Mercado',
    items: [
      { to: '/mercado', label: 'Mercado' },
      { to: '/regime', label: 'Regime' },
      { to: '/inteligencia', label: 'Inteligência' },
      { to: '/mesa-tecnica', label: 'Mesa Técnica' },
    ],
  },
  {
    label: 'Mentor IA',
    items: [
      { to: '/mesa-ia', label: 'Mesa IA' },
      { to: '/copiloto', label: 'Copiloto' },
      { to: '/assistente', label: 'Assistente IA' },
    ],
  },
  {
    label: 'Operação',
    items: [
      { to: '/watchlist', label: 'Watchlist & Regras' },
      { to: '/operacoes', label: 'Operações' },
      { to: '/alertas', label: 'Alertas' },
      { to: '/posicoes', label: 'Posições' },
    ],
  },
];

export function Sidebar() {
  const { user } = useAuth();

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {GROUPS.map((group) => (
          <div className="sidebar-group" key={group.label}>
            <p className="sidebar-group-label">{group.label}</p>
            {group.items.map((item) => (
              <NavLink key={item.to} to={item.to} className="sidebar-link">
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
        <div className="sidebar-group">
          <p className="sidebar-group-label">Conta</p>
          <NavLink to="/saas" className="sidebar-link">
            SaaS
          </NavLink>
          <NavLink to="/como-usar" className="sidebar-link">
            Como usar
          </NavLink>
          {user?.is_admin && (
            <NavLink to="/usuarios" className="sidebar-link">
              Usuários
            </NavLink>
          )}
        </div>
      </nav>
    </aside>
  );
}
