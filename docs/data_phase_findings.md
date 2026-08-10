# Fase de dados — achados (2026-08)

Registro dos resultados da auditoria de dados/features feita nesta sessão, para não repetir o
trabalho depois. Todos os scripts citados estão em `scripts/` e são reexecutáveis
(`python -m scripts.<nome>`), a maioria aceita `PAPER_SIM_SYMBOLS=A,B,C` para trocar o universo.

## Resumo executivo

Testamos se as 11 features técnicas de `app.paper_simulator.FEATURE_NAMES` (RSI, MACD, EMA,
ADX, ATR, volume, score composto, VIX) carregam vantagem estatística preditiva, em 4
formulações diferentes do problema. **Nenhuma sobreviveu a validação out-of-sample rigorosa.**
A causa mais provável não é falta de esforço de modelagem — é que a janela de preço disponível
(ago/2024–ago/2026) é um mercado de reversões em V (bull forte → correção violenta → recuperação
em V, repetido duas vezes), o pior cenário estrutural para indicador técnico de tendência/momentum.

## Fontes de dado corrigidas/adicionadas

- **FRED** (`app/market_data/fred_client.py`) — yields do Tesouro (2/5/10/30Y), Dollar Index
  (DTWEXBGS), VIX, agora vindos da fonte oficial em vez de proxies Yahoo. Resolveu o gap do
  US2Y que não tinha ticker Yahoo confiável.
- **Calendário econômico** — migrado de FMP (API v3 descontinuada em 2025-08-31, endpoint
  `/stable` restrito no plano grátis) para `fred_client.get_economic_calendar` (FRED
  `/releases/dates`, filtrado a 6 releases de alto impacto: FOMC, CPI, NFP, GDP, PCE, Retail
  Sales). Mesma key já configurada, sem cadastro novo.
- **FMP fundamentals** (`app/market_data/fmp_client.py`) — `get_key_metrics` /
  `get_income_statement`, plano grátis limitado a anual (não trimestral), `limit<=5`,
  `income-statement.filingDate` usado para join point-in-time correto (evita look-ahead).
- **Bug corrigido**: `finnhub_client.get_earnings_calendar()` sem `symbol` sempre lançava
  `TypeError` (a lib `finnhub-python` instalada exige `symbol` sempre; `""` = todos). Não afetava
  produção (os dois callers reais sempre passam symbol), mas era um bug latente.
- `scripts/api_health_check.py` — roda todo provider real (não só checa se a key existe) e
  reporta pass/fail. Rodar periodicamente para pegar esse tipo de quebra silenciosa cedo.

## Experimentos e resultados

| # | Script | Formulação testada | Resultado |
|---|---|---|---|
| 1 | `eda_report.py` | Auditoria do dataset (gaps, NaN, correlação pooled) | Dataset limpo; correlação feature×label máx. 0.07 |
| 2 | `label_horizon_scan.py` | Horizontes 1-20d, thresholds 0-1% | Melhor correlação 0.14, só em label desbalanceado (baseline 71%) |
| 3 | `feature_engineering_experiment.py` | +8 features (regime/cross-asset/lag) via A/B walk-forward | Holdout AUC piorou (0.475→0.452); não promovido |
| 4 | `cross_sectional_ic.py` | Ranking cross-sectional (padrão Gu-Kelly-Xiu / IC), 24 e depois 48 símbolos | IC subiu com universo maior (0.033→0.042, t=3.24) mas não sobreviveu à divisão temporal (t=3.96 → t=0.69) |
| 5 | `risk_label_experiment.py` | Triple-barrier (López de Prado) — prever stop-antes-do-alvo em vez de direção | Holdout AUC=0.463 (abaixo de 0.50); melhor feature muda entre metades |
| 6 | `fundamentals_experiment.py` | IC cross-sectional de fundamentals (revenue growth, ROE, ROIC, yields) | `revenue_growth_yoy` IC=0.031 (t=2.16) na amostra completa, mas inverte de sinal na segunda metade (t=4.11→t=-0.74) |
| 7 | `regime_timeline.py` | Reconstrução mensal do regime (score + VIX) pra achar a causa raiz | Não é uma quebra única — são 2 correções violentas (mar/2025, fev-mar/2026) intercaladas com bulls fortes |
| 8 | `regime_transition_experiment.py` | Prever transição pra regime BEAR nos próximos 10d (onset detection) | AUC=0.874 com o feature set completo — **mas isso é majoritariamente circular** (regime_score/rsi/adx são quase a mesma informação do label). Isolando só as features independentes (VIX, ATR, DXY, US10Y): AUC cai pra 0.571 e accuracy = exatamente o baseline. Sem sinal real. |

### Nota metodológica importante (achado #8)

Ao testar transição de regime, o primeiro resultado (AUC=0.874) parecia a melhor descoberta da
sessão — mas era um artefato: usar `regime_score` atual (e RSI/ADX, que compõem esse score) pra
prever se `regime_score` vai cruzar um limiar é quase circular — mede autocorrelação da própria
série, não um alerta antecipado de verdade. Rodar de novo só com features estruturalmente
independentes do label (VIX, variação de VIX, ATR, DXY, US10Y) derrubou o resultado pra AUC=0.571
(accuracy idêntica ao baseline). **Sempre que um resultado parecer bom demais, checar se alguma
feature carrega a mesma informação usada pra construir o label antes de comemorar.**

## Metodologia usada (para manter em qualquer experimento futuro)

1. Correlação feature↔label calculada **só no fold de treino**, nunca no holdout, antes de
   qualquer decisão de feature.
2. Split walk-forward com embargo/purging (López de Prado) — mesmos folds de
   `scripts/calibrate_decision_strategy.py`.
3. Métricas sempre com baseline (classe majoritária) ao lado — nunca accuracy sozinha.
4. **Checagem de estabilidade temporal (primeira metade vs segunda metade) é obrigatória** antes
   de qualquer promoção — foi o teste que derrubou os experimentos #4, #5 e #6 depois de
   parecerem promissores na correlação agregada.
5. Múltiplas comparações corrigidas com Bonferroni quando testando várias features de uma vez.
6. **Checar se alguma feature é circular com o label** (carrega quase a mesma informação usada
   pra construir o alvo) — foi o que inflou o AUC do experimento #8 pra 0.874 antes de cair pra
   0.571 quando isolado.

## Não promovido para produção

`app/probability_model.py` e `app/decision_engine.py` **não foram alterados** por nenhum desses
experimentos — nenhum passou na barra de validação que a própria equipe definiu. O modelo salvo
em produção continua sendo o treinado por `scripts/train_probability_model.py` (holdout accuracy
48.99%, abaixo do baseline 51.49% — ver histórico em `probability_model_history.json`).

## Estado em 2026-08-09: nenhuma vantagem estatística demonstrada ainda

Nove formulações de problema testadas (direção absoluta, direção por horizonte, A/B de
features, ranking cross-sectional, risco via triple-barrier, fundamentals, transição de
regime, e um segundo universo de ativos) — nenhuma sobreviveu à validação out-of-sample
completa (holdout + estabilidade temporal + checagem de circularidade). Isso não significa
"não há vantagem nenhuma possível" — significa que o material testado até aqui (preço/volume
de um único ativo + macro público + fundamentals anuais grátis) não a demonstrou.

### #9 — Universo small/mid-cap (hipótese: mega-cap é eficiente demais)

Testamos se a ausência de sinal era um efeito de eficiência de mercado (mega-caps arbitradas
demais) trocando o universo de 48 mega/blue-chips por 32 símbolos small/mid-cap diversos
(consumo, biotech, software). Resultado: sinal ainda **mais fraco** que nas mega-caps (melhor
IC com t=1.19, nem passa no limiar de significância de 1.96; `annualized_volatility`, que era a
melhor feature nos universos anteriores, inverteu de sinal e sumiu aqui). Isso descarta a
hipótese de eficiência-do-ativo como explicação — reforça que o teto é o **tipo de dado**
(técnico/preço), não a escolha de qual ativo testar.

### Dados de natureza diferente (order flow, opções, sentimento) — bloqueados por orçamento, não por engenharia

Pesquisamos as três categorias (2026-08-09):

- **Order flow / opções (book L2, dark pool, put/call)**: nenhuma fonte grátis viável na escala
  necessária. Databento (trial c/ $125 credito), Polygon/Massive (US$79+/mes), QuantData/OptionData
  (pagos desde o 1o request). FlashAlpha tem tier grátis mas 5 chamadas/dia — inutilizável pra
  dataset de 30-48 símbolos × 2 anos.
- **Sentimento histórico de notícias**: testamos com o que já tínhamos (Finnhub, grátis, já
  integrado) — `get_company_news` só devolve os **últimos dias**, zero artigos pra qualquer mês
  passado (testado em jan/2025 e set/2024: 0 resultados nos dois). EODHD demo (sentimento)
  retornou 502 em múltiplas tentativas — inutilizável/instável.
- **Padrão geral**: dado em tempo real é grátis; **arquivo histórico é a parte monetizada** pelos
  provedores. Isso não é contornável com engenharia — é decisão de orçamento.

Caminhos que restam:
1. Pagar por arquivo histórico (order flow ou sentimento) — decisão de orçamento explícita,
   ainda não tomada.
2. Começar a coletar notícias/eventos a partir de agora (Finnhub tempo real, grátis) para
   acumular um dataset próprio ao longo do tempo — não serve para testar hoje.
3. ~~Universo de ativos menos eficiente~~ — testado no #9, descartado como explicação.
4. **Aceitar o resultado por ora** e manter Market Regime / Cross-Asset / Macro-News AI
   (rule-based, já funcionam) como motor principal, revisitando Signal Quality quando (1) ou
   (2) mudarem.

## Decisão (2026-08-09): pausar Signal Quality AI

Depois de 9 formulações de problema e 2 universos de ativos testados com rigor (walk-forward,
holdout, estabilidade temporal, checagem de circularidade), e com as três fontes de dado de
natureza diferente (order flow, opções, sentimento histórico) bloqueadas por orçamento — não
por falta de tentativa de engenharia — a decisão foi **pausar a pesquisa de Signal Quality AI**.

O motor de recomendação da plataforma continua sendo as IAs rule-based e já validadas:
Market Regime AI e Cross-Asset AI (`app/regime_engine.py`), Macro-News AI
(`app/market_data/fred_client.py` + calendário econômico + Finnhub). `probability_model.py`
permanece no código, sem uso na tomada de decisão real (`decision_engine.py` só usa pra
*apertar* uma recomendação já aprovada pelas regras, nunca pra aprovar sozinho — comportamento
que já existia antes desta sessão e continua correto).

**Retomar quando**: (a) houver orçamento aprovado para dado histórico de order flow/opções/
sentimento, ou (b) uma nova fonte gratuita e genuinamente diferente aparecer, ou (c) o dataset
próprio de notícias (opção 2 acima) tiver acumulado profundidade suficiente para testar.

## Coleta própria de notícias — já existia, agora confirmada ativa

Ao investigar a opção (c) acima, achamos que a infraestrutura **já existia** antes desta sessão:
`app.scheduler.refresh_news` (por símbolo, a cada `NEWS_REFRESH_SECONDS`, padrão 30min) e
`refresh_global_news` (por categoria, a cada `GLOBAL_NEWS_REFRESH_SECONDS`, padrão 15min) já
gravam em `NewsItem`/`GlobalNewsItem` com dedup por URL e sem nenhuma limpeza/expiração — ou
seja, é um arquivo que só cresce desde que o scheduler esteja rodando.

O que fizemos nesta sessão:
- Confirmamos que `refresh_news` funciona (rodado manualmente, 248 artigos da AAPL sem erro) —
  o banco local só estava vazio porque o scheduler não tinha rodado ainda nesta máquina, não
  por bug.
- Adicionado `sentiment_score` (nullable) em `NewsItem` e `GlobalNewsItem`, com migração leve
  em `app/db.py` (`_ensure_sqlite_saas_columns`) seguindo o padrão já existente no projeto —
  prepara o schema para quando houver um scorer, sem exigir migração depois.

**Confirmado nesta sessão**: o `docker-compose.prod.yml` tem o serviço `worker` (roda
`app.worker`, que inicia o scheduler via `build_scheduler`) configurado com
`restart: unless-stopped` — desenhado pra rodar contínuo. Mas hoje (2026-08-09) ele só roda
**localmente**, sob demanda, não 24/7 em servidor. Isso significa que a coleta atual tem buracos
toda vez que a máquina fica desligada — não é ainda um arquivo histórico confiável para o
experimento de sentimento futuro. Pra virar isso, precisa de deploy contínuo do `worker`
(VPS, Fly.io, Railway, etc. — decisão de infraestrutura/custo, não resolvida aqui).

**Decisão (2026-08-09)**: deixar como está por ora — sem decisão de deploy/custo agora. O
schema (`sentiment_score`) já está pronto para quando isso mudar. Se quiser retomar depois,
os passos são: (1) decidir onde hospedar o `worker` 24/7, (2) deployar, (3) esperar acumular
profundidade (meses), (4) então testar sentimento com o mesmo protocolo de rigor usado nos
9 experimentos anteriores.
