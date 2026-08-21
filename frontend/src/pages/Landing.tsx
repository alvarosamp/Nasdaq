import { Link } from 'react-router-dom';
import type { CSSProperties } from 'react';
import { MarketingLayout } from '../components/marketing/MarketingLayout';

const academyItems = ['Aulas essenciais', 'Trilhas por nivel', 'Gestao de risco', 'Pratica guiada', 'Lives'];
const terminalItems = ['Watchlist', 'Alertas', 'Resumo diario', 'Posicoes manuais', 'Assistente IA'];

function TerminalHeroVisual() {
  return (
    <div className="oneb-terminal-visual" aria-label="Previa visual do OneB Terminal">
      <div className="terminal-glass-window terminal-window-main">
        <header>
          <span>OneB Terminal</span>
          <strong>NASDAQ</strong>
        </header>
        <div className="terminal-candle-board">
          {[48, 58, 46, 72, 64, 86, 74, 94, 82].map((height, index) => (
            <i key={`${height}-${index}`} style={{ height: `${height}%` }} />
          ))}
        </div>
        <footer>
          <span>Regime BULL</span>
          <span>RSI 58.4</span>
          <span>Risco 1.2%</span>
        </footer>
      </div>
      <div className="terminal-glass-window terminal-window-side">
        <span>Mesa IA</span>
        <strong>NO_TRADE</strong>
        <small>Dado fraco ou risco alto vira motivo para esperar, nao para forcar entrada.</small>
      </div>
      <div className="metal-candles" aria-hidden="true">
        {[0, 1, 2, 3, 4].map((item) => (
          <span key={item} style={{ '--i': item } as CSSProperties}>
            <i />
          </span>
        ))}
      </div>
    </div>
  );
}

function EcosystemCard({ title, subtitle, items, to }: { title: string; subtitle: string; items: string[]; to: string }) {
  return (
    <article className="ecosystem-card-pro">
      <div>
        <p className="oneb-eyebrow">{subtitle}</p>
        <h3>{title}</h3>
      </div>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <Link to={to} className="oneb-secondary">
        Abrir ambiente
      </Link>
    </article>
  );
}

export function Landing() {
  return (
    <MarketingLayout>
      <main>
        <section className="oneb-hero oneb-section oneb-hero-redesign">
          <div className="oneb-hero-copy oneb-reveal">
            <p className="oneb-eyebrow">ONEB - ESCOLA + TERMINAL</p>
            <h1>
              Aprenda mercado.
              <br />
              Pratique com dados.
              <br />
              Decida com metodo.
            </h1>
            <p>
              A OneB une escola de investimentos e ferramenta de monitoramento para transformar estudo,
              alertas, risco e revisao em uma rotina simples de decisao.
            </p>
            <div className="oneb-hero-actions">
              <a href="#ecossistema" className="oneb-primary">
                Ver MVP
              </a>
              <Link to="/login" className="oneb-secondary">
                Entrar na plataforma
              </Link>
            </div>
          </div>
          <TerminalHeroVisual />
        </section>

        <section className="oneb-section ecosystem-section" id="ecossistema">
          <div className="oneb-section-heading split">
            <div>
              <p className="oneb-eyebrow">Um ecossistema</p>
              <h2>Do estudo a decisao.</h2>
            </div>
            <p>
              O MVP fica claro: a escola ensina o metodo, o terminal ajuda o aluno a aplicar esse metodo
              em watchlist, alertas, resumo diario e gestao de risco.
            </p>
          </div>
          <div className="ecosystem-grid-pro">
            <EcosystemCard title="OneB Escola" subtitle="Aprendizado" items={academyItems} to="/aulas" />
            <EcosystemCard title="OneB Terminal" subtitle="Aplicacao" items={terminalItems} to="/ferramenta" />
          </div>
        </section>

        <section className="oneb-section product-preview-section">
          <div className="oneb-section-heading">
            <p className="oneb-eyebrow">MVP viavel</p>
            <h2>O que precisa funcionar muito bem no primeiro produto.</h2>
          </div>
          <div className="product-preview-grid">
            <article>
              <span>Escola</span>
              <h3>Aulas com aplicacao pratica</h3>
              <p>Trilhas, progresso, checklist e exercicios conectados ao uso real do terminal.</p>
            </article>
            <article>
              <span>Terminal</span>
              <h3>Watchlist, alertas e resumo diario</h3>
              <p>Ativos acompanhados, regras de alerta, noticias, eventos e historico para revisao.</p>
            </article>
            <article>
              <span>Risco</span>
              <h3>Decisao com explicacao</h3>
              <p>NO_TRADE quando os dados estiverem fracos, IA explicando contexto e posicoes manuais.</p>
            </article>
          </div>
        </section>

        <section className="oneb-final-cta oneb-section final-cta-redesign">
          <div>
            <h2>O MVP e uma escola com ferramenta, nao uma promessa de sinal certo.</h2>
            <p>Comece pela rotina: estudar, monitorar, receber alertas, revisar risco e decidir melhor.</p>
          </div>
          <Link to="/cadastro" className="oneb-primary">
            Criar conta
          </Link>
        </section>
      </main>
    </MarketingLayout>
  );
}
