# 🌟 PICTA
**Assistente de Comunicação e Expressão Emocional com Apoio Visual para Crianças Neurodiversas**

> Projeto de Desenvolvimento de Software — FACCAT · Curso de Sistemas de Informação · 2026  
> Autora: Iasmin Hahn Oliveira

---

## 📋 Sobre o Projeto

O PICTA é um assistente digital de Comunicação Aumentativa e Alternativa (CAA), desenvolvido em Python com o framework Streamlit. Utiliza pictogramas baseados no **Método DHACA** para apoiar a comunicação e expressão emocional de crianças neurodiversas (7–10 anos).

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.11+
- pip

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/SEU-USUARIO/picta.git
cd picta

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a aplicação
streamlit run app.py
```

A aplicação abrirá automaticamente em `http://localhost:8501`.

---

## 🔐 Credenciais de Demonstração

| Perfil | Utilizador | Senha |
|---|---|---|
| 👩‍⚕️ Cuidador / Terapeuta | `cuidador_teste` | `senha123` |
| 🧒 Criança | `joao` | `joao123` |

> O banco de dados é criado e populado automaticamente na primeira execução.

---

## 📁 Estrutura do Projeto

```
picta/
├── app.py                  # Entry point — roteador de perfis
├── requirements.txt
├── README.md
├── picta.db                # SQLite (gerado em runtime)
│
├── database/
│   └── db.py               # Conexão, esquema e seed do banco de dados
│
├── modules/
│   ├── auth.py             # Autenticação e consulta de perfis
│   └── logs.py             # Registo e consulta de interações
│
├── views/
│   ├── login.py            # Tela de Login
│   ├── painel_crianca.py   # Grade de pictogramas (perfil Criança)
│   └── dashboard_cuidador.py # Dashboard analítico (perfil Cuidador)
│
└── assets/
    └── pictogramas/        # Imagens dos pictogramas (Ciclos futuros)
```

---

## 📦 Banco de Dados (SQLite)

O arquivo `picta.db` é gerado automaticamente com as seguintes tabelas:

| Tabela | Descrição |
|---|---|
| `Utilizadores` | Contas de login (criança e cuidador), senha em hash SHA-256 |
| `Criancas` | Dados das crianças vinculadas a um cuidador |
| `Pictogramas` | Catálogo de pictogramas por categoria (emoção, ação, necessidade) |
| `Registos_Interacao` | Log de cada clique da criança (data, hora, pictograma) |

---

## 🗓️ Sprints de Desenvolvimento

| Ciclo | Período | Entregas |
|---|---|---|
| **Ciclo 1** ✅ | 28/03 – 06/04 | Ambiente, BD, Autenticação |
| **Ciclo 2** | 11/04 – 11/05 | Interface da Criança, Log de cliques |
| **Ciclo 3** | 16/05 – 22/06 | Dashboard completo, Exportação, UX final |

---

## 🧰 Tecnologias

- **Python 3.11+**
- **Streamlit** — framework de interface web
- **SQLite** — banco de dados relacional local
- **Pandas** — análise de dados (Ciclo 3)
- **hashlib** — hash seguro de senhas (SHA-256)

---

## 📄 Licença

Projeto acadêmico — uso educacional.  
FACCAT · Sistemas de Informação · Taquara, RS · 2026
