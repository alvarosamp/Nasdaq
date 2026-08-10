import { Link } from 'react-router-dom';

const FEATURES = [
  {
    tag: 'Escola',
    title: 'Aulas',
    description: 'Trilhas e módulos gravados, do básico à gestão de risco avançada.',
  },
  {
    tag: 'Ao vivo',
    title: 'Lives',
    description: 'Salas de mercado em tempo real e replays das últimas transmissões.',
  },
  {
    tag: 'Terminal',
    title: 'Ferramenta de Trading',
    description: 'Watchlist, radar de ativos, mesa técnica e mesa de decisão em um só lugar.',
  },
  {
    tag: 'Mentor IA',
    title: 'Copiloto & Assistente IA',
    description: 'Análises, respostas e checklists de entrada apoiados por IA sobre seus dados.',
  },
];

export function Landing() {
  return (
    <div className="landing-body">
      <header className="landing-topbar">
        <span className="brand">OneB</span>
        <div className="landing-topbar-actions">
          <Link to="/login" className="landing-btn landing-btn-ghost">
            Entrar
          </Link>
          <Link to="/cadastro" className="landing-btn landing-btn-primary">
            Criar conta
          </Link>
        </div>
      </header>

      <main className="landing-hero">
        <p className="eyebrow">OneB · Escola de Investimentos</p>
        <h1>Aprenda, pratique e opere com um único ecossistema.</h1>
        <p className="muted landing-hero-sub">
          Cursos, lives e um terminal profissional de mercado com apoio de IA, para você evoluir
          como trader do primeiro clique à operação real.
        </p>
        <div className="landing-hero-actions">
          <Link to="/cadastro" className="landing-btn landing-btn-primary">
            Criar conta gratuita
          </Link>
          <Link to="/login" className="landing-btn landing-btn-ghost">
            Já tenho conta
          </Link>
        </div>
      </main>

      <section className="landing-features">
        {FEATURES.map((feature) => (
          <div key={feature.title} className="landing-feature-card">
            <span className="hub-card-tag">{feature.tag}</span>
            <h2>{feature.title}</h2>
            <p className="muted">{feature.description}</p>
          </div>
        ))}
      </section>

      <footer className="disclaimer">
        Ferramenta apenas de monitoramento e sugestão. Não executa ordens e não constitui
        recomendação de investimento. Dados podem ter atraso. Valide qualquer sinal antes de
        decidir.
      </footer>
    </div>
  );
}
