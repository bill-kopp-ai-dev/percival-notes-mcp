# Notes MCP — ciclo de imagem da remediação da bateria funcional (2026-11-09)

- **Data:** 2026-11-09 (UTC).
- **Objetivo:** qualificar o candidato que corrige os 12 achados de
  [docs/issues/2026-11-09-notes-functional-battery-findings.md](../issues/2026-11-09-notes-functional-battery-findings.md),
  conforme
  [docs/plans/2026-11-09-notes-functional-battery-remediation-plan.md](../plans/2026-11-09-notes-functional-battery-remediation-plan.md).
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
- **O flag `dirty` do host permanece `true` mesmo com a árvore commitada.**
  A causa foi reproduzida e está documentada em **Diagnóstico do flag `dirty`**:
  o executor exclui `AGENTS.md` do manifesto de contexto e compara a
  contagem com a árvore do Git, o que torna `dirty` estruturalmente `true`
  neste repositório. O contexto de build é idêntico à árvore do commit
  `7c1a87e`, e `changed` é vazio. O sinal não deve ser lido como "árvore
  suja".
- **Não houve promoção para produção nem publicação.** O pin permanece no
  candidato para avaliação do owner; o registry do Percival, o broker e
  containers de produção não foram tocados.
- Os **7 skips** da suíte local (dependentes de daemon Docker e da imagem
  local) não foram reexecutados aqui; a suíte local está verde com 111 passed,
  7 skipped.
- A semântica de D-01 (somente `0600`) **mantém** a limitação de F-04: o
  operador host precisa de root ou de uma ACL explícita no vault para ler as
  notas criadas pelo servidor. Isso foi aceito explicitamente pelo owner.

## Próximo passo

Nenhum passo de código pendente neste ciclo: a remediação foi commitada
(`7c1a87e`) e publicada em `refs/heads/main`, e o candidato D foi construído a
partir dessa árvore commitada, pinado e requalificado.

Pendências apenas de decisão do owner:

- **Promoção para produção:** o pin atual é a referência do servidor `notes`
  (revisão 25). Não houve promoção nem publicação de configuração de produção.
- **Harness de conformidade:** `scripts/docker-ci-conformance.py` continua não
  executado, por ausência de Docker CLI no executor. Rodá-lo no host fecha
  esse limite.
- **Flag `dirty` do executor:** a causa está documentada em **Diagnóstico do
  flag `dirty`**. A correção é no executor do host, não neste repositório.

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
