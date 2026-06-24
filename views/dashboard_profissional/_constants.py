"""
PICTA — views/dashboard_profissional/_constants.py
Constantes compartilhadas entre os sub-módulos do dashboard profissional.
"""

EMOCOES_ALERTA    = {'ANSIOSO', 'TRISTE', 'CHORANDO', 'ASSUSTADO', 'BRAVO', 'CONFUSO'}
EMOCOES_POSITIVAS = {'FELIZ', 'CALMO', 'AMADO', 'ORGULHOSO', 'SURPRESO'}

COR_CAT   = {'emocao': '#f97316', 'acao': '#6366f1', 'necessidade': '#22c55e'}
LABEL_CAT = {'emocao': 'EMOÇÃO', 'acao': 'AÇÃO', 'necessidade': 'PEDIDO'}
BADGE_CAT = {
    'emocao':      ('badge-emocao',      'EMOÇÃO'),
    'acao':        ('badge-acao',        'AÇÃO'),
    'necessidade': ('badge-necessidade', 'NEC.'),
}

PESO_EMOCAO = {
    **{p: +1 for p in EMOCOES_POSITIVAS},
    **{p: -1 for p in EMOCOES_ALERTA},
}

NAV = [
    ("painel",    "📋", "Painel Clínico", "KPIs, alertas e diário do paciente"),
    ("pacientes", "👥", "Pacientes",      "Gerencie os pacientes vinculados"),
    ("insights",  "🔬", "Insights IA",   "Análise estatística automática"),
    ("exportar",  "💾", "Exportação",     "Baixar dados em CSV ou PDF"),
    ("perfil",    "👤", "Meu Perfil",    "Edite seus dados e senha"),
]

_GRADS = [
    "linear-gradient(135deg,#e0e7ff,#c7d2fe)",
    "linear-gradient(135deg,#fce7f3,#fbcfe8)",
    "linear-gradient(135deg,#d1fae5,#a7f3d0)",
    "linear-gradient(135deg,#fef3c7,#fde68a)",
    "linear-gradient(135deg,#dbeafe,#bfdbfe)",
]
