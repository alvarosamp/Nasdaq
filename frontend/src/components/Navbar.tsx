import { useEffect, useRef, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { fetchBlob } from '../api/client';
import { useToast } from '../context/ToastContext';
import { useTheme } from '../context/ThemeContext';

export function Navbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const toast = useToast();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const userMenuRef = useRef<HTMLDivElement | null>(null);

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
      toast('Erro ao gerar o relatório PDF', 'error');
    } finally {
      setDownloading(false);
      setUserMenuOpen(false);
    }
  }

  return (
    <header className="topbar">
      <NavLink to="/" className="brand">
        OneB
      </NavLink>
      <input
        type="checkbox"
        id="nav-toggle"
        className="nav-toggle-input"
        checked={menuOpen}
        onChange={(e) => setMenuOpen(e.target.checked)}
      />
      <label htmlFor="nav-toggle" className="nav-toggle-label" aria-label="Abrir menu">
        ☰
      </label>
      <nav>
        <NavLink to="/" end>
          Início
        </NavLink>
        <NavLink to="/aulas">Aulas</NavLink>
        <NavLink to="/lives">Lives</NavLink>
        <NavLink to="/ferramenta">Ferramenta</NavLink>

        <button type="button" className="nav-link theme-toggle" onClick={toggleTheme} aria-label="Alternar Tema">
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>

        <div className="user-menu" ref={userMenuRef}>
          <button
            type="button"
            className="user-menu-trigger"
            onClick={() => setUserMenuOpen((v) => !v)}
          >
            {user.username}
            <span className="user-menu-caret">▾</span>
          </button>
          {userMenuOpen && (
            <div className="user-menu-dropdown">
              <NavLink to="/perfil" className="user-menu-item" onClick={() => setUserMenuOpen(false)}>
                Perfil
              </NavLink>
              <button type="button" className="user-menu-item" onClick={handleDownloadPdf} disabled={downloading}>
                {downloading ? 'Gerando PDF...' : 'Baixar PDF'}
              </button>
              <button type="button" className="user-menu-item user-menu-danger" onClick={handleLogout}>
                Sair
              </button>
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}
