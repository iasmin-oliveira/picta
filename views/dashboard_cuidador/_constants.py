"""
PICTA — views/dashboard_cuidador/_constants.py
Constantes compartilhadas entre os sub-módulos do dashboard do cuidador.
"""

LABEL_PERFIL = {'responsavel': 'Responsável', 'cuidador': 'Cuidador'}

FRASE_EMOCAO = {
    'FELIZ':     'estava feliz 😊',     'TRISTE':    'estava triste 😢',
    'BRAVO':     'estava bravo(a) 😠',  'ASSUSTADO': 'estava assustado(a) 😨',
    'CALMO':     'estava calmo(a) 😌',  'CHORANDO':  'estava chorando 😭',
    'SURPRESO':  'ficou surpreso(a) 😲','CANSADO':   'estava cansado(a) 😴',
    'AMADO':     'se sentiu amado(a) 🥰','ANSIOSO':  'estava ansioso(a) 😰',
    'ORGULHOSO': 'se sentiu orgulhoso(a) 🥹','CONFUSO':'estava confuso(a) 😕',
}

COR_CAT = {'emocao': '#f97316', 'acao': '#6366f1', 'necessidade': '#22c55e'}

BADGE_CAT = {
    'emocao':      ('badge-emocao',      'Emoção'),
    'acao':        ('badge-acao',        'Ação'),
    'necessidade': ('badge-necessidade', 'Pedido'),
}

EMOCOES_ATENCAO   = {'ANSIOSO', 'TRISTE', 'CHORANDO', 'ASSUSTADO', 'BRAVO', 'CONFUSO'}
EMOCOES_POSITIVAS = {'FELIZ', 'CALMO', 'AMADO', 'ORGULHOSO', 'SURPRESO'}

# (chave, emoji, título, descrição)
NAV = [
    ("hoje",     "🏠", "Hoje",          "Veja as comunicações de hoje"),
    ("hist",     "📅", "Histórico",      "Timeline de dias anteriores"),
    ("crianca",  "👶", "Minha Criança",  "Dados e dicas sobre a criança"),
    ("vinculos", "🔗", "Vínculos",       "Profissionais de saúde vinculados"),
    ("perfil",   "👤", "Meu Perfil",     "Edite seus dados e senha"),
]

_GRADS = [
    "linear-gradient(135deg,#e0e7ff,#c7d2fe)",
    "linear-gradient(135deg,#fce7f3,#fbcfe8)",
    "linear-gradient(135deg,#d1fae5,#a7f3d0)",
    "linear-gradient(135deg,#fef3c7,#fde68a)",
]
