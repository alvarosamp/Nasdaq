import { MarketingLayout } from '../components/marketing/MarketingLayout';
import { ApplicationCard } from '../components/marketing/ApplicationCard';
import { applications } from '../content/onebMarketing';

export function Aplicacoes() {
  return (
    <MarketingLayout>
      <main className="oneb-page oneb-section">
        <section className="oneb-section-heading compact">
          <p className="oneb-eyebrow">Aplicacoes OneB</p>
          <h1>O MVP funcionando como rotina de estudo e decisao.</h1>
          <p>
            A OneB combina escola, terminal financeiro e explicacao por IA em poucos fluxos bem definidos:
            aprender, monitorar, receber alerta e revisar risco.
          </p>
        </section>

        <section className="oneb-app-grid">
          {applications.map((app, index) => (
            <ApplicationCard key={app.key} app={app} index={index} />
          ))}
        </section>
      </main>
    </MarketingLayout>
  );
}
