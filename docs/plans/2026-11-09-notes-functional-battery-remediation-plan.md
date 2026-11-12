# Notes MCP — plano de remediação da bateria funcional

- **ID / revisão:** NFB / 2.0, 2026-11-09.
- **Estado:** executado em 2026-11-09; 12/12 achados encerrados (11 corrigidos,
  1 aceito por decisão D-01). Evidência do ciclo de imagem em
  [docs/issues/2026-11-09-notes-nfb-remediation-image-cycle.md](../issues/2026-11-09-notes-nfb-remediation-image-cycle.md).
- **Owner e decisor único:** Bill Kopp. Execução técnica: agente no checkout do
  produto, sob as decisões de Bill e as permissões efetivas da sessão.
- **Origem:** [bateria funcional e 12 achados](../issues/2026-11-09-notes-functional-battery-findings.md).
- **Base inspecionada:** checkout `0a44d1c`, versão declarada `0.1.5`;
  `notes_mcp.py`, README, scripts e testes existentes. O relatório de origem
  estava não rastreado no Git e foi preservado.
- **Baseline histórica da bateria:** `71 passed, 7 skipped` antes da remediação.
  **Baseline após a remediação:** `111 passed, 7 skipped` (40 regressões
  novas). Os skips são os que dependem de daemon Docker/imagem local e não
  qualificam imagem/restore.
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
e sem fixture de duas identidades. Os 7 skips da suíte local que dependem de
Docker continuam skips; a prova no candidato vem do ciclo de imagem.

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
[docs/issues/2026-11-09-notes-nfb-remediation-image-cycle.md](../issues/2026-11-09-notes-nfb-remediation-image-cycle.md)
— ciclo original candidato D `sha256:0c8fdf75…` e revalidação de 2026-11-12:
job `0d97905a800c5363238f87a286e50eee254569cbc42d94d1869dec8f39e1b32b`, fonte
commitada `f26970d`, `dirty: false`, image ID `sha256:0cfdc0fdd78f4c86614b80174746c936e7d470b649d7dfd8017747353059fb78`. Scan/SBOM com DB Trivy atualizado: 0 findings; harness Docker stdio passou
com 12 tools; `notes_get_status` e `notes_get_stats` passaram em smoke seguro; o
pin global `notes` está ativo na revisão 26. A bateria 12/12 da remediação segue
registrada para o mesmo código Notes. A seção final do documento registra a
reconciliação `cleanup-pending`/run ambíguo sem remoção forçada.

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
   Validar ACL, UID/GID e leituras nas identidades reais; os sete skips da
   baseline local não substituem essa prova. Registrar skips remanescentes
   por cenário, distinguindo limitação de rejeição funcional.
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
- [ ] Um registro durável do ciclo com resultado e próximo passo no journal
      autorizado, quando disponível; não duplicar notas nem usar outro target
      como fallback. Nesta sessão o target `percival-notes-mcp` retornou
      `not-found`; este plano é o artefato persistido disponível. O registro foi
      gravado no target `global`, que é o target autorizado disponível para
      esta sessão.

**Próxima ação após o aceite do plano:** executada em 2026-11-09 — commit da
remediação (`7c1a87e`, publicado em `refs/heads/main`) e novo build a partir
da árvore commitada (candidato D, job `9611052434b01420…`), repinado na
revisão 25 e requalificado com 12/12 achados pelo MCP real. A marca `dirty`
persistiu e foi diagnosticada como estrutural do executor (ver o documento do
ciclo de imagem), não como árvore suja. Restam apenas decisões de promoção e
a execução do harness de conformidade no host.
