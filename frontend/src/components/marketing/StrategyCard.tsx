import type { strategies } from '../../content/onebMarketing';

type Strategy = (typeof strategies)[number];

export function StrategyCard({ strategy, index }: { strategy: Strategy; index: number }) {
  return (
    <article className="oneb-strategy-card">
      <div className={`oneb-card-chart chart-${index % 3}`} aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
        <span />
      </div>
      <p>{strategy.category}</p>
      <h3>{strategy.title}</h3>
      <span>{strategy.description}</span>
      <footer>
        <small>{strategy.lessons} aulas</small>
        <small>{strategy.level}</small>
        <button type="button" aria-label={`Acessar ${strategy.title}`}>
          ▶
        </button>
      </footer>
    </article>
  );
}
