import { Link } from 'react-router-dom';
import { MarketingLayout } from '../components/marketing/MarketingLayout';
import { StrategyCard } from '../components/marketing/StrategyCard';
import { strategies } from '../content/onebMarketing';

const filters = ['Todas', 'Iniciante', 'Intermediario', 'Avancado', 'Mercado americano', 'Analise tecnica', 'Gestao de risco'];

export function Estrategias() {
  return (
    <MarketingLayout>
      <main className="oneb-page oneb-section">
        <section className="oneb-page-hero">
          <div>
            <p className="oneb-eyebrow">Metodo OneB</p>
            <h1>Aprenda estrategias como processo, nao como promessa.</h1>
            <p>
              Conteudo pratico para entender contexto, risco, invalidacao e revisao antes de qualquer decisao no mercado.
            </p>
          </div>
          <aside className="oneb-progress-card circular">
            <div className="oneb-circle">65%</div>
            <div>
              <span>Seu progresso</span>
              <p>Voce concluiu 48 de 72 aulas.</p>
              <Link to="/login">Ver meu progresso</Link>
            </div>
          </aside>
        </section>
        <div className="oneb-filters">
          {filters.map((filter) => (
            <button key={filter} className={filter === 'Todas' ? 'active' : ''} type="button">
              {filter}
            </button>
          ))}
        </div>
        <div className="oneb-strategy-grid">
          {strategies.map((strategy, index) => (
            <StrategyCard key={strategy.title} strategy={strategy} index={index} />
          ))}
        </div>
      </main>
    </MarketingLayout>
  );
}
