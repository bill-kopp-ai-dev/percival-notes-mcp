# Stage-2 — Remediação do Percival Notes MCP

**Data / revisão:** 2026-10-27 / 1.0.  
**ID / estado:** S2-NT / planejado; execução não iniciada.  
**Checkout executor:** `/home/bill/Projects/percival-notes-mcp`.  
**Responsável:** executor Notes a designar por bill; operação do vault/gestores com seus donos.

## 1. Objetivo, fontes e fronteira

Tratar os 16 achados da **seção 6** do
[relatório Notes](../../../positronic-bean-IaC/docs/reports/2026-10-27-percival-notes-mcp-iac-readiness-report.md#6-achados-issues-e-inconsistências),
com seções 7/9 como complemento: 12 ações (2 P1, 6 P2, 4 P3), sem P0.
Snapshot/HEAD na emissão: `83980418b3239be5476f6d347ceb8dad32d90e8e`.
Exclusões locais preexistentes da nota F3 e `docs/search-benchmark.md` preservadas.

[Coordenador stage-2](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md)
— retorno S2-NT, seções 3 e 7. Referências:
[consolidação](../../../positronic-bean-IaC/docs/reports/2026-10-26-stage-1-consolidated-readiness-report.md)
e [D-01..D-06](../../../positronic-bean-IaC/docs/decisions/2026-10-27-iac-stage-1-scope-and-pilot-decisions.md).

Emissão documental; execução técnica futura somente no checkout dono. Notes é o
servidor do par piloto Percival + Notes (D-01). A seleção não homologa a imagem em
uso nem autoriza mexer no vault do operador. Preservar contrato das tools, OKF,
busca ripgrep/fallback, containment e envelopes de conteúdo não confiável.

## 2. Preparação e decisões

- [x] Ler instruções/README/contrato de vault; baseline do checkout `40fd2af2902ed2f94d528b84052428ec808b0b1e`; preservadas as exclusões preexistentes de `docs/search-benchmark.md` e, até a decisão explícita abaixo, da nota F3.
- [x] Criar somente fixtures sintéticas para falhas, restore, permissões e symlinks; restore validado com UID/GID `65532:65532`, manifesto SHA-256, leitura MCP, busca e escrita; negativo de owner incorreto explícito.
- [x] Owner (Bill, 2026-10-28) definiu retenção de backups fora do vault, 7 diários + 4 semanais; init único pelo launcher; aceitação da limitação de reprodutibilidade após medição; logs com path somente em DEBUG; contrato `{notes, omitted}`; autorização histórica para commit/push em `origin/main` do produto. O destino F3 registrado anteriormente foi substituído por `R-05`: canônico em `pblabs-mcp-index`, sem espelho local de conteúdo. Sem VEX se o scan não encontrar CVEs, conforme o gate de `R-07`.
- [x] Decisões do operador de 2026-10-28 aplicáveis: `R-02` fixa `mounts=[]` como default do broker, exige mounts explícitos e trata `null` como operação separada, confirmada e auditada; `R-03` remove dimensionamento de esforço, custo e prazo; `R-05` centraliza F3 por imagem em `pblabs-mcp-index`; `R-06` adota schema externo de `server.json`, extensão operacional versionada `pblabs.app.yaml` e destino `pblabs-mcp-index`, sem dependência do Docker MCP Catalog; `R-07` exige VEX por CVE ligado ao image ID e assinado pelo owner, com CVEs da imagem base tratados por herança; `R-08` fixa pin aprovado e janela única datada para operações que dependem dela.

## 3. Backlog integral e aceite

O backlog e os aceites abaixo preservam o escopo emitido. O retorno parcial e o estado por ação estão na seção 6; parcelas de runtime/CI permanecem externas.

| Ação | Achados / P | Trabalho e áreas previstas | Dependência / dono externo | Aceite verificável |
|---|---|---|---|---|
| A-001 | F-001 / P1 | Tornar busca resiliente a symlink externo nos caminhos ripgrep e fallback em `notes_mcp.py` | Sem dependência externa | Arquivo fora do vault ignorado com aviso sanitizado; notas válidas encontradas; nenhum conteúdo/path externo exposto; testar ambos os caminhos |
| A-002 | F-002 / P1 | Publicar backup/restore preservando owner numérico/permissões e exigindo leitura após restore | Decisão do owner sobre cópias/retenção | Restore em fixture com manifesto SHA-256 igual, UID/GID compatíveis (baseline UID 65532, confirmar candidato), leitura/busca/escrita funcionais; negativo de owner errado explícito |
| A-003 | F-003 / P2 | Produzir candidato rastreável, solicitar repin e hardening do runtime ao dono | S2-AP-X01 e S2-NB A-007; etapa 2 IaC; `R-08` | Image ID/revision com pin aprovado, cap-drop ALL/NNP/RO conforme perfil; vault correto identificado; operação real somente em janela única datada e autorizada, com owner e rollback |
| A-004 | F-004 / P2 | Declarar init único requerido ou embutir init com decisão compatível; registrar contrato de implantação | S2-C01 e donos dos launchers | `docker stop` em menos de 1 s no perfil piloto/fixture homologada; sem init duplo; ausência de init recusada/documentada conforme decisão |
| A-005 | F-005 / P2 | Normalizar build ou declarar/medir limitação de reprodutibilidade com decisão do owner | Entradas/builder identificados; etapa 2 IaC | Dois builds sem cache com image ID igual, ou limitação aceita e diferenças medidas conforme aceite original; pin sempre do artefato efetivamente validado |
| A-006 | F-006 / P2 | Solicitar investigação da saída 255 e reconciliação saved/observed no broker | S2-NB A-007/A-012; acesso de owner ao log | Causa discriminada/registrada; inventário e observação atual coerentes; sob-demanda parado não implica falha; não editar state manualmente |
| A-007 | F-007 / P2 | Rescan do candidato e referência ao tracker F3 canônico; produzir VEX conforme `R-07` quando houver CVEs | Owner; CI/etapa 2 IaC | Scan com DB/data/image ID atual; tracker central por imagem em `pblabs-mcp-index`; VEX por CVE detectado, ligado ao image ID e assinado pelo owner; CVEs herdados da imagem base tratados por herança; nenhum VEX inventado se scan limpo |
| A-008 | F-008, F-015 / P2 | Expor leituras parciais em stats/read_multiple com motivo de omitidos, sem vazamento de path externo | Compatibilidade do contrato de resposta com consumidores | Fixture com arquivo ilegível distinguida de vault vazio; notas lidas preservadas, omitidos/motivos explícitos; envelope e controle de path mantidos |
| A-009 | F-009 / P3 | Validar glob antes da enumeração e sanitizar aviso | Sem dependência externa | `../../*` e padrão absoluto recusados antes de varrer; sem resultado espúrio `.` nem caminhos externos nos logs |
| A-010 | F-010, F-011 / P3 | Remover raiz interna do status e retirar paths de notas de INFO | Política de privacidade do produto | Status sem path absoluto; logs operacionais sem nome/caminho sensível; DEBUG privado apenas se explicitamente configurado |
| A-011 | F-012, F-013 / P3 | Tolerar quebra final/CRLF no frontmatter e derivar versão do pacote no serverInfo | Contrato OKF preservado | Frontmatter válido aceito e persistido corretamente; initialize informa versão do produto (0.1.5 só se vigente), não do SDK |
| A-012 | F-014, F-016 / P3 | Corrigir README do ripgrep/restore e remover apt/setuid residuais não usados | A-002; compatibilidade da imagem | Docs conferem com versão embarcada; inventário limpo sem eliminar dependência necessária; smoke/protocolo/busca permanecem verdes |

### 3.1. Complemento de distribuição não detalhado nas A-* originais

| ID | Origem | Entrega / aceite |
|---|---|---|
| S2-NT-X01 | DIST-02 e seção 8 do relatório; X-04/C-09 | Preparar `server.json` conforme schema externo adotado e `pblabs.app.yaml` operacional versionado (`R-06`); manifests destinados a `pblabs-mcp-index`; produto/versão/transporte/permissões/imagem coerentes; referência OCI real apenas após publicação nas etapas 2/4 |

Esse complemento não aumenta as 12 ações de origem. Registro de image ID local
não é digest de manifesto de registry; não preencher metadados com imagem pública
ou digest fictícios. Não há rede/provedor necessário para o teste funcional local.

## 4. Sequência e dependências

1. **NT-1:** A-001/A-002; A-003 prepara candidato e solicitação de owner em
   paralelo. A-001/A-002 são condições antes de piloto com vault real; os ensaios
   deste plano usam sempre fixture sintética.
2. **NT-2:** A-008/A-009/A-010/A-011; A-004 com S2-C01; A-012 após o runbook
   de restore. Mudanças na forma de resposta devem ser coordenadas com clientes.
3. **NT-3:** A-005/A-007, S2-NT-X01 e recebimento de A-003/A-006 pelos gestores.
   A recomendação de harness comum S2-C04 aguarda aceite; qualificação
   remota/publicação são separadas. `R-08` define pin/janela como política, mas
   data/autorização concreta deve ser registrada antes de operação real.

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
- [ ] Revalidar `V-BUILD`, `V-RUN`, `V-CONFIG`, `V-DATA`, `V-MCP`, `V-FUNC` e
  `V-REUSE` afetados; `V-PILOT` só muda com prova do plano próprio, não com mock. Build/smoke locais não qualificam o runtime nem o piloto.
- [ ] Receber evidência dos gestores, CI/scan e limites externos; não afirmar que
  imagem histórica ativa está qualificada pelos testes do candidato.

Aceite de produto local pode ser entregue com retorno parcial. Ação de runtime
ou publicação pendente não se encerra por documentação da solicitação.

## 6. Penúltima etapa — documentar execução neste plano

- [x] Registrar ações/subtarefa, owner/data, SHA inicial/final, mudanças, comandos,
  ambiente, evidências sanitizadas locais e vereditos `V-*` pós-correção.
- [x] Registrar decisões de retenção/owner e pendências; complementar seção 9 do
  relatório IaC quando autorizado, preservando baseline e sem conteúdo do vault real.

| Data / owner | Ações / achados | SHA inicial → final | Mudanças / evidências locais | Resultado / V-* / pendências |
|---|---|---|---|---|
| 2026-10-28 / bill (owner), Positronic (execução local) | A-001, A-002, A-004, A-005, A-007–A-012 verificadas localmente (**10/12**); A-003 parcial (candidato pronto; solicitação de repin/hardening a encaminhar aos gestores); A-006 pendente de encaminhamento/investigação no broker; S2-NT-X01 segue com materialização/validação de schema e manifests pendentes, mas formato e destino decididos por `R-06` | Inicial `40fd2af2902ed2f94d528b84052428ec808b0b1e`; baseline do candidato `fbf1a2911e522f184c1945924c95796533062fb6` | `uv run pytest -q`: 68 passed; smoke MCP stdio (12 tools, resource, prompts, read/write/search, containment, persistence) e `docker-ci-conformance.py` aprovados. Dois builds `--no-cache`: image IDs `sha256:c7944fbd28a5f0b0a6fda557a2597c636facb136fe9a58451875c4ac19aa8674` e `sha256:618845639f43f1297a400231df4fa551149b2e5584b166cea4fecd8474041eec`; rootfs 7.363 membros, 6 diferenças de conteúdo/hash (cache ldconfig, logs apt/dpkg, `RECORD`, `uv_cache.json`) e 2.308 mtimes divergentes; não reprodutibilidade aceita pelo owner. Trivy 0.76.1, DB atualizada em 2026-10-28: 0 CVEs em 105 pacotes Debian e dependências Python; nota F3 local preservada/excluída, tracker canônico definido em `pblabs-mcp-index`, sem VEX quando scan limpo. Lifecycle: com `--init` 99 ms/exit 143; sem init, cerca de 1,8 s/exit 0 no candidato; E-022 original não reproduzido. Restore em fixture verificou SHA, modos, UID/GID, leitura/busca/escrita MCP e negativo owner 0:0. | Local: A-001/A-002 liberam somente fixture sintética; A-004 e A-012 aceitos localmente; A-005 limitação aceita. Externos pendentes: repin/hardening em janela aprovada (`R-08`), vault correto/rollback; encaminhamento/investigação do broker A-006; scan CI/retenção e assinatura de VEX se CVEs forem detectados; materialização/schema/index S2-C03 e harness comum S2-C04; nenhum piloto/publicação liberado. `V-*`: evidência parcial local, V-PILOT não avaliado. |

## 7. Última etapa — atualizar o plano coordenador

- [x] Reler o [stage-2 geral](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md);
  atualizar **S2-NT na seção 3** e adicionar retorno na **seção 7**, com contagens,
  SHA/evidências, aceites locais/externos e dependências liberadas para o piloto.
- [x] Preservar outros retornos e informar efeito sobre M1/etapas 2/4/5. Sem
  acesso à IaC, entregar resumo e manter **aguardando sincronização**. Concluído
  exige aceites e retorno efetivo; registrar parcial se existir ação transferida/aberta.
