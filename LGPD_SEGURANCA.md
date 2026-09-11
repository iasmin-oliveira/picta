# PICTA — Segurança e Privacidade

**Documento técnico de referência · TCC FACCAT · 2026**

> Este documento descreve controles técnicos do protótipo. Não substitui análise jurídica, política de privacidade, DPIA ou revisão de segurança para uso clínico/produção.

## 1. Escopo e princípio de uso

O PICTA foi desenvolvido como protótipo acadêmico de Comunicação Aumentativa e Alternativa para crianças neurodiversas. Os controles abaixo têm como objetivo reduzir acesso indevido entre contas e crianças.

**Não utilizar dados reais de crianças em desenvolvimento, demonstrações públicas ou ambientes de teste.** Para uso real com dados de crianças, a arquitetura deve passar por avaliação de segurança, privacidade e conformidade antes da disponibilização.

## 2. Credenciais

- Novas senhas e senhas alteradas usam **PBKDF2-HMAC-SHA-256 com 600.000 iterações e salt aleatório**.
- Hashes legados SHA-256 são aceitos somente para migração e substituídos por PBKDF2 após login bem-sucedido.
- O código não armazena senhas em texto plano.
- A senha mínima atualmente exigida no cadastro é de 6 caracteres.

## 3. Sessões e autenticação

- Cada login cria um token aleatório de sessão armazenado no banco.
- O token de autenticação do PICTA fica somente no `st.session_state` da sessão do Streamlit e **não é gravado em cookie próprio nem exposto ao JavaScript da página**.
- A sessão possui **máximo absoluto de 8 horas**.
- Há expiração por **30 minutos de inatividade**.
- O token é revogado de forma síncrona no logout.
- A aplicação revalida a sessão periodicamente durante a navegação.
- O PICTA não depende mais de `streamlit-cookies-controller` para autenticação.

A remoção do cookie próprio é intencional: o Streamlit não oferece ao código da aplicação uma API para definir diretamente um cookie próprio com `HttpOnly`. Em vez de tentar simular `HttpOnly` via JavaScript, o token de autenticação da aplicação permanece no estado de sessão do servidor.

## 4. Isolamento de dados por usuário

O acesso a uma criança é validado no servidor:

| Perfil | Regra de acesso |
|---|---|
| `crianca` | somente o registro associado ao próprio `utilizador_id` |
| `responsavel` / `cuidador` | somente crianças cujo `cuidador_id` corresponde ao usuário autenticado |
| `profissional` | somente crianças relacionadas por `Vinculos` |

Além da interface, operações de leitura e gravação de interações passam por `exigir_acesso_crianca`.

As operações de alteração da própria conta também verificam que o ID recebido corresponde ao usuário autenticado. Listagens de crianças e vínculos são igualmente vinculadas à sessão.

## 5. Proteções contra XSS e manipulação de parâmetros

- Valores controlados pelo usuário exibidos em HTML customizado passam por `html.escape`.
- IDs de criança usados no painel infantil são derivados da sessão da criança, e não de um ID fornecido na URL.
- Parâmetros de pictogramas são validados antes do registro.
- Consultas SQL utilizam parâmetros em vez de concatenar valores fornecidos pelo usuário.
- O cadastro de uma criança não procura nem reutiliza registros globais pelo nome. A relação é feita pelo usuário proprietário.

## 6. Logs e exportações

- Registro de interação: somente se a sessão puder acessar a criança alvo.
- Consulta de histórico: somente se a sessão puder acessar a criança alvo.
- Consulta por período, usada pelas exportações CSV/PDF, reutiliza a mesma autorização dos históricos.
- Exportações não devem ser interpretadas como uma autorização independente: o acesso aos dados continua condicionado à autorização da criança.

## 7. Banco de dados

- PostgreSQL/Neon é usado quando `DATABASE_URL` ou `NEON_DATABASE_URL` está configurada.
- SQLite é destinado ao desenvolvimento local.
- Arquivos locais `*.db`, `*.sqlite` e `*.sqlite3` são ignorados pelo Git.
- Segredos do Streamlit em `.streamlit/secrets.toml` também são ignorados pelo Git.
- O repositório não deve conter credenciais reais ou banco de produção.

## 8. Testes automatizados

A suíte de segurança cobre, entre outros:

- hash com salt e verificação de senha;
- migração de hash SHA-256 legado;
- isolamento de crianças com nomes iguais;
- matriz de autorização por perfil;
- expiração e revogação de sessão;
- operações SQL parametrizadas;
- vinculação de listagens e operações à sessão autenticada;
- bloqueio de alteração de conta por ID de outro usuário;
- isolamento real de registros em SQLite;
- autorização de leitura/gravação dos históricos;
- autorização em PostgreSQL executado em container;
- presença de escaping nas áreas com HTML customizado;
- ausência de cookie de autenticação criado por JavaScript;
- configurações que não desativam explicitamente XSRF/CORS.

A GitHub Actions executa a suíte em `tests/` a cada push na branch de segurança e em pull requests para `main`.

## 9. Pendências para uma versão de produção real

Mesmo com o token fora de cookies próprios, estes pontos continuam sendo necessários antes de um uso clínico/produção com dados reais:

- implementar rate limiting ou proteção equivalente contra tentativas repetidas de login;
- executar análise de dependências/vulnerabilidades periodicamente;
- revisar retenção, exclusão, consentimento/base legal e demais requisitos de privacidade aplicáveis ao contexto real;
- realizar teste de segurança do ambiente implantado, incluindo HTTPS, banco, segredos e permissões;
- adicionar monitoramento/auditoria apropriados para acessos a dados;
- validar o comportamento de sessão e reconexão no provedor de hospedagem escolhido.

**Conclusão:** o branch de hardening reduz significativamente a superfície de ataque da autenticação e reforça o isolamento entre contas e crianças no protótipo. O uso com dados reais de crianças ainda depende de avaliação de segurança, privacidade e do ambiente de implantação.
