# Mapa de Navegação do PICTA

## Visão geral

O PICTA utiliza uma navegação condicionada ao perfil autenticado. Após o login, cada usuário é encaminhado para a área correspondente ao seu perfil, mantendo a interface e as funcionalidades adequadas ao contexto de uso.

```text
LOGIN
│
├── Cadastro
├── Recuperação de senha
└── Autenticação
    │
    ├── Criança
    │   └── Painel da Criança
    │       ├── Como me sinto
    │       ├── O que quero fazer
    │       └── O que preciso
    │
    ├── Responsável / Cuidador
    │   └── Área do Responsável
    │       ├── Hoje
    │       ├── Histórico
    │       ├── Minha Criança
    │       ├── Vínculos
    │       └── Meu Perfil
    │
    └── Profissional de Saúde
        └── Área do Profissional
            ├── Painel Clínico
            ├── Pacientes
            ├── Insights IA
            ├── Exportação
            ├── Coleta TCC
            └── Meu Perfil
```

## 1. Entrada do sistema

### Login

É a porta de entrada da aplicação.

A partir da tela de login, o usuário pode:

- autenticar-se;
- acessar o cadastro;
- recuperar a senha.

O encaminhamento após a autenticação depende do perfil associado à conta.

## 2. Perfil Criança

Fluxo principal:

```text
Login
  ↓
Painel da Criança
  ↓
Categoria de comunicação
  ↓
Seleção de pictograma
  ↓
Registro da interação
```

As categorias disponíveis no painel são:

- **Como me sinto**: comunicação de emoções e sentimentos;
- **O que quero fazer**: comunicação de ações/desejos;
- **O que preciso**: comunicação de necessidades/pedidos.

A interface infantil prioriza reconhecimento visual, toque e simplicidade, sem expor funcionalidades administrativas.

## 3. Perfil Responsável / Cuidador

Fluxo principal:

```text
Login
  ↓
Área do Responsável
  ├── Hoje
  ├── Histórico
  ├── Minha Criança
  ├── Vínculos
  └── Meu Perfil
```

### Hoje

Apresenta as comunicações registradas no dia e informações resumidas de acompanhamento.

### Histórico

Permite consultar interações de períodos anteriores em formato de linha do tempo.

### Minha Criança

Apresenta dados e informações de acompanhamento da criança vinculada ao responsável.

### Vínculos

Permite consultar e gerenciar os vínculos com profissionais de saúde conforme as regras do sistema.

### Meu Perfil

Permite consultar e atualizar informações do próprio usuário e realizar operações de perfil disponíveis na aplicação.

## 4. Perfil Profissional de Saúde

Fluxo principal:

```text
Login
  ↓
Área do Profissional
  ├── Painel Clínico
  ├── Pacientes
  ├── Insights IA
  ├── Exportação
  ├── Coleta TCC
  └── Meu Perfil
```

### Painel Clínico

Exibe indicadores, alertas e registros recentes relacionados ao paciente selecionado.

### Pacientes

Permite consultar os pacientes vinculados ao profissional.

### Insights IA

Apresenta análises estatísticas e indicadores derivados das interações registradas.

### Exportação

Permite baixar dados disponíveis para exportação em formatos suportados pela aplicação, incluindo CSV e PDF quando aplicável.

### Coleta TCC

Área destinada à coleta controlada do estudo de campo. Trabalha com participantes identificados por código pseudonimizado, faixa etária, tarefas, sessões e métricas de interação.

### Meu Perfil

Permite consultar e atualizar informações do próprio usuário e operações de perfil disponíveis.

## 5. Regras de navegação

- A navegação é determinada pelo perfil autenticado.
- O usuário não deve depender do botão de voltar do navegador para acessar as áreas principais.
- Cada item de navegação corresponde a uma tela ou funcionalidade existente.
- O encerramento da sessão permanece disponível nas áreas administrativas.
- A área infantil possui fluxo próprio e simplificado.

## 6. Relação com a coleta do TCC

A opção **Coleta TCC** faz parte exclusivamente da área do profissional de saúde. O fluxo de coleta é separado das demais funcionalidades do PICTA e foi projetado para trabalhar com dados de pesquisa pseudonimizados.

> Este documento descreve a navegação implementada no projeto. Ele não substitui protocolos de pesquisa, instruções éticas ou orientações institucionais.
