export const navLinks = [
  { href: '/', label: 'Inicio' },
  { href: '/aulas', label: 'Escola' },
  { href: '/aplicacoes', label: 'Terminal' },
  { href: '/estrategias', label: 'Metodo' },
  { href: '/planos', label: 'Planos' },
  { href: '/sobre', label: 'Sobre' },
];

export const courseTracks = [
  {
    slug: 'fundamentos',
    title: 'Fundamentos do mercado americano',
    level: 'Iniciante',
    status: 'Liberado',
    theme: 'Base',
    progress: 72,
  },
  {
    slug: 'analise-tecnica-avancada',
    title: 'Analise tecnica e price action',
    level: 'Intermediario',
    status: 'Em andamento',
    theme: 'Tecnica',
    progress: 66,
  },
  {
    slug: 'gestao-de-risco-e-psicologia',
    title: 'Gestao de risco e psicologia',
    level: 'Essencial',
    status: 'Liberado',
    theme: 'Risco',
    progress: 38,
  },
  {
    slug: 'processo-diario-e-revisao',
    title: 'Processo, diario e revisao',
    level: 'Pratica',
    status: 'Liberado',
    theme: 'Metodo',
    progress: 24,
  },
  {
    slug: 'analise-tecnica-avancada',
    title: 'Leitura de regime e contexto',
    level: 'Intermediario',
    status: 'Liberado',
    theme: 'Macro',
    progress: 18,
  },
  {
    slug: 'mesa-ia-aplicada',
    title: 'Mesa IA aplicada',
    level: 'Avancado',
    status: 'Bloqueado',
    theme: 'IA',
    progress: 0,
  },
];

export const plans = [
  {
    name: 'Escola',
    description: 'Para aprender o metodo OneB e praticar com simulacao guiada.',
    price: 'R$ 49',
    featured: false,
    benefits: [
      'Aulas e trilhas essenciais',
      'Checklists de estudo e risco',
      'Simulacao guiada antes da operacao',
      'Lives e revisoes da comunidade',
    ],
  },
  {
    name: 'Escola + Terminal',
    description: 'O MVP principal: educacao, watchlist, alertas e apoio a decisao.',
    price: 'R$ 97',
    featured: true,
    benefits: [
      'Tudo do plano Escola',
      'Watchlist com alertas configuraveis',
      'Resumo diario e contexto de mercado',
      'Posicoes manuais, P&L e risco',
      'Assistente IA explicando dados coletados',
    ],
  },
  {
    name: 'Mesa Guiada',
    description: 'Para alunos que querem acompanhamento mais proximo e rotina de revisao.',
    price: 'R$ 197',
    featured: false,
    benefits: [
      'Tudo do Escola + Terminal',
      'Lives praticas com revisao de cenarios',
      'Trilhas avancadas de estrategia',
      'Roteiro de evolucao individual',
    ],
  },
];

export const applications = [
  {
    key: 'school',
    category: 'Escola',
    title: 'Trilhas de aprendizado',
    description: 'Aulas, checklists e pratica guiada para formar metodo antes da decisao.',
    href: '/aulas',
    metrics: ['72 aulas', 'Progresso', 'Checklists'],
  },
  {
    key: 'terminal',
    category: 'Terminal',
    title: 'Watchlist e alertas',
    description: 'Monitoramento de ativos, regras configuraveis, historico e resumo diario.',
    href: '/ferramenta',
    metrics: ['Alertas', 'Noticias', 'Resumo'],
  },
  {
    key: 'risk',
    category: 'Risco',
    title: 'Decisao protegida',
    description: 'Leitura de qualidade dos dados, risco e motivos claros para operar ou esperar.',
    href: '/mesa-ia',
    metrics: ['NO_TRADE', 'Contexto', 'Revisao'],
  },
];

export const strategies = [
  {
    category: 'Metodo',
    title: 'Contexto antes do setup',
    description: 'Aprenda a ler regime, tendencia e invalidacao antes de procurar entrada.',
    lessons: 12,
    level: 'Iniciante',
  },
  {
    category: 'Risco',
    title: 'Tamanho de posicao',
    description: 'Transforme risco por operacao em uma regra objetiva e repetivel.',
    lessons: 8,
    level: 'Essencial',
  },
  {
    category: 'Tecnica',
    title: 'Price Action com confirmacao',
    description: 'Use gatilho, volume e zonas importantes sem depender de promessa de acerto.',
    lessons: 14,
    level: 'Intermediario',
  },
  {
    category: 'Revisao',
    title: 'Diario operacional',
    description: 'Registre decisoes, motivos de espera e aprendizados para evoluir com evidencia.',
    lessons: 6,
    level: 'Pratica',
  },
];

export const resultStats = [
  { value: '5-10', label: 'usuarios piloto para validar o MVP' },
  { value: '1 rotina', label: 'estudar, monitorar, alertar e revisar' },
  { value: '0 ordens', label: 'sem execucao automatica no MVP' },
];
