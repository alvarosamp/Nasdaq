# Monitor NASDAQ

Sistema de **monitoramento e alerta** (não executa ordens) para uma watchlist de ações da
NASDAQ. Acompanha preço/volume, calcula indicadores técnicos (SMA, EMA, RSI, MACD, Bollinger,
volume médio) e dispara alertas configuráveis via **Telegram** e num **dashboard web**.

> ⚠️ Ferramenta de apoio à decisão. Não é recomendação de investimento, não executa ordens de
> compra/venda e usa dados de fontes gratuitas que podem ter atraso. Sempre valide antes de
> operar de verdade (ex: na Exness ou outra corretora).

Inclui também um **painel de mercado** (`/mercado`) com notícias por ativo, calendário
econômico e calendário de earnings — o equivalente ao "Panorama" de plataformas como a Laatus,
construído com fontes de dados legítimas (ver nota abaixo sobre Investing.com).

**Front-end**: dashboard, watchlist, mercado e alertas (`/alertas`) se auto-atualizam via
polling (sem precisar dar F5), são responsivos para celular, usam toasts/modal em vez de
`alert()`/`confirm()` do navegador, e o gráfico do ativo (`/ativo/{symbol}`) é candlestick com
seletor de período/intervalo, EMA9/EMA21 sobrepostas e painéis de RSI/MACD.

**Regras de alerta compostas**: cada regra pode ter várias condições combinadas com E (todas
precisam disparar) ou OU (basta uma) — ex: "RSI sobrecomprado E volume 2x acima da média".
Antes de salvar, dá pra **testar a regra contra os últimos meses de histórico** (`/watchlist`,
botão "Testar regra") e ver quantas vezes ela teria disparado e o retorno médio depois.

**Posições/P&L** (`/posicoes`): registro manual de compras/vendas (não integra com nenhuma
corretora, é só contabilidade) com custo médio, lucro realizado e não-realizado, histórico
completo por ativo.

**Assistente com IA** (`/assistente` no dashboard, `/pergunta` no Telegram): responde perguntas
sobre a watchlist usando só os dados que o próprio sistema já coletou (preços, notícias,
alertas) — nunca dá recomendação de compra/venda, só explica. O resumo diário do Telegram
também vira um parágrafo narrativo em vez de só uma lista de números quando a IA está
configurada. Ver seção "Assistente com IA" abaixo.

## Stack

- **Backend**: FastAPI + SQLAlchemy (SQLite) + APScheduler
- **Dados**: [Finnhub](https://finnhub.io) (cotação, notícias e earnings, free tier) +
  `yfinance` (histórico para indicadores, sem necessidade de API key) +
  [Financial Modeling Prep](https://financialmodelingprep.com) (calendário econômico, free tier)
- **Alertas**: bot do Telegram (`python-telegram-bot`)
- **Dashboard**: Jinja2 + Chart.js, com login por sessão de verdade (tela de cadastro/login
  própria, senha com hash bcrypt, cookie assinado — ver seção "Autenticação" abaixo)

### Por que não Investing.com?

O Investing.com não oferece API pública. O único jeito de puxar dados de lá programaticamente
é via scraping não-oficial (bibliotecas como `investiny`), o que viola os termos de uso do site
e quebra sem aviso quando eles mudam o HTML — não é uma base confiável para algo que o pai do
seu amigo vai usar de verdade. Por isso, cotações/notícias/calendário econômico vêm de APIs
oficiais (Finnhub + FMP), que cobrem a mesma necessidade com estabilidade e dentro do free tier.

## Setup local

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
```

Edite o `.env`:

1. **Finnhub**: crie uma conta grátis em https://finnhub.io/register e copie a API key para
   `FINNHUB_API_KEY` (usada para cotação, notícias e calendário de earnings).
2. **Financial Modeling Prep**: crie uma conta grátis em
   https://financialmodelingprep.com/developer/docs/ e copie a API key para `FMP_API_KEY`
   (usada só para o calendário econômico — juros, payroll, inflação etc.). Se não configurar,
   o sistema roda normalmente, só sem o calendário econômico.
3. **Telegram**:
   - Fale com [@BotFather](https://t.me/BotFather) no Telegram, crie um bot (`/newbot`) e
     copie o token para `TELEGRAM_BOT_TOKEN`.
   - Envie qualquer mensagem (ex: `/start`) para o seu bot recém-criado.
   - Rode `python get_chat_id.py` para descobrir o `TELEGRAM_CHAT_ID` — cole no `.env`. Isso
     garante que só esse chat (o do pai do seu amigo) pode usar o bot.
4. **Login do dashboard**: gere uma `SECRET_KEY` com
   `python -c "import secrets; print(secrets.token_hex(32))"` e cole no `.env`. Sem isso o
   sistema ainda funciona (gera uma chave temporária e avisa no log), mas todo mundo é
   deslogado a cada restart do servidor — não use isso em produção.
5. **Assistente com IA** (opcional): crie uma conta em https://console.anthropic.com e copie a
   API key para `ANTHROPIC_API_KEY`. Sem essa chave, o sistema roda normal — o resumo diário
   fica no formato de lista simples (sem narrativa) e o assistente avisa que está desativado
   em vez de responder.

Rodar localmente:

```bash
uvicorn app.main:app --reload
```

Acesse `http://localhost:8000` — a primeira visita redireciona pra `/cadastro`, que só fica
aberta enquanto não existir nenhuma conta (ver seção "Autenticação" abaixo).

## Autenticação

Não é mais Basic Auth — é uma tela de cadastro/login de verdade, pensada pra ficar exposta na
internet 24/7 sem virar um cadastro público:

- **Primeiro acesso**: `/cadastro` só funciona enquanto **não existir nenhum usuário** no banco.
  A primeira conta criada vira administradora automaticamente.
- **Depois disso, `/cadastro` se fecha sozinho** — mostra "cadastro fechado" e manda pro login.
  Novas contas só podem ser criadas por um admin já logado, na tela `/usuarios`.
- Senhas ficam com hash bcrypt (nunca em texto plano). Sessão via cookie assinado
  (`itsdangerous`/Starlette `SessionMiddleware`), `httponly` + `samesite=lax`.
- Login tem rate limit simples: 5 tentativas erradas seguidas bloqueiam por 5 minutos (esse
  contador vive em memória, então reseta se o processo reiniciar — é uma trava contra brute
  force casual, não uma solução enterprise).
- Sem "esqueci minha senha" — se alguém esquecer, um admin recria o usuário direto no banco
  (ou me chama que eu ajudo). Não há serviço de e-mail configurado no projeto pra reset automático.

Fluxo sugerido: você acessa primeiro, faz seu próprio cadastro (vira admin), depois cria a conta
do pai do seu amigo em `/usuarios`.

## Rodando os testes

```bash
pytest
```

Os testes cobrem os indicadores técnicos e o motor de regras de alerta com dados sintéticos
(não dependem de API externa).

## Uso

1. Acesse `/watchlist` no dashboard (ou use `/add SYMBOL` no bot do Telegram) para cadastrar
   ativos, ex: `AAPL`, `MSFT`, `NVDA`.
2. Para cada ativo, crie regras de alerta na própria tela de watchlist: adicione uma ou mais
   condições (preço acima/abaixo, RSI, cruzamento de médias, MACD, spike de volume, variação %),
   escolha se é "TODAS" (E) ou "QUALQUER" (OU) entre elas, e clique em "Testar regra" pra ver o
   backtest antes de salvar.
3. Registre suas compras/vendas em `/posicoes` pra acompanhar custo médio e P&L — é só um
   registro manual, não afeta nem depende de nenhuma corretora.
4. Use `/assistente` no dashboard (ou `/pergunta <texto>` no Telegram) pra perguntar coisas
   como "por que a AAPL caiu hoje?" — a resposta usa só os dados que o sistema já coletou.
5. O scheduler interno:
   - a cada `QUOTE_POLL_SECONDS` (padrão 60s) busca a cotação atual de cada ativo ativo;
   - a cada `INDICATOR_REFRESH_SECONDS` (padrão 5min) recalcula indicadores e avalia as regras;
   - a cada `NEWS_REFRESH_SECONDS` (padrão 30min) busca notícias novas de cada ativo;
   - todo dia às `CALENDAR_REFRESH_HOUR_UTC` atualiza calendário econômico e de earnings;
   - todo dia às `DAILY_SUMMARY_HOUR_UTC` envia um resumo pelo Telegram (preços + notícias das
     últimas 24h + eventos econômicos de alto impacto do dia + earnings da semana).
6. Quando uma regra dispara: grava no histórico de alertas, aparece no dashboard e é enviado
   via Telegram (respeitando o `cooldown_minutes` de cada regra, pra não spammar).
7. Acesse `/mercado` para ver o painel completo de notícias, calendário econômico e earnings.
8. Baixe um relatório em PDF a qualquer momento pelo link "Baixar PDF" no dashboard
   (`/relatorio.pdf`) ou mande `/relatorio` para o bot no Telegram — ele gera e envia o PDF na
   hora, com watchlist, alertas recentes, notícias, calendário econômico e earnings.

## Assistente com IA

Usa um LLM só pra **explicar dados que o sistema já coletou**, nunca pra decidir ou executar
nada. Dois provedores suportados via `LLM_PROVIDER` no `.env`:

- **`gemini`** (padrão) — grátis, sem cartão de crédito, ótimo pra testar. Crie a key em
  https://aistudio.google.com/apikey e cole em `GEMINI_API_KEY`.
- **`anthropic`** — pago (créditos pré-pagos), recomendado quando for pra produção de verdade.
  Crie a key em https://console.anthropic.com e cole em `ANTHROPIC_API_KEY`.

O código dos dois é idêntico (mesmos prompts, mesmo comportamento) — só troca o `LLM_PROVIDER`
quando quiser migrar de um pro outro.

- **Resumo diário narrativo**: o job `daily_summary` monta os mesmos dados de sempre (preços,
  notícias, eventos econômicos, earnings) e pede pro Claude escrever um parágrafo curto em vez
  de só listar números. Se a API falhar ou a chave não estiver configurada, cai automaticamente
  pro formato de lista simples — nunca quebra o envio do resumo.
- **Chat** (`/assistente` no dashboard, `/pergunta <texto>` no Telegram): responde só com base
  na watchlist/notícias/alertas que já estão no banco. Instruído a dizer "não sei" em vez de
  inventar quando a informação não está disponível, e a nunca recomendar comprar/vender.
- **Contexto nos alertas** (`LLM_ENRICH_ALERTS=true`, desligado por padrão): adiciona uma frase
  de contexto em cada alerta disparado. Fica desligado por padrão porque alertas podem disparar
  com frequência e cada um vira uma chamada de API paga — ligue só se souber o volume de
  alertas que sua watchlist costuma gerar.

Custo esperado: com o modelo padrão (Haiku, o mais barato) e uso de baixo volume (1 resumo/dia
+ perguntas ocasionais), fica na faixa de centavos de dólar por mês.

## Deploy 24/7 (grátis / baixo custo)

O projeto já vem com `Dockerfile` e `docker-compose.yml`. Escolhemos **Render** (não pede
cartão de crédito no free tier e tem suporte nativo a Docker). Passos gerais (execute você
mesmo, já que envolve criar conta e credenciais em serviços externos):

### Opção A — Render (recomendado)

1. Crie uma conta grátis em https://render.com (pode entrar com GitHub).
2. Suba este repositório para o GitHub (crie um repo **privado** — o `.env` não vai junto,
   está no `.gitignore`).
3. No painel do Render: **New +** → **Web Service** → conecte o repositório.
4. Environment: **Docker** (ele detecta o `Dockerfile` automaticamente). Porta: `8000`.
5. Em **Environment Variables**, cole todas as chaves do seu `.env` local (`FINNHUB_API_KEY`,
   `FMP_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SECRET_KEY`,
   `SESSION_COOKIE_SECURE=true`, `ANTHROPIC_API_KEY`, etc.) — uma por uma no painel, nunca
   commitando o arquivo.
   `SECRET_KEY` **precisa** ser fixa aqui (gerada uma vez, colada no painel) — se ficar em
   branco cada restart gera uma nova e desloga todo mundo.
6. Plano **Free**: o serviço "dorme" após ~15 min sem requisições HTTP, mas o scheduler
   interno (jobs do APScheduler) só roda enquanto o processo está de pé — ou seja, no free
   tier o monitoramento não é 100% contínuo. Para monitoramento 24/7 de verdade, migre pro
   plano **Starter** (~US$7/mês), que não dorme.
7. Persistência: o SQLite fica no filesystem do container, que é efêmero no Render — se o
   serviço reiniciar, **o histórico de preços/alertas E as contas de usuário/senha zeram**
   (o `/cadastro` reabre sozinho, o que é seguro mas incômodo). Pra persistir de verdade,
   adicione um **Render Disk** (storage persistente, tem custo baixo) apontando pro caminho do
   `DATABASE_URL`, ou migre para o Render Postgres (free tier disponível) trocando
   `DATABASE_URL` para a connection string do Postgres — o SQLAlchemy já suporta ambos sem
   mudar código. Recomendo fortemente configurar isso antes de considerar o deploy "definitivo".

### Opção B — Railway

Alternativa ao Render, mesmo fluxo (conectar repo do GitHub, apontar pro Dockerfile, configurar
env vars no painel). Hoje em dia costuma pedir cartão pra liberar o free tier — por isso ficamos
com o Render como recomendação principal.

### Opção C — Fly.io

```bash
fly launch          # gera fly.toml, escolha "no" para banco gerenciado (usamos SQLite local)
fly secrets set FINNHUB_API_KEY=... FMP_API_KEY=... TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... SECRET_KEY=... SESSION_COOKIE_SECURE=true ANTHROPIC_API_KEY=...
fly deploy
```

Fly.io tem free allowance mensal que cobre uma instância pequena rodando continuamente.

### Opção D — VPS próprio (Oracle Cloud free tier, etc.)

```bash
docker compose up -d --build
```

Isso sobe o serviço na porta 8000 com restart automático. Configure um proxy reverso
(Caddy/Nginx) com HTTPS na frente se for expor publicamente, e lembre de setar
`SESSION_COOKIE_SECURE=true` nesse caso — sem HTTPS o cookie de sessão marcado como `secure`
não funciona, e sem essa flag em produção o cookie trafega sem essa proteção.

## Estrutura do projeto

```
app/
  main.py            # FastAPI app + lifecycle (DB, bot, scheduler, sessão de login)
  config.py          # variáveis de ambiente
  db.py, models.py, schemas.py
  auth.py             # hash de senha, sessão, rate limit de login, CSRF
  indicators.py      # SMA, EMA, RSI, MACD, Bollinger, volume ratio
  rules_engine.py     # avalia condições/regras (com lógica E/OU) contra dados de mercado
  backtest.py          # roda uma regra contra o histórico antes de salvar
  positions.py           # custo médio, P&L realizado/não-realizado a partir de transações
  llm_client.py            # wrapper async da API da Anthropic (resumo, chat, contexto)
  dedup.py                  # dedup pura de notícias/eventos (testável sem DB/rede)
  scheduler.py                # jobs periódicos (cotação, regras, notícias, calendários, resumo)
  telegram_bot.py               # comandos do bot + envio de alertas
  market_data/                    # clientes Finnhub (cotação/notícias/earnings), yfinance (histórico)
                                    # e FMP (calendário econômico)
  reports.py                        # gera o relatório PDF (reportlab), usado pela web e pelo bot
  routers/                            # auth, dashboard, watchlist (+ regras/backtest), positions,
                                        # assistant, api — endpoints REST + páginas HTML
  templates/, static/                  # dashboard web (login, cadastro, usuarios, positions,
                                         # assistant, etc.)
tests/                                  # testes unitários (indicadores, regras, backtest,
                                          # posições, dedup, API, auth, assistente)
```

## Limitações conhecidas (free tier)

- Dados podem ter alguns minutos de atraso dependendo do plano do Finnhub/yfinance/FMP.
- Finnhub free tier: 60 requisições/minuto — suficiente para uma watchlist pequena/média.
- yfinance é uma biblioteca não-oficial que consome dados públicos do Yahoo Finance; pode
  falhar ocasionalmente se o Yahoo mudar algo — o código já trata erros sem derrubar o serviço.
- Calendário econômico depende da FMP; sem `FMP_API_KEY` configurada essa seção fica vazia mas
  o resto do sistema continua funcionando normalmente.
- Assistente/resumo narrativo dependem da `ANTHROPIC_API_KEY`; sem ela, tudo cai pro
  comportamento sem IA (sem quebrar nada).
- Backtest é simplificado (não é um motor de backtesting completo): reavalia a regra em janela
  deslizante sobre o histórico do yfinance, não simula slippage/custos/execução real.
- Sem execução de ordens: qualquer decisão de compra/venda continua manual, feita por você na
  corretora (ex: Exness).
