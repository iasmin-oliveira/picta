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

Para criar usuários de teste, configure explicitamente a variável de ambiente:

```text
CREATE_TEST_USER=true
```

Em produção, mantenha `CREATE_TEST_USER=false` e utilize contas individuais com senhas próprias.

---

## 📁 Estrutura do Projeto

```
picta/
├── app.py
├── requirements.txt
├── README.md
├── picta.db                  # SQLite somente para desenvolvimento local
│
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

---

## 🔒 Segurança e Isolamento de Dados

O acesso aos dados de uma criança é condicionado ao usuário autenticado e ao vínculo correspondente:

- **Criança:** somente seu próprio registro.
- **Responsável/Cuidador:** somente crianças vinculadas à sua conta.
- **Profissional:** somente pacientes vinculados explicitamente.
- **Interações:** leitura e gravação passam por autorização no servidor.
- **Senhas:** novas senhas usam PBKDF2-SHA-256 com salt aleatório. Hashes SHA-256 antigos são migrados automaticamente no primeiro login.
- **Sessões:** expiração por inatividade de 30 minutos e duração máxima de 8 horas.
- **Produção:** o banco PostgreSQL/Neon deve ser configurado por segredo/variável de ambiente; SQLite é destinado ao desenvolvimento local.

Não use dados reais de crianças em ambientes de demonstração ou desenvolvimento.

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
- **Pandas** — análise de dados
- **hashlib / PBKDF2** — armazenamento seguro de senhas

---

## 📄 Licença

Projeto acadêmico — uso educacional.  
FACCAT · Sistemas de Informação · Taquara, RS · 2026
