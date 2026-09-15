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
git clone https://github.com/SEU-USUARIO/picta.git
cd picta
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\\Scripts\\activate      # Windows
pip install -r requirements.txt
streamlit run app.py
```

A aplicação abrirá automaticamente em `http://localhost:8501`.

---

## 🔐 Ambiente de Demonstração

As credenciais de demonstração **não são mantidas no README nem devem ser usadas em produção**.

Para criar usuários de teste, configure explicitamente:

```text
CREATE_TEST_USER=true
```

Em ambientes reais, mantenha `CREATE_TEST_USER=false` e utilize contas individuais com senhas próprias.

**Não utilize dados reais de crianças em desenvolvimento, demonstrações públicas ou ambientes de teste.**

---

## 📁 Estrutura do Projeto

```text
picta/
├── app.py
├── requirements.txt
├── README.md
├── database/
│   └── db.py                 # Conexão, esquema e seed do banco
├── modules/
│   ├── auth.py               # Autenticação, sessões e vínculos
│   └── logs.py               # Registro e consulta de interações
├── utils/
│   ├── passwords.py          # Hash de senhas com PBKDF2 + migração legada
│   └── security.py           # Autorização por criança/vínculo
├── views/
│   ├── login.py
│   ├── painel_crianca.py
│   └── dashboard_cuidador/
└── assets/
```

O banco SQLite local (`picta.db`) é criado em tempo de execução e é ignorado pelo Git. Nunca versionar banco local ou banco de produção.

---

## 🔒 Segurança e Isolamento de Dados

O acesso aos dados de uma criança é condicionado ao usuário autenticado e ao vínculo correspondente:

- **Criança:** somente seu próprio registro.
- **Responsável/Cuidador:** somente crianças vinculadas à sua conta.
- **Profissional:** somente pacientes vinculados explicitamente.
- **Interações:** leitura e gravação passam por autorização no servidor.
- **Vínculos:** uma criança já vinculada a outro responsável não pode ser tomada por outra conta através do formulário de vínculo.
- **Senhas:** novas senhas usam PBKDF2-HMAC-SHA-256 com salt aleatório e 600.000 iterações. Hashes SHA-256 antigos são migrados automaticamente no primeiro login.
- **Sessões:** expiração por inatividade de 30 minutos e duração máxima de 8 horas.
- **HTML customizado:** valores controlados pelo usuário são escapados antes da renderização.
- **Banco:** PostgreSQL/Neon deve ser configurado por segredo/variável de ambiente; SQLite é destinado ao desenvolvimento local.

### Limitação conhecida da sessão

O cookie de sessão atual é criado pelo navegador via JavaScript, portanto não é possível marcar esse cookie como `HttpOnly` com a arquitetura atual. Em produção com dados reais, recomenda-se migrar para uma sessão gerenciada pelo servidor/provedor de identidade com proteção equivalente a `HttpOnly; Secure; SameSite=Strict`.

---

## 📦 Banco de Dados

O PICTA utiliza PostgreSQL/Neon quando `DATABASE_URL` ou `NEON_DATABASE_URL` está configurada. Na ausência dessas configurações, o projeto usa SQLite local para desenvolvimento.

Principais tabelas:

| Tabela | Descrição |
|---|---|
| `Utilizadores` | Contas de acesso e hashes de senha |
| `Criancas` | Dados das crianças e relações de responsabilidade |
| `Pictogramas` | Catálogo de pictogramas |
| `Registos_Interacao` | Registros de comunicação da criança |
| `Vinculos` | Relações de acesso entre usuários e crianças |
| `Sessoes` | Sessões autenticadas com expiração |

---

## 🧪 Testes de Segurança

A suíte em `tests/` cobre autenticação, migração de senha, isolamento por perfil, sessões, autorização de logs, isolamento real em SQLite, prevenção de sequestro de vínculo e escaping de valores exibidos em HTML customizado.

A GitHub Actions executa a suíte completa a cada push na branch de segurança e em pull requests para `main`.

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
- **PostgreSQL / SQLite** — persistência
- **Pandas** — análise e exportação
- **PBKDF2-HMAC-SHA-256** — armazenamento seguro de senhas

---

## 📄 Licença

Projeto acadêmico — uso educacional.  
FACCAT · Sistemas de Informação · Taquara, RS · 2026
