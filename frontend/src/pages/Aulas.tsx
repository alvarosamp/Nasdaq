import { Link } from 'react-router-dom';
import { MarketingLayout } from '../components/marketing/MarketingLayout';
import { courseTracks } from '../content/onebMarketing';

const filters = ['Todos', 'Iniciante', 'Intermediario', 'Avancado', 'Analise tecnica', 'Risco', 'Estrategia', 'IA', 'Psicologia'];

export function Aulas() {
  return (
    <MarketingLayout>
      <main className="oneb-page oneb-section oneb-learning-page">
        <section className="oneb-page-hero">
          <div>
            <p className="oneb-eyebrow">Escola OneB</p>
            <h1>Construa sua evolucao no mercado com pratica e processo.</h1>
            <p>
              Trilhas por nivel, aulas recentes, pratica guiada e revisao para estudar com a mesma seriedade de uma
              mesa profissional, sem prometer sinal certo.
            </p>
          </div>
          <aside className="oneb-progress-card circular">
            <div className="oneb-circle">65%</div>
            <div>
              <span>Progresso geral</span>
              <p>Voce concluiu 48 de 72 aulas.</p>
              <Link to="/login">Ver historico completo</Link>
            </div>
          </aside>
        </section>

        <section className="oneb-learning-summary">
          <article>
            <span>Sequencia</span>
            <strong>12 dias</strong>
            <p>Ritmo constante de estudo.</p>
          </article>
          <article>
            <span>Certificado</span>
            <strong>78%</strong>
            <p>Faltam 8 aulas para liberar.</p>
          </article>
          <article>
            <span>Proximo passo</span>
            <strong>Gestao de Risco</strong>
            <p>Recomendado antes do simulador.</p>
          </article>
        </section>

        <section className="oneb-continue">
          <div>
            <p className="oneb-eyebrow">Continue de onde parou</p>
            <h2>Price Action na Pratica</h2>
            <p>Retome a aula de contexto, gatilho e invalidacao no ponto exato em que parou.</p>
          </div>
          <Link to="/aulas/analise-tecnica-avancada" className="oneb-primary">
            Continuar aula
          </Link>
        </section>

        <div className="oneb-filters">
          {filters.map((filter) => (
            <button key={filter} className={filter === 'Todos' ? 'active' : ''} type="button">
              {filter}
            </button>
          ))}
        </div>

        <div className="oneb-course-track-grid">
          {courseTracks.map((track) => (
            <article key={track.title} className={`oneb-course-track ${track.status === 'Bloqueado' ? 'locked' : ''}`}>
              <div className="course-track-thumb">
                <span>{track.theme}</span>
              </div>
              <div className="course-track-body">
                <div className="course-track-top">
                  <span>{track.level}</span>
                  <small>{track.status}</small>
                </div>
                <h2>{track.title}</h2>
                <p>Aula, checklist, exercicio pratico e simulacao para aplicar o conceito em cenario controlado.</p>
                <div className="course-track-progress">
                  <i style={{ width: `${track.progress}%` }} />
                </div>
                <Link to={track.status === 'Bloqueado' ? '/planos' : `/aulas/${track.slug}`}>
                  {track.status === 'Bloqueado' ? 'Desbloquear trilha' : 'Abrir trilha'}
                </Link>
              </div>
            </article>
          ))}
        </div>
      </main>
    </MarketingLayout>
  );
}
