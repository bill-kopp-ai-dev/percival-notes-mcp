# Notes MCP — bateria funcional de testes e achados

- **Data:** 2026-11-09 (UTC).
- **Escopo:** as 12 tools públicas de `percival-notes-mcp` 0.1.5, exercitadas
  contra o binário real em modo stdio e contra a **imagem pinada em uso**
  (`sha256:6c1640ce…`, server id `notes`, revisão 22 do registry).
- **Árvore:** `percival-notes-mcp` em `0a44d1c` (working tree limpa).
- **Baseline antes da bateria:** `.venv/bin/python -m pytest -q` → **71 passed,
  7 skipped** (os skips são os casos que dependem de Docker/imagem local).
  Nenhum teste foi alterado; a suíte continua verde no fim da bateria.
- **Harness:** `/home/bill/.positronic/runtime/tmp/opencode/` —
  `notes_battery.py` (48 probes), `notes_battery2.py` (48 probes),
  `confirm_findings.py`, `fm_probe.py`, mais um roteiro de revalidação
  isolada por achado (12 checks). Probes ~96, dos quais **12 achados
  confirmados** abaixo. Probes que falharam por defeito do próprio harness foram
  descartados e não estão aqui (ver "Achados descartados").

---

## 1. Resumo

| # | ID | Severidade | Tool | Resumo |
|---|---|---|---|---|
| F-01 | `NOTES-SRCH-ABORT` | **P1** | `notes_search` | Uma nota ilegível aborta a busca inteira |
| F-02 | `NOTES-GLOB-DOT` | **P2** | `notes_glob` | `pattern="."` estoura `IndexError` não tratado |
| F-03 | `NOTES-GLOB-ROOT` | **P2** | `notes_glob` | `pattern="**"` devolve `"."` como resultado espúrio |
| F-04 | `NOTES-WRITE-MODE` | **P2** | `notes_write` | Nota nova nasce `0600`, anulando a ACL padrão do vault |
| F-05 | `NOTES-RM-SYMLINK` | **P2** | `notes_rm` | Remove o **alvo** do symlink, não o link |
| F-06 | `NOTES-RMDIR-SYMLINK` | **P2** | `notes_rmdir` | Idem para diretórios (apaga a árvore real) |
| F-07 | `NOTES-RM-UTF8` | **P3** | `notes_read_multiple` | UTF-8 inválido é rotulado `too_large` |
| F-08 | `NOTES-TAGS-PRECED` | **P3** | `notes_list_tags` | `keywords` é ignorado quando `tags` existe |
| F-09 | `NOTES-BACKLINK-PATH` | **P3** | `notes_get_backlinks` | Path de alvo não é validado |
| F-10 | `NOTES-STATS-ALIAS` | **P3** | `notes_get_stats` | Symlink in-vault infla `total_notes` |
| F-11 | `NOTES-RO-WRITE` | **P3** | `notes_write` | Sobrescreve arquivo `0444` preservando o modo read-only |
| F-12 | `NOTES-GLOB-GHOST` | **P3** | `notes_glob` | Symlink quebrado gera resultado que não existe |

Severidade aqui = impacto sobre a operação do servidor, não sobre a
confidencialidade do vault. **Nenhum achado permite ler, escrever ou apagar
conteúdo fora do vault.** A contenção de path (o invariante mais importante do
produto) permaneceu íntegra em toda a bateria — ver §3.

---

## 2. Achados

### F-01 — `notes_search` aborta a busca inteira por causa de uma nota ilegível

**Severidade: P1.** É o achado mais grave: uma única nota que o processo não
consegue ler torna `notes_search` inútil para o vault inteiro.

**Reprodução** (local, stdio):

```
vault/
  good.md     -> "---\ntype: A\n---\nalpha\n"
  locked.md   -> "---\ntype: L\n---\nsecret\n"   (chmod 000)
```

`notes_search(query="alpha")` →

```
Error executing tool notes_search: [Errno 13] Permission denied: 'locked.md'
```

**Confirmado na imagem pinada em uso.** O vault real
(`~/.positronic-reports/f3-0-1-notes-vault-20261020T172539Z`) recebe notas
criadas pelo host; uma delas com `0600` e owner `1000` reproduz o mesmo erro
contra o container (que roda como `65532`):

```
Error executing tool notes_search: [Errno 13] Permission denied: 'hostlocked_root.md'
```

**Causa-raiz.** `_rg_matches` abre cada candidato por descriptor e propaga
qualquer `OSError` sem tratamento (`notes_mcp.py:658`):

```python
fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
```

O `PermissionError` sobe por `_rg_matches` → `_search_notes_rg` → `search` e
vira erro da tool. Note que `notes_mcp.py:322` tem a mesma chamada, mas ali o
`OSError` é absorvido por `except OSError: reason = "unreadable"`.

O caminho alternativo (walker Python, usado quando a query contém NUL) tem o
mesmo defeito — confirmado: `notes_search(query="a\0b")` também estoura com
`Permission denied`.

**Por que importa.** As outras duas tools que tocam o mesmo arquivo degradam
com elegância e foram confirmadas no mesmo vault: `notes_get_stats` reportou
`unreadable_files: 1` com `unreadable_paths: ["hostlocked_root.md"]`, e
`notes_read_multiple` reportou `{"path": "hostlocked_root.md", "reason":
"unreadable"}`. Ou seja, o contrato "expor leituras parciais com motivo
explicito" (A-008 do plano stage-2) foi implementado para `stats` e
`read_multiple`, mas **não** para `search`. A tool de descoberta — a que o
cliente mais usa para navegar o vault — é a única que morre.

**Correção sugerida.** Tratar `OSError` ao abrir o descriptor em
`notes_mcp.py:658` como arquivo ilegível: registrar em log, contabilizar e
continuar, em vez de propagar. Vale decidir se o `search` deve expor um
contador de arquivos ilegíveis junto com os resultados, para não perder a
informação que `stats` já fornece.

**Nota de escopo.** O gate de tempo (`operation_timeout_seconds`) e os limites
de varredura continuam valendo; o defeito é a ausência de tratamento de erro,
não a ausência de limite.

---

### F-02 — `notes_glob(pattern=".")` estoura com `IndexError` não tratado

**Severidade: P2.** Erro interno de Python exposto ao cliente, em vez de uma
mensagem de validação.

**Reprodução** (idêntica no local e na imagem pinada):

```
notes_glob(pattern=".") -> Error executing tool notes_glob: tuple index out of range
```

**Causa-raiz.** `_validate_glob_pattern` (`notes_mcp.py:497`) rejeita padrão
vazio, absoluto e com `..`, mas aceita `"."`. Em Python 3.12,
`Path(".").parts` é vazio, então a checagem de `..` passa; depois
`root_dir.glob(".")` (`notes_mcp.py:913`) quebra dentro do `pathlib`, em
`_make_selector`, com `IndexError: tuple index out of range`. A exceção não é
`ValueError`, então escapa das validações do produto e chega ao cliente como
erro interno.

**Por que importa.** A tool promete rejeitar padrões inválidos *antes* de
enumerar (A-009 do plano stage-2, critério de aceite explícito). `"."` passa
pela validação e produz um traceback em vez de uma recusa limpa. O agente
cliente recebe uma mensagem que não orienta correção.

**Correção sugerida.** Rejeitar em `_validate_glob_pattern` qualquer padrão
cujo `PurePosixPath(pattern).parts` seja vazio (o que cobre `"."`, `"./"` e
`"//"`), com mensagem no mesmo estilo das existentes.

---

### F-03 — `notes_glob(pattern="**")` devolve `"."` como resultado espúrio

**Severidade: P2.** Contraria diretamente um critério de aceite já fechado do
próprio projeto.

**Reprodução** (local e imagem pinada):

```
notes_glob(pattern="**") -> ['.', 'sub']      # local
notes_glob(pattern="**") -> ['.', 'data']     # imagem pinada
```

**Causa-raiz.** `Path.glob("**")` no Python 3.12 emite o próprio diretório
raiz como primeiro resultado. `_collect_safe_matches` (`notes_mcp.py:450`)
converte o caminho resolvido em relativo e, para a raiz, obtém `"."`. Não há
filtro que descarte esse resultado.

**Por que importa.** O plano stage-2 (A-009) fixa como critério de aceite:
"`../../*` e padrão absoluto recusados antes de varrer; **sem resultado espúrio
`.`** nem caminhos externos nos logs". O critério foi declarado cumprido, mas
`.` continua alcançável por `**` — que é justamente o padrão mais natural para
"listar tudo no vault". Um cliente que percorra os resultados e tente ler `.`
como nota recebe um erro; um cliente que conte arquivos recebe um a mais.

**Correção sugerida.** Descartar o resultado que resolve para a própria raiz do
vault, dentro de `_collect_safe_matches`.

---

### F-04 — Nota escrita pelo servidor nasce `0600` e anula a ACL padrão do vault

**Severidade: P2.** Perde o acesso do operador host às próprias notas — sem
violar o vault.

**Reprodução na imagem pinada em uso.** O vault é um bind mount com ACL
default que concede `USER(1000)=rwx` (o operador, uid 1000) e `USER(65532)=rwx`
(o container). Depois de um `notes_write` pela tool:

```
-rw-------+ 1 65532 65532 40 _mode_probe.md        # criado pelo servidor
-rw-rw----+ 1 1000 1000  0 .probe                 # criado pelo host
```

O arquivo do servidor não é legível pelo operador host:

```
$ cat .../_mode_probe.md
cat: .../_mode_probe.md: Permission denied
```

ACL efetiva do arquivo criado pelo servidor:

```
USER_OBJ()=6  USER(1000)=7  USER(65532)=7  GROUP_OBJ()=0  MASK()=0  OTHER()=0
```

Note `MASK()=0`: a entrada `USER(1000)=7` herdada do default ACL do diretório
existe, mas o mask zerado a anula. O operador tem a permissão declarada e não
a tem na prática.

**Causa-raiz.** `_atomic_write` (`notes_mcp.py:545`) cria o arquivo temporário
com `os.open(..., 0o600, ...)`:

```python
temp_fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                  0o600, dir_fd=parent_fd)
```

O `0600` explícito **sobrescreve o default ACL do diretório** (herdado seria
`0660`, como mostra o `.probe` criado pelo host) e zera o mask. Depois,
`os.fchmod` (`notes_mcp.py:556`) só é aplicado quando o alvo já existe, para
preservar o modo anterior — um arquivo novo nunca passa por esse caminho, então
fica em `0600`.

**Por que importa.** O README (seção "Vault backup and restore") já reconhece
que o chamador precisa de root para ler notas mode-0600. Mas a consequência
operacional é mais ampla que o backup: o operador não consegue ler, com
ferramentas do host, as notas que o agente escreve no vault compartilhado. É a
assimetria oposta à de F-01 — a mesma incompatibilidade de owner/mode, vista do
outro lado.

**Correção sugerida.** Criar o temporário com o modo que o umask/default ACL do
diretório produziria (não `0600` explícito), e preservar o modo existente
apenas no caminho de substituição — que é o que o código já faz. Como
`os.open` com modo `0o600` corta o default ACL, a alternativa é criar o
temporário com `0o666` e deixar o umask/ACL do diretório decidir, ou aplicar
`os.set_default_acl`/ajustar o mask após a criação. **Decisão do owner
requerida:** o comportamento desejado é "nota legível pelo operador host" ou
"nota privada do usuário do container"? O README e os scripts de backup
(`scripts/vault-backup.sh`, `scripts/vault-restore.sh`) assumem `0600`; mudar
isso é uma mudança de contrato que deve ser coordenada antes de implementada.

**Impacto verificado nos scripts.** `scripts/vault-backup.sh` já exige root
para ler notas mode-0600, então a mudança não quebraria o backup — mas alteraria
a superfície de segurança e exigiria revisar o README, o `vault-restore.sh` e o
teste `tests/test_vault_backup_restore.py`, que fixa `0600`/`0640` explicitamente.

---

### F-05 — `notes_rm` remove o alvo do symlink, não o link

**Severidade: P2.** Destruição de arquivo diferente do pedido.

**Reprodução**:

```
victim.md        -> conteudo real
alias.md         -> symlink para victim.md
notes_rm(path="alias.md")
```

Resultado: `"File removed: victim.md"` — **`victim.md` é apagado** e
`alias.md` permanece como symlink quebrado (`alias2.md still symlink: True`,
`victim2.md still exists: False`).

**Causa-raiz.** `_resolve_safe_path` (`notes_mcp.py:275`) resolve o caminho
com `Path.resolve(strict=False)`, que **segue** symlinks. O `os.unlink` em
`notes_rm` (`notes_mcp.py:964`) opera sobre o nome resolvido, dentro do
diretório resolvido. O path do usuário é normalizado antes de qualquer checagem
de identidade.

**Por que importa.** A contenção de path permanece correta (o symlink apontava
para dentro do vault). Mas a **identidade do objeto** não é: o cliente pediu
para remover `alias.md` e perdeu `victim.md`. Um agente que constrói aliases
para organizar um vault pode, sem querer, apagar a nota original. O retorno
traz o caminho real (`victim.md`), o que é honesto, mas o dano já ocorreu e não
é reversível pelo mesmo caminho.

**Correção sugerida.** Em `notes_rm`, decidir explicitamente entre remover o
link ou remover o alvo, e documentar. A opção mais segura para um servidor de
notas é remover o **link** (é o objeto nomeado pelo cliente), preservando o
alvo.

---

### F-06 — `notes_rmdir` apaga o diretório real por trás do symlink

**Severidade: P2.** Mesmo defeito de F-05, com impacto maior: apaga uma
subárvore inteira.

**Reprodução**:

```
emptytarget/    (diretorio vazio)
emptylink   -> symlink para emptytarget
notes_rmdir(path="emptylink")
```

Resultado: `"Directory removed: emptytarget"`, `emptytarget` não existe mais e
`emptylink` continua como symlink quebrado. Com um diretório **não vazio**, o
erro é `Errno 39: Directory not empty` — a proteção é do `rmdir` do sistema
operacional, não do servidor.

**Causa-raiz.** Mesma de F-05 (`_resolve_safe_path` resolve o symlink antes da
operação).

**Por que importa.** `notes_rmdir` é a operação mais destrutiva em potência do
produto. Com F-05 e F-06 juntos, um alias apontando para um diretório
populoso expõe a remoção de toda a árvore, enquanto o nome pedido permanece
intacto — o pior arranjo possível para o cliente, que acredita ter removido
só o alias.

**Correção sugerida.** Mesma de F-05: operar sobre o link nomeado, ou
recusar explicitamente symlinks em `notes_rm`/`notes_rmdir` com uma mensagem
que explique a escolha.

---

### F-07 — `notes_read_multiple` rotula UTF-8 inválido como `too_large`

**Severidade: P3.** Motivo errado no contrato `{notes, omitted}`.

**Reprodução**: arquivo com bytes não-UTF-8 (`b"---\ntype: X\n---\n\xff\xfe"`)
→ `omitted: [{"path": "bin.md", "reason": "too_large"}]`.

**Causa-raiz.** `UnicodeDecodeError` é subclasse de `ValueError`. Em
`notes_mcp.py:1175`, o `except ValueError` — que existe para o limite de
tamanho — captura também o erro de decodificação e atribui `too_large`. O
motivo `unreadable` (`notes_mcp.py:1177`) só é alcançado por `OSError`.

**Por que importa.** O contrato público documenta os motivos
`not_found, outside_vault, not_a_file, too_large, unreadable`. Um cliente que
decide "reler com mais espaço" ou "avisar o usuário" conforme o motivo recebe
uma informação errada: o arquivo tem 13 bytes, não excede limite nenhum.

**Correção sugerida.** Separar a decodificação do controle de tamanho, para que
`UnicodeDecodeError` resulte em `unreadable`. Vale fazer o mesmo no
`notes_read` (que hoje propaga o erro cru do codec — ver §3).

---

### F-08 — `notes_list_tags` ignora `keywords` quando `tags` está presente

**Severidade: P3.** Perda silenciosa de metadados.

**Reprodução**: frontmatter com `tags: [t1]` **e** `keywords: [k1]` →
`notes_list_tags` devolve `['t1']`. A tag `k1` não aparece.

**Causa-raiz.** `_extract_tags` (`notes_mcp.py:386`):

```python
raw_tags = yaml_dict.get("tags") or yaml_dict.get("keywords") or []
```

O `or` implementa *fallback*, não *união*: `keywords` só é lido quando `tags`
está ausente ou vazio. O docstring da tool diz "Scans YAML frontmatter fields
'tags' and 'keywords'" (plural, ambíguo) e o guide do recurso OKF menciona
ambos.

**Por que importa.** É uma divergência silenciosa entre o contrato documentado
e o comportamento: o cliente recebe uma lista de tags incompleta, sem indicação
de que existem outras fontes. Efeito colateral: `tags: []` + `keywords: [k1]`
**inclui** `k1` (porque lista vazia é falsy) — a mesma combinação de campos
produz resultados diferentes dependendo do conteúdo, o que é difícil de
prever.

**Correção sugerida.** Unir os dois conjuntos explicitamente
(`tags` + `keywords`), preservando a normalização atual de caixa e espaços.

---

### F-09 — `notes_get_backlinks` não valida o path de alvo

**Severidade: P3.** Aceita entradas que as outras tools rejeitam.

**Reprodução**: `notes_get_backlinks(path="../a.md")`, `path="/etc/passwd"`,
`path=""` e `path="sub/../a.md"` são **todos aceitos** e devolvem `[]` (ou
resultados), sem erro.

**Causa-raiz.** `get_backlinks` (`notes_mcp.py:1082`) não chama
`_resolve_safe_path`; ele deriva `target_name`/`target_full` por manipulação
de string e compara contra o corpo das notas.

**Por que importa.** Não há vazamento: a tool não lê o alvo, apenas compara
nomes, e o corpus varrido é sempre o vault. Mas o comportamento diverge das
11 outras tools, que rejeitam path fora do vault. Um cliente que constrói
`get_backlinks` a partir de uma entrada não confiável obtém um "não há
backlinks" silencioso em vez de um erro, e não distingue "alvo inexistente" de
"alvo malformado".

**Correção sugerida.** Validar o path de alvo com a mesma routine das demais
tools, devolvendo erro para path fora do vault.

---

### F-10 — `notes_get_stats` infla `total_notes` com symlink interno

**Severidade: P3.** Contagem inconsistente entre tools.

**Reprodução**: vault com `a.md`, `victim.md` e `alias.md -> victim.md`:

```
notes_glob(pattern="*.md") -> ['a.md', 'victim.md']    (2 caminhos)
notes_get_stats()          -> total_notes = 3            (3 notas)
```

**Causa-raiz.** `get_stats` (`notes_mcp.py:1210`) itera `root_dir.rglob("*.md")`
e conta cada entrada, **incluindo symlinks**, enquanto `_collect_safe_matches`
(`notes_mcp.py:450`) deduplica por caminho resolvido. A mesma nota aparece uma
vez em cada contagem, mas só uma em `glob`.

Medido em vault limpo (sem as demais fixtures da bateria), com `a.md`,
`victim.md` e `alias.md -> victim.md`:

```
notes_glob(pattern="*.md") -> ['a.md', 'victim.md']    (2 caminhos)
notes_get_stats()          -> total_notes = 3            (3 notas)
```

**Por que importa.** `total_notes` é o número que o cliente usa para decidir se
o vault está vazio. Duas tools reports discordantes sobre o mesmo vault
minam a confiança em qualquer contagem. O caso é realista: alias dentro do
vault é um padrão comum para notas duplicadas ou indexação.

**Correção sugerida.** Deduplicar por caminho resolvido em `get_stats`,
alinhando com `glob` — ou resolver links e contar o destino uma única vez.
Como F-12 mostra que `glob` também precisa de decisão sobre symlinks, as duas
correções devem ser tomadas juntas para que as tools voltem a concordar.

---

### F-11 — `notes_write` sobrescreve arquivo `0444` preservando o modo read-only

**Severidade: P3.** Escrita em arquivo marcado como somente-leitura.

**Reprodução**: arquivo `0444` (owner-writablebit não, read-only) →
`notes_write` reporta `"File written: ro.md"`, o **conteúdo é substituído**, e o
modo continua `0444`.

**Causa-raiz.** `_atomic_write` cria um temporário em `0600` e faz
`os.replace` sobre o alvo. `os.replace` exige permissão de escrita no
*diretório*, não no arquivo — então a proteção `0444` do arquivo não bloqueia a
substituição. O `os.fchmod` posterior (`notes_mcp.py:556`) copia o modo `0444`
para o novo conteúdo.

**Por que importa.** O efeito é contraditório: o arquivo fica com conteúdo novo
e continua marcado como read-only, então um cliente que leia o modo para decidir
se pode editar recebe uma informação errada. Combinado com F-04 (novos
arquivos nascem `0600`), o controle de permissão por arquivo é inconsistente:
não protege contra escrita e é reportável de forma enganosa.

**Correção sugerida.** Decidir a política: ou respeitar o bit read-only como
intenção de "não sobrescrever" (erro explícito), ou deixar de reportar o modo
como se fosse uma garantia. O `README` promete que "replacement preserves
existing permission bits" — o que é verdade, e é justamente por isso que o
resultado é um arquivo read-only com conteúdo novo.

---

### F-12 — `notes_glob` devolve um caminho que não existe (symlink quebrado)

**Severidade: P3.** Um resultado de glob pode ser lido como nota válida e
existir em lugar nenhum.

**Reprodução** (vault com `real.md` e `broken.md -> nonexistent.md`):

```
notes_glob(pattern="*.md") -> ['nonexistent.md', 'real.md']
```

`'nonexistent.md'` **não existe** — nem como symlink, nem como arquivo:

```
exists on disk? False
notes_read(path="nonexistent.md") -> Error: Path not found: nonexistent.md
```

**Confirmado na imagem pinada em uso.** Com um symlink relativo quebrado
criado no vault da fixture F3 (`_broken_link.md -> _ghost_target.md`):

```
notes_glob(pattern="*.md") -> ['_ghost_target.md']
```

O `_broken_link.md` — que é o objeto que existe de fato — **não aparece** no
resultado; o que aparece é o alvo inexistente. `notes_get_stats` conta
`total_notes: 0` para o mesmo vault, e `notes_search` não encontra nada.

**Causa-raiz.** `_collect_safe_matches` (`notes_mcp.py:463`) resolve cada
candidato e converte o **resultado da resolução** em relativo:

```python
resolved = path.resolve(strict=False)
...
matches.add(_to_relative(root_dir, resolved))
```

Para um symlink quebrado, `resolve(strict=False)` devolve o caminho do alvo
(sem erro), e é esse caminho — inexistente — que entra no resultado. O symlink
em si é descartado porque o resultado é o alvo. O mesmo mecanismo explica
F-05/F-06 (o alvo real é afetado, o link não).

**Por que importa.** `notes_glob` é a tool de enumeração do vault: o cliente
usa a saída para decidir o que existe. Um caminho retornado que não existe
faz o cliente tentar ler um arquivo inexistente. E o caminho que *de fato*
existe (o symlink) fica invisível — a tool mente sobre a estrutura do vault
nas duas direções.

**Correção sugerida.** Em `_collect_safe_matches`, decidir explicitamente o que
um symlink significa para o glob: ou reportar o **link** (caminho como o
cliente o nomeia, que é o objeto real do vault), ou resolver o alvo e exigir
que ele exista (`resolved.exists()`) antes de reportar. A primeira opção é
coerente com a leitura por link; a segunda é coerente com a contagem por
alvo — mas as duas tools precisam concordar entre si (ver F-10).

---

## 3. O que não quebrou (evidência negativa)

Registrado porque é o invariante mais importante do produto.

**Contenção de path íntegra em todos os testes.** Nenhuma operação leu,
escreveu ou apagou conteúdo fora do vault:

- `notes_read`/`notes_write` em symlink para arquivo externo → `Path escapes
  root directory`.
- `notes_write`/`notes_mkdir` sob symlink para diretório externo → recusados.
- `notes_glob("outlink/*.md")` → `[]` (symlink externo ignorado).
- `notes_search` não encontra conteúdo externo por symlink.
- `notes_get_backlinks`, `notes_read_multiple` com path fora do vault →
  `outside_vault` / `[]`.

**Envelope de conteúdo não confiável preservado.** Todos os retornos de leitura
continuam com `UNTRUSTED_DATA_WARNING`, `Source:` e os marcadores
`<<<BEGIN_UNTRUSTED_NOTE_CONTENT>>>` / `<<<END_UNTRUSTED_NOTE_CONTENT>>>`.

**Regras OKF validadas.** `notes_write` recusa corretamente: `type` ausente,
`type` não-string, `type` vazio ou só-espaços, `type: null`, frontmatter que
não é mapping, YAML inválido, delimitador ausente, `log.md`/`index.md`
reservados com frontmatter, `index.md` de raiz com chave extra ou `okf_version`
não canônico.

**Busca.** Termos literais (metacaracteres de regex tratados como texto),
OR entre termos, query por lista, query vazia, CRLF no frontmatter, `İ`
(case-folding do Python vs. ripgrep), query com NUL (fallback para o walker
Python), escopo por `path`, limite de argumentos do ripgrep, arquivo
sobresizado pulado com aviso.

**Atomicidade e concorrência.** 20 escritas concorrentes no mesmo path → uma
consistência final, **sem** arquivos temporários `.notes-*` residuais. 30
escritas concorrentes em paths distintos → todas bem-sucedidas.

**Sobrevivência do processo.** Notas persistem entre reinicializações do
servidor (já coberto pelo smoke existente).

**Endurecimento preservado.** `notes_get_status` não revela path absoluto;
`notes_write` preserva o modo em substituição; symlink externo nunca é lido.

---

## 4. Achados descartados (falso positivo do harness)

Registrados para que não sejam reabertos sem evidência nova:

1. **`notes_write` rejeitando frontmatter válido** — falha do harness: em uma
   das chamadas o parâmetro chegou ao servidor com `\n` literal (barra+n) em vez
   de newline real. Reproduzido e confirmado como erro do cliente
   (`notes_write` com `---\ntype...` literal → `YAML frontmatter must have ---
   delimiters on their own lines`), e o mesmo valor com newline real é aceito.
   **Comportamento correto do servidor.**
2. **`notes_search` não encontrando termo em arquivo sem frontmatter** — o
   arquivo de teste continha "no frontmatter here" e a query procurava
   "plainmarker", que não estava no texto. Com termo correto, o arquivo **é**
   encontrado com `in_markdown=True`. **Comportamento correto.**
3. **`notes_search` com "alpha, body b"** — o termo com espaço é tratado como
   um termo só ("body b"), e o body só é buscado com `in_markdown=True`. A
   divisão por vírgula é documentada no guide. **Comportamento correto.**
4. **Duplicate paths em `notes_read_multiple`** — o dicionário `notes`
   deduplica por path, que é a semântica correta de um mapa.
5. **`notes_search` com entradas de lista não-string** — rejeitado na
   validação de schema (pydantic), antes de chegar ao handler. Correto.

---

## 5. Rastreabilidade

| Achado | Local (código) | Teste local | Imagem pinada |
|---|---|---|---|
| F-01 | `notes_mcp.py:658` (e `:322` no walker) | sim | **sim** |
| F-02 | `notes_mcp.py:497`, `:913` | sim | **sim** |
| F-03 | `notes_mcp.py:450`, `:913` | sim | **sim** |
| F-04 | `notes_mcp.py:545` | sim | **sim** |
| F-05 | `notes_mcp.py:275`, `:964` | sim | não |
| F-06 | `notes_mcp.py:275`, `:989` | sim | não |
| F-07 | `notes_mcp.py:1175` | sim | não |
| F-08 | `notes_mcp.py:386` | sim | não |
| F-09 | `notes_mcp.py:1082` | sim | não |
| F-10 | `notes_mcp.py:1210` vs `:450` | sim | não |
| F-11 | `notes_mcp.py:545`, `:556` | sim | não |
| F-12 | `notes_mcp.py:463` | sim | **sim** |

F-05 a F-11 (exceto F-12, ver adiante) foram verificados apenas localmente:
reproduzi-los na imagem pinada exigiria criar symlinks dentro do vault de
fixture, e a sessão de verificação optou por não alterar esse vault além de
notas sintéticas removidas ao final. **O código-fonte é idêntico** — a imagem
`6c1640ce…` foi construída do commit `e6a8005`, e `notes_mcp.py` não muda
desde `fbf1a29` (`git log -- notes_mcp.py`), que é anterior. A replicabilidade
na imagem está, portanto, garantida pelo código, mas não foi executada para
F-05..F-11.

**Exceção registrada:** F-12 **foi** executado na imagem pinada (symlink
relativo quebrado no vault da fixture F3, removido ao final). Para F-05/F-06 o
mesmo vetor foi usado apenas localmente, por prudência — o mecanismo de
resolução de path é idêntico e está demonstrado por F-12 na imagem.

### Ambiente

- Host: Linux x86_64, uid 1000 (`bun`), umask padrão do processo de teste.
- Python 3.12.15 (`.venv/`), ripgrep 14.1.1 no host.
- Imagem pinada: `sha256:6c1640ce8d0c823186858dcc04b7e793a997cf301ae4680f1c00d0b30cf3a7dd`,
  versão 0.1.5, usuário do container `65532:65532`, `network: none`.
- Vault da verificação: `~/.positronic-reports/f3-0-1-notes-vault-20261020T172539Z`
  (fixture do gate F3, não vault de usuário). **Restaurado ao estado original**
  ao final: todas as notas sintéticas criadas foram removidas e o diretório
  temporário de teste foi apagado.

### Limites desta bateria

- Nenhum teste Destrutivo foi executado contra vault de usuário real; apenas
  fixtures sintéticas e a fixture F3.
- Não foi exercitado o comportamento sob carga sustentada (limites de
  `max_search_files`, `max_glob_results`, `max_search_matches` e o timeout de
  20 s só foram observados emBoundary).
- Não foi exercitada a interação com Nanobot (o consumidor do contrato).
- A suíte existente (`71 passed, 7 skipped`) não cobre nenhum dos 12 achados
  acima — nenhum teste novo foi adicionado nesta etapa; a correção e a
  cobertura de regressão ficam a cargo do ciclo de remediação.
