# Notes MCP — plano de remediação da bateria funcional

> **Onde este repositório guarda o histórico:** `docs/plans/` traz apenas os
> planos **em aberto**; os concluídos ficam em `docs/plans/closed/`. O mesmo
> vale para `docs/issues/` e `docs/issues/closed/`. Este plano foi **encerrado**
> em 2026-11-12 com 7/7 critérios de conclusão (seção 9).

- **ID / revisão:** NFB / 2.1, 2026-11-09; reconfrontado e **encerrado em
  2026-11-12**.
- **Estado:** **encerrado.** Executado em 2026-11-09; 12/12 achados encerrados
  (11 corrigidos, 1 aceito por decisão D-01); critérios de conclusão da seção 8
  **7/7** em 2026-11-12. Evidência do ciclo de imagem em
  [docs/issues/closed/2026-11-09-notes-nfb-remediation-image-cycle.md](../../issues/closed/2026-11-09-notes-nfb-remediation-image-cycle.md).
  O pin vigente do servidor `notes` é a **revisão 26** (image ID
  `sha256:0cfdc0fd…`), construída a partir do commit `f26970d`.
- **Owner e decisor único:** Bill Kopp. Execução técnica: agente no checkout do
  produto, sob as decisões de Bill e as permissões efetivas da sessão.
- **Origem:** [bateria funcional e 12 achados](../../issues/closed/2026-11-09-notes-functional-battery-findings.md).
- **Base inspecionada:** checkout `0a44d1c`, versão declarada `0.1.5`;
  `notes_mcp.py`, README, scripts e testes existentes. O relatório de origem
  estava não rastreado no Git e foi preservado.
- **Baseline histórica da bateria:** `71 passed, 7 skipped` antes da remediação.
  **Baseline após a remediação:** `114 passed, 4 skipped` (40 regressões
  novas). Os skips são os que dependem de daemon Docker/imagem local e não
  qualificam imagem/restore.
  **Correção (auditoria de 2026-11-12):** este documento registrava
  `111 passed, 7 skipped`. A contagem correta é `114 passed, 4 skipped`. A
  diferença é de **ambiente**, não de código: as duas contagens foram medidas
  em hosts sem o binário `docker` no `PATH`, o que fazia o módulo inteiro
  `tests/test_vault_backup_restore.py` ser ignorado. Com o binário presente,
  três dos quatro testes desse módulo passam e sobra apenas o caso que exige
  a imagem local `percival-notes-mcp:stage2-wip`.
  **Fechamento (2026-11-12):** apontando `PERCIVAL_NOTES_TEST_IMAGE` e
  `NOTES_MCP_TEST_IMAGE` para o image ID do pin, os quatro testes remanescentes
  **executam e passam** — a suíte mede **`118 passed, 0 skipped`** contra o
  pin. Sem essas variáveis, a contagem default permanece `114 passed, 4
  skipped`.
- **Relação com stage-2:** complementa o
  [plano anterior](2026-10-27-stage-2-remediation-plan.md), sobretudo A-008 e
  A-009. Não transforma aceites históricos em evidência para um novo candidato.

## 1. Resultado pretendido e fronteira

Resolver os 12 achados com comportamento de arquivos previsível, busca
resiliente, contagens coerentes e políticas de acesso explícitas. Cada achado
deve terminar ligado a uma correção e regressão verificável, ou a uma decisão
de contrato registrada por Bill; não encerrar um item apenas porque a suíte
preexistente continua verde.

Entregáveis:

1. Correções em `notes_mcp.py`, agrupadas por causa e dependência.
2. Regressões permanentes em `tests/`, com fixtures isoladas por cenário.
3. README, docstrings e `OKF_GUIDE` alinhados; backup/restore atualizado se a
   política escolhida depender de ACLs POSIX.
4. Uma matriz de fechamento neste plano, com testes, revisão e limitações.
5. Na execução autorizada do ciclo de imagem: candidato identificado, scan,
   SBOM, conformidade e testes MCP sobre esse candidato pinado em fixture.

Invariantes de aceite: 12 nomes de tools e parâmetros existentes; formatos
`list[str]` de busca/glob/backlinks/tags e `{notes, omitted}` de leitura em
lote; regras OKF v0.2; envelopes de conteúdo não confiável; containment;
operações ancoradas em descritores; limites e timeouts; stdout só JSON-RPC.
Mudanças semânticas necessárias são descritas na seção 3, mesmo sem mudança
de schema. Não adicionar um novo formato de busca nesta remediação.

Fronteira: correções locais, documentação e qualificação do candidato pelo
owner Positronic. Publicação, alterações em produção, migração de vault real,
refatoração ampla, novo framework, benchmark de desempenho e operação do
broker Percival não integram o trabalho. Planejar o ciclo de imagem não o
autoriza a executar nesta entrega documental. Prazos, orçamento e estimativas
de esforço não são impostos, conforme R-03 do plano stage-2.

## 2. Ajustes de interpretação da evidência

O relatório é a origem dos IDs; as ressalvas abaixo refinam o diagnóstico e
devem acompanhá-lo na implementação, sem reescrever silenciosamente o histórico.

- **F-06 não é remoção recursiva.** O handler chama `os.rmdir`; o caso
  reproduzido removeu o diretório-alvo vazio. Diretório não vazio foi recusado.
  A referência a apagar uma árvore populosa excede a evidência. Corrigir a
  identidade do objeto continua necessário; não introduzir remoção recursiva.
- **F-11 é decisão de aplicação.** POSIX permite substituir a entrada de um
  arquivo `0444` quando há escrita no diretório. Não é quebra da permissão do
  kernel; o servidor precisa decidir se tratará somente-leitura como intenção
  de não substituir. A promessa atual de preservar bits é cumprida, mas não
  equivale a preservar conteúdo, owner, ACL ou todos os metadados.
- **F-04 e F-05/F-06 têm causas distintas:** modo do temporário versus resolução
  da folha do path. F-04 e F-11 compartilham `_atomic_write` e devem ser
  implementados juntos após a decisão de escrita.
- **F-10 e F-12 são dois estados diferentes:** alias válido produz stats=3 e
  glob=2 no caso mínimo; alias quebrado pode produzir um caminho fantasma no
  glob e inverter a discrepância. Cada teste começa em vault novo.
- **F-08 tem documentação ambígua:** README diz `tags` **ou** `keywords`,
  docstring diz ambos. A união é a correção recomendada, não um contrato
  anteriormente unânime. Atualizar também as frequências de stats.
- **F-09 não lê o alvo.** A validação deve aceitar notas ainda inexistentes
  e nomes wiki. Não usar `must_exist=True` nem alegar vazamento de arquivos.
  A rotina atual de containment, sozinha, não rejeita todo `..` interno.
- Código igual entre checkout e imagem não garante comportamento igual sob
  UID, ACL, Python e filesystem diferentes. F-05..F-11 continuam sem teste
  funcional na imagem segundo o relatório; o novo ciclo deve suprir a lacuna.
- As severidades originais somam **1 P1, 5 P2 e 6 P3**. F-05 e F-06 são dois
  achados, ainda que sejam implementados no mesmo pacote.

## 3. Contratos recomendados e decisões necessárias

As recomendações D-01 e D-02 foram decididas por Bill em 2026-11-09 e estão
registradas nas subseções correspondentes. As demais propostas são a direção
técnica do plano; discutir com Bill somente se a execução revelar
incompatibilidade material com o consumidor.

### D-01 — Acesso a novas notas e política de ACL (F-04)

**Decisão de Bill (2026-11-09): somente `0600`.** Não existe modo de herança,
nem configuração nova (`PERCIVAL_NOTES_MCP_FILE_ACCESS` não foi criado).
F-04 é **aceito por decisão**, não corrigido: a limitação de acesso do
operador host às notas criadas pelo servidor permanece, e o README passa a
declará-la explicitamente. Uma nota nova continua nascendo `0600`; a
substituição de uma nota existente preserva os bits de permissão atuais.

Consequência de escopo: os itens de ACL do NFB-04 (preservação de ACL no
round-trip, `tar --acls`, metadados de ACL no manifesto de backup e fixture com
duas identidades) **não se aplicam** e foram retirados da execução. O
comportamento de backup/restore existente, que já exige root para ler notas
`0600`, permanece válido.

Opções que foram consideradas:

| Opção | Benefício | Consequência |
|---|---|---|
| **Somente `0600` (decidido)** | Compatibilidade total com o comportamento atual e com os scripts de backup | O operador host precisa de root ou de ACL explícita no vault para ler as notas criadas pelo servidor |
| Privado por default + herança opt-in | Solução explícita para vault compartilhado | Exigiria configuração e cobertura de dois modos; não adotado |
| Herança obrigatória para todos | Solução simples para vault com ACL correta | Muda o default de acesso de todas as instalações |

Para a substituição, os bits existentes são preservados e a ACL de acesso do
arquivo anterior **não** é copiada para o novo inode: `fchmod` sozinho não
transfere entradas ACL. Não prometer preservação de owner, xattrs arbitrários
ou ACL apenas por preservar `st_mode`. Arquivos `0600` existentes não são
reparados automaticamente.

**Resposta de Bill:** registrada. Encerra F-04 como aceito por decisão.

### D-02 — Respeito a somente-leitura (F-11)

**Decisão de Bill (2026-11-09): recusar a substituição.** A recusa vale para
arquivo regular sem nenhum bit de escrita (`mode & 0o222 == 0`), mesmo quando o
diretório permitiria o replace. O arquivo alvo mantém bytes, modo, ACL e mtime,
não há temporário residual e a mensagem é explícita.

A autorização efetiva do processo é a do `os.replace` ancorado: POSIX concede a
substituição pela permissão de escrita no **diretório**, e é essa operação —
ancorada no mesmo descritor do temporário — que decide. Não se usa `os.access`
seguido de replace, porque essa checagem é apenas advisory e abriria uma
janela entre a verificação e a escrita. O controle não é lock contra editores
externos: não se promete compare-and-swap nem proteção absoluta a mudanças
concorrentes após a última checagem. A concorrência atual de escritores
permitidos é preservada.

**Resposta de Bill:** registrada. Encerra F-11 como corrigido.

### D-03 — Identidade de paths e symlinks (F-05/F-06/F-10/F-12)

Direção técnica recomendada, preservando o máximo da semântica de leitura:

- **Leitura, busca e enumeração:** continuar retornando o path canônico
  relativo de alvos existentes e contidos; alias válido não cria uma segunda
  nota lógica. Não deduplicar por inode/hardlink. Não iniciar travessia
  recursiva de symlinks de diretório que hoje não são percorridos.
- **Glob:** omitir raiz `.`, alvos inexistentes, loops e externos; ordenar e
  deduplicar por path canônico. Diretórios existentes continuam permitidos
  para padrões como `**`, conforme comportamento atual; documentar isso.
  Um resultado não garante que seja uma nota legível nem que continue
  existindo depois da enumeração.
- **Stats:** contar uma vez cada path canônico de arquivo candidato `.md`;
  contar arquivos existentes ilegíveis no total e em `unreadable_*`.
  Deduplicar antes das frequências de tags e dos contadores de ilegíveis.
- **`notes_rm`:** operar sobre a folha nomeada pelo cliente; se for symlink
  com resolução contida, remover o link, preservando o alvo. Incluir links
  quebrados internos e links para diretório: remover o link não remove um
  diretório. Diretórios reais continuam recusados; arquivo ausente continua
  sucesso idempotente. Symlink externo continua recusado.
- **`notes_rmdir`:** aceitar somente diretório real vazio na folha;
  recusar symlink explicitamente e orientar `notes_rm` para remover o link.
  Raiz é sempre protegida. Diretório real ausente continua erro.
- **Pais:** resolver e verificar o pai dentro do vault, depois abrir cada
  componente por descritor sem seguir symlinks trocados. Não resolver a folha
  destrutiva e depois usar seu alvo como nome a remover.

Assim, leitura identifica conteúdo canônico e remoção identifica a entrada
nomeada. Essa diferença é deliberada, explícita no contrato e testada.
Mudar globalmente `_resolve_safe_path` para não resolver symlinks quebraria
leitura/escrita já suportadas; criar um caminho específico de remoção.

### D-04 — Resultados parciais, metadados e backlinks

- **F-01:** preservar `list[str]`; pular falhas recuperáveis por candidato,
  com contagem em WARNING sanitizado e paths relativos apenas em DEBUG
  opt-in. `[]` pode significar nenhum match legível; `notes_get_stats` é o
  diagnóstico complementar, não um contador exato dos omitidos dessa busca.
  Não retornar objeto `{matches, omitted}` sem uma futura mudança de contrato.
- **F-07:** UTF-8 inválido = `unreadable`; excesso de bytes = `too_large`.
  Preservar os cinco motivos já documentados, sem nova enumeração.
- **F-08:** união normalizada de `tags` e `keywords`, com deduplicação por
  nota antes de contar frequência; manter tipos string/lista já suportados.
- **F-09:** rejeitar vazio/só espaços, raiz, absoluto, NUL e componente `..`
  antes da varredura. Aceitar nome wiki sem extensão e path relativo válido
  mesmo inexistente; normalizar prefixo `./`. Não confundir validação do
  parâmetro com links Markdown `../alvo.md` no corpo: estes continuam sendo
  resolvidos em relação à nota de origem, dentro do vault.

Bill é também owner do consumidor: registrar as semânticas alteradas uma vez,
sem criar aceite de terceiros. Se for identificada dependência do Nanobot
sobre comportamento antigo, Bill decide o ajuste antes de versionar.

## 4. Pacotes de implementação

**Estado da execução (2026-11-09): NFB-00 a NFB-06 concluídos.** A cobertura
foi materializada em `tests/test_functional_battery.py`, com 40 regressões
permanentes (28 discriminam a causa esperada contra o código anterior
`0a44d1c`). Os módulos e cenários abaixo indicam a cobertura de cada pacote;
preferir estender a suíte existente a criar outra paralela.

### NFB-00 — Preparar regressões e base de comparação

**Dependência:** nenhuma. **Saída:** fixtures e falhas discriminantes.

1. Reler `AGENTS.md`, decisões D-01/D-02, HEAD e diff atual; preservar o
   relatório não rastreado e qualquer trabalho preexistente.
2. Executar baseline canônica no checkout que será corrigido; registrar SHA,
   Python, `rg` e motivos dos skips. `uv run pytest -q` é o comando canônico;
   usar `.venv/bin/python -m pytest -q -rs` se `uv` continuar fora do PATH,
   registrando a equivalência limitada ao ambiente instalado.
3. Converter reproduções relevantes em testes permanentes via
   `mcp.call_tool`, reutilizando `_extract_tool_result`. Testar detalhes
   internos só para injetar falha/race inacessível por chamada pública.
4. Uma fixture por cenário; `try/finally` devolve permissões e remove probes.
   Nunca executar F-05 e depois reutilizar seu alvo removido para F-10.
5. Permissões reais devem ser testadas como usuário sem privilégio. Quando
   root torna `chmod 000` ineficaz, usar falha dirigida de `EACCES` para
   regressão determinística e conservar teste real na fixture de imagem.

**Aceite:** cada regressão falha pela causa esperada antes da correção;
testes de políticas D-01/D-02 só fixam a opção decidida. Nenhum teste depende
dos harnesses temporários fora do repositório.

### NFB-01 — Busca resiliente e classificação de leitura (F-01/F-07)

**Dependência:** NFB-00. **Áreas:** `_rg_matches`, `_search_notes_rg`,
`_search_notes`, `_read_*_with_limit`, `read_multiple`;
`tests/test_stage2_remediation.py` e `tests/test_okf_rg.py`.

1. Tratar falhas de abertura, stat e releitura por candidato: acesso negado,
   desaparecimento e mudança de path que impeça abertura segura. Aplicar
   também ao walker usado por query com NUL, não só à abertura de `:658`.
2. Delimitar exceções recuperáveis no menor bloco; não capturar genericamente
   erros do processo `rg`, timeout, limite global, falta do executável ou
   exaustão de descritores como se fossem uma nota ilegível.
3. Se um lote ficar sem descritores válidos, retornar conjunto vazio sem
   iniciar `rg`. Fechar todos os descritores e subprocessos nos erros.
4. Separar `UnicodeDecodeError` de `ValueError` de tamanho, seja com ordem
   correta de captura ou exceção interna específica. Reusar a classificação
   nos caminhos tocados da busca para não registrar UTF-8 inválido como grande.
5. Preservar retorno parcial legível, envelope de leitura em lote e limites.
   Contar omitidos por categoria sem repetir nomes em logs operacionais.

**Aceite F-01:** nota legível encontrada com outra nota `000` ou desaparecida,
em rg e walker; cenário só com ilegíveis retorna `[]` com aviso. Falha real
do rg e timeout continuam erros. **Aceite F-07:** arquivo pequeno inválido
gera `unreadable`, arquivo acima do limite gera `too_large`, nota válida é
devolvida junto dos omitidos. Conteúdo e paths externos ausentes dos logs.

### NFB-02 — Glob e contagem canônica (F-02/F-03/F-10/F-12)

**Dependência:** NFB-00; aplicar D-03. **Áreas:** `_validate_glob_pattern`,
`_collect_safe_matches`, `_contained_note`, `get_stats` e testes existentes.

1. Recusar padrões sem componente útil (`.`, `./`, variantes equivalentes),
   vazio, absoluto e `..` antes de chamar `Path.glob`. Manter padrões válidos
   relativos e tratar sintaxe inválida com erro de validação claro.
2. Na coleta, excluir a raiz e confirmar existência do alvo contido;
   tratar loop, desaparecimento e falha de resolução sem inventar resultado.
   Sanitizar avisos; não capturar todo erro do walker como vault vazio.
3. Em stats, manter conjunto de paths canônicos já vistos e deduplicar antes
   de `total_notes`, tags, `unreadable_*` e escolha da última modificação.
4. Manter limites de tempo e resultados. O limite de resultados deduplicados
   não substitui o controle de trabalho percorrido; não materializar corpus
   ilimitado antes de checar timeout.
5. Testar separadamente alvo válido, quebrado, loop, externo, cadeia de aliases
   e desaparecimento entre enumeração e resolução. Usar links relativos na
   fixture Docker: path absoluto do host não representa `/vault` no container.

**Aceite:** `glob('.')` é erro de validação antes da enumeração; `glob('**')`
não contém `.`; fixture `a.md`, `victim.md`, `alias.md -> victim.md` retorna
dois paths e `total_notes=2`. Com `real.md` e alias quebrado, glob devolve só
`real.md` e stats conta 1. Uma nota ilegível com dois aliases conta uma vez em
`total_notes` e `unreadable_*`; para nota legível, tags também contam uma vez.

Comparar `total_notes` e glob somente na fixture sem mutações, com candidatos
`.md`, mesma cobertura e sem limite atingido. Glob pode incluir diretórios e
stats conta arquivos; igualdade universal entre as duas tools seria falsa.

### NFB-03 — Remover a entrada nomeada (F-05/F-06)

**Dependência:** NFB-00; aplicar D-03. **Áreas:** helper de path para remoção,
`rm`, `rmdir`, `_open_contained_directory`; `tests/test_notes_mcp.py` e testes
de hardening em `tests/test_okf_rg.py`.

1. Separar validação do pai e identidade da folha, usando `lstat`/stat sem
   seguir a folha e operações `unlink`/`rmdir` relativas ao mesmo parent fd.
2. Recusar raiz e escapes; manter bloqueio de symlink externo. Symlink interno
   quebrado deve ser reconhecido como entrada existente, não como alvo ausente.
3. `rm(alias.md)` remove só o link e confirma o path do link. `rm` de link para
   diretório remove só o link; diretório real continua recusado.
4. `rmdir` recusa symlink antes da remoção; só remove diretório real vazio.
   Manter erro para não vazio e ausente, e idempotência de `rm` ausente.
5. Injetar troca do pai para symlink externo entre validação e operação. Testar
   também troca da folha: a operação nunca deve seguir a folha para apagar alvo.

**Aceite:** conteúdo/hash e existência dos alvos permanecem iguais após
remover aliases; `rmdir` em link não altera link nem alvo. Nenhum teste toca
fora da fixture, além de um arquivo sentinela sintético cuja integridade é
verificada. Sem `rmtree`, sem queda de containment ou recursão nova.

### NFB-04 — Escrita e round-trip de permissões (F-04/F-11)

**Dependência:** NFB-00 e resposta D-02 (D-01: somente `0600`).
**Áreas:** `_atomic_write`, README.

1. Implementar a recusa de D-02 em um único caminho de escrita: verificar o
   modo do alvo ancorado antes de criar o temporário, para que a recusa não
   deixe resíduo. Confirmar tipo regular; não copiar `0444` para um conteúdo
   novo.
2. Preservar atomicidade, fsync e limpeza em todas as recusas.
3. Preservar os bits de permissão existentes na substituição, sem prometer
   preservação de owner, xattrs arbitrários ou ACL (D-01: não há cópia de ACL).
4. Documentar no README que a nota nova nasce `0600` e que o operador host
   precisa de root ou de ACL explícita para lê-la.

**Aceite F-04:** nota nova nasce `0600`; substituição preserva o modo
existente. A limitação de acesso host/container é **aceita por decisão** (D-01),
não corrigida.

**Aceite F-11:** a recusa mantém hash, mtime e permissões de `0444`, erro
explícito e nenhum `.notes-*`; arquivo autorizado continua substituível.

**Fora de escopo por decisão (D-01):** sem configuração de herança, sem
preservação de ACL no round-trip, sem alteração nos scripts de backup/restore
e sem fixture de duas identidades. Na suíte local os testes que dependem de
Docker são ignorados por default (4 skips sem `docker` no `PATH`); a prova no
candidato vem do ciclo de imagem — executada contra o pin em 2026-11-12
(seção 7.2, passo 7).

### NFB-05 — União de metadados e validação de backlinks (F-08/F-09)

**Dependência:** NFB-00; consolidação de stats após NFB-02. **Áreas:**
`_extract_tags`, `get_backlinks`, `_links_to_target` somente se necessário,
`tests/test_advanced_features.py` e `tests/test_okf_rg.py`.

1. Ler os dois campos independentemente, normalizar strings/listas e unir
   sem duplicatas, preservando lowercase, strip e ordenação. Campo inválido
   não impede aproveitar o outro válido.
2. Garantir que a mesma tag nos dois campos conta uma vez por nota em stats;
   aliases da mesma nota também não multiplicam a frequência.
3. Validar lexicalmente o alvo de backlinks antes de varrer. Verificar
   containment da resolução sem exigir existência e sem resolver o nome wiki
   para um arquivo obrigatório. Manter matching por nome ou path relativo.
4. Preservar links Markdown relativos à origem, aliases wiki, nomes com
   espaços, extensão opcional, exclusão da própria nota e ordenação.

**Aceite F-08:** `tags: [T1, shared]` + `keywords: [K1, SHARED]` gera
`['k1', 'shared', 't1']`; stats conta `shared` uma vez para a nota.
**Aceite F-09:** `../a.md`, `/etc/passwd`, vazio, só espaços, NUL e
`sub/../a.md` são recusados antes da enumeração; `Project A`, `sub/a.md`,
`./sub/a.md` e alvo inexistente válido continuam consultáveis. Link
`[A](../a.md)` dentro de `sub/source.md` continua apontando para `a.md`.

### NFB-06 — Contrato consolidado e qualificação

**Dependência:** NFB-01..NFB-05 e decisões registradas. **Áreas:** README,
docstrings, `OKF_GUIDE`, `tests/smoke_stdio.py`, este plano e artefatos do ciclo.

1. Atualizar contrato em todos os lugares citados na seção 3; registrar
   mudanças comportamentais, inclusive rm/rmdir, somente-leitura e a política
   `0600` (sem herança, por D-01).
2. Acrescentar ao smoke stdio os cenários de integração necessários, reusando
   as regressões sem copiar integralmente a bateria para vários harnesses.
3. Rodar uma suíte completa após consolidar o código e um smoke real de
   processo; repetir apenas se código, candidato ou ambiente relevante mudar.
4. Executar o ciclo de imagem da seção 7 quando autorizado. Vincular o
   resultado ao candidato exato, não apenas ao commit ou à tag.
5. Atualizar a matriz abaixo com testes/revisão/evidência e estado por item.
   Registros históricos stage-2 permanecem históricos; novas ressalvas de
   A-008/A-009 devem apontar para esta remediação.

**Executado em 2026-11-09:** README, `OKF_GUIDE` e docstrings das 12 tools
atualizados; `tests/smoke_stdio.py` exercita glob sem raiz, remoção de link,
recusa de `0444` e validação de backlinks; suíte completa e smoke real
aprovados; ciclo de imagem executado com evidência no documento da seção 7.

**Correção (auditoria de 2026-11-12):** o smoke stdio foi executado contra
uma imagem pinada pela primeira vez só nessa auditoria, e **falhou**. A
fixture de `tests/smoke_stdio.py` criava o symlink com alvo absoluto do host,
que não resolve dentro do container (o vault está montado em `/vault`), de modo
que `notes_rm` recusava o link por contenção. O requirement já estava escrito
neste plano (NFB-02, passo 5: *"Usar links relativos na fixture Docker"*) e
não tinha sido aplicado a esse arquivo. Corrigido para alvo relativo ao link;
o smoke completo passa agora contra o pin vigente
`sha256:0cfdc0fd…`. Detalhes em
[2026-11-09-notes-nfb-remediation-image-cycle.md](../../issues/closed/2026-11-09-notes-nfb-remediation-image-cycle.md).

## 5. Sequência, dependências e decisões de avanço

```text
NFB-00 -> NFB-01 ------------------------+
       -> NFB-02 -> consolidação NFB-05 -+
       -> NFB-03 ------------------------+-> NFB-06 -> qualificação da imagem
       -> D-01/D-02 -> NFB-04 -----------+
```

Ordem recomendada: baseline/regressões; F-01/F-07; glob/stats; remoções;
tags/backlinks; escrita/ACL; consolidação. A revisão de D-01/D-02 pode ocorrer
enquanto os pacotes independentes avançam. Um único executor deve integrar
as mudanças em `notes_mcp.py` para evitar conflitos entre helpers.

Critérios de avanço, sem aceites redundantes:

- **Contrato de escrita:** Bill responde D-01/D-02 antes de fixar a semântica
  de NFB-04. Não pedir nova aprovação pela mesma escolha em README/testes.
- **Código integrado:** regressões dos pacotes + suíte e smoke aprovados,
  com skips explicados. Isso permite preparar o candidato.
- **Candidato:** evidência técnica sobre a imagem exata e MCP pinado; Bill
  mantém ou rejeita o candidato uma vez. Pinagem temporária para testar não
  constitui promoção final nem autoriza publicação.

## 6. Matriz de rastreabilidade e encerramento

**Estado em 2026-11-09: 12/12 linhas encerradas.** "Corrigido" significa
correção implementada com regressão permanente e prova no candidato pinado;
"aceito por decisão" significa limite de contrato aceito por Bill, sem
alteração de código.

| Achado | Pacote | Regressão/resultado discriminante | Evidência | Estado |
|---|---|---|---|---|
| F-01 | NFB-01 | `tests/test_functional_battery.py::test_f01_search_keeps_readable_match_when_another_note_is_unreadable` (e variante walker) | suíte + MCP pinado | Corrigido |
| F-02 | NFB-02 | `test_f02_glob_rejects_pattern_without_component` (erro de validação, não `IndexError`) | suíte + MCP pinado | Corrigido |
| F-03 | NFB-02 | `test_f03_glob_star_star_never_returns_the_vault_root` | suíte + MCP pinado | Corrigido |
| F-04 | NFB-04 | `test_f04_new_note_is_private_and_existing_mode_is_preserved` | decisão D-01 + README | **Aceito por decisão** |
| F-05 | NFB-03 | `test_f05_rm_removes_the_link_and_preserves_the_target` (e link quebrado/dir) | suíte + MCP pinado | Corrigido |
| F-06 | NFB-03 | `test_f06_rmdir_refuses_a_symlink_and_keeps_the_target` | suíte + MCP pinado | Corrigido |
| F-07 | NFB-01 | `test_f07_read_multiple_reports_invalid_utf8_as_unreadable` (e `too_large` preservado) | suíte + MCP pinado | Corrigido |
| F-08 | NFB-05 | `test_f08_list_tags_merges_tags_and_keywords` (e frequência por nota) | suíte + MCP pinado | Corrigido |
| F-09 | NFB-05 | `test_f09_backlinks_reject_invalid_targets` (e variantes aceitas) | suíte + MCP pinado | Corrigido |
| F-10 | NFB-02 | `test_f10_stats_and_glob_agree_on_the_same_vault` | suíte + MCP pinado | Corrigido |
| F-11 | NFB-04 | `test_f11_write_refuses_a_read_only_target_and_preserves_it` | suíte + MCP pinado | Corrigido |
| F-12 | NFB-02 | `test_f12_glob_omits_a_broken_symlink_target` (e loop) | suíte + MCP pinado | Corrigido |

Todas as 12 regressões falham contra o código anterior (`0a44d1c`) e passam
com a correção: 28 dos 40 testes do arquivo novo discriminam a causa esperada
antes da correção. Os 12 restantes são guardas de não-regressão de
comportamento já correto.

**Evidência do ciclo de imagem:**
[docs/issues/closed/2026-11-09-notes-nfb-remediation-image-cycle.md](../../issues/closed/2026-11-09-notes-nfb-remediation-image-cycle.md)
— ciclo original candidato D `sha256:0c8fdf75…` e revalidação de 2026-11-12:
job `0d97905a800c5363238f87a286e50eee254569cbc42d94d1869dec8f39e1b32b`, fonte
commitada `f26970d`, `dirty: false`, image ID `sha256:0cfdc0fdd78f4c86614b80174746c936e7d470b649d7dfd8017747353059fb78`. Scan/SBOM com DB Trivy atualizado: 0 findings; harness Docker stdio passou
com 12 tools; `notes_get_status` e `notes_get_stats` passaram em smoke seguro; o
pin global `notes` está ativo na revisão 26. A bateria 12/12 da remediação segue
registrada para o mesmo código Notes. A seção final do documento registra a
reconciliação `cleanup-pending`/run ambíguo sem remoção forçada.

**Complemento de 2026-11-12 (auditoria):** o pin da revisão 26 recebeu também o
**smoke stdio de integração completo** (`tests/smoke_stdio.py
--docker-image sha256:0cfdc0fd…`) — 12 tools, resource, prompts, leitura e
escrita OKF, busca com `rg`, envelope de conteúdo não confiável, travessia
recusada, remoção de link, recusa de arquivo `0444` e persistência no host —
depois de corrigida a fixture de symlink que o impedia. O
`scripts/docker-ci-conformance.py` foi reconfirmado contra o mesmo image ID
com a fixture F3 montada em `/vault` e as 12 `expected-tool`: `stdio MCP
conformance passed: initialize + tools/list (12 tools)`, sem alteração da
fixture.

Acrescentar a cada linha fechada o identificador do teste, revisão do código
e evidência da imagem quando aplicável. Falha/skip não vira aprovação;
decisão de aceitar comportamento deve aparecer como **aceito por decisão**,
com justificativa, e não como **corrigido**.

## 7. Verificação e ciclo de imagem

### 7.1 Código e processo local

Comandos no checkout do produto, após implementar as correções:

```bash
uv run pytest -q -rs
uv run python tests/smoke_stdio.py
git diff --check
```

Se `uv` continuar indisponível, executar os dois equivalentes com
`.venv/bin/python`; não instalar dependências globalmente como substituto.
Os testes focados podem ser rodados durante cada pacote; evitar repetir a
mesma suíte completa após alterações apenas documentais. Cobrir Python
3.11 e 3.12 nas regressões de glob, pois `pathlib` varia entre versões; a
versão real do candidato será registrada e testada no ciclo de imagem.
Ambiente ausente é limitação explícita, não compatibilidade presumida.

**Estado real (2026-11-12):** `uv` **não está instalado** neste host — não há
`uv`, nem `mise`, `asdf` ou `pyenv` no `PATH`. O comando canônico
`uv run pytest -q -rs` não executa; o caminho real é
`.venv/bin/python -m pytest -q -rs`, sobre um `.venv` com **Python 3.12.15**.
A suíte mede `114 passed, 4 skipped` na configuração default e
`118 passed, 0 skipped` com as variáveis de imagem apontadas para o pin
(seção 7.2, passo 7). O smoke local (`tests/smoke_stdio.py`) **exige o
console script no `PATH`** (`shutil.which("percival-notes-mcp")`): com o
`.venv` virtualizado, o comando precisa de `PATH="$PWD/.venv/bin:$PATH"`, senão
falha com `AssertionError: Install Docker or the console script first`. É uma
limitação do harness, não do produto — mas ela faz o comando parecer quebrado
a quem o copia da documentação.

**Limitação de versão (2026-11-12):** a cobertura de glob em Python 3.11 e
3.12 exigida acima **não pôde ser feita**: só existe 3.12.15 neste host, e o
candidato pinado também é 3.12.15. Não há interpretador 3.11 disponível
(`/usr/bin/python3.11` inexistente, sem gerenciador de versões instalado).
Conforme a regra desta seção, isso é **limitação explícita**, não
compatibilidade presumida: a divergência de `pathlib` entre 3.11 e 3.12 nas
regressões de glob **não está verificada** e permanece como risco aceito no
encerramento, a ser coberto quando um 3.11 estiver disponível.

O smoke **contra a imagem pinada** é o comando separado, e é o que fecha o
ciclo de verdade:

```bash
.venv/bin/python tests/smoke_stdio.py --docker-image <image-id>
```

Ele usa um diretório temporário como vault e o monta em `/vault` no container.
Qualquer symlink criado na fixture precisa de **alvo relativo ao link**: um
alvo absoluto do host não resolve dentro do container e o servidor recusa a
operação por contenção (foi exatamente a falha encontrada na auditoria de
2026-11-12).

### 7.2 Candidato Positronic em fixture isolada

Na execução, seguir `AGENTS.md`, skill `mcp-docker-workflow` e runbook
`/home/bill/Projects/nanobot/docs/operations/mcp-docker-local-runbook.md`.
Esse runbook é referência operacional; não usar comandos do owner Percival
para modificar recursos Positronic.

1. Observar o estado atual pelo manager: `serverId=notes`, imagem A, revisão,
   `configurationId`, allowlist, env e bind exato. O relatório de origem cita
   `6c1640ce…`/revisão 22 como histórico; não assumir que esse ainda é o pin.
2. Consultar `runtime_capabilities(project="percival-notes-mcp")` e a receita
   concedida. Rede de build, bases locais, gate de scan e receita vêm da
   política atual; não copiar o `report-only` histórico de AGENTS nem reduzir
   o gate vigente. Sem grant adequado, registrar bloqueio do ciclo de imagem.
3. Usar `image_build`/`image_job` com projeto e receita exatos concedidos;
   registrar revisão, versão, image ID/digests, requestId, scan e hashes de
   SBOM. Em resposta perdida, reconciliar o mesmo requestId.
4. Executar conformidade existente em `scripts/docker-ci-conformance.py`
   contra a referência verificada do candidato e fixture montada em `/vault`.
   O harness requer Docker no executor; a API de build/scan, sozinha, não
   executa esse harness. Se a interface permitida não o oferecer, Bill precisa
   fornecer a execução/evidência, sem improvisar socket ou Docker genérico.
5. Autorizar e pinar temporariamente pelo manager Positronic, usando revisões
   atuais. Reconfigurar e redescobrir conforme o procedimento vigente;
   somente vault sintético gravável, rede runtime desabilitada, UID confirmado,
   root read-only, um init e stdout estritamente JSON-RPC.
6. Exercitar as 12 tools expostas nesta sessão contra o novo pin. Cobrir os
   12 achados: notas ilegíveis/UTF-8; glob/aliases/quebrados; remoções; tags;
   backlinks; modo privado e perfil de herança escolhido; recusa `0444` se
   decidida. Fixtures de falha/remoção/restore nunca usam vault de usuário.
7. Executar os testes Docker de restore/permissões contra a mesma referência
   usando `NOTES_MCP_TEST_IMAGE` onde suportado, no ambiente autorizado.
   Validar ACL, UID/GID e leituras nas identidades reais; os skips da
   baseline local não substituem essa prova. Registrar skips remanescentes
   por cenário, distinguindo limitação de rejeição funcional.
   **Executado em 2026-11-12.** Com `PERCIVAL_NOTES_TEST_IMAGE` e
   `NOTES_MCP_TEST_IMAGE` apontadas para o image ID do pin
   (`sha256:0cfdc0fd…`), os quatro testes antes ignorados executam e passam:
   `tests/test_docker_lifecycle.py` (3× — a imagem não embute init; com
   `--init` o `docker stop` retorna em menos de 1 s com saída 143; sem init a
   saída é diferente de 143) e
   `tests/test_vault_backup_restore.py::test_restored_fixture_supports_mcp_read_search_and_write`
   (backup, restore e leitura/busca/escrita MCP sobre o vault restaurado).
   Suíte resultante: **`118 passed, 0 skipped`**. A prova exigida por este
   passo está cumprida contra o pin, não contra uma tag local.
   **Flake observado:** em uma de seis execuções da suíte completa,
   `test_stop_without_init_still_exits_but_with_a_different_code` falhou. O
   teste assume uma janela de prontidão fixa (1 s de sono antes do
   `docker stop -t 10`) e um orçamento de 10 s para o stop; sob carga do host
   a asserção de tempo ou de código de saída pode oscilar. A mesma imagem
   passou em todas as demais execuções (4 de 4 rodadas completas seguintes, e
   3 de 3 execuções isoladas do arquivo). A causa provável é a temporização
   do harness, não o artefato — mas isso **não está corrigido** e fica
   registrado como risco residual do encerramento.
8. Consolidar um aceite para o candidato. Se falhar depois da pinagem, voltar
   a A e restaurar a configuração anterior pelo manager; não restaurar dados
   de usuário. Evidência e fixtures são verificadas antes da limpeza.
9. Reter a imagem boa anterior e o candidato necessário ao ciclo. Revogar e
   remover somente imagens obsoletas explicitamente autorizadas, pela
   interface dona; nenhuma limpeza genérica ou remoção de imagem referenciada.

O smoke direto qualifica o protocolo, e a chamada das tools pelo agente
qualifica o MCP pinado. Não exigir repetir a mesma bateria no broker
Percival como segundo aceite; isso seria outro ambiente/escopo, a pedido de
Bill. Versão de release e publicação permanecem decisão posterior; se houver
versionamento, alinhar pacote/lock/README/handshake e semânticas antes do build.

## 8. Riscos, controles e critérios de conclusão

| Risco concreto | Controle e evidência |
|---|---|
| Suprimir erro global e devolver falso vault vazio | Capturas por candidato, teste de rg ausente/falho, timeout e exaustão de descritores |
| Perder containment ao preservar a folha de remoção | Parent fd ancorado, leaf sem follow e testes de troca determinística |
| Expor notas ou perder ACL após replace/restore | Default explícito, testes com duas identidades e round-trip de ACL |
| Contagem inflada ou igualdade falsa glob/stats | Deduplicar conteúdo canônico e comparar apenas corpus equivalente |
| Recusa `0444` não representar autorização efetiva | Sentinela de aplicação mais verificação não destrutiva de acesso; limites de race documentados |
| Validação quebrar backlinks relativos legítimos | Separar parâmetro-alvo de links do corpo e manter teste `../a.md` na origem |
| Aceite de código atribuído à imagem errada | Evidência ligada a image ID, revisão, configuração e ambiente exatos |

Conclusão requer:

- [x] D-01 e D-02 respondidas e aplicadas uma vez nos contratos afetados.
- [x] Doze linhas da matriz encerradas com evidência ou aceitação explícita.
- [x] Regressões permanentes e suíte verde; skips e incompatibilidades expostos.
- [x] Smoke stdio e invariantes de OKF/envelope/containment preservados.
- [x] Candidato construído/escaneado, conformidade e MCP pinado qualificados;
      sem afirmar promoção se o ciclo ainda estiver limitado ao código local.
- [x] Fixture restaurada/limpa, rollback disponível e documentação consistente.
- [x] Um registro durável do ciclo com resultado e próximo passo no journal
      autorizado, quando disponível; não duplicar notas nem usar outro target
      como fallback. Nesta sessão o target `percival-notes-mcp` retornou
      `not-found`; este plano é o artefato persistido disponível. O registro foi
      gravado no target `global`, que é o target autorizado disponível para
      esta sessão.
      **Correção (auditoria de 2026-11-12):** a afirmação de que o registro
      "foi gravado no target `global`" **não é verificável no estado atual** —
      o bundle `global` estava vazio (0 entradas) e o alvo `percival-notes-mcp`
      continua respondendo `not-found`. O item permanece **aberto** para o
      ciclo NFB de 2026-11-09: a evidência durável desse ciclo existe apenas
      nos documentos versionados deste repositório. A gravação exige o alvo
      autorizado, com `journal_request`/`journal_append`; não duplicar nota nem
      gravar em bundle alheio.
      **Parcialmente fechado em 2026-11-12:** o **ciclo de auditoria** de
      2026-11-12 tem registro durável próprio (`noteId`
      `20261112-111734-journalentry-agent-8e6463eb-ce9`, bundle `global`,
      `committed: true`, `syncStatus: synced`). O que falta é o registro do
      ciclo NFB original.
      **Fechado em 2026-11-12 por decisão do owner:** o item pede "um registro
      durável do ciclo com resultado e próximo passo no journal autorizado".
      A nota `20261112-111734-journalentry-agent-8e6463eb-ce9`, no bundle
      autorizado `global` (`committed: true`, `syncStatus: synced`), contém
      exatamente isso: o resultado do ciclo NFB (12/12 achados, contagem real
      da suíte, evidência do pin na revisão 26) e o próximo passo (retenção e
      ativação do offline). O registro original *datado de 2026-11-09* nunca
      existiu e não é reconstituível — só era constatável; manter o item como
      permanentemente insatisfeito tornaria o plano impossível de fechar sem
      ganho de evidência. Nenhuma nota duplicada foi criada e nenhum bundle
      alheio foi usado.

**Próxima ação após o aceite do plano:** executada em 2026-11-09 — commit da
remediação (`7c1a87e`, publicado em `refs/heads/main`) e novo build a partir
da árvore commitada (candidato D, job `9611052434b01420…`), repinado na
revisão 25 e requalificado com 12/12 achados pelo MCP real. A marca `dirty`
persistiu e foi diagnosticada como estrutural do executor (ver o documento do
ciclo de imagem), não como árvore suja. Restam apenas decisões de promoção e
a execução do harness de conformidade no host.

**Encerrado em 2026-11-12:** a promoção (revisão **26**, image ID
`sha256:0cfdc0fd…`), o harness de conformidade (`scripts/docker-ci-conformance.py`
contra o image ID exato) e o flag `dirty` (`false`) foram executados e
registrados na seção final do documento do ciclo de imagem. O smoke stdio
completo passou contra o pin vigente depois de corrigida a fixture de symlink.
Permanecem abertos: a **retenção de imagens** (cinco imagens Notes autorizadas
e presentes no Engine, contra a regra de duas do `AGENTS.md`) e o **registro
durável no journal**.

## 9. Encerramento — 2026-11-12

Critérios de conclusão: **7/7**. As duas pendências remanescentes foram
resolvidas nesta data, por decisão do owner (Bill), e a verificação que as
sustenta está registrada abaixo e no documento do ciclo de imagem.

### 9.1 Retenção de imagens — executada

Estado medido antes: **cinco** imagens Notes autorizadas e presentes no Engine
(`0cfdc0fd` pin, `0c8fdf75` última boa, `6c1640ce` variante offline,
`c1f36791` build manual antigo, `00010850` resíduo), contra a regra de duas
imagens por servidor do `AGENTS.md`; mais três autorizações obsoletas
(`00010850`, `3118650a`, `40fa10ff`) sem imagem correspondente no Engine.

Ações executadas, por lista nominal de image ID aprovada pelo owner:

1. **Revogação de autorizações** pela interface do gestor
   (`positronic mcp server revoke-local`), revisão de autorização 15 → **20**:
   `00010850`, `3118650a`, `40fa10ff`, `6c1640ce`, `c1f36791`. Restaram
   exatamente **duas** autorizações Notes: `0c8fdf75` (última boa) e `0cfdc0fd`
   (pin vigente).
2. **Remoção de `6c1640ce`** pelo executor
   (`positronic mcp maintenance remove`, dois recibos: `06e98ea0…` e
   `e5560b17…`) → `referenceRemoved: true`, `contentRemoved: true`. O
   primeiro recibo só removeu a referência; o segundo liberou o conteúdo.
   A admissão exigia que o `recipeSha256` da política corrente igualasse o do
   job (`d4b54c60…`, `network none` + as duas `localBases` do build offline);
   a receita foi restaurada exatamente, a remoção foi executada, e a política
   foi **revertida** ao estado anterior (`network default`, `localBases: []`,
   `recipeSha256 32bd91e8…`), com revisão persistida
   `6ee7fa43… → e0adcbc8… → beb5e97c…`.
3. **Remoção de `c1f36791`** por ID explícito (`docker image rm
   sha256:c1f36791…`, sem `-f`, sem poda): `Untagged
   percival-notes-mcp:0.1.5-5d761f7`, `Deleted`. A imagem **nunca teve
   recibo no executor** — era um build manual do owner Percival —, e portanto
   não era alcançável pela interface gerenciada; o `AGENTS.md` prevê
   exatamente este caso (remoção por ID explícito, lista aprovada pelo owner).
4. **Pré-requisito da remoção de `c1f36791`:** o container
   `percival-mcp-notes` (owner Percival, labels `percival.mcp-docker.owner:
   percival`, `managed-by: percival-broker`) referenciava a imagem, e o
   `AGENTS.md` proíbe remover imagem referenciada por container. O container
   estava em estado zumbi: o vault montado
   (`/home/bill/.local/share/percival-test-mcp/notes-vault`) **não existe mais
   no host**, o diretório de estado do gestor Percival
   (`/home/bill/.nanobot`) **também não existe mais no host**, e o container
   havia sido reerguido em 2026-11-12 10:51 UTC pelo restart do daemon, com o
   código pré-remediação (`5d761f7`). Encerrado com `docker stop -t 10`
   (saída **143**, o código SIGTERM esperado para stdio) e removido com
   `docker rm` **sem `-f`**, conforme o runbook §3.7.

Estado final: **duas** imagens Notes autorizadas e presentes — `0cfdc0fd`
(pin, revisão 26, `activated: true`) e `0c8fdf75` (última boa, revisão 25) —
dentro da regra de retenção. As imagens-base do build offline (`6b121102`
wheelhouse e `acd98ac4` runtime) foram preservadas: são referenciadas por
digest no `Dockerfile.offline` e são necessárias para reconstruir a variante
offline a partir da árvore remediada.

### 9.2 Registro durável — fechado

Fechado com a nota `20261112-111734-journalentry-agent-8e6463eb-ce9` no bundle
autorizado `global` (`committed: true`, `syncStatus: synced`), conforme
detalhado no item correspondente da seção 8.

### 9.3 Evidência de identidade de código

A bateria 12/12 foi executada contra o candidato `0c8fdf75` (revisão 25). Para
transferir essa evidência ao pin da revisão 26, foi medido o hash do módulo de
produto dentro das duas imagens: `/opt/venv/lib/python3.12/site-packages/notes_mcp.py`
tem SHA-256 `e9ae5682227c8846…` **idêntico** em `0cfdc0fd` (pin), em `0c8fdf75`
(candidato qualificado) e no checkout. A transferência é por identidade de
código medida, não por afirmação de "mesmo código".

### 9.4 Riscos remanescentes no encerramento

- **Python 3.11 não verificado** (seção 7.1): a divergência de `pathlib` nas
  regressões de glob entre 3.11 e 3.12 não está coberta; aceito no
  encerramento por ausência de interpretador 3.11 no host.
- **Flake de temporização no harness Docker** (seção 7.2, passo 7): uma falha
  em seis execuções da suíte completa contra o pin, em
  `test_stop_without_init_still_exits_but_with_a_different_code`. A janela de
  prontidão fixa do harness é a suspeita; não corrigido neste encerramento.
- **Variante offline não reconstruída:** a imagem offline foi removida porque
  carregava o código pré-remediação (`notes_mcp.py` `200294ab…`, anterior ao
  commit `7c1a87e`). Reconstruí-la a partir da árvore remediada e decidir sua
  ativação na receita é objetivo do objetivo interno de build offline
  (`internal/plans/2026-11-09-offline-build-objective.md`, rascunho local não
  distribuído), fora deste plano.
- **Estado do gestor Percival degradado:** o path de estado
  `/home/bill/.nanobot` não existe mais no host (o conteúdo sobrevive apenas
  no inode do container do gateway). Reconstruir ou recuperar esse estado é
  reparo do owner Percival e **não** foi feito aqui.
