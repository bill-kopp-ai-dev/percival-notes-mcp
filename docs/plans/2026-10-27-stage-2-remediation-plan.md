# Stage-2 — Remediação do Percival Notes MCP

**Data / revisão:** 2026-10-30 / 1.5.
**ID / estado:** S2-NT / implementação local majoritariamente presente; requalificação com 2 falhas de teste abertas; 10 ações ativas.
**Checkout executor:** `/home/bill/Projects/percival-notes-mcp`.  
**Owner e signatário único:** Bill Kopp (`bill.kopp.dev@gmail.com`), responsável único pelo Notes MCP e pela infraestrutura IaC da Positronic Bean Labs (`https://labs.positronicbean.com`); único colaborador destes projetos.

## 1. Objetivo, fontes e fronteira

Tratar os 16 achados da **seção 6** do
[relatório Notes](../../../positronic-bean-IaC/docs/reports/2026-10-27-percival-notes-mcp-iac-readiness-report.md#6-achados-issues-e-inconsistências),
com seções 7/9 como complemento. O relatório de origem tinha 12 ações (2 P1,
6 P2, 4 P3), sem P0; esta revisão mantém 10 ações ativas.
Snapshot do relatório de origem: `83980418b3239be5476f6d347ceb8dad32d90e8e`.
Checkout confrontado nesta revisão: `06059988367419c144535898bf0ac6ddfc173eb3`.
O estado preexistente `D docs/search-benchmark.md` foi preservado; o arquivo não
foi restaurado nem editado nesta revisão. A nota F3 local continua sendo evidência
histórica específica do candidato identificado nela, não evidência de um candidato
atual.

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

- [x] Ler instruções/README/contrato de vault; baseline histórica do checkout `40fd2af2902ed2f94d528b84052428ec808b0b1e`. O estado local preexistente de `docs/search-benchmark.md` foi preservado; `docs/issues/2026-10-10-f3-status.md` permanece como registro histórico do candidato, conforme detalhado acima.
- [x] Criar somente fixtures sintéticas para falhas, restore, permissões e symlinks; restore validado com UID/GID `65532:65532`, manifesto SHA-256, leitura MCP, busca e escrita; negativo de owner incorreto explícito.
- [x] Owner (Bill, 2026-10-28) definiu retenção de backups fora do vault, 7 diários + 4 semanais; init único pelo launcher; aceitação da limitação de reprodutibilidade após medição; logs com path somente em DEBUG; contrato `{notes, omitted}`; autorização histórica para commit/push em `origin/main` do produto. O destino F3 registrado anteriormente foi substituído por `R-05`: canônico em `pblabs-mcp-index`, sem espelho local de conteúdo. Sem VEX se o scan não encontrar CVEs, conforme o gate de `R-07`.
- [x] Atualização de decisão do operador, 2026-10-29: `R-10` supersede `R-02` quanto ao default do broker Percival, que permanece amplo conforme B14/B22/B23–B25. Notes mantém configuração explícita do bind de vault necessário; perfil e dados existentes não devem ser ampliados nem mutados implicitamente. `R-03` remove dimensionamento de esforço, custo e prazo; `R-05` centraliza F3 por imagem em `pblabs-mcp-index`; `R-06` adota schema externo de `server.json`, extensão operacional versionada `pblabs.app.yaml` e destino `pblabs-mcp-index`, sem dependência do Docker MCP Catalog; `R-07` exige VEX por CVE ligado ao image ID e assinado pelo owner, com CVEs da imagem base tratados por herança; `R-08` fixa pin aprovado e janela única datada para operações que dependem dela.
- [x] `R-11` (2026-10-29): Trivy é o scanner padrão e está instalado; o agente
  pode executá-lo autonomamente para scans locais quando necessário, cobrindo
  todas as severidades, atualizando a DB e registrando versão/data da DB, SHA e
  image ID. A evidência local
  existente é histórica; novos candidatos exigem novo scan. Scan não aprova
  publicação ou VEX, que segue `R-07`.
- [x] Cruzamento de código desta revisão (2026-10-30): os handlers, scripts,
  contratos Docker e testes foram inspecionados no checkout acima. A suíte
  canônica foi executada; seus resultados e as duas falhas estão registrados nas
  seções 5 e 6. Não foram alterados código, imagens, runtime gerenciado ou vault.

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

### 2.2. Governança enxuta — decisão do owner, 2026-10-30

Bill reafirmou: “Eu, Bill Kopp, sou o único "owner" dessa aplicação e também
o "owner" da infraestrutura IaC, também sou o único a trabalhar nesses projetos.
Logo, sou o único a decidir e assinar.” Também determinou: “Estamos perdendo
muito tempo com validações cruzadas, provas desnecessárias e multiplos aceites
para a mesma coisa. Como eu sou o único dono e a única pessoa a trabalhar nessas
aplicações isso não faz sentido.”

Efeito vinculante para este plano:

- Não há gates de aprovação entre colaboradores nem aceite repetido por outra
  pessoa. Uma decisão do owner é registrada uma vez e vale para os artefatos
  abrangidos.
- Cada ação recebe um aceite técnico consolidado com as evidências existentes
  mais adequadas. Repetir uma verificação somente para cobrir risco diferente,
  mudança de artefato ou ambiente-alvo.
- Não criar relatórios brutos, checklists paralelos, provas de reprodutibilidade
  ou gates novos sem necessidade técnica concreta ou exigência explícita do owner.
- Continuam obrigatórios os controles diretamente ligados a riscos distintos:
  suíte e smoke local, integridade/owner do restore em fixture sintética e scan
  de cada imagem candidata quando A-007 for executada.
- Esta simplificação não autoriza ações em produção, publicação de imagem, nem
  uso do vault real em ensaios.

## 3. Backlog ativo e aceite

Por decisão do owner registrada na seção 2.1, duas ações de origem foram retiradas;
a tabela contém as 10 ações ativas. Os IDs originais das ações mantidas foram
preservados. O estado histórico e a contagem vigente estão na seção 6.

| Ação | Achados / P | Trabalho e áreas previstas | Dependência / execução | Aceite verificável | Estado confrontado com o checkout |
|---|---|---|---|---|
| A-001 | F-001 / P1 | Tornar busca resiliente a symlink externo nos caminhos ripgrep e fallback em `notes_mcp.py` | Sem dependência externa | Arquivo fora do vault ignorado com aviso sanitizado; notas válidas encontradas; nenhum conteúdo/path externo exposto; testar ambos os caminhos | Implementado; `tests/test_stage2_remediation.py` chama os caminhos rg e walker e verifica aviso sanitizado; suíte atual passou nesses casos. |
| A-002 | F-002 / P1 | Publicar backup/restore preservando owner numérico/permissões e exigindo leitura após restore | Decisão do owner sobre cópias/retenção | Restore em fixture com manifesto SHA-256 igual, UID/GID compatíveis (baseline UID 65532, confirmar candidato), leitura/busca/escrita funcionais; negativo de owner errado explícito | Scripts e testes existem. Requalificação atual parcial: o verificador rejeitou owners incorretos, mas duas asserções da suíte falharam; ver seção 6. |
| A-004 | F-004 / P2 | Declarar init único requerido ou embutir init com decisão compatível; registrar contrato de implantação | S2-C01 aprovado por Bill; launchers | `docker stop` em menos de 1 s na fixture; sem init duplo; ausência de init recusada/documentada conforme decisão | Contrato implementado em Dockerfile/Compose/README; testes estáticos e de lifecycle passaram na suíte atual. Medições detalhadas disponíveis são históricas (2026-10-28), não repetidas nesta revisão. |
| A-005 | F-005 / P2 | Normalizar build ou declarar/medir limitação de reprodutibilidade com decisão do owner | Limitação aceita por Bill e diferenças já medidas | Aceite satisfeito: diferenças registradas e limitação aceita; promoção/publicação não é gate desta etapa | Aceite do owner e comparação histórica registrados; não foi reconstruído um par de imagens nesta revisão. |
| A-007 | F-007 / P2 | Rescan local do candidato com Trivy (`R-11`) e registrar o resultado; produzir VEX conforme `R-07` se houver CVEs | Agente pode executar scan local autonomamente; candidato identificado | Scan com versão/data da DB, SHA/image ID identificados e resultado registrado; sem VEX se o scan estiver limpo. Gates de tracker, distribuição e publicação não pertencem a esta etapa | Pendente nesta revisão: o resultado F3 refere-se ao image ID histórico de 2026-10-28; não foi identificado nem escaneado candidato atual. |
| A-008 | F-008, F-015 / P2 | Expor leituras parciais em stats/read_multiple com motivo de omitidos, sem vazamento de path externo | Compatibilidade do contrato de resposta com consumidores | Fixture com arquivo ilegível distinguida de vault vazio; notas lidas preservadas, omitidos/motivos explícitos; envelope e controle de path mantidos | Implementado; teste de stats/read_multiple passou na suíte atual, inclusive motivos e envelope. |
| A-009 | F-009 / P3 | Validar glob antes da enumeração e sanitizar aviso | Sem dependência externa | `../../*` e padrão absoluto recusados antes de varrer; sem resultado espúrio `.` nem caminhos externos nos logs | Implementado antes de `root_dir.glob`; testes de padrões relativos inválidos e logs sanitizados passaram. |
| A-010 | F-010, F-011 / P3 | Remover raiz interna do status e retirar paths de notas de INFO | Política de privacidade do produto | Status sem path absoluto; logs operacionais sem nome/caminho sensível; DEBUG privado apenas se explicitamente configurado | Implementado; testes de status, logs INFO sem paths e DEBUG opt-in passaram. |
| A-011 | F-012, F-013 / P3 | Tolerar quebra final/CRLF no frontmatter e derivar versão do pacote no serverInfo | Contrato OKF preservado | Frontmatter válido aceito e persistido corretamente; initialize informa versão do produto (0.1.5 só se vigente), não do SDK | Implementado e testado; `pyproject.toml` declara 0.1.5 e initialize usa a versão do produto. |
| A-012 | F-014, F-016 / P3 | Corrigir README do ripgrep/restore e remover apt/setuid residuais não usados | A-002; compatibilidade da imagem | Docs conferem com versão embarcada; inventário limpo sem eliminar dependência necessária; smoke/protocolo/busca permanecem verdes | README, scripts e receita Docker refletem `rg` 15.2.0, restore e remoção de apt/dpkg/setuid; suíte atual passou fora das duas falhas de A-002. Inventário citado pela nota F3 segue específico à imagem histórica. |

## 4. Sequência e dependências

1. **NT-1:** A-001 implementada e verificada. A-002 tem scripts e evidência
   histórica, mas a requalificação atual ainda não satisfaz todos os testes;
   manter aberta até corrigir as duas asserções e repetir os testes em fixture.
   Nenhum ensaio usa runtime gerenciado ou vault real.
2. **NT-2:** A-008/A-009/A-010/A-011 implementadas e cobertas por testes;
   A-004 tem contrato aprovado e testes atuais verdes; A-012 está refletida no
   README e nos scripts. Revisar a documentação após fechar A-002.
3. **NT-3:** A-005 aceita com a limitação medida; A-007 aguarda candidato atual
   e novo scan local. Bill implementa S2-C04 e comprova o reuso do harness nos
   dois MCPs previstos.

Riscos distintos: skip silencioso pode ocultar falha, nova resposta parcial pode
quebrar cliente e restore com UID errado pode parecer perda de tags. Cobrir cada
risco com a verificação direcionada já prevista; não duplicar evidências nem
fazer chown/cópia no vault real.
`R-03` remove a exigência de estimar esforço, custo ou prazo.

## 5. Qualificação futura no projeto

- [!] Reexecutado `uv run pytest -q` em 2026-10-30 no checkout
  `06059988367419c144535898bf0ac6ddfc173eb3`: 66 passed, 2 failed em 50,11 s.
  Ambas as falhas são de `tests/test_vault_backup_restore.py` e estão detalhadas
  na seção 6; portanto a qualificação integral não está verde. Não introduzir
  lint/cobertura como requisito novo sem decisão do produto.
- [x] Build identificado e smoke MCP stdio, init único, stdout JSON-RPC-only;
  write/read/search em fixture OKF com ripgrep e fallback aplicáveis (evidência
  histórica de 2026-10-28; não repetida nesta revisão).
- [x] A suíte atual exercitou contenção/glob/symlinks, frontmatter,
  stats/leituras parciais, logs e lifecycle; casos correspondentes passaram.
- [!] Backup/restore foi exercitado em fixture sintética, mas 2 asserções
  falharam. A verificação de owner incorreto detectou mismatch; porém, o arquivo
  da fixture tem permissão de leitura para outros usuários, então a leitura por
  UID 65532 não prova que o restore com owner incorreto ficou inacessível. O
  teste de retenção esperava literalmente `20261028T`, embora a execução de
  2026-10-30 tenha criado `20261030T`. Corrigir a qualificação e repetir, sem
  ampliar o escopo para vault real.
- [ ] Após corrigir as duas asserções abertas de A-002, executar uma única
  qualificação local consolidada: `uv run pytest -q`; se a mudança afetar a
  imagem, construir uma vez e executar um smoke MCP stdio em fixture sintética
  para startup, configuração, bind, protocolo e funções (`V-BUILD` a `V-FUNC`).
  Registrar um resumo único do resultado, sem aceite separado por dimensão.
- [ ] Para S2-C04, verificar uma vez o reuso do harness nos dois MCPs previstos
  junto da qualificação consolidada (`V-REUSE`); não abrir aceite, relatório ou
  checklist separado para cada `V-*`.

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
  bloqueia a continuação local. Não reconstruir evidências por suposição nem
  exigir anexação de saídas brutas para repetir resultados já resumidos.

| Data / owner | Ações / achados | SHA inicial → final | Mudanças / evidências locais | Resultado / V-* / pendências |
|---|---|---|---|---|
| 2026-10-28 (estado histórico, não vigente) / Bill Kopp | A-001, A-002, A-004, A-005, parcela local de A-007 e A-008–A-012 verificadas localmente (**10/12**); A-003 parcial (candidato pronto; solicitação de repin/hardening a encaminhar aos gestores); A-006 pendente de encaminhamento/investigação no broker; para A-007, referência ao tracker central e scan CI continuam externos; S2-NT-X01 segue com materialização/validação de schema e manifests pendentes, mas formato e destino decididos por `R-06` | Inicial `40fd2af2902ed2f94d528b84052428ec808b0b1e`; baseline do candidato `fbf1a2911e522f184c1945924c95796533062fb6` | `uv run pytest -q`: 68 passed; smoke MCP stdio (12 tools, resource, prompts, read/write/search, containment, persistence) e `docker-ci-conformance.py` aprovados. Dois builds `--no-cache`: image IDs `sha256:c7944fbd28a5f0b0a6fda557a2597c636facb136fe9a58451875c4ac19aa8674` e `sha256:618845639f43f1297a400231df4fa551149b2e5584b166cea4fecd8474041eec`; rootfs 7.363 membros, 6 diferenças de conteúdo/hash (cache ldconfig, logs apt/dpkg, `RECORD`, `uv_cache.json`) e 2.308 mtimes divergentes; não reprodutibilidade aceita por Bill. Trivy 0.76.1, DB atualizada em 2026-10-28: 0 CVEs em 105 pacotes Debian e dependências Python; resultado local resumido na [nota F3](../issues/2026-10-10-f3-status.md), sem VEX quando scan limpo. Lifecycle: com `--init` 99 ms/exit 143; sem init, cerca de 1,8 s/exit 0 no candidato; E-022 original não reproduzido. Restore em fixture verificou SHA, modos, UID/GID, leitura/busca/escrita MCP e negativo owner 0:0. | Estado então: pendentes repin/hardening, investigação do broker, tracker/scan CI e materialização S2-NT-X01; sem piloto/publicação liberado. O registro seguinte contém o estado vigente. |
| 2026-10-29 / Bill Kopp (owner único) | S2-C01/S2-C02 aprovados; S2-C04 aceito, implementação atribuída a Bill; publicação/registry/manifests/índice e gates de distribuição fora do escopo. A-005 aceita com diferenças medidas. A-003/A-006 retiradas do escopo ativo por decisão do owner. | Sem alteração do candidato. | A-003/A-006 não são executadas nem avaliadas neste plano. Artefatos brutos históricos não anexados/referenciados. | Prosseguir com as 10 ações restantes, S2-C04 e `V-*` locais. Este plano não declara runtime/piloto qualificado nem causa do `exit 255`. |
| 2026-10-30 / Bill Kopp (owner e signatário únicos) | Decisão de governança enxuta registrada na seção 2.2. | Sem alteração do candidato. | Uma qualificação consolidada substitui aceites/checklists redundantes; os riscos distintos de restore e scan continuam cobertos. | Aplicar este modelo às ações restantes, sem ampliar autorização de produção/publicação nem usar vault real em ensaios. |

**Contagem vigente:** 10 ações permanecem ativas; a contagem não significa que
10/10 estejam aceitas. A-001, A-004 e A-008–A-012 têm implementação local
confirmada no código e testes relevantes verdes nesta execução; A-005 tem aceite
decisório histórico. A-002 requer corrigir/repetir dois testes, A-007 requer scan
de candidato atual e S2-C04/`V-REUSE` continua pendente. A-003 e A-006 foram
retiradas e não entram no denominador. O registro histórico de 2026-10-28 acima
e a contagem **9 verificadas, 2 parciais e 1 aberta** do relatório daquela data
são históricos.

### 6.1. Trilha e limites das evidências

| Verificação | Registro disponível | Limite atual |
|---|---|---|
| Suíte (`uv run pytest -q`, 68 aprovados) | Resultado resumido no retorno acima | Saída bruta e identificação detalhada do ambiente não estão anexadas/referenciadas |
| Smoke MCP stdio e `docker-ci-conformance.py` | Escopo e resultado resumidos no retorno acima | Logs, argumentos completos e arquivos de resultado do candidato não estão anexados/referenciados |
| Trivy 0.76.1 / candidato `sha256:c7944fbd…` | [Nota F3 local](../issues/2026-10-10-f3-status.md) registra ID, data/base do DB e contagem | Nota-resumo; JSON bruto e SBOM do candidato não foram localizados nos artefatos versionados consultados |
| Builds `--no-cache` e comparação de rootfs | IDs e diferenças resumidos no retorno acima | Manifestos/saída da comparação não foram localizados nos artefatos versionados consultados |
| Restore e lifecycle em fixture | Resultado resumido no retorno acima | Manifestos SHA-256 e logs/JSON das execuções do candidato não foram anexados/referenciados |
| Diagnóstico inicial (snapshot `83980418…`) | [Índice das evidências originais](../../../positronic-bean-IaC/docs/reports/evidence/percival-notes-mcp/83980418b323/README.md) | Evidência do snapshot inicial, não substitui artefatos do candidato `fbf1a291…` |
| Suíte e cruzamento de código (2026-10-30; checkout `0605998…`) | Execução local de `uv run pytest -q`: 66 passed, 2 failed; inspeção dos handlers em `notes_mcp.py`, scripts de backup/restore, Dockerfile, Compose e testes A-001/A-004/A-008–A-012 | `test_restore_without_owner_preservation_is_rejected` rejeitou corretamente owners incorretos, mas `PROBE_EXIT=1` falhou: o arquivo de fixture permite leitura por outros usuários, então UID 65532 ainda pode lê-lo mesmo com owner errado. A asserção não comprova inacessibilidade. `test_backup_keeps_the_documented_retention` falhou por data fixa `20261028T`; a execução criou snapshot `20261030T`. Nenhum arquivo de código foi alterado nesta revisão. |

## 7. Última etapa — atualizar o plano coordenador

- [x] Reler o [stage-2 geral](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md);
  atualizar **S2-NT na seção 3** e adicionar retorno na **seção 7**, com contagens,
  SHA/evidências, aceites locais/externos e dependências liberadas para o piloto.
- [x] Preservar outros retornos e informar efeito sobre M1/etapas 2/4/5; manter o
  coordenador parcial enquanto houver ações abertas ou gates não executados.
- [ ] Sincronizar as decisões de Bill, incluindo a retirada de A-003/A-006, e a
  exclusão de publicação do escopo no retorno S2-NT do plano coordenador.
