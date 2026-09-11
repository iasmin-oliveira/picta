# PICTA — Coleta de dados para estudo de campo

## Objetivo

O PICTA possui um modo específico para coleta de métricas do TCC. Esse modo foi separado dos cadastros clínicos existentes para reduzir a quantidade de dados pessoais usados na análise.

A coleta técnica registra apenas um código pseudônimo do participante, faixa etária, tarefa, eventos de interação e métricas de sessão.

## Antes da primeira criança

A coleta com crianças reais deve seguir o protocolo aprovado pela instituição e pelo sistema CEP/CONEP quando aplicável. Para crianças, o protocolo deve justificar sua inclusão e prever consentimento do responsável legal e assentimento da criança, preservando sua autonomia conforme sua capacidade.

O sistema **não substitui** o TCLE/TALE nem o registro institucional da pesquisa.

## Fluxo no PICTA

1. Entrar com uma conta de perfil `profissional` autorizada para a pesquisa.
2. Abrir **Coleta TCC**.
3. Criar o participante com um código como `P01`, `P02` ou `P100`.
4. Selecionar somente a faixa etária `7-8` ou `9-10`.
5. Confirmar, antes do cadastro, que o consentimento do responsável e o assentimento da criança foram obtidos conforme o protocolo aprovado.
6. Selecionar uma tarefa padronizada:
   - **Como estou me sentindo**
   - **O que eu preciso**
   - **O que eu quero fazer**
   - **Exploração livre**
7. Iniciar a sessão.
8. Entregar a interface visual à criança. Cada escolha de pictograma é registrada automaticamente.
9. Marcar **Precisei de ajuda** quando houver necessidade de assistência durante a tarefa.
10. Finalizar a sessão.
11. Na aba **Métricas**, revisar os registros e exportar o CSV pseudonimizado.

## Dados coletados pelo modo de pesquisa

| Dado | Coletado | Finalidade |
|---|---:|---|
| Código do participante | Sim | Diferenciar participantes sem usar nome |
| Faixa etária | Sim | Caracterizar a amostra por faixa |
| Tarefa | Sim | Comparar tarefas |
| Início/fim da sessão | Sim | Calcular duração |
| Pictograma escolhido | Sim | Medir padrão de interação |
| Ordem da escolha | Sim | Analisar sequência de interações |
| Conclusão da tarefa | Sim | Medir taxa de conclusão |
| Necessidade de ajuda | Sim | Medir necessidade de assistência |
| Nome da criança | Não | Não é necessário para as métricas |
| Data de nascimento | Não | Substituída por faixa etária |
| CPF | Não | Não é necessário |
| E-mail da criança | Não | Não é necessário |
| Foto/áudio/vídeo | Não | Não é necessário para o estudo técnico |
| Campo livre sobre a criança | Não | Evita registro acidental de PII |

## Métricas disponíveis para o TCC

A partir das sessões coletadas, o CSV permite calcular:

- quantidade de sessões por participante;
- taxa de conclusão;
- duração da sessão;
- quantidade média de interações por sessão;
- necessidade de ajuda;
- distribuição de interações por categoria de pictograma;
- distribuição de pictogramas selecionados;
- comparação entre tarefas;
- comparação entre faixas etárias.

## Segurança e isolamento

Cada participante da pesquisa fica associado ao profissional que o cadastrou. Outro profissional não consegue listar o participante, iniciar sessão, registrar interação ou consultar suas métricas.

A exclusão de um participante remove em cascata suas sessões e interações pseudonimizadas.

## Regras para a coleta

- Não usar nome da criança como código.
- Não usar CPF, telefone, endereço, escola ou outros identificadores no campo de código.
- Não registrar diagnóstico em campos da coleta.
- Não registrar informações clínicas ou familiares em observações, porque o modo de pesquisa não possui campo livre para isso.
- Não realizar coleta com criança real antes da autorização ética/institucional aplicável ao estudo.
- Usar dados de teste fictícios durante desenvolvimento e demonstrações.

## Observação sobre o cadastro clínico existente

O PICTA ainda possui o fluxo clínico/demonstrativo existente com cadastro de criança contendo nome e data de nascimento. O modo **Coleta TCC** não utiliza esses campos para identificar os participantes da pesquisa.

Essa separação permite testar o protótipo com um conjunto mínimo de dados para a análise do TCC, sem alterar o funcionamento dos fluxos já existentes.
