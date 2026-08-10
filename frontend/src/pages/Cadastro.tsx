import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ApiError } from '../api/client';

export function Cadastro() {
  const { cadastro } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (username.trim().length < 3) {
      setError('Usuario precisa ter pelo menos 3 caracteres.');
      return;
    }
    if (password.length < 8) {
      setError('Senha precisa ter pelo menos 8 caracteres.');
      return;
    }
    if (password !== passwordConfirm) {
      setError('As senhas nao coincidem.');
      return;
    }

    setSubmitting(true);
    try {
      await cadastro(username, password);
      navigate('/inicio', { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Erro ao criar conta. Tente de novo.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-body">
      <main className="auth-shell">
        <div className="auth-card">
          <div className="auth-brand">OneB · Escola de Investimentos</div>
          <h1>Criar conta</h1>
          <p className="muted">Cadastre seu usuario e senha para entrar no sistema.</p>
          {error && <p className="form-error">{error}</p>}
          <form className="auth-form" onSubmit={handleSubmit}>
            <label className="field-label">
              Usuario
              <input
                type="text"
                autoComplete="username"
                minLength={3}
                required
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </label>
            <label className="field-label">
              Senha
              <input
                type="password"
                autoComplete="new-password"
                minLength={8}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            <label className="field-label">
              Confirmar senha
              <input
                type="password"
                autoComplete="new-password"
                minLength={8}
                required
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
              />
            </label>
            <button type="submit" className="auth-submit" disabled={submitting}>
              {submitting ? 'Criando...' : 'Criar conta'}
            </button>
          </form>
          <p className="auth-footer-link">
            Ja tem conta? <Link to="/login">Entrar</Link>
          </p>
        </div>
        <p className="disclaimer auth-disclaimer">
          Ferramenta apenas de monitoramento e sugestao. Nao executa ordens e nao constitui
          recomendacao de investimento.
        </p>
      </main>
    </div>
  );
}
