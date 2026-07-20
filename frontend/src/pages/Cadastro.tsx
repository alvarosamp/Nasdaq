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
  const [closed, setClosed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (username.trim().length < 3) {
      setError('Usuário precisa ter pelo menos 3 caracteres.');
      return;
    }
    if (password.length < 8) {
      setError('Senha precisa ter pelo menos 8 caracteres.');
      return;
    }
    if (password !== passwordConfirm) {
      setError('As senhas não coincidem.');
      return;
    }

    setSubmitting(true);
    try {
      await cadastro(username, password);
      navigate('/', { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setClosed(true);
      } else {
        setError(err instanceof ApiError ? err.message : 'Erro ao criar conta. Tente de novo.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-body">
      <main className="auth-shell">
        <div className="auth-card">
          <div className="auth-brand">📈 Monitor NASDAQ</div>
          {closed ? (
            <>
              <h1>Cadastro fechado</h1>
              <p className="muted">
                Já existe uma conta configurada neste sistema. Novas contas só podem ser criadas
                por um administrador já logado.
              </p>
              <p className="auth-footer-link">
                <Link to="/login">Voltar para o login</Link>
              </p>
            </>
          ) : (
            <>
              <h1>Criar a primeira conta</h1>
              <p className="muted">
                Você é a primeira pessoa a acessar este sistema, então essa conta vira
                administradora automaticamente. Depois deste cadastro, essa tela se fecha e
                novas contas só podem ser criadas por um admin.
              </p>
              {error && <p className="form-error">{error}</p>}
              <form className="auth-form" onSubmit={handleSubmit}>
                <label className="field-label">
                  Usuário
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
                Já tem conta? <Link to="/login">Entrar</Link>
              </p>
            </>
          )}
        </div>
        <p className="disclaimer auth-disclaimer">
          Ferramenta apenas de monitoramento e sugestão. Não executa ordens e não constitui
          recomendação de investimento.
        </p>
      </main>
    </div>
  );
}
