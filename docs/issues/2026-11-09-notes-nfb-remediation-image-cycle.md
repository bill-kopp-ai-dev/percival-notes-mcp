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

Candidato final: **C**. Um candidato intermediário (B) foi construído e
qualificado antes de um último ajuste de normalização de path em
`_resolve_destructive_path`; ele foi superado por C e removido do host.

| Campo | Valor |
|---|---|
| Image ID (manifesto) | `sha256:0c8fdf7500c2ec989adbfcf512cded3575032f6cd9540e62570e99b782e614d6` |
| `configDigest` | `sha256:5d9198d4cd37ad189a10c02035fae9ed90ee44b6658cf930adcea44d7bba4896` |
| `manifestMediaType` | `application/vnd.oci.image.manifest.v1+json` |
| `imageName` | `docker.io/positronic-build/e3c0ebddd73c4cdd0650740249dcca7429cf40d7bfa225cc56be1fd5d7b8b7a0:30861ecd0706a83477db370dace60d5a5dd333cb750293081f782d6433cc4cce` |
| `imageResolution` | `verified` |
| Job de build (requestId) | `734728be97533c7de29dedf75c36d50fcb609bec0c1b621e05bbf8ce61d57e5e` |
| Fonte | commit `0a44d1cce61cc8f0eca02781a4a2ee8bfa1f2f6b`, árvore **dirty** (as correções desta remediação ainda não commitadas) |
| `contextSha256` | `3ae586ca65a4a60dc587ff2dd180d48ecf10509e1be16368316f864b41d52348` |
| `recipeSha256` | `32bd91e8c9a521d96eb586b491ed0e8238c9567dbba0956c9f552a0f0d8eb5c5` (receita `canonical`, rede `default`) |
| Versão do produto | `0.1.5` (inalterada nesta remediação) |

Candidato intermediário superado: `sha256:1157f51f2677f5153f85be500e183591764393db4988f8ac58d7570775289d57`
(job `eeb27185dff552da13fad43d0a5f288b9a0ed92d2343af46617e4cf967aa686c`,
`contextSha256` `7cf5497ad3d81deca59a694149cbce99d5e0cc164654b4d44a971f3c4bb5be18`).

## Scan e SBOM

- **Scanner:** Trivy `0.76.1` (`scannerSha256` `4ab0e6d9c77528fd876a6dda49c506cd5b5317be0396a5a7d34ff5a6f7e8ad54`).
- **Base de vulnerabilidades:** `updatedAt 2026-11-09T00:56:17Z`, `downloadedAt 2026-11-09T02:29:13Z`.
- **Resultado:** **0 findings** em todas as severidades, no candidato C e
  também no candidato B superado.
- **Gate:** `[HIGH, CRITICAL]`, **bloqueante** (diferente do `report-only` citado
  no histórico de `AGENTS.md`; a política vigente do host é a que vale).
- **Hashes de evidência (candidato C):** `scanSha256` `b87e6471b4aa1b92061732ff005c75e195b42d5ed57665160517041d8eec75e0`;
  `sbomSha256` `3011578a019e3ad5e8b3f02fad717094d74b9687af7e0ef583b11b6298e4f479`;
  `scannerSha256` `4ab0e6d9…`.
- **Fases do job:** `engine`, `build`, `scanner-version`, `scan`, `sbom` — todas com
  `exitCode: 0`; `state: succeeded`.

O relatório bruto do Trivy e o SBOM ficaram no host; o executor expõe apenas os
hashes. Mesma lacuna já registrada em `2026-11-09-notes-offline-6c1640ce-scan.md`.

## Autorização e pin

1. `image_authorize` aceito para `sha256:0c8fdf75…` (`serverId notes`).
2. `positronic mcp server update-image notes sha256:0c8fdf75… 23` → revisão do
   servidor **24**, `configurationId` `9bcf1480-cade-4999-a047-1632a40e9a6a`.
3. Configuração reaplicada com `positronic mcp server configure`: rede `none`,
   mount do vault de fixture F3 em `/vault` (`rw`) e allowlist das **12 tools**.
   O `update-image` invalida a `configurationId` anterior e **redefine a revisão
   de configuração para 0**; por isso o `configure` seguinte usa a revisão 0, e
   não a revisão 7 que existia antes do pin.
4. `positronic mcp server discover notes` devolveu as **12 tools** esperadas.
5. `positronic mcp server activate notes 24` → servidor ativo no candidato.

**Estado A preservado para rollback:** imagem `sha256:6c1640ce8d0c823186858dcc04b7e793a997cf301ae4680f1c00d0b30cf3a7dd`
(revisão 22), ainda autorizada e fixável com um comando.

## Qualificação funcional no MCP pinado

Executado pela sessão connected ao pin final (candidato C), com a fixture F3
montada em `/vault`. Todas as notas usadas foram sintéticas e removidas ao
final.

| Achado | Prova na imagem `0c8fdf75…` | Resultado |
|---|---|---|
| F-01 | `notes_search("alpha")` com `locked.md` em modo `000` no vault → devolve `["_nfb_probe/good.md"]` | corrigido |
| F-02 | `notes_glob(".")` → `Glob pattern must name a path component inside the vault` | corrigido |
| F-03 | `notes_glob("**")` → sem `"."`; devolve `["_nfb_probe", "_nfb_probe/realdir", "data"]` | corrigido |
| F-04 | nota nova nasce `0600`; decisão D-01 aplicada | aceito por decisão |
| F-05 | `notes_rm("_nfb_probe/alias.md")` removeu o link; `good.md` manteve o conteúdo | corrigido |
| F-06 | `notes_rmdir("_nfb_probe/dirlink")` → recusa; link e diretório-alvo intactos; `notes_rmdir` do diretório real vazio removeu-o | corrigido |
| F-07 | `notes_read_multiple` com bytes não-UTF-8 → `reason: unreadable`; `notes_read` → erro explícito de UTF-8 | corrigido |
| F-08 | `tags: [T1, shared]` + `keywords: [K1, SHARED]` → `["k1","shared","t1"]`; stats com 1 nota por tag | corrigido |
| F-09 | `notes_get_backlinks("../a.md")` → recusa; `""` e `/etc/passwd` → recusa; alvo válido → funciona | corrigido |
| F-10 | `notes_get_stats` = 6 notas para 8 entradas com alias/link → contagem canônica | corrigido |
| F-11 | `notes_write` em `0444` → recusa; conteúdo, modo `444` preservados; zero temporários `.notes-*` | corrigido |
| F-12 | `notes_glob` não lista link quebrado nem caminho fantasma | corrigido |

**Containção de path intacta na imagem:** `notes_read` e `notes_rm` de symlink
externo (`/etc/passwd`) → `Path escapes root directory`; o alvo externo não foi
lido nem removido.

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
- **A árvore estava dirty no build:** o commit `0a44d1c` não contém as
  correções desta remediação. A identidade do candidato está ligada ao
  `contextSha256` acima, não ao commit. Um build reprodutível exige commit
  antes da promoção definitiva.
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

Commit da remediação (com `notes_mcp.py`, `tests/test_functional_battery.py`,
README e docs) e, se o owner quiser reexecutar o ciclo, novo build a partir da
árvore commitada para eliminar a marca `dirty` da evidência.

## Limpeza

O candidato intermediário B (`sha256:1157f51f…`) foi **superado** por C. A
autorização local de B foi revogada (`revoke-local`, revisão de autorização
13 → 14) e a imagem removida pelo owner interface (`image_remove`): `state:
completed`, `referenceRemoved: true`, `contentRemoved: true`. O pin nunca
apontou para B durante a remoção.

Retenção após o ciclo: o candidato C (pinado, promovido) e a imagem A
`sha256:6c1640ce…` (rollback, ainda autorizada). Nenhuma limpeza genérica
(`docker image prune`, `docker rmi -f`) foi executada.
