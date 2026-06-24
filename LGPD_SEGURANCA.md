# 🔒 PICTA — Medidas de Segurança e Privacidade (LGPD)

**Documento de referência técnica · Ciclo 2 · TCC FACCAT 2026**

---

## 1. Base Legal e Enquadramento LGPD

O PICTA trata dados pessoais de crianças (menores de 12 anos), o que configura
**categoria especial de dados sensíveis** (Art. 11, Lei 13.709/2018).

| Princípio LGPD        | Implementação no PICTA                                     |
|-----------------------|------------------------------------------------------------|
| Finalidade            | Dados usados exclusivamente para comunicação terapêutica   |
| Necessidade           | Coleta mínima: nome, username, data de nascimento          |
| Transparência         | Perfis com acesso segregado (criança / responsável / prof) |
| Segurança             | Hash SHA-256, isolamento por cuidador_id, sessões TTL      |
| Prevenção             | Timeout de inatividade (60 min), cookies SameSite=Strict   |
| Não discriminação     | Dados não usados para fins de perfilamento comercial       |

---

## 2. Proteção de Credenciais

### 2.1 Hash de Senhas — SHA-256

```python
# database/db.py — linha hash_senha()
import hashlib
def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()
```

- Senhas **nunca armazenadas em texto plano**
- Hash é **unidirecional** — impossível recuperar a senha original
- Mínimo de **6 caracteres** obrigatório no cadastro

### 2.2 Sessões com TTL e Timeout de Inatividade

```python
# modules/auth.py
INACTIVITY_MINUTES = 60          # sessão expira após 60 min sem uso
COOKIE_MAX_AGE = 30 * 24 * 3600  # cookie do navegador: 30 dias
```

- Cada login gera um **token UUID v4** único
- Sessão validada a cada request: verifica `expira_em` + `ultima_atividade`
- Logout revoga o token no banco imediatamente

### 2.3 Segurança do Cookie

```python
# controllers/auth_controller.py
f'{COOKIE_NAME}={token}; max-age={COOKIE_MAX_AGE}; path=/; SameSite=Strict'
```

- `SameSite=Strict` — previne ataques CSRF
- `path=/` — cookie restrito ao domínio da aplicação

---

## 3. Isolamento de Dados por Papel (RBAC)

| Perfil         | Acesso a dados                                      |
|----------------|-----------------------------------------------------|
| `crianca`      | Apenas seu próprio painel de pictogramas            |
| `responsavel`  | Apenas crianças com `cuidador_id = seu id`          |
| `profissional` | Apenas crianças vinculadas via tabela `Vinculos`    |

### Query de isolamento (responsável):
```sql
SELECT id, nome FROM Criancas WHERE cuidador_id = ?  -- id do responsável logado
```

### Query de isolamento (profissional):
```sql
SELECT c.id, c.nome FROM Criancas c
JOIN Vinculos v ON v.crianca_id = c.id
WHERE v.usuario_id = ?  -- id do profissional logado
```

**Teste de bloqueio demonstrado:** Um profissional com `usuario_id = 5` não consegue
acessar dados de uma criança cujo vínculo não foi criado pelo responsável —
a query `JOIN Vinculos` retorna zero linhas, e a interface exibe "Nenhuma criança vinculada".

---

## 4. Dados Coletados e Finalidade

| Dado                   | Tabela               | Finalidade                          | Tempo de Retenção |
|------------------------|----------------------|-------------------------------------|-------------------|
| Nome                   | Utilizadores         | Identificação na interface          | Enquanto ativo    |
| Username               | Utilizadores         | Autenticação                        | Enquanto ativo    |
| Senha (hash SHA-256)   | Utilizadores         | Autenticação segura                 | Enquanto ativo    |
| Data de nascimento     | Criancas             | Contextualização clínica            | Enquanto ativo    |
| Interações/cliques     | Registos_Interacao   | Relatórios terapêuticos             | Enquanto ativo    |
| Token de sessão        | Sessoes              | Gestão de autenticação              | 30 dias           |

**Dados NÃO coletados:** localização GPS, dados biométricos, histórico de navegação,
dados de terceiros, cookies de rastreamento.

---

## 5. Teste de Bloqueio por Isolamento

### Cenário de teste manual:

1. Criar responsável `resp_a` com criança `crianca_x`
2. Criar responsável `resp_b` sem crianças
3. Logar como `resp_b` → aba "Dados da criança" deve exibir **"Nenhuma criança vinculada"**
4. Confirma que `crianca_x` está inacessível para `resp_b` ✅

### Verificação via SQL:
```sql
-- Deve retornar 0 linhas para resp_b
SELECT id, nome FROM Criancas WHERE cuidador_id = <id_resp_b>;
```

---

## 6. Recomendações para Produção (Streamlit Cloud / Neon)

- [ ] Usar **HTTPS** obrigatório (Streamlit Cloud já provê TLS)
- [ ] Adicionar flag `Secure` ao cookie (requer HTTPS)
- [ ] Substituir SHA-256 por **bcrypt** ou **Argon2** (mais resistente a brute force)
- [ ] Implementar rate limiting no login (máx. 5 tentativas / 15 min)
- [ ] Log de auditoria para acessos a dados de crianças
- [ ] Política de retenção: apagar dados após inatividade > 2 anos

---

*Documento gerado para o TCC PICTA · FACCAT · Sistemas de Informação · 2026*
