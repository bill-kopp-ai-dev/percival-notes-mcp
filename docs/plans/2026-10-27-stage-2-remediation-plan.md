# Stage-2 — Remediação do Percival Notes MCP

**Data / revisão:** 2026-10-29 / 1.4.
**ID / estado:** S2-NT / execução local em andamento; 10 ações ativas.
**Checkout executor:** `/home/bill/Projects/percival-notes-mcp`.  
**Owner e aprovador final:** Bill Kopp (`bill.kopp.dev@gmail.com`), responsável único pelo Notes MCP e pela infraestrutura IaC da Positronic Bean Labs (`labs.positronicbean.com`, em desenvolvimento).

## 1. Objetivo, fontes e fronteira

Tratar os 16 achados da **seção 6** do
[relatório Notes](../../../positronic-bean-IaC/docs/reports/2026-10-27-percival-notes-mcp-iac-readiness-report.md#6-achados-issues-e-inconsistências),
com seções 7/9 como complemento. O relatório de origem tinha 12 ações (2 P1,
6 P2, 4 P3), sem P0; esta revisão mantém 10 ações ativas.
Snapshot/HEAD na emissão: `83980418b3239be5476f6d347ceb8dad32d90e8e`.
Exclusões locais preexistentes da nota F3 e `docs/search-benchmark.md` preservadas.

[Coordenador stage-2](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md)
— retorno S2-NT, seções 3 e 7. Referências:
[consolidação](../../../positronic-bean-IaC/docs/reports/2026-10-26-stage-1-consolidated-readiness-report.md)
e [D-01..D-06](../../../positronic-bean-IaC/docs/decisions/2026-10-27-iac-stage-1-scope-and-pilot-decisions.md).

Emissão documental e execução técnica local no checkout dono. Operações em runtime
gerenciado e qualificação de piloto não fazem parte do escopo vigente deste plano.
Notes permanece o servidor previsto para o par piloto Percival + Notes (D-01), mas
este plano não homologa runtime nem autoriza mexer no vault do operador. Preservar
contrato das tools, OKF, busca ripgrep/fallback, containment e envelopes de conteúdo
não confiável.

## 2. Preparação e decisões

- [x] Ler instruções/README/contrato de vault; baseline do checkout `40fd2af2902ed2f94d528b84052428ec808b0b1e`; preservadas as exclusões preexistentes de `docs/search-benchmark.md` e o não espelhamento local da nota F3.
- [x] Criar somente fixtures sintéticas para falhas, restore, permissões e symlinks; restore validado com UID/GID `65532:65532`, manifesto SHA-256, leitura MCP, busca e escrita; negativo de owner incorreto explícito.
- [x] Owner (Bill, 2026-10-28) definiu retenção de backups fora do vault, 7 diários + 4 semanais; init único pelo launcher; aceitação da limitação de reprodutibilidade após medição; logs com path somente em DEBUG; contrato `{notes, omitted}`; autorização histórica para commit/push em `origin/main` do produto. O destino F3 registrado anteriormente foi substituído por `R-05`: canônico em `pblabs-mcp-index`, sem espelho local de conteúdo. Sem VEX se o scan não encontrar CVEs, conforme o gate de `R-07`.
- [x] Atualização de decisão do operador, 2026-10-29: `R-10` supersede `R-02` quanto ao default do broker Percival, que permanece amplo conforme B14/B22/B23–B25. Notes mantém configuração explícita do bind de vault necessário; perfil e dados existentes não devem ser ampliados nem mutados implicitamente. `R-03` remove dimensionamento de esforço, custo e prazo; `R-05` centraliza F3 por imagem em `pblabs-mcp-index`; `R-06` adota schema externo de `server.json`, extensão operacional versionada `pblabs.app.yaml` e destino `pblabs-mcp-index`, sem dependência do Docker MCP Catalog; `R-07` exige VEX por CVE ligado ao image ID e assinado pelo owner, com CVEs da imagem base tratados por herança; `R-08` fixa pin aprovado e janela única datada para operações que dependem dela.

### 2.1. Decisões do owner — Bill Kopp, 2026-10-29

Bill Kopp é o único owner e decisor final do Notes MCP e da infraestrutura
IaC da Positronic Bean Labs. As decisões abaixo são finais; não há aprovação
adicional a solicitar a terceiros.

| Item | Decisão registrada por Bill | Efeito no plano |
|---|---|---|
| S2-C02 | “Aprovado.” | ADR aprovado; não é bloqueio para este plano. |
| S2-C01 | “Revisado e aprovado.” | Contrato aprovado; não é bloqueio pendente para A-004. |
| S2-C04 | “Proposta aceita e eu (Bill) sou o responsável.” | Bill assume a implementação; permanecem a implementação e a prova de `V-REUSE`. |
| Publicação | “A publicação está totalmente fora do escopo dessa etapa; retirar do plano.” | Push da imagem a registry, `RepoDigest`, manifests de distribuição, índice e gates de publicação/CI associados ficam fora do escopo e não são bloqueios desta etapa. |
| A-003/A-006 | “Eu não tenho e nem vou ter essas informações, dessa forma não faz sentido mante-las.” | Bill retira A-003 e A-006 do escopo ativo deste plano. Não são ações adiadas, bloqueios ou critérios de aceite; não inferir qualificação de runtime nem causa do `exit 255`. |

## 3. Backlog ativo e aceite

Por decisão do owner registrada na seção 2.1, duas ações de origem foram retiradas;
a tabela contém as 10 ações ativas. Os IDs originais das ações mantidas foram
preservados. O estado histórico e a contagem vigente estão na seção 6.

| Ação | Achados / P | Trabalho e áreas previstas | Dependência / execução | Aceite verificável |
|---|---|---|---|---|
| A-001 | F-001 / P1 | Tornar busca resiliente a symlink externo nos caminhos ripgrep e fallback em `notes_mcp.py` | Sem dependência externa | Arquivo fora do vault ignorado com aviso sanitizado; notas válidas encontradas; nenhum conteúdo/path externo exposto; testar ambos os caminhos |
| A-002 | F-002 / P1 | Publicar backup/restore preservando owner numérico/permissões e exigindo leitura após restore | Decisão do owner sobre cópias/retenção | Restore em fixture com manifesto SHA-256 igual, UID/GID compatíveis (baseline UID 65532, confirmar candidato), leitura/busca/escrita funcionais; negativo de owner errado explícito |
| A-004 | F-004 / P2 | Declarar init único requerido ou embutir init com decisão compatível; registrar contrato de implantação | S2-C01 aprovado por Bill; launchers | `docker stop` em menos de 1 s na fixture; sem init duplo; ausência de init recusada/documentada conforme decisão |
| A-005 | F-005 / P2 | Normalizar build ou declarar/medir limitação de reprodutibilidade com decisão do owner | Limitação aceita por Bill e diferenças já medidas | Aceite satisfeito: diferenças registradas e limitação aceita; promoção/publicação não é gate desta etapa |
| A-007 | F-007 / P2 | Rescan local do candidato e registrar o resultado; produzir VEX conforme `R-07` se houver CVEs | Scan local do candidato | Scan com DB/data/image ID identificados e resultado registrado; sem VEX se o scan estiver limpo. Gates de tracker, distribuição e publicação não pertencem a esta etapa |
| A-008 | F-008, F-015 / P2 | Expor leituras parciais em stats/read_multiple com motivo de omitidos, sem vazamento de path externo | Compatibilidade do contrato de resposta com consumidores | Fixture com arquivo ilegível distinguida de vault vazio; notas lidas preservadas, omitidos/motivos explícitos; envelope e controle de path mantidos |
| A-009 | F-009 / P3 | Validar glob antes da enumeração e sanitizar aviso | Sem dependência externa | `../../*` e padrão absoluto recusados antes de varrer; sem resultado espúrio `.` nem caminhos externos nos logs |
| A-010 | F-010, F-011 / P3 | Remover raiz interna do status e retirar paths de notas de INFO | Política de privacidade do produto | Status sem path absoluto; logs operacionais sem nome/caminho sensível; DEBUG privado apenas se explicitamente configurado |
| A-011 | F-012, F-013 / P3 | Tolerar quebra final/CRLF no frontmatter e derivar versão do pacote no serverInfo | Contrato OKF preservado | Frontmatter válido aceito e persistido corretamente; initialize informa versão do produto (0.1.5 só se vigente), não do SDK |
| A-012 | F-014, F-016 / P3 | Corrigir README do ripgrep/restore e remover apt/setuid residuais não usados | A-002; compatibilidade da imagem | Docs conferem com versão embarcada; inventário limpo sem eliminar dependência necessária; smoke/protocolo/busca permanecem verdes |

## 4. Sequência e dependências

1. **NT-1:** A-001/A-002 concluídas. Os ensaios deste plano usam sempre fixture
   sintética; não fazem operações em runtime gerenciado nem em vault real.
2. **NT-2:** A-008/A-009/A-010/A-011; A-004 com S2-C01 aprovado; A-012 após o
   runbook de restore. Mudanças na forma de resposta devem ser coordenadas com clientes.
3. **NT-3:** A-005 aceita com a limitação medida; A-007 concluída pelo scan local;
   Bill implementa S2-C04 e comprova o reuso do harness nos dois MCPs previstos.

Riscos: skip silencioso pode ocultar falha, nova resposta parcial pode quebrar
cliente, restore com UID errado pode parecer perda de tags. Proteger com casos
positivos/negativos e manifesto de conteúdo; não fazer chown/cópia no vault real.
`R-03` remove a exigência de estimar esforço, custo ou prazo.

## 5. Qualificação futura no projeto

- [x] `uv run pytest -q`, regressões significativas e checks locais existentes;
  não introduzir lint/cobertura como requisito novo sem decisão do produto.
- [x] Build identificado e smoke MCP stdio, init único, stdout JSON-RPC-only;
  write/read/search em fixture OKF com ripgrep e fallback aplicáveis.
- [x] Repetir contenção/glob/symlinks, frontmatter, stats/leituras parciais e logs;
  comparar conteúdo/owner após backup/restore e recriação do container.
- [ ] Revalidar localmente `V-BUILD`, `V-RUN`, `V-CONFIG`, `V-DATA`, `V-MCP` e
  `V-FUNC`; implementar S2-C04 e provar `V-REUSE` nos dois MCPs previstos.

Esta qualificação cobre o produto e fixtures locais. Não conclui nem declara estado
de runtime gerenciado, piloto ou causa de eventos operacionais. Publicação e
distribuição da imagem também estão fora do escopo desta etapa.

## 6. Penúltima etapa — documentar execução neste plano

- [x] Registrar ações/subtarefa, owner/data, SHA inicial/final, mudanças, comandos e
  resultados locais resumidos, além dos limites e vereditos `V-*` conhecidos.
- [x] Registrar decisões de retenção/owner e pendências; complementar seção 9 do
  relatório IaC quando autorizado, preservando baseline e sem conteúdo do vault real.
- [x] Registrar que os artefatos brutos históricos não estão anexados/referenciados
  aqui. Os resumos abaixo não comprovam reprodutibilidade exata; essa lacuna não
  bloqueia a continuação local. Não reconstruir evidências por suposição.

| Data / owner | Ações / achados | SHA inicial → final | Mudanças / evidências locais | Resultado / V-* / pendências |
|---|---|---|---|---|
| 2026-10-28 (estado histórico, não vigente) / Bill Kopp | A-001, A-002, A-004, A-005, parcela local de A-007 e A-008–A-012 verificadas localmente (**10/12**); A-003 parcial (candidato pronto; solicitação de repin/hardening a encaminhar aos gestores); A-006 pendente de encaminhamento/investigação no broker; para A-007, referência ao tracker central e scan CI continuam externos; S2-NT-X01 segue com materialização/validação de schema e manifests pendentes, mas formato e destino decididos por `R-06` | Inicial `40fd2af2902ed2f94d528b84052428ec808b0b1e`; baseline do candidato `fbf1a2911e522f184c1945924c95796533062fb6` | `uv run pytest -q`: 68 passed; smoke MCP stdio (12 tools, resource, prompts, read/write/search, containment, persistence) e `docker-ci-conformance.py` aprovados. Dois builds `--no-cache`: image IDs `sha256:c7944fbd28a5f0b0a6fda557a2597c636facb136fe9a58451875c4ac19aa8674` e `sha256:618845639f43f1297a400231df4fa551149b2e5584b166cea4fecd8474041eec`; rootfs 7.363 membros, 6 diferenças de conteúdo/hash (cache ldconfig, logs apt/dpkg, `RECORD`, `uv_cache.json`) e 2.308 mtimes divergentes; não reprodutibilidade aceita por Bill. Trivy 0.76.1, DB atualizada em 2026-10-28: 0 CVEs em 105 pacotes Debian e dependências Python; resultado local resumido na [nota F3](../issues/2026-10-10-f3-status.md), sem VEX quando scan limpo. Lifecycle: com `--init` 99 ms/exit 143; sem init, cerca de 1,8 s/exit 0 no candidato; E-022 original não reproduzido. Restore em fixture verificou SHA, modos, UID/GID, leitura/busca/escrita MCP e negativo owner 0:0. | Estado então: pendentes repin/hardening, investigação do broker, tracker/scan CI e materialização S2-NT-X01; sem piloto/publicação liberado. O registro seguinte contém o estado vigente. |
| 2026-10-29 / Bill Kopp (owner único) | S2-C01/S2-C02 aprovados; S2-C04 aceito, implementação atribuída a Bill; publicação/registry/manifests/índice e gates de distribuição fora do escopo. A-005 aceita com diferenças medidas. A-003/A-006 retiradas do escopo ativo por decisão do owner. | Sem alteração do candidato. | A-003/A-006 não são executadas nem avaliadas neste plano. Artefatos brutos históricos não anexados/referenciados. | Prosseguir com as 10 ações restantes, S2-C04 e `V-*` locais. Este plano não declara runtime/piloto qualificado nem causa do `exit 255`. |

**Contagem vigente:** 10/10 ações ativas aceitas localmente. A-003 e A-006 foram
retiradas e não entram no denominador. O registro histórico de 2026-10-28 acima e a
contagem **9 verificadas, 2 parciais e 1 aberta** do relatório daquela data são históricos.

### 6.1. Trilha e limites das evidências

| Verificação | Registro disponível | Limite atual |
|---|---|---|
| Suíte (`uv run pytest -q`, 68 aprovados) | Resultado resumido no retorno acima | Saída bruta e identificação detalhada do ambiente não estão anexadas/referenciadas |
| Smoke MCP stdio e `docker-ci-conformance.py` | Escopo e resultado resumidos no retorno acima | Logs, argumentos completos e arquivos de resultado do candidato não estão anexados/referenciados |
| Trivy 0.76.1 / candidato `sha256:c7944fbd…` | [Nota F3 local](../issues/2026-10-10-f3-status.md) registra ID, data/base do DB e contagem | Nota-resumo; JSON bruto e SBOM do candidato não foram localizados nos artefatos versionados consultados |
| Builds `--no-cache` e comparação de rootfs | IDs e diferenças resumidos no retorno acima | Manifestos/saída da comparação não foram localizados nos artefatos versionados consultados |
| Restore e lifecycle em fixture | Resultado resumido no retorno acima | Manifestos SHA-256 e logs/JSON das execuções do candidato não foram anexados/referenciados |
| Diagnóstico inicial (snapshot `83980418…`) | [Índice das evidências originais](../../../positronic-bean-IaC/docs/reports/evidence/percival-notes-mcp/83980418b323/README.md) | Evidência do snapshot inicial, não substitui artefatos do candidato `fbf1a291…` |

## 7. Última etapa — atualizar o plano coordenador

- [x] Reler o [stage-2 geral](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md);
  atualizar **S2-NT na seção 3** e adicionar retorno na **seção 7**, com contagens,
  SHA/evidências, aceites locais/externos e dependências liberadas para o piloto.
- [x] Preservar outros retornos e informar efeito sobre M1/etapas 2/4/5; manter o
  coordenador parcial enquanto houver ações abertas ou gates não executados.
- [ ] Sincronizar as decisões de Bill, incluindo a retirada de A-003/A-006, e a
  exclusão de publicação do escopo no retorno S2-NT do plano coordenador.
