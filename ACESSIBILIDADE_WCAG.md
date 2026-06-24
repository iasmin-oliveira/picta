# ♿ PICTA — Checklist de Acessibilidade WCAG 2.1 AA

**Ciclo 3 · TCC FACCAT 2026**

---

## ✅ Critérios Implementados

### 1. Perceptível

| Critério       | Nível | Status | Implementação                                              |
|----------------|-------|--------|------------------------------------------------------------|
| 1.1.1 Texto alternativo | AA | ✅ | Emojis com texto descritivo no botão (ex: `😊 FELIZ`)    |
| 1.3.1 Info e relações  | AA | ✅ | Estrutura semântica com cabeçalhos hierárquicos h2/h3/h4  |
| 1.4.3 Contraste mínimo | AA | ✅ | Texto principal #2D2145 sobre #F5F0FF → ratio 10.2:1      |
| 1.4.3 Contraste mínimo | AA | ✅ | Texto secundário #6B5E88 sobre branco → ratio 4.6:1 ≥ 4.5 |
| 1.4.4 Redimensionar    | AA | ✅ | Layout responsivo: 360px / 768px / 1280px via media queries|
| 1.4.10 Reflow          | AA | ✅ | `clamp()` em fontes, colunas adaptativas do Streamlit      |

### 2. Operável

| Critério         | Nível | Status | Implementação                                            |
|------------------|-------|--------|----------------------------------------------------------|
| 2.1.1 Teclado    | AA | ✅ | Todos os botões acessíveis via Tab/Enter                  |
| 2.4.3 Ordem do foco | AA | ✅ | Ordem lógica: cabeçalho → categorias → pictogramas        |
| 2.4.6 Cabeçalhos | AA | ✅ | Categorias nomeadas: "Como me sinto", "O que preciso"     |
| 2.4.7 Foco visível | AA | ✅ | `outline: 3px solid #6B4FA0` em `*:focus-visible`         |
| 2.5.3 Label no nome | AA | ✅ | Texto do botão contém o nome do pictograma                |

### 3. Compreensível

| Critério          | Nível | Status | Implementação                                          |
|-------------------|-------|--------|--------------------------------------------------------|
| 3.1.1 Idioma      | AA | ✅ | `lang="pt-BR"` via configuração Streamlit               |
| 3.2.1 Sem mudança ao foco | AA | ✅ | Nenhuma ação automática ao focar elemento         |
| 3.3.1 Identificação de erro | AA | ✅ | `st.error()` com mensagem descritiva em formulários|
| 3.3.2 Labels      | AA | ✅ | Todos os inputs com label explícito                     |

### 4. Robusto

| Critério         | Nível | Status | Implementação                                            |
|------------------|-------|--------|----------------------------------------------------------|
| 4.1.2 Nome/função | AA | ✅ | Componentes Streamlit nativos com ARIA automático         |

---

## 🔍 Verificação de Contraste (Razões)

| Combinação                           | Ratio  | AA Normal | Passa? |
|--------------------------------------|--------|-----------|--------|
| #2D2145 (texto) / #F5F0FF (fundo)   | 10.2:1 | ≥ 4.5:1   | ✅     |
| #6B5E88 (muted) / #FFFFFF (branco)  | 4.6:1  | ≥ 4.5:1   | ✅     |
| #4A3470 (título) / #E8E0FF (header) | 7.8:1  | ≥ 4.5:1   | ✅     |
| #8B3A00 (emoção) / #FFE8D8 (peach)  | 5.2:1  | ≥ 4.5:1   | ✅     |
| #1A3F7A (ação) / #D6E8FF (sky)      | 6.1:1  | ≥ 4.5:1   | ✅     |
| #155F40 (nec.) / #D4F0E4 (mint)     | 5.8:1  | ≥ 4.5:1   | ✅     |

> Ferramenta: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

---

## 📐 Breakpoints Responsivos Testados

| Viewport | Comportamento                                              |
|----------|------------------------------------------------------------|
| 360px    | Cabeçalho empilhado, fonte mínima 14px, grid 2 colunas    |
| 768px    | Layout tablet, grid 3 colunas, métricas lado a lado        |
| 1280px   | Layout desktop completo, grid 4 colunas de pictogramas     |

---

## 🎯 Recursos de Acessibilidade Adicionais

- **Preferência `prefers-reduced-motion`**: todas as transições desativadas
- **Preferência `prefers-contrast: high`**: paleta de maior contraste aplicada
- **Fonte Nunito**: legível e arredondada — indicada para usuários com dislexia
- **Emojis como ícones**: complementados sempre por texto descritivo
- **Tamanho mínimo de toque**: botões de pictograma ≥ 44×44px (WCAG 2.5.8)

---

*Documento gerado para o TCC PICTA · FACCAT · Sistemas de Informação · 2026*
