# 🎨 Paleta de Cores — PICTA

Referência oficial de cores para toda a interface do PICTA, baseada no design `picta_ui_preview.html`.

## 📊 Variáveis CSS Base

```css
:root {
    /* Fundos */
    --bg-page:      #F5F0FF;    /* Fundo principal (lavender muito claro) */
    --lavender:     #E8E0FF;    /* Header e áreas destacadas */
    
    /* Cores Primárias */
    --purple-dark:  #6B4FA0;    /* Logo, títulos, ênfase */
    --purple-mid:   #8B6FC0;    /* Gradientes, hover */
    
    /* Categorias de Pictogramas */
    --peach:        #FFE8D8;    /* Fundo Emoções */
    --sky:          #D6E8FF;    /* Fundo Ações */
    --mint:         #D4F0E4;    /* Fundo Necessidades */
    
    /* Texto */
    --text-main:    #2D2145;    /* Texto principal (muito escuro) */
    --text-muted:   #8B7EA8;    /* Texto secundário (roxo cinzento) */
    --white:        #FFFFFF;    /* Branco puro */
    
    /* Acentos */
    --color-emocao:      #8B3A00;  /* Texto em emoções (marrom) */
    --color-acao:        #1A3F7A;  /* Texto em ações (azul escuro) */
    --color-necessidade: #155F40;  /* Texto em necessidades (verde escuro) */
    
    /* Bordas e Sombras */
    --border-light: #DDD6FE;    /* Bordas suaves */
    --shadow:       rgba(107, 79, 160, 0.10);  /* Sombra padrão */
}
```

## 🎯 Uso por Componente

### Header (Todas as telas)
- **Background**: `var(--lavender)` ou `#E8E0FF`
- **Texto principal**: `var(--purple-dark)` ou `#6B4FA0`
- **Texto secundário**: `var(--text-muted)` ou `#8B7EA8`
- **Sombra**: `0 3px 14px var(--shadow)`

### Categoria Emoções 😊
- **Background**: `var(--peach)` ou `#FFE8D8`
- **Texto/Ícone**: `#8B3A00` (marrom)
- **Label**: "😊 Como me sinto"

### Categoria Ações 🎮
- **Background**: `var(--sky)` ou `#D6E8FF`
- **Texto/Ícone**: `#1A3F7A` (azul escuro)
- **Label**: "🎮 O que quero fazer"

### Categoria Necessidades 💧
- **Background**: `var(--mint)` ou `#D4F0E4`
- **Texto/Ícone**: `#155F40` (verde escuro)
- **Label**: "💧 O que preciso"

### Botão Principal (Login)
- **Gradiente**: `linear-gradient(135deg, #8B6FC0 0%, #6B4FA0 100%)`
- **Cor do texto**: Branco (`#FFFFFF`)
- **Sombra (hover)**: `0 8px 24px rgba(107,79,160,0.40)`

### Inputs
- **Background**: `var(--white)` ou `#FFFFFF`
- **Border**: `2.5px solid #E8E0FF`
- **Texto**: `var(--text-main)` ou `#2D2145`
- **Placeholder**: `var(--text-muted)` ou `#8B7EA8`

### Badges
- **Criança**: Background `#FFE8D8`, texto `#8B3A00`
- **Cuidador**: Background `#D4F0E4`, texto `#155F40`

### Feedback/Alertas
- **Sucesso**: Background `#D4F0E4`, texto `#155F40`
- **Erro**: Mantém padrão Streamlit com prefix vermelho

---

## ✅ Checklist de Implementação

- [x] Login (cores corrigidas)
- [x] Painel Criança (cores já corretas)
- [x] Dashboard Cuidador (header corrigido)
- [ ] Assets/Pictogramas (para ciclos futuros)

---

**Última atualização**: 08/04/2026
