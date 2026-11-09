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
