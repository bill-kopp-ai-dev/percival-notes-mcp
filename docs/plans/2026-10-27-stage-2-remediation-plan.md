# Stage-2 — Remediação do Percival Notes MCP

**Data / revisão:** 2026-11-08 / 1.8.
**ID / estado:** S2-NT / 10/10 ações locais mantidas concluídas/aceitas; smoke funcional pontual no agente Percival passou com a imagem `c1f367…`; o candidato vigente `c1f367…` foi reescaneado em 2026-11-08 com base de vulnerabilidades de 2026-11-07 (0 findings); o build da árvore atual (`b0b25cf`) falha no host e não produziu candidato novo; qualificação ampla de V-PILOT/runtime e publicação não declaradas.
**Checkout executor:** `/home/bill/Projects/percival-notes-mcp`.  
**Owner e signatário único:** Bill Kopp (`bill.kopp.dev@gmail.com`), responsável único pelo Notes MCP e pela infraestrutura IaC da Positronic Bean Labs (`https://labs.positronicbean.com`); único colaborador destes projetos.

## 1. Objetivo, fontes e fronteira

Tratar os 16 achados da **seção 6** do
[relatório Notes](../../../positronic-bean-IaC/docs/reports/2026-10-27-percival-notes-mcp-iac-readiness-report.md#6-achados-issues-e-inconsistências),
com seções 7/9 como complemento. O relatório de origem tinha 12 ações (2 P1,
6 P2, 4 P3), sem P0; duas ações foram retiradas por decisão do owner e as 10
ações mantidas foram concluídas no escopo local aprovado.
Snapshot do relatório de origem: `83980418b3239be5476f6d347ceb8dad32d90e8e`.
Checkout de código qualificado: `5d761f747e4492dcca61c33a1a5880822b666233`.
O checkout `06059988367419c144535898bf0ac6ddfc173eb3` é a base da revisão
documental anterior e do resultado inicial de testes registrado na seção 6.
O estado preexistente `D docs/search-benchmark.md` foi preservado; o arquivo não
foi restaurado nem editado nesta revisão. A nota F3 local continua sendo evidência
histórica específica do candidato identificado nela, não evidência de um candidato
atual.

[Coordenador stage-2](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md)
— retorno S2-NT, seções 3 e 7. Referências:
[consolidação](../../../positronic-bean-IaC/docs/reports/2026-10-26-stage-1-consolidated-readiness-report.md)
e [D-01..D-06](../../../positronic-bean-IaC/docs/decisions/2026-10-27-iac-stage-1-scope-and-pilot-decisions.md).

O escopo original cobre emissão documental e execução técnica local no checkout
dono. Após seu encerramento, Bill solicitou um smoke funcional pontual do Notes
no agente Percival, registrado nas seções 2.4, 5.1 e 6.1. Esse resultado não
homologa runtime amplo, não autoriza mexer em vault real nem amplia o escopo para
publicação. Preservar contrato das tools, OKF, busca ripgrep/fallback, containment
e envelopes de conteúdo não confiável.

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
- [x] Cruzamento de código desta revisão (2026-10-31): os handlers, scripts,
  contratos Docker e testes foram inspecionados no checkout acima. A suíte
  canônica foi executada; a requalificação histórica e a rechecagem desta revisão
  estão registradas nas seções 5 e 6. Não foram alterados código, imagens, runtime
  gerenciado ou vault.

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

### 2.3. Decisões do owner — Bill Kopp, 2026-10-31

| Item | Decisão | Efeito no plano |
|---|---|---|
| Retorno ao coordenador IaC | Atualizar somente a linha S2-NT da seção 3 e o retorno S2-NT da seção 7 do coordenador; preservar os demais retornos e registrar contagem/status, SHAs e limites da evidência local. Não reabrir aprovações já concedidas. | Sincronização documental concluída neste retorno; outras seções do coordenador não foram alteradas. |
| Encerramento local S2-NT | Encerrar as ações locais com escopo explícito: candidato e scan valem somente para o image ID registrado; runtime gerenciado, piloto e publicação não foram qualificados. Registrar 64 passed/4 skipped como rechecagem do código, não da imagem. | 10/10 ações mantidas encerradas ou aceitas localmente. A-003/A-006 permanecem retiradas. V-PILOT não bloqueia o encerramento local. |
| V-PILOT futuro | Antes de eventual execução, confirmar pin e versão do manager, identificar fixture isolada e verificar que não existe bind para vault real; executar prompts pelo loop do agente e registrar resultado sem tratar smoke MCPProvider como substituto. | Orientação para eventual trabalho futuro; sem execução nem pendência de aceite nesta etapa. |
| Distribuição e revisão de licenças | Distribuição via Docker Hub será implementada somente no futuro; remover revisão de licenças como item/pendência deste plano. | Nenhuma distribuição ou revisão de licenças integra o escopo ou bloqueia o encerramento local. |

### 2.4. Decisão e teste pontual no agente Percival — 2026-10-31

Após o encerramento local S2-NT, Bill solicitou preparar e testar a imagem Notes
no agente Percival. O owner aplicou a pinagem pela interface do manager; as
capturas compartilhadas mostram a transição do pin `sha256:ef4082ef…` para
`sha256:c1f36791…` e o estado final `running`/`MCP connected`, com 12 tools
observadas. A execução usou uma nota sintética única e a removeu ao final.

Este é um smoke pós-encerramento, restrito ao image ID, à configuração observada
e às operações relatadas. Não reabre as 10 ações locais nem autoriza publicação,
produção, uso de vault real ou qualificação ampla de V-PILOT. Esta decisão
posterior atualiza o estado somente quanto ao smoke pontual; a linha 2.3 registra
corretamente que ainda não havia execução quando o encerramento local foi decidido.

## 3. Ações mantidas no escopo e aceite

Por decisão do owner registrada na seção 2.1, duas ações de origem foram retiradas;
a tabela contém as 10 ações mantidas no escopo. Os IDs originais foram preservados.
As ações locais foram encerradas com os limites de evidência e exclusões descritos
neste plano; o registro histórico e a contagem final estão na seção 6.

| Ação | Achados / P | Trabalho e áreas previstas | Dependência / execução | Aceite verificável | Estado confrontado com o checkout |
|---|---|---|---|---|
| A-001 | F-001 / P1 | Tornar busca resiliente a symlink externo nos caminhos ripgrep e fallback em `notes_mcp.py` | Sem dependência externa | Arquivo fora do vault ignorado com aviso sanitizado; notas válidas encontradas; nenhum conteúdo/path externo exposto; testar ambos os caminhos | Implementado; `tests/test_stage2_remediation.py` chama os caminhos rg e walker e verifica aviso sanitizado; suíte atual passou nesses casos. |
| A-002 | F-002 / P1 | Publicar backup/restore preservando owner numérico/permissões e exigindo leitura após restore | Decisão do owner sobre cópias/retenção | Restore em fixture com manifesto SHA-256 igual, UID/GID compatíveis (baseline UID 65532, confirmar candidato), leitura/busca/escrita funcionais; negativo de owner errado explícito | Scripts e testes existem; as duas asserções foram corrigidas nos testes e a requalificação de 2026-10-30 registrou 68 passed. Rechecagem 2026-10-31: 64 passed, 4 skipped por dependência de Docker/imagem; ver seção 6. |
| A-004 | F-004 / P2 | Declarar init único requerido ou embutir init com decisão compatível; registrar contrato de implantação | S2-C01 aprovado por Bill; launchers | `docker stop` em menos de 1 s na fixture; sem init duplo; ausência de init recusada/documentada conforme decisão | Contrato implementado em Dockerfile/Compose/README; testes estáticos e de lifecycle passaram na suíte atual. Medições detalhadas disponíveis são históricas (2026-10-28), não repetidas nesta revisão. |
| A-005 | F-005 / P2 | Normalizar build ou declarar/medir limitação de reprodutibilidade com decisão do owner | Limitação aceita por Bill e diferenças já medidas | Aceite satisfeito: diferenças registradas e limitação aceita; promoção/publicação não é gate desta etapa | Aceite do owner e comparação histórica registrados; não foi reconstruído um par de imagens nesta revisão. |
| A-007 | F-007 / P2 | Rescan local do candidato com Trivy (`R-11`) e registrar o resultado; produzir VEX conforme `R-07` se houver CVEs | Agente pode executar scan local autonomamente; candidato identificado | Scan com versão/data da DB, SHA/image ID identificados e resultado registrado; sem VEX se o scan estiver limpo. Gates de tracker, distribuição e publicação não pertencem a esta etapa | Scan local registrado para o candidato exato `1572c6b…` (seção 5); 0 CVEs, sem VEX requerido por `R-07`. Re-scan do candidato vigente `c1f367…` em 2026-11-08 com base de 2026-11-07: 0 findings, sem VEX; evidência em `../issues/2026-11-08-notes-c1f36791-scan.md`. Evidência vinculada somente a esses image IDs, sem promoção/publicação. |
| A-008 | F-008, F-015 / P2 | Expor leituras parciais em stats/read_multiple com motivo de omitidos, sem vazamento de path externo | Compatibilidade do contrato de resposta com consumidores | Fixture com arquivo ilegível distinguida de vault vazio; notas lidas preservadas, omitidos/motivos explícitos; envelope e controle de path mantidos | Implementado; teste de stats/read_multiple passou na suíte atual, inclusive motivos e envelope. |
| A-009 | F-009 / P3 | Validar glob antes da enumeração e sanitizar aviso | Sem dependência externa | `../../*` e padrão absoluto recusados antes de varrer; sem resultado espúrio `.` nem caminhos externos nos logs | Implementado antes de `root_dir.glob`; testes de padrões relativos inválidos e logs sanitizados passaram. |
| A-010 | F-010, F-011 / P3 | Remover raiz interna do status e retirar paths de notas de INFO | Política de privacidade do produto | Status sem path absoluto; logs operacionais sem nome/caminho sensível; DEBUG privado apenas se explicitamente configurado | Implementado; testes de status, logs INFO sem paths e DEBUG opt-in passaram. |
| A-011 | F-012, F-013 / P3 | Tolerar quebra final/CRLF no frontmatter e derivar versão do pacote no serverInfo | Contrato OKF preservado | Frontmatter válido aceito e persistido corretamente; initialize informa versão do produto (0.1.5 só se vigente), não do SDK | Implementado e testado; `pyproject.toml` declara 0.1.5 e initialize usa a versão do produto. |
| A-012 | F-014, F-016 / P3 | Corrigir README do ripgrep/restore e remover apt/setuid residuais não usados | A-002; compatibilidade da imagem | Docs conferem com versão embarcada; inventário limpo sem eliminar dependência necessária; smoke/protocolo/busca permanecem verdes | Parcial até 2026-11-08: o README ainda declarava `rg 13.0.0` enquanto a imagem instala 15.2.0, e a remoção de apt/dpkg/setuid não tinha teste que a garantisse. Corrigido em `c3867b1` (README 15.2.0 + declaração de não-reprodutibilidade do build) e `b0b25cf` (testes estáticos de guarda README↔Dockerfile, remoção de apt/dpkg e preservation do `/var/lib/dpkg/status`, bits setuid limpos). Inventário citado pela nota F3 segue específico à imagem histórica. |

## 4. Sequência e dependências

1. **NT-1 concluída:** A-001 verificada; A-002 encerrada com a requalificação
   em fixture de 2026-10-30 (68 passed). Os casos Docker foram ignorados na
   rechecagem de código de 2026-10-31, que não substitui nem invalida aquela
   evidência. Nenhum ensaio usa runtime gerenciado ou vault real.
2. **NT-2 concluída:** A-008/A-009/A-010/A-011 implementadas e cobertas por testes;
   A-004 tem contrato aprovado e verificações locais registradas; A-012 está
   refletida no README e nos scripts; documentação revisada junto ao encerramento
   local de A-002.
3. **NT-3 concluída no escopo local:** A-005 aceita com a limitação medida; A-007 foi escaneada para o
   candidato local identificado na seção 5, e o resultado não vale para outra
   imagem. S2-C04 e `V-REUSE` foram demonstrados em Notes e Weather. V-PILOT,
   que requer execução no loop de agente, está fora do escopo desta etapa
   conforme a seção 1 e não bloqueia as ações locais.

Riscos distintos: skip silencioso pode ocultar falha, nova resposta parcial pode
quebrar cliente e restore com UID errado pode parecer perda de tags. Cobrir cada
risco com a verificação direcionada já prevista; não duplicar evidências nem
fazer chown/cópia no vault real.
`R-03` remove a exigência de estimar esforço, custo ou prazo.

## 5. Qualificação local registrada no projeto

- [x] Reexecutada a suíte após corrigir as duas asserções de A-002: permissão
  `0600` no arquivo sintético torna o teste de owner incorreto discriminante; a
  retenção agora valida timestamp UTC gerado na execução, não uma data fixa.
  Na requalificação de 2026-10-30, `.venv/bin/python -m pytest -q` teve **68 passed**.
  Rechecagem do código no SHA `5d761f7` em 2026-10-31 com
  `.venv/bin/python -m pytest -q`:
  **64 passed, 4 skipped** (casos dependentes de Docker/imagem local ignorados
  neste ambiente); este resultado não requalifica a imagem nem runtime.
- [x] Construído o candidato local exato `percival-notes-mcp:stage2-vpilot-5d761f7`
  do SHA `5d761f747e4492dcca61c33a1a5880822b666233`, versão `0.1.5`,
  `linux/amd64`, UID/GID `65532:65532`, image ID local
  `sha256:1572c6b291afe67e3f77ac10840cd8d51227389ffc830e8122afd44e85ed6e0d`.
  O candidato não foi publicado.
- [x] Qualificação da imagem exata: `tests/smoke_stdio.py --docker-image
  percival-notes-mcp:stage2-vpilot-5d761f7` passou em fixture sintética; 12 tools,
  resource e prompts, read/write/search, negativas de path e persistência após
  recriação. `scripts/docker-ci-conformance.py` também passou `initialize` e
  `tools/list`; `docker compose config --quiet` passou.
- [x] Trivy 0.76.1, DB `UpdatedAt=2026-10-30T13:06:28Z`: 0 vulnerabilidades,
  0 misconfigurações e 0 secrets no candidato exato. JSON canônico:
  `docs/issues/2026-10-30-notes-5d761f7-1572c6b-scan.json`. A evidência vale
  somente para esse candidato e não qualifica distribuição.
- [x] Re-scan do candidato vigente (2026-11-08): Trivy 0.76.1 pelo host, DB
  `UpdatedAt=2026-11-07T18:32:58Z` (8 dias mais nova), **0 findings**, `gate`
  vazio, `scanSha256` `2a526503…`, `sbomSha256` `c684b60f…`, sobre o image ID
  `sha256:c1f36791…` (tag de inventário `percival-notes-mcp:0.1.5-5d761f7`,
  revisão `5d761f7`). Recibo e pendências em
  `docs/issues/2026-11-08-notes-c1f36791-scan.md`. Decisão de VEX inalterada:
  sem CVEs a declarar. O relatório bruto e o SBOM ficaram no host: o hash
  está registrado, e a evidência por imagem foi criada em
  `pblabs-mcp-index/servers/notes/security-scan-5d761f7-c1f36791.json` com a
  seção aplicável no tracker F3 canônico, conforme `R-05`. O relatório bruto
  permanece no host (mesma lacuna de evidência registrada para a imagem Weather
  0.10.0) e precisa ser arquivado se a imagem for publicada.
- [ ] **Bloqueado:** build da árvore atual (`b0b25cf`) falha no host. Dois
  jobs (`1c7c4614…`, `1e94c5a9…`) terminaram `phase-failed` na fase `build`
  (exit 1, ~9 s), com o mesmo `contextSha256` `fa0041c7…`; o recibo não expõe
  log de build. O mesmo host executou scan e SBOM sem falha, então a causa é
  da fase de build e precisa ser vista no host. Sem candidato novo para
  `b0b25cf`, o scan vigente cobre a revisão `5d761f7`, não a árvore atual.
  Diagnóstico de 2026-11-08: o executor descarta o stderr da fase de build e
  resolve a receita (inclusive `network` e `rejectSeverities`) no carregamento
  da policy, então a receita `canonical` deste projeto — registrada em
  2026-11-07 e nunca usada para um build — precisa de correção no host e de
  um restart do executor. Detalhes e experimento preparado em
  `docs/issues/2026-11-08-notes-c1f36791-scan.md`.
- [x] V-REUSE: harness comum `pblabs-mcp-stdio/v1`, fonte em
  `../../../positronic-bean-IaC/scripts/mcp_stdio_conformance.py`, SHA-256
  `299b1595e9281ad23b2a9e4547612154a1cf52e43bdf3776a3631b21a07319be`, passou
  nos candidatos Notes e Weather (identidades/versões/tools conferidas). O
  Weather comparado foi `sha256:821ea0f6761f7cd3d98f5737afc4753060a5eeb87e335aeaf2be23c50d007a58`,
  revision `ed2caa8c`; o código/Dockerfile do produto não diferem até o checkout
  atual, embora a imagem permaneça local e não publicada.
- [x] Preparação de integração V-PILOT: Bill autorizou o smoke DinD isolado com
  o par Percival/Notes exato; o harness gerente/MCPProvider passou. A evidência
  valida a ponte local, não a interação em linguagem natural.
- [x] Disposição V-PILOT no encerramento local: ainda não qualificado e fora do
  escopo. A tentativa E25 foi inconclusiva: o manager observou outro pin/versão
  e o vault sintético não foi confirmado; nenhuma escrita ocorreu. O smoke
  pontual posterior, solicitado por Bill e executado no agente Percival em
  2026-10-31, está registrado na seção 5.1; não equivale à qualificação ampla
  nem autoriza runtime persistente/publicação.

Esta qualificação cobre o produto e fixtures locais. Não conclui nem declara estado
de runtime gerenciado amplo ou causa de eventos operacionais. O smoke pontual no
agente Percival após o encerramento está delimitado na seção 5.1; publicação e
distribuição da imagem continuam fora do escopo.

### 5.1. Smoke funcional pontual no agente Percival — 2026-10-31

- **Pin observado nas capturas do manager:** estado inicial
  `sha256:ef4082ef13905cdaa0da23830bcc6c5b88ca3beb30074e11d56593d11a097460`;
  estado final `sha256:c1f36791f649c50c74c7f90e02708d1f415b114500bcfcfc5bb0626a2a6ac050`.
  O MCP não expõe a identidade da imagem; essa identidade vem da captura do
  manager, não de `notes_get_status`.
- **Estado final mostrado:** Docker `running`, MCP `connected`, gateway intent
  `running`, enabled, 12 tools observadas. `notes_get_status` retornou servidor
  operational, versão `0.1.5`, root reportado como `vault` (sem path absoluto).
- **Sequência relatada por Bill como executada pelo agente:** pré-checagem do
  caminho único com `notes_glob`; `notes_write`; `notes_read` confirmou marcador
  e envelope; `notes_search(in_markdown=true)` encontrou somente o caminho
  sintético; `notes_rm`; pós-checagem `notes_glob` e `notes_search` vazias.
- **Fixture sintética:** `_percival_smoke_20261031T210815_7f3a9c.md`, marcador
  `PERCIVAL_NOTES_SMOKE_20261031T210815_7f3a9c`. O relatório do agente não aponta
  falhas e confirma que apenas essa nota foi escrita/removida; nenhum conteúdo de
  outras notas foi lido, listado ou exportado.
- **Veredito limitado:** smoke de integração pelo agente passou para o pin
  mostrado. A versão do servidor, isoladamente, não comprova image ID; o pin é
  sustentado pela captura do manager. Evidência de execução é o relatório
  compartilhado por Bill, não há trace bruto anexado. O resultado não declara
  qualificação ampla de runtime/piloto, persistência operacional, uso de vault
  real ou publicação.

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

**Contagem final do escopo local:** 10/10 ações mantidas concluídas ou aceitas:
A-001, A-002, A-004, A-007–A-012 verificadas localmente; A-005 aceita pelo owner.
O scan A-007 cobre somente o candidato exato `1572c6b…`, sem CVEs; V-REUSE/S2-C04
foi demonstrado em Notes e Weather. A-003 e A-006 foram retiradas por Bill e não
entram no denominador. Na data desse encerramento, V-PILOT amplo, runtime gerenciado
e publicação não foram qualificados; o smoke pontual posterior está registrado
na seção 5.1 e não altera a contagem local. A distribuição via Docker Hub e
qualquer revisão associada ficam para trabalho futuro, fora deste plano.

### 6.1. Trilha e limites das evidências

| Verificação | Registro disponível | Limite atual |
|---|---|---|
| Suíte (`uv run pytest -q`, 68 aprovados) | Resultado resumido no retorno acima | Saída bruta e identificação detalhada do ambiente não estão anexadas/referenciadas |
| Smoke MCP stdio e `docker-ci-conformance.py` | Escopo e resultado resumidos no retorno acima | Logs, argumentos completos e arquivos de resultado do candidato não estão anexados/referenciados |
| Trivy 0.76.1 / candidato `sha256:c7944fbd…` | [Nota F3 local](../issues/2026-10-10-f3-status.md) registra ID, data/base do DB e contagem | Nota-resumo; JSON bruto e SBOM do candidato não foram localizados nos artefatos versionados consultados |
| Builds `--no-cache` e comparação de rootfs | IDs e diferenças resumidos no retorno acima | Manifestos/saída da comparação não foram localizados nos artefatos versionados consultados |
| Restore e lifecycle em fixture | Resultado resumido no retorno acima | Manifestos SHA-256 e logs/JSON das execuções do candidato não foram anexados/referenciados |
| Diagnóstico inicial (snapshot `83980418…`) | [Índice das evidências originais](../../../positronic-bean-IaC/docs/reports/evidence/percival-notes-mcp/83980418b323/README.md) | Evidência do snapshot inicial, não substitui artefatos do candidato `fbf1a291…` |
| Suíte inicial (2026-10-30; checkout `0605998…`) | `66 passed, 2 failed`; investigação em `tests/test_vault_backup_restore.py` | Resultado histórico substituído pela requalificação abaixo: uma permissão de fixture tornava o negativo de owner não discriminante e outra asserção fixava a data do snapshot. |
| Requalificação (2026-10-30; source `5d761f747e4492dcca61c33a1a5880822b666233`) | Correções apenas nos testes; `.venv/bin/python -m pytest -q`: **68 passed**. Build exato `percival-notes-mcp:stage2-vpilot-5d761f7`, image ID `sha256:1572c6b291afe67e3f77ac10840cd8d51227389ffc830e8122afd44e85ed6e0d`; arquitetura `linux/amd64`, UID/GID `65532:65532`; smoke `tests/smoke_stdio.py` passou com tools/resources/prompts, operações em fixture sintética e persistência. Trivy 0.76.1, DB `2026-10-30T13:06:28Z`: 0 CVEs, 0 misconfigurações, 0 secrets; scan JSON em `docs/issues/2026-10-30-notes-5d761f7-1572c6b-scan.json`. | `V-BUILD`, `V-RUN`, `V-CONFIG`, `V-DATA`, `V-MCP` e `V-FUNC` locais aprovados somente para este image ID e fixtures. Não houve deploy, uso do vault real nem publicação. V-PILOT não foi qualificado e está fora do escopo desta etapa. |
| Integração Percival+Notes em DinD (2026-10-30; autorização de Bill) | `scripts/percival-i2-runtime-smoke.py` com os image IDs exatos; Engine 27.5.1; resultado `completed=true`. | `/home/bill/.positronic/runtime/tmp/opencode/i2-u4m8rp3u/results.json`; MCP tools/resources/prompts, read/write, protected path, restart/recovery e cleanup passaram pelo manager/MCPProvider. | Fixture e vault sintéticos; nenhuma LLM prompt ou vault real. Isso é pré-prova de ponte/runtime para V-PILOT, não fecha o teste por prompts no agente. |
| Re-scan do candidato vigente (2026-11-08) | Recibo do job `02b5f0ff…`: Trivy 0.76.1, DB `2026-11-07T18:32:58Z`, 0 findings, `gate` vazio, `scanSha256` `2a526503…`, `sbomSha256` `c684b60f…`; image ID `sha256:c1f36791…` (tag `0.1.5-5d761f7`). | Evidência canônica em `pblabs-mcp-index/servers/notes/security-scan-5d761f7-c1f36791.json` + seção do tracker F3; [nota do candidato vigente](../issues/2026-11-08-notes-c1f36791-scan.md) | Relatório bruto e SBOM ficaram no host (só os hashes estão registrados), mesma lacuna da imagem Weather 0.10.0: arquivar se a imagem for publicada. Evidência vale para esse image ID e para a base datada; não qualifica distribuição. |
| Build da árvore atual (2026-11-08) | Jobs `1c7c4614…` (18:04:44Z) e `1e94c5a9…` (18:11:10Z): `phase-failed`, fase `build` exit 1, `commit` `b0b25cf…`, `contextSha256` `fa0041c7…`, `recipeSha256` `b98957d6…`. | Recibo do job de manutenção (sem log de build exposto) | Diagnóstico exige o host: o mesmo host escaneou a imagem `c1f367…` sem falha. Nenhuma imagem foi produzida para `b0b25cf`. |
| Smoke funcional no agente Percival (2026-10-31; relato e capturas compartilhados por Bill) | Pin observado na UI: `sha256:ef4082ef…` → `sha256:c1f36791…`; status final running/connected, 12 tools. O agente reportou status v0.1.5 e ciclo de nota sintética write/read/search/remove, seguido de glob/search vazios. | Caminho `_percival_smoke_20261031T210815_7f3a9c.md`; marcador `PERCIVAL_NOTES_SMOKE_20261031T210815_7f3a9c`; relatório e capturas fornecidos por Bill nesta conversa. | Evidência reportada pelo owner; MCP não identifica a imagem e não há trace bruto anexado. Smoke funcional de um caminho passou; não representa qualificação ampla de runtime/piloto. Nota sintética removida; nenhuma outra nota acessada. |

### 6.2. Reconciliação dos gates V-* do candidato local

| Gate | Estado neste candidato | Evidência e limite |
|---|---|---|
| `V-BUILD` | **aprovado localmente para `5d761f7`; falho para `b0b25cf` (2026-11-08)** | SHA/image ID, versão, plataforma, UID/GID e labels conferidos no build exato; não é `RepoDigest` publicado. Em 2026-11-08 o build da árvore atual (`b0b25cf`) falhou no host na fase `build` (exit 1, ~9 s, dois jobs, sem log no recibo), então não há build válido para a revisão corrente. |
| `V-RUN` | **aprovado localmente** | Inicialização stdio, EOF/exit 0 e recriação exercitados em container sintético; não avalia runtime gerenciado. |
| `V-CONFIG` | **aprovado localmente** | Requalificação de 2026-10-30: suíte 68/68 e smoke com rede desativada, user não-root, vault sintético e negativas previstas. Rechecagem 2026-10-31: 64 passed, 4 skipped por dependência de Docker/imagem, sem requalificar o candidato. |
| `V-DATA` | **aprovado em fixture** | Backup/restore confere owner numérico, SHA/conteúdo e retenção; write/read permanece após recriação do container. Nenhum vault real foi lido ou alterado. |
| `V-MCP` | **aprovado localmente** | `initialize`, `notifications/initialized`, `tools/list` (12 tools), resource read, prompts list/get; stdout somente JSON-RPC. |
| `V-FUNC` | **aprovado em fixture** | `notes_write`, `notes_read`, `notes_search` e negativos de path/symlink exercitados na imagem exata; sem dados externos. |
| `V-PILOT` | **smoke funcional pontual passou; qualificação ampla não declarada** | Após E25, Bill pinou `sha256:c1f367…` no Percival; capturas mostram `running`/`connected` e 12 tools. O agente executou status e ciclo write/read/search/remove de nota sintética, com pós-checagem vazia (seção 5.1). Image ID vem da captura, não da resposta MCP; o relato é do owner, sem trace bruto anexado. Isso cobre um caminho funcional no agente, não qualifica runtime amplo, vault real, publicação ou promoção. |
| `V-REUSE` | **demonstrado localmente** | Harness comum versionado `pblabs-mcp-stdio/v1` (SHA-256 acima) passou em Notes e Weather; limita-se às probes MCP comuns, sem substituir testes funcionais específicos de cada produto. |

### 6.3. Harmonização com IaC — 2026-10-31

- A convenção de ownership `R-12` do coordenador IaC consolida Bill como owner
  e decisor final, sem duplicar aprovações; gates técnicos e autorização para
  runtime/publicação permanecem distintos.
- `R-10` não amplia o perfil Notes: o bind explícito do vault continua estreito
  e os dados existentes não são alterados implicitamente. O default amplo é
  exclusivo do broker Percival.
- O C02/D-05 comprovado é específico ao Percival e ao smoke DinD Percival+Notes.
  A prova via manager/MCPProvider e o smoke funcional pontual do agente (seção
  5.1) são evidências distintas. O novo teste exercitou um caminho sintético de
  status/write/read/search/remove; não resolve todos os limites de E25 nem
  autoriza runtime persistente ou publicação.
- O harness comum `pblabs-mcp-stdio/v1` foi demonstrado em Notes e Weather para
  identidade/versão, `initialize`, `tools/list`, stdout de protocolo, UID
  opcional e encerramento. Isso não substitui a suíte Notes, os testes
  funcionais, transporte HTTP ou `V-PILOT`.
- A ação A-011 do plano IaC, sobre provenance, refere-se ao bootstrap Percival
  e aos doubles/fixtures locais; bundle/release/atestação pública seguem
  pendentes. O scan/VEX Notes
  descrito aqui pertence somente ao image ID registrado; assinatura VEX por
  CVE e promoção são gates próprios, sem promoção implícita deste candidato.

## 7. Última etapa — atualizar o plano coordenador

- [x] Reler o [stage-2 geral](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md);
  atualizar **S2-NT na seção 3** e adicionar retorno na **seção 7**, com contagens,
  SHA/evidências, aceites locais/externos e dependências liberadas para o piloto.
- [x] Preservar outros retornos e informar efeito sobre M1/etapas 2/4/5; manter o
  coordenador parcial enquanto houver ações abertas ou gates não executados.
- [x] Sincronizar as decisões de Bill, incluindo a retirada de A-003/A-006, o
  encerramento das ações locais e a exclusão de publicação do escopo, no retorno
  S2-NT do plano coordenador.
