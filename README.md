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
2. Para cada ativo, crie regras de alerta na própria tela de watchlist (preço acima/abaixo,
   RSI, cruzamento de médias, MACD, spike de volume).
3. O scheduler interno:
   - a cada `QUOTE_POLL_SECONDS` (padrão 60s) busca a cotação atual de cada ativo ativo;
   - a cada `INDICATOR_REFRESH_SECONDS` (padrão 5min) recalcula indicadores e avalia as regras;
   - a cada `NEWS_REFRESH_SECONDS` (padrão 30min) busca notícias novas de cada ativo;
   - todo dia às `CALENDAR_REFRESH_HOUR_UTC` atualiza calendário econômico e de earnings;
   - todo dia às `DAILY_SUMMARY_HOUR_UTC` envia um resumo pelo Telegram (preços + notícias das
     últimas 24h + eventos econômicos de alto impacto do dia + earnings da semana).
4. Quando uma regra dispara: grava no histórico de alertas, aparece no dashboard e é enviado
   via Telegram (respeitando o `cooldown_minutes` de cada regra, pra não spammar).
5. Acesse `/mercado` para ver o painel completo de notícias, calendário econômico e earnings.
6. Baixe um relatório em PDF a qualquer momento pelo link "Baixar PDF" no dashboard
   (`/relatorio.pdf`) ou mande `/relatorio` para o bot no Telegram — ele gera e envia o PDF na
   hora, com watchlist, alertas recentes, notícias, calendário econômico e earnings.

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
   `SESSION_COOKIE_SECURE=true`, etc.) — uma por uma no painel, nunca commitando o arquivo.
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
fly secrets set FINNHUB_API_KEY=... FMP_API_KEY=... TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... SECRET_KEY=... SESSION_COOKIE_SECURE=true
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
  rules_engine.py     # avalia regras de alerta contra dados de mercado
  dedup.py               # dedup pura de notícias/eventos (testável sem DB/rede)
  scheduler.py            # jobs periódicos (cotação, regras, notícias, calendários, resumo)
  telegram_bot.py           # comandos do bot + envio de alertas
  market_data/                # clientes Finnhub (cotação/notícias/earnings), yfinance (histórico)
                                # e FMP (calendário econômico)
  reports.py                    # gera o relatório PDF (reportlab), usado pela web e pelo bot
  routers/                        # endpoints REST + páginas HTML (auth, dashboard, watchlist, mercado, PDF)
  templates/, static/              # dashboard web (inclui login.html, cadastro.html, usuarios.html)
tests/                            # testes unitários (indicadores, regras, dedup, API, auth)
```

## Limitações conhecidas (free tier)

- Dados podem ter alguns minutos de atraso dependendo do plano do Finnhub/yfinance/FMP.
- Finnhub free tier: 60 requisições/minuto — suficiente para uma watchlist pequena/média.
- yfinance é uma biblioteca não-oficial que consome dados públicos do Yahoo Finance; pode
  falhar ocasionalmente se o Yahoo mudar algo — o código já trata erros sem derrubar o serviço.
- Calendário econômico depende da FMP; sem `FMP_API_KEY` configurada essa seção fica vazia mas
  o resto do sistema continua funcionando normalmente.
- Sem execução de ordens: qualquer decisão de compra/venda continua manual, feita por você na
  corretora (ex: Exness).
