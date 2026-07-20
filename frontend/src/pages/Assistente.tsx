import { useState, type FormEvent } from 'react';
import { api, ApiError } from '../api/client';

interface Message {
  role: 'user' | 'assistant';
  text: string;
}

export function Assistente() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question) return;
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: question }, { role: 'assistant', text: 'Pensando...' }]);
    setSending(true);

    try {
      const res = await api.post<{ answer: string }>('/api/assistant/ask', { question });
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = { role: 'assistant', text: res.answer };
        return copy;
      });
    } catch (err) {
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = {
          role: 'assistant',
          text: err instanceof ApiError ? `Erro: ${err.message}` : 'Erro de conexão com o assistente.',
        };
        return copy;
      });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="container">
      <h1>Assistente IA</h1>
      <p className="muted">
        Responde com base nos dados que o sistema já coletou (preços, notícias, alertas
        recentes). Não dá recomendação de compra/venda — só explica o que já está na watchlist.
      </p>

      <div className="chat-log">
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble chat-${m.role}`}>
            {m.text}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Ex: por que a AAPL caiu hoje?"
          required
          autoComplete="off"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" disabled={sending}>
          Perguntar
        </button>
      </form>
    </div>
  );
}
