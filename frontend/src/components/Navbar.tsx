import { useEffect, useRef, useState } from 'react';
import { Bell, ChevronDown, FileDown, LogOut, Menu, Moon, Search, Sun, User, X } from 'lucide-react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { fetchBlob } from '../api/client';
import { useToast } from '../context/ToastContext';
import { useTheme } from '../context/ThemeContext';

const terminalRoutes = new Set([
  '/ferramenta',
  '/watchlist',
  '/mercado',
  '/analise-matinal',
  '/resumo-diario',
  '/inteligencia',
  '/mesa-ia',
  '/mesa-tecnica',
  '/regime',
  '/alertas',
  '/posicoes',
  '/operacoes',
  '/copiloto',
  '/assistente',
  '/saas',
  '/como-usar',
]);

export function Navbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const userMenuRef = useRef<HTMLDivElement | null>(null);
  const inTerminal = terminalRoutes.has(location.pathname) || location.pathname.startsWith('/ativo/');

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!user) return null;

  function handleLogout() {
    logout();
    navigate('/login');
  }

  async function handleDownloadPdf() {
    setDownloading(true);
    try {
      const blob = await fetchBlob('/api/reports/pdf');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `oneb-relatorio-${new Date().toISOString().slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast('Erro ao gerar o relatorio PDF', 'error');
    } finally {
      setDownloading(false);
      setUserMenuOpen(false);
    }
  }

  return (
    <header className="topbar app-topbar">
      <NavLink to="/inicio" className="brand oneb-app-brand" onClick={() => setMenuOpen(false)}>
        <span className="brand-mark" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        <span>
          OneB
          <small>Escola de Investimentos</small>
        </span>
      </NavLink>

      <button
        type="button"
        className="nav-toggle-label"
        aria-label={menuOpen ? 'Fechar menu' : 'Abrir menu'}
        onClick={() => setMenuOpen((value) => !value)}
      >
        {menuOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      <nav className={`app-topbar-nav ${menuOpen ? 'open' : ''}`}>
        <div className="workspace-switcher" aria-label="Ambiente OneB">
          <NavLink to="/inicio" end onClick={() => setMenuOpen(false)}>
            Escola
          </NavLink>
          <NavLink to="/ferramenta" className={inTerminal ? 'active' : ''} onClick={() => setMenuOpen(false)}>
            Terminal
          </NavLink>
        </div>
        <NavLink to="/aprendizado" onClick={() => setMenuOpen(false)}>
          Aulas
        </NavLink>
        <NavLink to="/lives" onClick={() => setMenuOpen(false)}>
          Lives
        </NavLink>
      </nav>

      <div className="topbar-actions">
        <span className="market-status">
          <i />
          Mercado aberto
        </span>
        <button type="button" className="icon-button" aria-label="Pesquisar">
          <Search size={18} />
        </button>
        <button type="button" className="icon-button" aria-label="Notificacoes">
          <Bell size={18} />
        </button>
        <button type="button" className="icon-button" onClick={toggleTheme} aria-label="Alternar tema">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <div className="user-menu" ref={userMenuRef}>
          <button
            type="button"
            className="user-menu-trigger"
            onClick={() => setUserMenuOpen((value) => !value)}
          >
            <span className="avatar-dot">{user.username.slice(0, 1).toUpperCase()}</span>
            <span className="user-menu-name">{user.username}</span>
            <ChevronDown size={16} className="user-menu-caret" />
          </button>
          {userMenuOpen && (
            <div className="user-menu-dropdown">
              <NavLink to="/perfil" className="user-menu-item" onClick={() => setUserMenuOpen(false)}>
                <User size={16} />
                Perfil
              </NavLink>
              <NavLink to="/saas" className="user-menu-item" onClick={() => setUserMenuOpen(false)}>
                <User size={16} />
                Workspace
              </NavLink>
              <button type="button" className="user-menu-item" onClick={handleDownloadPdf} disabled={downloading}>
                <FileDown size={16} />
                {downloading ? 'Gerando PDF...' : 'Baixar PDF'}
              </button>
              <button type="button" className="user-menu-item user-menu-danger" onClick={handleLogout}>
                <LogOut size={16} />
                Sair
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
