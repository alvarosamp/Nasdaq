import { Link } from 'react-router-dom';

const steps = [
  {
    title: '1. Monte a watchlist',
    text: 'Cadastre os ativos que voce quer acompanhar e mantenha so os simbolos realmente relevantes ativos.',
    link: '/watchlist',
    label: 'Abrir watchlist',
  },
  {
    title: '2. Crie regras objetivas',
    text: 'Use preco, variacao, RSI, medias, MACD e volume. Prefira regras compostas e teste o historico antes de salvar.',
    link: '/watchlist',
    label: 'Criar regras',
  },
  {
    title: '3. Leia o dashboard por prioridade',
    text: 'Comece pelo radar: score alto pede investigacao. Depois confira qualidade do dado, noticias, eventos e alertas.',
    link: '/',
    label: 'Ver dashboard',
  },
  {
    title: '4. Valide risco e posicao',
    text: 'Registre compras e vendas para acompanhar exposicao, P&L e tamanho real do risco antes de qualquer nova decisao.',
    link: '/posicoes',
    label: 'Ver posicoes',
  },
  {
    title: '5. Use a IA como analista auxiliar',
    text: 'Pergunte o motivo de um movimento, mas trate a resposta como explicacao dos dados coletados, nao como ordem.',
    link: '/assistente',
    label: 'Abrir IA',
  },
];

export function ComoUsar() {
  return (
    <div className="container">
      <div className="page-header">
        <div>
          <p className="eyebrow">Manual rapido</p>
          <h1>Como usar o Monitor NASDAQ</h1>
          <p className="muted">
            O objetivo e transformar dados soltos em um processo de decisao: triagem, validacao,
            risco e acompanhamento. Ele nao executa ordens e nao substitui sua decisao.
          </p>
        </div>
      </div>

      <section className="guide-grid">
        {steps.map((step) => (
          <article className="guide-card" key={step.title}>
            <h2>{step.title}</h2>
            <p>{step.text}</p>
            <Link to={step.link}>{step.label}</Link>
          </article>
        ))}
      </section>

      <section className="panel">
        <h2>Fluxo recomendado para analisar uma acao</h2>
        <ol className="decision-list">
          <li>Confirme se o dado esta recente e se a fonte faz sentido para o tipo de analise.</li>
          <li>Veja se o ativo esta no radar por movimento de preco, noticia, alerta ou evento proximo.</li>
          <li>Abra o grafico do ativo e compare preco, medias, RSI, MACD e volume.</li>
          <li>Cheque noticias e earnings antes de aceitar qualquer sinal tecnico.</li>
          <li>Defina cenario de entrada, alvo, stop, perda maxima e tamanho da posicao.</li>
          <li>Registre a operacao em Posicoes para medir resultado e aprender com historico.</li>
        </ol>
      </section>

      <section className="panel">
        <h2>Como interpretar o score</h2>
        <p className="muted">
          O score do dashboard e uma triagem operacional. Ele combina variacao do dia, alertas,
          noticias, eventos de earnings e idade da cotacao. Score alto nao significa compra; significa
          que o ativo merece investigacao primeiro.
        </p>
      </section>
    </div>
  );
}
