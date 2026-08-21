import { Link } from 'react-router-dom';
import type { applications } from '../../content/onebMarketing';

type Application = (typeof applications)[number];

export function ApplicationCard({ app, index }: { app: Application; index: number }) {
  return (
    <article className={`oneb-app-card app-${app.key}`}>
      <div className="oneb-app-preview" aria-hidden="true">
        <div className="app-preview-top">
          <span>{app.category}</span>
          <b>{String(index + 1).padStart(2, '0')}</b>
        </div>
        <div className="app-preview-body">
          <div className="app-preview-chart">
            {[38, 64, 52, 78, 58, 88].map((height) => (
              <i key={height} style={{ height: `${height}%` }} />
            ))}
          </div>
          <div className="app-preview-side">
            <span />
            <span />
            <span />
          </div>
        </div>
      </div>
      <div className="oneb-app-content">
        <span className="oneb-app-category">{app.category}</span>
        <h3>{app.title}</h3>
        <p>{app.description}</p>
        <div className="oneb-app-metrics">
          {app.metrics.map((metric) => (
            <small key={metric}>{metric}</small>
          ))}
        </div>
        <Link to={app.href}>Abrir aplicação →</Link>
      </div>
    </article>
  );
}
