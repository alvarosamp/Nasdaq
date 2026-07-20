import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { api, ApiError } from '../api/client';

interface Message {
  role: 'user' | 'assistant';
  text: string;
  createdAt: string;
  pending?: boolean;
}

const SUGGESTIONS = [
  'Quais ativos da minha watchlist merecem mais atencao agora?',
  'Resuma os alertas recentes e explique os riscos.',
  'Tem algum earnings proximo que pode mexer com a carteira?',
  'Compare noticias recentes com a variacao dos ativos.',
  'Monte um checklist para validar uma possivel entrada.',
];

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

export function Assistente() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      text:
        'Oi. Eu consigo analisar a sua watchlist, noticias, alertas e precos ja coletados. ' +
        'Pergunte algo sobre um ativo, um alerta, risco de evento ou contexto de mercado.',
      createdAt: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  async function ask(question: string) {
    const cleanQuestion = question.trim();
    if (!cleanQuestion || sending) return;

    const now = new Date().toISOString();
    const history = messages
      .filter((m) => !m.pending)
      .slice(-8)
      .map((m) => ({ role: m.role, text: m.text }));

    setInput('');
    setMessages((prev) => [
      ...prev,
      { role: 'user', text: cleanQuestion, createdAt: now },
      { role: 'assistant', text: 'Analisando os dados disponiveis...', createdAt: now, pending: true },
    ]);
    setSending(true);

    try {
      const res = await api.post<{ answer: string }>('/api/assistant/ask', { question: cleanQuestion, history });
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = {
          role: 'assistant',
          text: res.answer,
          createdAt: new Date().toISOString(),
        };
        return copy;
      });
    } catch (err) {
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = {
          role: 'assistant',
          text: err instanceof ApiError ? `Erro: ${err.message}` : 'Erro de conexao com o assistente.',
          createdAt: new Date().toISOString(),
        };
        return copy;
      });
    } finally {
      setSending(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    ask(input);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      ask(input);
    }
  }

  return (
    <div className="container assistant-container">
      <div className="page-header">
        <div>
          <p className="eyebrow">Chatbot de mercado</p>
          <h1>Assistente IA</h1>
          <p className="muted">
            Conversa com os dados ja coletados pelo sistema: watchlist, precos, noticias e alertas.
            Use como analista auxiliar, nao como ordem de compra ou venda.
          </p>
        </div>
        <button type="button" className="btn-link" onClick={() => setMessages([])} disabled={sending}>
          Limpar chat
        </button>
      </div>

      <section className="assistant-shell">
        <aside className="assistant-sidebar">
          <h2>Perguntas rapidas</h2>
          <div className="prompt-list">
            {SUGGESTIONS.map((suggestion) => (
              <button type="button" key={suggestion} onClick={() => ask(suggestion)} disabled={sending}>
                {suggestion}
              </button>
            ))}
          </div>
          <div className="quality-box warn">
            <strong>Limite importante</strong>
            <span>A IA so sabe o que esta no banco do app. Ela nao consulta corretora nem executa ordens.</span>
          </div>
        </aside>

        <div className="chat-panel">
          <div className="chat-log">
            {messages.length === 0 ? (
              <div className="chat-empty">
                <strong>Conversa limpa.</strong>
                <span>Escolha uma pergunta rapida ou escreva sua propria analise.</span>
              </div>
            ) : (
              messages.map((m, i) => (
                <article key={`${m.createdAt}-${i}`} className={`chat-message chat-${m.role}`}>
                  <div className="chat-meta">
                    <strong>{m.role === 'user' ? 'Voce' : 'Assistente'}</strong>
                    <span>{fmtTime(m.createdAt)}</span>
                  </div>
                  <div className={`chat-bubble ${m.pending ? 'is-pending' : ''}`}>{m.text}</div>
                </article>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          <form className="chat-form" onSubmit={handleSubmit}>
            <textarea
              placeholder="Ex: compare NVDA e AAPL com base nos alertas e noticias recentes..."
              required
              autoComplete="off"
              value={input}
              rows={3}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <div className="chat-actions">
              <span className="muted">Perguntas melhores geram analises melhores.</span>
              <button type="submit" disabled={sending || !input.trim()}>
                {sending ? 'Analisando...' : 'Enviar'}
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}
