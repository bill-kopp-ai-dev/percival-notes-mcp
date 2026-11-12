# Notes MCP — ciclo de imagem da remediação da bateria funcional (2026-11-09)

> **Onde este repositório guarda o histórico:** `docs/issues/` traz apenas as
> issues **em aberto**; as encerradas ficam em `docs/issues/closed/`. O mesmo
> vale para `docs/plans/` e `docs/plans/closed/`. Esta nota documenta o ciclo
> de imagem da remediação NFB.
>
> **Estado: encerrado (2026-11-12).** O pin vigente do servidor `notes` é a
> revisão **26** (image ID `sha256:0cfdc0fd…`), construída a partir do commit
> `f26970d`. A seção final desta nota registra a revalidação de 2026-11-12; a
> auditoria de 2026-11-12 também apurou que o smoke stdio completo
> **nunca** tinha sido executado contra uma imagem pinada — e que a fixture
> que ele usava estava quebrada para o caminho Docker. O defeito foi
> corrigido e o smoke agora passa contra o pin vigente. A retenção de imagens
> foi executada no mesmo dia, e o plano associado foi encerrado com **7/7**
> critérios de conclusão. Detalhes em **Revalidação com executor corrigido e
> promoção do pin global — 2026-11-12** e **Retenção executada — 2026-11-12**.

- **Data:** 2026-11-09 (UTC); **auditado e requalificado em 2026-11-12.**
- **Objetivo:** qualificar o candidato que corrige os 12 achados de
  [docs/issues/closed/2026-11-09-notes-functional-battery-findings.md](2026-11-09-notes-functional-battery-findings.md),
  conforme
  [docs/plans/closed/2026-11-09-notes-functional-battery-remediation-plan.md](../../plans/closed/2026-11-09-notes-functional-battery-remediation-plan.md).
- **Servidor:** `server id notes` (registry `$POSITRONIC_HOME/mcp/registry.json`),
  escopo global, transporte stdio.
- **Decisões do owner aplicadas:** D-01 = somente `0600` (sem modo de herança);
  D-02 = recusar substituição de arquivo regular sem bit de escrita.

## Artefato

Candidato final: **D**. A imagem final do ciclo foi construída a partir da
árvore **commitada** (`7c1a87e`), logo após a publicação da remediação.

| Campo | Valor |
|---|---|
| Image ID (manifesto) | `sha256:0c8fdf7500c2ec989adbfcf512cded3575032f6cd9540e62570e99b782e614d6` |
| `configDigest` | `sha256:5d9198d4cd37ad189a10c02035fae9ed90ee44b6658cf930adcea44d7bba4896` |
| `manifestMediaType` | `application/vnd.oci.image.manifest.v1+json` |
| `imageName` | `docker.io/positronic-build/e3c0ebddd73c4cdd0650740249dcca7429cf40d7bfa225cc56be1fd5d7b8b7a0:4cc172bd73cfdcfb0d9c1fb861dd92829aefef4c1cee05920c037ac5db6d75f4` |
| `imageResolution` | `verified` |
| Job de build (requestId) | `9611052434b01420acf374086a571ffc056ef26ea7f5e9d7ce2bcdcaec366b99` |
| Fonte | commit `7c1a87e4f98541317850d54a77563b645d40959c` (árvore commitada) |
| `contextSha256` | `189209371dfca572e536a3a341efaa6523cc52bf483f9e29da5074336067744c` |
| `recipeSha256` | `32bd91e8c9a521d96eb586b491ed0e8238c9567dbba0956c9f552a0f0d8eb5c5` (receita `canonical`, rede `default`) |
| Versão do produto | `0.1.5` (inalterada nesta remediação) |
| `dirty` reportado pelo host | `true` — ver **Diagnóstico do flag `dirty`** abaixo |

O candidato D é **byte-idêntico** ao candidato C: mesmo `imageId`, mesmo
`configDigest`. O `Dockerfile` copia apenas `pyproject.toml`, `uv.lock`,
`README.md`, `notes_mcp.py`, `LICENSE` e o entrypoint; os documentos
adicionados após o build de C não entram na imagem. O que muda entre C e D é
a **proveniência**: o job de D registra o commit `7c1a87e` como fonte, e o
`contextSha256` reflete o contexto já com a documentação final versionada.

Candidato intermediário superado: `sha256:1157f51f2677f5153f85be500e183591764393db4988f8ac58d7570775289d57`
(job `eeb27185dff552da13fad43d0a5f288b9a0ed92d2343af46617e4cf967aa686c`,
`contextSha256` `7cf5497ad3d81deca59a694149cbce99d5e0cc164654b4d44a971f3c4bb5be18`).

## Diagnóstico do flag `dirty`

O host reporta `dirty: true` para o candidato D, embora a árvore esteja
commitada e limpa. A causa foi reproduzida localmente e **não é** alteração
não commitada.

O executor calcula (em `positronic-mcp-executor`):

```js
job.dirty = changed.size > 0 || tree.size !== manifest.length;
```

- `tree` = `git ls-tree -r HEAD` no repositório (53 entradas).
- `manifest` = arquivos copiados do working tree, com a lista vinda de
  `git ls-files --cached --others --exclude-standard`, **menos** os caminhos
  rejeitados pela política de contexto — entre eles `AGENTS.md`, `.positronic`,
  `.venv`, `secrets`, `credentials`, `*.pem|key|p12|pfx` (52 entradas).
- `changed` = arquivos cujo blob ou modo difere do commit.

Reprodução local do cálculo na árvore `7c1a87e`:

```text
tree.size       = 53
manifest.length = 52
changed         = []            # nenhum blob ou modo difere do commit
skipped         = ['AGENTS.md']
tree entries not in manifest: ['AGENTS.md']
```

Ou seja: `changed` é vazio — **nenhum arquivo rastreado difere do commit** — e
a desigualdade `tree.size !== manifest.length` decorre exclusivamente do
`AGENTS.md`, que o executor exclui do contexto de build por política (é um
arquivo de instruções de agente e não deve entrar na imagem) mas que continua
sendo uma entrada da árvore do Git.

Consequência: **em qualquer repositório que versione um `AGENTS.md` na raiz, o
flag `dirty` do executor é structuralmente `true`**, mesmo com a árvore
perfeitamente limpa. O sinal não distingue "árvore suja" de "política de
contexto aplicada". Para este repositório, a afirmação verificável é a
oposta do rótulo: o contexto de build é idêntico à árvore do commit `7c1a87e`,
exceto pelo `AGENTS.md` deliberadamente excluído.

Correção sugerida ao executor (fora do escopo deste repositório): comparar a
árvore do commit apenas com o subconjunto do manifesto, em vez de comparar
contagens de conjuntos de domínios diferentes.

## Scan e SBOM

- **Scanner:** Trivy `0.76.1` (`scannerSha256` `4ab0e6d9c77528fd876a6dda49c506cd5b5317be0396a5a7d34ff5a6f7e8ad54`).
- **Base de vulnerabilidades:** `updatedAt 2026-11-09T00:56:17Z`, `downloadedAt 2026-11-09T02:29:13Z`.
- **Resultado:** **0 findings** em todas as severidades, nos candidatos C, D e
  também no B superado.
- **Gate:** `[HIGH, CRITICAL]`, **bloqueante** (diferente do `report-only` citado
  no histórico de `AGENTS.md`; a política vigente do host é a que vale).
- **Hashes de evidência (candidato D):** `scanSha256` `d9429125ccd7ccc262d23e6045f3ffe6259a94bf44d20106445121d61a5c787f`;
  `sbomSha256` `97e5e3da9deb35b82e6eacce3fdd6985d9baf287af9aaec633336146384e4e7a`;
  `scannerSha256` `4ab0e6d9…`.
- **Fases do job:** `engine`, `build`, `scanner-version`, `scan`, `sbom` — todas com
  `exitCode: 0`; `state: succeeded`.

O relatório bruto do Trivy e o SBOM ficaram no host; o executor expõe apenas os
hashes. Mesma lacuna já registrada em `2026-11-09-notes-offline-6c1640ce-scan.md`.

## Autorização e pin

Ciclo do candidato D (build a partir da árvore commitada):

1. `image_build(project="percival-notes-mcp", recipe="canonical")` → job
   `9611052434b01420acf374086a571ffc056ef26ea7f5e9d7ce2bcdcaec366b99`,
   `state: succeeded`, todas as fases com `exitCode: 0`, `findings: 0`.
2. `image_authorize` aceito para `sha256:0c8fdf75…` (`serverId notes`).
3. `positronic mcp server update-image notes sha256:0c8fdf75… 24` → revisão do
   servidor **25**, `configurationId` `eb88e213-fe47-4f62-a02b-ad773145752d`.
4. Configuração reaplicada com `positronic mcp server configure`: rede `none`,
   mount do vault de fixture F3 em `/vault` (`rw`) e allowlist das **12 tools**.
   O `update-image` invalida a `configurationId` anterior e **redefine a revisão
   de configuração para 0**; por isso o `configure` seguinte usa a revisão 0.
5. `positronic mcp server discover notes` devolveu as **12 tools** esperadas.
6. `positronic mcp server activate notes 25` → servidor ativo no candidato.

Ciclo anterior (candidato C), para histórico: `update-image … 23` → revisão 24,
`configurationId` `9bcf1480-cade-4999-a047-1632a40e9a6a`, mesma allowlist de 12
tools e `activate notes 24`.

**Estado A preservado para rollback:** imagem `sha256:6c1640ce8d0c823186858dcc04b7e793a997cf301ae4680f1c00d0b30cf3a7dd`
(revisão 22), ainda autorizada e fixável com um comando.

## Qualificação funcional no MCP pinado

Executado pela sessão connected ao pin final (candidato D, revisão 25), com a
fixture F3 montada em `/vault`. Todas as notas usadas foram sintéticas e
removidas ao final.

| Achado | Prova na imagem `0c8fdf75…` (candidato D) | Resultado |
|---|---|---|
| F-01 | `notes_search("alpha")` com `locked.md` em modo `000` e `bin.md` não-UTF-8 no vault → devolve `["_nfb_probe/good.md"]`; `notes_search("secret")` → `[]` sem abortar | corrigido |
| F-02 | `notes_glob(".")` → `Glob pattern must name a path component inside the vault` | corrigido |
| F-03 | `notes_glob("**")` → sem `"."`; devolve `["_nfb_probe", "_nfb_probe/realdir", "data"]` | corrigido |
| F-04 | nota nova nasce `0600` (owner `65532:65532` no host); decisão D-01 aplicada | aceito por decisão |
| F-05 | `notes_rm("_nfb_probe/alias.md")` removeu o link; `good.md` manteve o conteúdo | corrigido |
| F-06 | `notes_rmdir("_nfb_probe/dirlink")` → recusa; link e diretório-alvo intactos; `notes_rmdir` do diretório real vazio removeu-o | corrigido |
| F-07 | `notes_read_multiple` → `bin.md` e `locked.md` com `reason: unreadable`, ausente com `not_found`; `notes_read` → erro explícito de UTF-8 | corrigido |
| F-08 | `tags: [T1, shared]` + `keywords: [K1, SHARED]` → `["k1","shared","t1"]`; stats com 1 nota por tag | corrigido |
| F-09 | `notes_get_backlinks("../a.md")` → recusa; `/etc/passwd` → recusa; alvo válido → `["_nfb_probe/source.md"]` | corrigido |
| F-10 | `notes_get_stats` = 6 notas para 8 entradas com alias/link → contagem canônica; `unreadable_files: 2` | corrigido |
| F-11 | `notes_write` em `0444` → recusa; conteúdo, modo `444` e owner preservados; zero temporários `.notes-*` | corrigido |
| F-12 | `notes_glob("**/*.md")` → 6 entradas; link quebrado, alias e link externo omitidos | corrigido |

**Containção de path intacta na imagem:** `notes_read` e `notes_rm` de symlink
externo (`/etc/passwd`) → `Path escapes root directory`; o alvo externo não foi
lido nem removido (`/etc/passwd` intacto no host).

**Integridade da fixture:** ao final, `notes_get_stats` devolveu 0 notas, 0 tags
e 0 ilegíveis; `notes_glob("**")` devolveu apenas `["data"]`. A árvore do vault
F3 foi restaurada ao estado original (`.probe`, `data/`, `khal.conf`), sem
resíduo de notas sintéticas.

## Limites desta qualificação

- **O harness `scripts/docker-ci-conformance.py` não foi executado:** ele exige
  o binário `docker` no executor, e este agente não tem Docker CLI nem socket
  (`docker: command not found`, `/var/run/docker.sock` ausente). A API de
  build/scan do host não executa esse harness. A conformidade do contrato
  stdio foi verificada pelo handshake `initialize` → `tools/list` → leitura
  segura feito pelo próprio manager no `discover`, e o comportamento funcional
  foi exercitado pelo MCP real sobre o pin.
  **Superado em 2026-11-12:** o host passou a ter binário `docker` e socket
  (`/var/run/docker.sock`, Engine 29.9.2); o harness foi executado contra o
  image ID exato e passou, e reconfirmado na auditoria.
- **O flag `dirty` do host permanece `true` mesmo com a árvore commitada.**
  A causa foi reproduzida e está documentada em **Diagnóstico do flag `dirty`**:
  o executor exclui `AGENTS.md` do manifesto de contexto e compara a
  contagem com a árvore do Git, o que torna `dirty` estruturalmente `true`
  neste repositório. O contexto de build é idêntico à árvore do commit
  `7c1a87e`, e `changed` é vazio. O sinal não deve ser lido como "árvore
  suja".
  **Superado em 2026-11-12:** a correção do executor foi publicada e o build
  seguinte reporta `dirty: false`.
- **Não houve promoção para produção nem publicação.** O pin permanece no
  candidato para avaliação do owner; o registry do Percival, o broker e
  containers de produção não foram tocados.
- Os **7 skips** da suíte local (dependentes de daemon Docker e da imagem
  local) não foram reexecutados aqui; a suíte local está verde com 111 passed,
  7 skipped.
  **Correção (auditoria de 2026-11-12):** essa contagem não corresponde ao
  estado real. A suíte mede **114 passed, 4 skipped**. A diferença é de
  ambiente, não de código: com o binário `docker` presente no `PATH`, três dos
  quatro testes de `tests/test_vault_backup_restore.py` passam em vez de
  ser ignorados, e sobra apenas o caso que exige a imagem local
  `percival-notes-mcp:stage2-wip`.
- A semântica de D-01 (somente `0600`) **mantém** a limitação de F-04: o
  operador host precisa de root ou de uma ACL explícita no vault para ler as
  notas criadas pelo servidor. Isso foi aceito explicitamente pelo owner.

## Próximo passo

Nenhum passo de código pendente neste ciclo: a remediação foi commitada
(`7c1a87e`) e publicada em `refs/heads/main`, e o candidato D foi construído a
partir dessa árvore commitada, pinado e requalificado.

As pendências abaixo estavam em aberto quando esta seção foi escrita; o
registro de **2026-11-12** no fim deste documento as encerrou. Elas são
mantidas aqui como histórico, com o estado final anotado:

- **Promoção para produção:** ~~o pin atual é a referência do servidor `notes`
  (revisão 25)~~ → **encerrado em 2026-11-12**: o pin avançou para a revisão
  **26** com a imagem `sha256:0cfdc0fd…`, `configurationId`
  `67d6ee4e-c055-4d1c-95f6-720f8a3f7437`. Não houve, nem há, promoção no
  registry do Percival, no broker ou em containers de produção.
- **Harness de conformidade:** ~~continua não executado, por ausência de
  Docker CLI no executor~~ → **encerrado em 2026-11-12**: o executor tem
  Docker CLI e socket; `scripts/docker-ci-conformance.py` passou contra o image
  ID exato (`initialize` + `tools/list`, 12 tools) e foi **reconfirmado** na
  auditoria de 2026-11-12.
- **Flag `dirty` do executor:** **encerrado em 2026-11-12**: a correção do
  executor foi publicada e o build seguinte reporta `dirty: false`.

Pendências que **permanecem abertas** após a auditoria de 2026-11-12:

1. **Retenção de imagens.** A regra do `AGENTS.md` do projeto manda reter no
   máximo duas imagens por servidor (a boa anterior e a promovida/candidata).
   Hoje o Engine do host tem **cinco** imagens Notes autorizadas e presentes:
   `sha256:c1f36791…` (`0.1.5-5d761f7`), `sha256:00010850…`,
   `sha256:6c1640ce…` (offline), `sha256:0c8fdf75…` (candidato D) e
   `sha256:0cfdc0fd…` (pin vigente). As três primeiras são resíduo de ciclos
   encerrados. A lista de autorização local (`positronic mcp server
   local-images`, revisão 15) contém ainda `sha256:3118650a…` e
   `sha256:40fa10ff…`, que **não estão no Engine** — autorizações obsoletas de
   origem não registrada neste repositório. A remoção tem de ser feita por
   image ID, pela interface dona; nada de `docker image prune`.
   **Encerrado em 2026-11-12:** ver **Retenção executada — 2026-11-12**, ao
   final deste documento. A lista de autorização local está na revisão **20** e
   o Engine tem **duas** imagens Notes.
2. **Registro durável no journal.** O alvo `percival-notes-mcp` continua
   respondendo `not-found`. O bundle `global` estava **vazio** (0 entradas)
   quando a auditoria começou, o que torna **não verificável** a afirmação de
   que a nota do ciclo NFB "foi gravada no target `global`". A evidência
   durável do ciclo NFB existe apenas nos documentos deste repositório.
   *Parcialmente fechado:* o **ciclo de auditoria de 2026-11-12** tem registro
   próprio (`noteId` `20261112-111734-journalentry-agent-8e6463eb-ce9`,
   `committed: true`, `syncStatus: synced`).
   **Encerrado em 2026-11-12 por decisão do owner:** a nota acima, no bundle
   autorizado, contém o resultado do ciclo NFB e o próximo passo; o registro
   original datado de 2026-11-09 nunca existiu e não é reconstituível.
3. **Smoke stdio contra a imagem pinada** — resolvido na auditoria de
   2026-11-12; ver a seção de auditoria abaixo.

## Limpeza

O candidato intermediário B (`sha256:1157f51f…`) foi **superado** por C e
depois por D. A autorização local de B foi revogada (`revoke-local`, revisão de
autorização 13 → 14) e a imagem removida pelo owner interface
(`image_remove`): `state: completed`, `referenceRemoved: true`,
`contentRemoved: true`. O pin nunca apontou para B durante a remoção.

O candidato D é **byte-idêntico** ao candidato C (mesmo `imageId`), portanto
não há imagem adicional a reter: o digest pinado na revisão 25 é o mesmo
digest Pinado na revisão 24, agora com proveniência do commit `7c1a87e`.

Retenção após o ciclo: o candidato D (pinado, promovido) e a imagem A
`sha256:6c1640ce…` (rollback, ainda autorizada). Nenhuma limpeza genérica
(`docker image prune`, `docker rmi -f`) foi executada.

**Correção (auditoria de 2026-11-12):** a retenção descrita acima já não
corresponde ao Engine. Além do pin vigente (`sha256:0cfdc0fd…`) e do retorno
`0c8fdf75…`, o host ainda tem **presentes e autorizadas** `sha256:00010850…`,
`sha256:6c1640ce…` e `sha256:c1f36791…` — resíduo de ciclos encerrados, que a
regra de retenção de duas imagens do `AGENTS.md` não permite. A lista de
autorização local (revisão 15) tem ainda `sha256:3118650a…` e
`sha256:40fa10ff…`, que **não existem no Engine**: autorizações obsoletas, sem
origem registrada neste repositório. A limpeza tem de ser feita por image ID
pela interface dona (`positronic mcp server revoke-local` + remoção explícita),
sem poda genérica.

## Revalidação com executor corrigido e promoção do pin global — 2026-11-12

Esta atualização supersede as pendências de promoção, conformidade e `dirty`
listadas acima. O executor host atualizado foi exercitado por um build gerenciado
novo da árvore commitada do Notes.

### Build, `dirty`, scan e SBOM

| Campo | Resultado |
|---|---|
| Job de build | `0d97905a800c5363238f87a286e50eee254569cbc42d94d1869dec8f39e1b32b` (`succeeded`) |
| Fonte | commit `f26970d6738e84fdb3a6abeb90a22ebb86b5c5e5` |
| `dirty` | `false` |
| `contextSha256` | `e6b2c5655da2dd82f7031658bf52788eeef1848b8659c28fc69cd34d9932b4e1` |
| Image ID / manifest | `sha256:0cfdc0fdd78f4c86614b80174746c936e7d470b649d7dfd8017747353059fb78` |
| `configDigest` | `sha256:3f8a09a515b6b9b81a26a2c607e96f5b21eeda92196c06acd69b0884ddb5b6b1` |
| `imageResolution` | `verified` |
| Scan inicial | Trivy 0.76.1, 0 findings; DB observado como vencido em relação à data do build, então foi repetido antes da promoção |
| Job de scan atualizado | `47ca6587647e58004e85ddd52a924c1fc3b58661f2798256b34dbe565d995640` (`succeeded`, gate `[HIGH, CRITICAL]`, 0 findings) |
| DB Trivy da repetição | `UpdatedAt=2026-11-12 01:03:48 UTC`; `NextUpdate=2026-11-13 01:03:48 UTC` |
| `scanSha256` atualizado | `eb0ba6897606eda5a0821adef0433c97f3ef086c7ecae45c2e692acbaa20176d` |
| `sbomSha256` atualizado | `95d61413d36494640fe9385198d3d77a44c5ff34d38ad5507d44efbeeeb5750b` |
| Scanner | SHA-256 `58d85fb5068b0ab9764a0d0cd8e2ad7664741054479fb1769da9b1c47c5cd0dd`, versão `0.76.1` |

O primeiro build e a repetição de scan terminaram com código 0 em todas as fases.
A correção de `dirty` publicada em `alternative-positronic` foi assim verificada
no backend instalado: `AGENTS.md` continua fora do contexto efetivo, mas já não
é comparado como uma diferença de contagem contra a árvore inteira.

### Conformance e smoke MCP no image ID exato

O `scripts/docker-ci-conformance.py` foi executado com `.venv/bin/python` contra
o image ID acima, Docker Engine `29.9.2`, Buildx `0.39.0` e Compose `5.7.1`.
Parâmetros: fixture F3 montada em `/vault`, `--expected-uid 65532` e os 12
`expected-tool` da allowlist Notes. Resultado: **`stdio MCP conformance passed:
initialize + tools/list (12 tools)`**.

No mesmo image ID, um smoke MCP direto executou `initialize`, `tools/list`,
`notes_get_status` e `notes_get_stats`. A resposta confirmou servidor
operacional, versão `0.1.5`, 12 tools, e stats com 0 notas, 0 tags e 0 arquivos
ilegíveis. O checksum da árvore fixture antes e depois dos testes foi idêntico:
`7c43a43799a80e6c418b6a8728dbcc31651c7e015c33650f8f82b18998069ae0`
(2 arquivos, 1 diretório, 0 symlinks). Nenhum conteúdo foi alterado.

A bateria funcional 12/12 permanece evidência do ciclo anterior sobre o mesmo
código Notes; este build é da revisão documental posterior `f26970d`. A nova
identidade de imagem recebeu conformance completo e smoke seguro de status/stats.

### Promoção e estado do manager

`image_authorize` aceitou o digest derivado do job; revisão de autorização local
15. O servidor global `notes` foi atualizado da revisão 25 para **26**, imagem
`sha256:0cfdc0fdd78f4c86614b80174746c936e7d470b649d7dfd8017747353059fb78`,
configuração `67d6ee4e-c055-4d1c-95f6-720f8a3f7437`, config revision 1. A
allowlist de 12 tools, rede `none` e mount F3 `/vault` (`rw`) foram preservados.
`positronic mcp server show notes` reportou `activated: true` e o image ID novo.
O candidato D anterior (`sha256:0c8fdf75…`) permanece autorizado como retorno;
nenhuma imagem foi removida.

**Ressalva de lifecycle:** um `positronic mcp server discover notes` após a troca
retornou `MCP cleanup-pending`. `positronic mcp server recover-runs` classificou
o run Notes `3751b93c-2e9d-4948-bbdc-bd50c24638d2` como `ambiguous`; o container
marcado como Positronic continua `Up`. Não foi parado nem removido, pois a
identidade disponível não prova que seu owner morreu. O conformance e o smoke
acima foram executados em containers efêmeros independentes e passaram; o
estado do pin foi confirmado pelo manager. Para uma confirmação adicional do
manager, a execução ambígua precisa ser reconciliada pelo lifecycle owner sem
forçar remoção.

## Auditoria do estado real — 2026-11-12

Confronto entre os documentos deste repositório e o estado efetivo do código,
do Engine e do registry, na árvore `1d0b69e` (publicada em `origin/main`).

### 1. Smoke stdio contra a imagem pinada: defeito de fixture corrigido

O smoke stdio completo (`tests/smoke_stdio.py --docker-image <id>`) **nunca
tinha sido executado contra uma imagem pinada**. A seção de 2026-11-12 acima
registrou apenas um smoke reduzido (`initialize`, `tools/list`,
`notes_get_status`, `notes_get_stats`) e o harness de conformance.

A execução completa contra o pin vigente falhou:

```
AssertionError: ('notes_rm', ... "Error executing tool notes_rm:
Path escapes root directory: alias.md")
```

**Causa-raiz.** `tests/smoke_stdio.py` criava o symlink da fixture com alvo
**absoluto do host**:

```python
Path(vault, "group/alias.md").symlink_to(Path(vault, "group/two.md"))
```

Dentro do container o vault está montado em `/vault`, então o alvo absoluto do
host não existe: o link fica quebrado, resolve para fora do vault e o
`notes_rm` o recusa por contenção. O mesmo requisito já estava escrito no
plano de remediação (NFB-02, passo 5: *"Usar links relativos na fixture
Docker: path absoluto do host não representa `/vault` no container"*) — a
regra foi aplicada a `tests/test_functional_battery.py` e **não** a
`tests/smoke_stdio.py`.

**Correção aplicada:** o alvo do symlink passou a ser relativo ao próprio link
(`"two.md"`), que resolve de forma idêntica no host e no container.

```python
Path(vault, "group/alias.md").symlink_to("two.md")
```

**Resultado após a correção:**

- `tests/smoke_stdio.py` (processo local, `.venv/bin/python`): **passou** —
  `12 tools, resource, prompts, OKF read/write, rg, envelope, traversal,
  missing rg`.
- `tests/smoke_stdio.py --docker-image sha256:0cfdc0fd…` (pin vigente): **passou**
  — `12 tools, resource, prompts, OKF read/write, rg, envelope, traversal,
  mounted image and host persistence`.
- `scripts/docker-ci-conformance.py` contra o mesmo image ID, com a fixture F3
  em `/vault`, `--expected-uid 65532` e as 12 `expected-tool`: **passou** —
  `stdio MCP conformance passed: initialize + tools/list (12 tools)`. A
  fixture F3 ficou inalterada (`.probe`, `data/`, `khal.conf`).

Este é o primeiro smoke de integração completo (escrita, leitura, busca,
remoção de link, recusa de arquivo `0444`, validação de backlinks, travessia,
persistência no host) executado sobre uma imagem Notes pinada. O vault de
fixture é um diretório temporário; o vault F3 só foi montado para o
conformance, que não escreve.

### 2. Contagem real da suíte

`.venv/bin/python -m pytest -q -rs` na árvore `1d0b69e`:

```
114 passed, 4 skipped
```

Os 4 skips são dependentes de daemon/imagem local: 3 ×
`tests/test_docker_lifecycle.py` (`image percival-notes-mcp:stage2-wip is not
built locally`) e 1 × `tests/test_vault_backup_restore.py` (`requires the local
stage2 candidate image`). As contagens "111 passed, 7 skipped" e
"71 passed, 7 skipped" que circulam nos documentos foram medidas em hosts sem
o binário `docker` no `PATH`; com o binário presente, 3 dos 4 testes de
`test_vault_backup_restore.py` passam em vez de ser ignorados.

### 3. Estado do registry e do recipe

| Item | Valor verificado |
|---|---|
| Servidor | `notes`, escopo global, `activated: true`, revisão **26** |
| Image ID | `sha256:0cfdc0fdd78f4c86614b80174746c936e7d470b649d7dfd8017747353059fb78` |
| `configurationId` | `67d6ee4e-c055-4d1c-95f6-720f8a3f7437` (config revision 1) |
| Rede / mount | `none` / fixture F3 em `/vault` (`rw`) |
| Allowlist | as 12 tools `notes_*` |
| Receita `canonical` | `dockerfile: Dockerfile` (com rede), `network: default`, `timeoutMs: 120000`, `rejectSeverities: [HIGH, CRITICAL]` **bloqueante**, `localBases: []` |
| Engine | Docker 29.9.2; binário `docker` e socket disponíveis no host |
| Publicação | `origin/main` == `HEAD` (`1d0b69e`); commits publicados |

### 4. Registro durável

O alvo de journal `percival-notes-mcp` responde `not-found`. Na auditoria de
2026-11-12, o bundle `global` estava **vazio** (0 entradas): a nota de ciclo
que o plano de remediação declara gravada **não está presente** em nenhum
bundle, de modo que a afirmação não é verificável no estado atual. A evidência
durável do ciclo NFB existe apenas nos documentos versionados deste repositório.

O **ciclo de auditoria de 2026-11-12** tem registro próprio, gravado no bundle
autorizado desta sessão: `noteId` `20261112-111734-journalentry-agent-8e6463eb-ce9`,
`committed: true`, `syncStatus: synced`.

## Retenção executada — 2026-11-12

Por decisão do owner (Bill), a retenção de imagens do servidor `notes` foi
executada neste dia. Todas as operações foram feitas por **image ID explícito**,
pela interface dona de cada gestor, sem `docker image prune`, sem
`docker system prune` e sem `docker rmi -f`.

### Estado medido antes

| Image ID | Papel | Autorizada | No Engine |
|---|---|---|---|
| `sha256:0cfdc0fd…` | pin vigente (revisão 26) | sim | sim |
| `sha256:0c8fdf75…` | última boa (revisão 25, candidato D) | sim | sim |
| `sha256:6c1640ce…` | variante offline (revisão 22) | sim | sim |
| `sha256:c1f36791…` | build manual `0.1.5-5d761f7` (2026-10-30) | sim | sim |
| `sha256:00010850…` | resíduo de ciclo encerrado | sim | não |
| `sha256:3118650a…` | autorização obsoleta | sim | não |
| `sha256:40fa10ff…` | autorização obsoleta | sim | não |

Cinco imagens Notes autorizadas e presentes contra a regra de duas do
`AGENTS.md`, mais três autorizações sem imagem correspondente.

### 1. Revogação de autorizações

`positronic mcp server revoke-local <image-id> <revision-atual>`, uma por vez,
releitura da revisão a cada passo: **15 → 16 → 17 → 18 → 19 → 20**. Revogadas
`00010850`, `3118650a`, `40fa10ff`, `6c1640ce` e `c1f36791`. A lista ficou com
**8** autorizações, das quais **2** são Notes: `0c8fdf75` e `0cfdc0fd`.

### 2. Remoção da imagem offline `6c1640ce`

Removida pela interface gerenciada: `positronic mcp maintenance remove` com os
dois recibos do build offline.

| Recibo | Resultado |
|---|---|
| `06e98ea0a754d74853ecde1eee2028a251850843e37d264ca31f44991eb9e0cb` | `referenceRemoved: true`, `contentRemoved: false` |
| `e5560b171120643cb2268e2ef7fd6b5ec0fd66d833653898ccae649496100c2a` | `referenceRemoved: true`, `contentRemoved: true` |

A primeira operação removeu só a referência (a tag do job); a segunda liberou
o conteúdo. A admissão da remoção exige que o `recipeSha256` da política
corrente iguale o do job (`d4b54c60…`, construído com `network none` e as duas
`localBases` do build offline), o que não era verdade enquanto a receita
vigente era `network default` + `localBases: []` (`recipeSha256 32bd91e8…`).
A receita foi restaurada exatamente para o estado do job, as duas remoções foram
executadas e a política foi **revertida** ao estado anterior — revisão
persistida `6ee7fa43… → e0adcbc8… → beb5e97c…`, valores finais conferidos
(`network default`, `localBases: []`, `recipeSha256 32bd91e8…`).

**Por que remover e não reter:** a imagem offline carrega o módulo de produto
`notes_mcp.py` com SHA-256 `200294ab…`, **diferente** do código remediado
(`e9ae5682…`). Foi construída em 2026-11-09 13:49 UTC, antes do commit da
remediação `7c1a87e` (22:22 UTC do mesmo dia): **ativá-la subiria o produto
pré-remediação**. As imagens-base que ela consome (`6b121102` wheelhouse,
`acd98ac4` runtime) foram preservadas — são referenciadas por digest no
`Dockerfile.offline` e permitem reconstruir a variante a partir da árvore
remediada.

### 3. Remoção de `c1f36791` e o container Percival

Essa imagem **nunca teve recibo no executor** — era um build manual do owner
Percival (`percival-notes-mcp:0.1.5-5d761f7`, revisão `5d761f7`), não um build
gerenciado —, e portanto não era alcançável por `maintenance remove`
(`job-not-found`). O `AGENTS.md` prevê esse caso: remoção por **ID explícito**,
após aprovação nominal do owner.

Pré-requisito: o container `percival-mcp-notes` referenciava a imagem, e o
`AGENTS.md` proíbe remover imagem referenciada por container. O container era
do **owner Percival** (labels `percival.mcp-docker.owner: percival`,
`managed-by: percival-broker`, `server-id: notes`) e estava em estado zumbi:

- o vault montado `/home/bill/.local/share/percival-test-mcp/notes-vault`
  **não existe mais no host**;
- o diretório de estado do gestor Percival `/home/bill/.nanobot` **não existe
  mais no host** (o conteúdo sobrevive apenas no inode do container do
  gateway, que o mantém montado);
- o container havia sido reerguido em 2026-11-12 10:51 UTC pelo restart do
  daemon, rodando o código pré-remediação.

Encerramento: `docker stop -t 10 percival-mcp-notes` → saída **143** (SIGTERM,
o código esperado para MCP stdio), e `docker rm percival-mcp-notes` **sem
`-f`**, conforme o runbook §3.7. Só então a imagem foi removida por ID
explícito:

```text
Untagged: percival-notes-mcp:0.1.5-5d761f7
Deleted: sha256:c1f36791f649c50c74c7f90e02708d1f415b114500bcfcfc5bb0626a2a6ac050
```

### Estado final verificado

- **Duas** imagens Notes autorizadas e presentes: `0cfdc0fd` (pin, revisão 26,
  `activated: true`) e `0c8fdf75` (última boa, revisão 25) — dentro da regra.
- Autorizações locais: revisão **20**, 8 entradas, 2 Notes.
- Pin do servidor `notes` intacto: revisão **26**, image ID `0cfdc0fd`,
  `configurationId` `67d6ee4e-c055-4d1c-95f6-720f8a3f7437`, config revision 1,
  rede `none`, allowlist das 12 tools; `notes_get_status` responde
  ("operational, versão 0.1.5").
- Suíte contra o pin: **`118 passed, 0 skipped`** (ver seção de testes Docker
  abaixo).

### Resíduo observado, não removido

- `sha256:7b6a283b…` — saída do estágio *wheelhouse* do build offline, sem
  referência em nenhum Dockerfile: resíduo intermediário, fora da lista
  nominal aprovada.
- `sha256:1640d59c…` (`percival-notes-runtime:offline-base`) — tag local do
  build da base runtime, também sem referência em Dockerfile vigente.
- `sha256:6b121102…` e `sha256:acd98ac4…` — bases do build offline,
  referenciadas por digest no `Dockerfile.offline`; preservadas de propósito.

### Testes Docker contra o pin — 2026-11-12

O passo 7 do ciclo de imagem (testes de restore/permissões contra a mesma
referência) estava pendente desde 2026-11-09: os quatro testes dependem de uma
imagem local com tag e eram ignorados. Executados contra o image ID do pin:

```bash
PERCIVAL_NOTES_TEST_IMAGE=sha256:0cfdc0fd… \
NOTES_MCP_TEST_IMAGE=sha256:0cfdc0fd… \
.venv/bin/python -m pytest -q -rs
# => 118 passed, 0 skipped
```

Cobertura: `tests/test_docker_lifecycle.py` (3× — a imagem não embute init; com
`--init` o `docker stop` retorna em menos de 1 s com saída 143; sem init a saída
difere de 143) e
`tests/test_vault_backup_restore.py::test_restored_fixture_supports_mcp_read_search_and_write`
(backup, restore e leitura/busca/escrita MCP real sobre o vault restaurado).

**Flake observado:** em uma de seis execuções completas da suíte contra o pin,
`test_stop_without_init_still_exits_but_with_a_different_code` falhou. O teste
assume 1 s de espera de prontidão antes de `docker stop -t 10` e um orçamento
de 10 s para o stop; sob carga do host a asserção de tempo ou de código de
saída oscila. A mesma imagem passou em 4 de 4 rodadas completas seguintes e em
3 de 3 execuções isoladas do arquivo. A suspeita recai sobre a temporização do
harness, não sobre a imagem; **não está corrigido** e fica registrado como
risco residual.

### Identidade de código entre o pin e o candidato qualificado

A bateria 12/12 foi executada contra o candidato `0c8fdf75` (revisão 25). Para
transferir a evidência ao pin da revisão 26, foi medido o hash do módulo de
produto **dentro das imagens**: `/opt/venv/lib/python3.12/site-packages/notes_mcp.py`
tem SHA-256 `e9ae5682227c8846…` idêntico em `0cfdc0fd` (pin), em `0c8fdf75`
(candidato que passou a bateria) e no checkout. A transferência é por
identidade medida, não por afirmação.
