# F3 — scan do candidato **offline** `percival-notes-mcp` `6c1640ce…` (2026-11-09)

- **Atualizado:** 2026-11-09 UTC.
- **Artefato escopado:** image ID (manifesto) `sha256:6c1640ce8d0c823186858dcc04b7e793a997cf301ae4680f1c00d0b30cf3a7dd`; `configDigest` `sha256:8241420ec91072d26cba849939f7b9ad7ddf3efc980fe0981336d9c262596746`; `manifestMediaType` `application/vnd.oci.image.manifest.v1+json`. É a imagem **em uso** pelo servidor Notes registrado no Positronic (`$POSITRONIC_HOME/mcp/registry.json`, `server id notes`, revisão 22).
- **Diferença para o candidato anterior:** esta imagem foi construída **sem egress** (`--network none`), a partir de duas bases locais verificadas pelo executor. O candidato anterior (`0001085057…`) foi construído com rede. O código do produto é o mesmo; as dependências Python são as mesmas versões, fixadas por hash.
- **Origem do artefato:** revisão `e6a800555894799c5fa306f222cd060391b45fd8` (commit com a variante offline fixada pelas `localReference` do executor e com a criação de `/vault` corrigida); `contextSha256` `ab88bb56fd7487d05da0d77fdecd06ec3875852a8b76444f4084a5da6a03dc7f`.
- **Job de build:** `06e98ea0a754d74853ecde1eee2028a251850843e37d264ca31f44991eb9e0cb` (request `f6ff3a8e8861fbeb25617a327b8cf3095a95d252c0dfc383ffbaafe2c5e9096c`), `state: succeeded`, `exitCode: 0`, fases `engine`, `build`, `identity`, `scanner-version`, `scan` e `sbom` com exit 0, `imageResolution: verified`.
- **Reprodutibilidade:** um segundo build do mesmo conteúdo (job `e5560b171120643cb2268e2ef7fd6b5ec0fd66d833653898ccae649496100c2a`, request `94ccc6199e7814b404242777d2adaa28f2f96a8e764799926cb42d5b73f0f61d`, árvore ainda não commited) devolveu **o mesmo image ID** e o mesmo `contextSha256`. O candidato é reprodutível no mesmo Engine.
- **Scanner:** Trivy 0.76.1 (`scannerSha256` `4ab0e6d9c77528fd876a6dda49c506cd5b5317be0396a5a7d34ff5a6f7e8ad54`), base de vulnerabilidades `updatedAt 2026-11-09T00:56:17Z` (`downloadedAt 2026-11-09T02:29:13Z`), executado pelo host na receita `canonical` do projeto `percival-notes-mcp`.
- **Resultado:** **0 findings** em todas as severidades; gate `[HIGH, CRITICAL]` **bloqueante** e vazio.
- **Hashes de evidência:** `scanSha256` `769e1036490ba71c41fde40e402ea1dea3aed866a6fba8d7e5056b3fa163216b`; `sbomSha256` `0bd5a18bdbc3ef2415789ee6b8ae385b4017fc6e6ff03256833fad1f2e56bdff`; `contextSha256` `ab88bb56…`; `recipeSha256` `d4b54c609db41fc9e72b31aa3b13cb0b86183a57d7ad38048060aa773014a40d` (`network: none` com as duas `localBases` declaradas).
- **Cadeia de bases locais** (cada uma construída e escaneada pelo executor, com `imageResolution: verified` e 0 findings):
  - runtime — job `bbda217d0100c6163b5fda3e0359135809e9c30ea59773504f0f056f9bc675c9`, manifesto `sha256:acd98ac4…`, `configDigest` `sha256:5392929f…`, `scanSha256` `961a09b2…`, `sbomSha256` `f0b03758…`;
  - wheelhouse — job `fd234fc2fce4cb3d505f73a3a270e3e72bf9a25a16d5bb2bcefb44aa79a6bf00`, manifesto `sha256:6b121102…`, `configDigest` `sha256:df0b02cf…`, `scanSha256` `774aaa8c…`, `sbomSha256` `ac31a263…`.
  - Os digests da base de runtime são **idênticos** aos do build directo feito pelo owner no host (`configDigest` `5392929f…`, manifesto `acd98ac4…`): o build via executor é reprodutível face ao build manual.
- **Autorização e pin:** `image_authorize` aceito (imagem `6c1640ce…`, `serverId notes`); `update-image` levou o servidor à revisão 22 com novo `configurationId` `9434f3a0-e89c-45f3-b8cc-906d5010aea7`; configuração reaplicada com rede `none`, o vault da fixture F3 e allowlist mínima (`notes_get_status`, `notes_get_stats`); `discover` devolveu as **12 tools** esperadas.
- **Decisão do owner (Bill, 2026-10-28), mantida:** não emitir OpenVEX, porque o scan não encontra CVEs a declarar. Válida para este image ID.

## Smoke funcional na imagem offline pinada

Executado contra a imagem `6c1640ce…`, com a fixture F3 montada em `/vault`:

1. `notes_get_status` → "Percival Notes MCP Server operational. Version: 0.1.5. Root: vault" (sem path absoluto);
2. `notes_get_stats` → 0 notas, 0 tags, 0 arquivos ilegíveis;
3. `notes_write` de `_percival_smoke_20261109T140000_5f81c3.md` → "File written";
4. `notes_read` → conteúdo íntegro com o marcador `PERCIVAL_NOTES_SMOKE_20261109T140000_5f81c3`, dentro do envelope de conteúdo não confiável;
5. `notes_search(in_markdown=true)` pelo marcador → **apenas** o caminho sintético;
6. `notes_rm` → "File removed";
7. pós-checagem `notes_glob` → `[]`.

A única nota escrita foi a sintética acima, removida ao final; nenhum conteúdo de usuário foi lido, listado ou exportado. O `write` funcionou porque a variante offline passou a criar `/vault` com a titularidade `65532:65532`, como a imagem com rede — sem essa correção o vault montado não seria gravável pelo uid do serviço.

## Defeitos encontrados e corrigidos na variante offline

- `scripts/offline-wheelhouse.py` não entrava no contexto de build: a etapa de verificação do wheelhouse falharia.
- `/usr/local/bin/python3.12` não era copiado para o estágio de runtime: o entrypoint ficaria sem interpretador.
- `/vault` não era criado nem ajustado ao owner `65532:65532` no estágio de runtime (divergência em relação à imagem com rede).
- `.dockerignore` excluía `docker/offline-wheelhouse-fetch.py`, o que impedia o comando de build documentado no próprio Dockerfile de funcionar.
- `COPY ${WHEELHOUSE_MANIFEST}` usava expansão de ARG, recusada pelo modo de base local do executor: a referência passou a literal.

## Limites e pendências

- **A variante offline continua não ativada na receita.** O `Dockerfile` da raiz (o que a receita constrói) é o do produto com rede; a variante offline é construída sob demanda e a sua ativação permanente é decisão do owner. Enquanto a receita não apontar para `Dockerfile.offline`, o build com rede continua a ser o caminho do dia a dia.
- **As `localReference` literais mudam a cada reconstrução de base.** O procedimento está documentado nos Dockerfiles: reconstruir a base, declarar o novo job produtor em `localBases` (policy do projeto) e atualizar o literal. Sem `localBases` declaradas, o executor recusa um Dockerfile que use `positronic-build/` (`local-base-invalid`), o que impede ativação acidental.
- **O gate de scan do builder é o host e é bloqueante** (`rejectSeverities: [HIGH, CRITICAL]` no escopo do projeto): um achado bloqueante faz o job falhar, não apenas reportar.
- **O relatório bruto do Trivy e o SBOM ficaram no host**; o executor expõe apenas os hashes. Mesma lacuna já registrada para `0001085057…` e para a imagem Weather 0.10.0. Se a imagem for publicada, o relatório bruto deve ser arquivado em `pblabs-mcp-index/servers/notes/` e a seção do tracker atualizada com caminho e SHA-256.
- **Evidência canônica por imagem (`R-05`):** `pblabs-mcp-index/servers/notes/security-scan-e6a8005-6c1640ce.json`, com a seção aplicável em `pblabs-mcp-index/docs/f3-tracker.md`.
- **Regressão disponível:** o candidato anterior `sha256:0001085057…` continua autorizado e fixável com um comando, caso o owner prefira o runtime com rede.
- O gateway e o broker do Percival são do outro owner; a reconciliação com o gate do gateway continua externa a este projeto.

## Rastreabilidade

- A identidade da imagem vem do registro do host (`registry.json`), não da resposta do MCP: o MCP não expõe a imagem em que corre.
- O vault montado é `/home/bill/.positronic-reports/f3-0-1-notes-vault-20261020T172539Z` — diretório de fixture do gate F3, não vault de usuário.
- A postura do produto (usuário `65532:65532`, `init` único do launcher, `cap_drop: ALL`, `no-new-privileges`, rootfs somente-leitura) está no `docker-compose.yml` e é verificada estaticamente por `tests/test_docker_contract.py`; o manager do Positronic é quem aplica a postura do runtime.
