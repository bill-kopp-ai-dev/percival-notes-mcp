# Stage-2 — Remediação do Percival Notes MCP

**Data / revisão:** 2026-10-27 / 1.0.  
**ID / estado:** S2-NT / planejado; execução não iniciada.  
**Checkout executor:** `/home/bill/Projects/percival-notes-mcp`.  
**Responsável:** executor Notes a designar por bill; operação do vault/gestores com seus donos.

## 1. Objetivo, fontes e fronteira

Tratar os 16 achados da **seção 6** do
[relatório Notes](../../../positronic-bean-IaC/docs/reports/2026-10-27-percival-notes-mcp-iac-readiness-report.md#6-achados-issues-e-inconsistências),
com seções 7/9 como complemento: 12 ações (2 P1, 6 P2, 4 P3), sem P0.
Snapshot/HEAD na emissão: `83980418b3239be5476f6d347ceb8dad32d90e8e`.
Exclusões locais preexistentes da nota F3 e `docs/search-benchmark.md` preservadas.

[Coordenador stage-2](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md)
— retorno S2-NT, seções 3 e 7. Referências:
[consolidação](../../../positronic-bean-IaC/docs/reports/2026-10-26-stage-1-consolidated-readiness-report.md)
e [D-01..D-06](../../../positronic-bean-IaC/docs/decisions/2026-10-27-iac-stage-1-scope-and-pilot-decisions.md).

Emissão documental; execução técnica futura somente no checkout dono. Notes é o
servidor do par piloto Percival + Notes (D-01). A seleção não homologa a imagem em
uso nem autoriza mexer no vault do operador. Preservar contrato das tools, OKF,
busca ripgrep/fallback, containment e envelopes de conteúdo não confiável.

## 2. Preparação e decisões

- [ ] Ler instruções/README/contrato de vault; registrar SHA/worktree e reconciliar
  documentos localmente excluídos com o owner sem restaurá-los implicitamente.
- [ ] Criar somente fixtures sintéticas para falhas, restore, permissões e symlinks;
  registrar UID/GID efetivos, manifestos de conteúdo e caminhos de teste.
- [ ] Owner define retenção/restore do vault; gestores definem candidato/runtime.
  S2-C01 fixa init/perfil/mount; S2-C03 metadados/scan, S2-C04 harness.
- [ ] Dimensionar lotes com bill (D-06). Broker só após `nanobot/A-001` fechado;
  plano operacional do piloto aguarda D-05. Nenhum vault real no piloto deste plano.

## 3. Backlog integral e aceite

Todas as ações **não iniciadas**; parcelas de runtime/CI permanecem externas.

| Ação | Achados / P | Trabalho e áreas previstas | Dependência / dono externo | Aceite verificável |
|---|---|---|---|---|
| A-001 | F-001 / P1 | Tornar busca resiliente a symlink externo nos caminhos ripgrep e fallback em `notes_mcp.py` | Sem dependência externa | Arquivo fora do vault ignorado com aviso sanitizado; notas válidas encontradas; nenhum conteúdo/path externo exposto; testar ambos os caminhos |
| A-002 | F-002 / P1 | Publicar backup/restore preservando owner numérico/permissões e exigindo leitura após restore | Decisão do owner sobre cópias/retenção | Restore em fixture com manifesto SHA-256 igual, UID/GID compatíveis (baseline UID 65532, confirmar candidato), leitura/busca/escrita funcionais; negativo de owner errado explícito |
| A-003 | F-003 / P2 | Produzir candidato rastreável, solicitar repin e hardening do runtime ao dono | S2-AP-X01 e S2-NB A-007; etapa 2 IaC | Image ID/revision efetivos do candidato aprovado, cap-drop ALL/NNP/RO conforme perfil; vault correto identificado; operação real só com owner e rollback |
| A-004 | F-004 / P2 | Declarar init único requerido ou embutir init com decisão compatível; registrar contrato de implantação | S2-C01 e donos dos launchers | `docker stop` em menos de 1 s no perfil piloto/fixture homologada; sem init duplo; ausência de init recusada/documentada conforme decisão |
| A-005 | F-005 / P2 | Normalizar build ou declarar/medir limitação de reprodutibilidade com decisão do owner | Entradas/builder identificados; etapa 2 IaC | Dois builds sem cache com image ID igual, ou limitação aceita e diferenças medidas conforme aceite original; pin sempre do artefato efetivamente validado |
| A-006 | F-006 / P2 | Solicitar investigação da saída 255 e reconciliação saved/observed no broker | S2-NB A-007/A-012; acesso de owner ao log | Causa discriminada/registrada; inventário e observação atual coerentes; sob-demanda parado não implica falha; não editar state manualmente |
| A-007 | F-007 / P2 | Atualizar nota de segurança no destino acordado e rescan/decisão VEX do candidato | Owner; CI/etapa 2 IaC | Scan com DB/data/image ID atual; estado F3 correto; decisão sobre necessidade de VEX por CVE, sem inventar finding quando scan limpo |
| A-008 | F-008, F-015 / P2 | Expor leituras parciais em stats/read_multiple com motivo de omitidos, sem vazamento de path externo | Compatibilidade do contrato de resposta com consumidores | Fixture com arquivo ilegível distinguida de vault vazio; notas lidas preservadas, omitidos/motivos explícitos; envelope e controle de path mantidos |
| A-009 | F-009 / P3 | Validar glob antes da enumeração e sanitizar aviso | Sem dependência externa | `../../*` e padrão absoluto recusados antes de varrer; sem resultado espúrio `.` nem caminhos externos nos logs |
| A-010 | F-010, F-011 / P3 | Remover raiz interna do status e retirar paths de notas de INFO | Política de privacidade do produto | Status sem path absoluto; logs operacionais sem nome/caminho sensível; DEBUG privado apenas se explicitamente configurado |
| A-011 | F-012, F-013 / P3 | Tolerar quebra final/CRLF no frontmatter e derivar versão do pacote no serverInfo | Contrato OKF preservado | Frontmatter válido aceito e persistido corretamente; initialize informa versão do produto (0.1.5 só se vigente), não do SDK |
| A-012 | F-014, F-016 / P3 | Corrigir README do ripgrep/restore e remover apt/setuid residuais não usados | A-002; compatibilidade da imagem | Docs conferem com versão embarcada; inventário limpo sem eliminar dependência necessária; smoke/protocolo/busca permanecem verdes |

### 3.1. Complemento de distribuição não detalhado nas A-* originais

| ID | Origem | Entrega / aceite |
|---|---|---|
| S2-NT-X01 | DIST-02 e seção 8 do relatório; X-04/C-09 | Preparar manifesto/server.json aplicável e instruções versionadas conforme S2-C03; schema válido, produto/versão/transporte/permissões/imagem coerentes; referência OCI real apenas após publicação nas etapas 2/4 |

Esse complemento não aumenta as 12 ações de origem. Registro de image ID local
não é digest de manifesto de registry; não preencher metadados com imagem pública
ou digest fictícios. Não há rede/provedor necessário para o teste funcional local.

## 4. Sequência e dependências

1. **NT-1:** A-001/A-002; A-003 prepara candidato e solicitação de owner em
   paralelo. A-001/A-002 são condições antes de piloto com vault real; os ensaios
   deste plano usam sempre fixture sintética.
2. **NT-2:** A-008/A-009/A-010/A-011; A-004 com S2-C01; A-012 após o runbook
   de restore. Mudanças na forma de resposta devem ser coordenadas com clientes.
3. **NT-3:** A-005/A-007, S2-NT-X01 e recebimento de A-003/A-006 pelos gestores.
   Versionar/adotar harness com S2-C04; qualificação remota/publicação separadas.

Riscos: skip silencioso pode ocultar falha, nova resposta parcial pode quebrar
cliente, restore com UID errado pode parecer perda de tags. Proteger com casos
positivos/negativos e manifesto de conteúdo; não fazer chown/cópia no vault real.
Sem prazo/horas/custo presumidos.

## 5. Qualificação futura no projeto

- [ ] `uv run pytest -q`, regressões significativas e checks locais existentes;
  não introduzir lint/cobertura como requisito novo sem decisão do produto.
- [ ] Build identificado e smoke MCP stdio, init único, stdout JSON-RPC-only;
  write/read/search em fixture OKF com ripgrep e fallback aplicáveis.
- [ ] Repetir contenção/glob/symlinks, frontmatter, stats/leituras parciais e logs;
  comparar conteúdo/owner após backup/restore e recriação do container.
- [ ] Revalidar `V-BUILD`, `V-RUN`, `V-CONFIG`, `V-DATA`, `V-MCP`, `V-FUNC` e
  `V-REUSE` afetados; `V-PILOT` só muda com prova do plano próprio, não com mock.
- [ ] Receber evidência dos gestores, CI/scan e limites externos; não afirmar que
  imagem histórica ativa está qualificada pelos testes do candidato.

Aceite de produto local pode ser entregue com retorno parcial. Ação de runtime
ou publicação pendente não se encerra por documentação da solicitação.

## 6. Penúltima etapa — documentar execução neste plano

- [ ] Registrar ações/subtarefa, owner/data, SHA inicial/final, mudanças, comandos,
  ambiente, evidências sanitizadas locais e vereditos `V-*` pós-correção.
- [ ] Registrar decisões de retenção/owner e pendências; complementar seção 9 do
  relatório IaC quando autorizado, preservando baseline e sem conteúdo do vault real.

| Data / owner | Ações / achados | SHA inicial → final | Mudanças / evidências locais | Resultado / V-* / pendências |
|---|---|---|---|---|
| Pendente | A-001–A-012; S2-NT-X01 | A registrar | Nenhuma execução nesta emissão | Não iniciada |

## 7. Última etapa — atualizar o plano coordenador

- [ ] Reler o [stage-2 geral](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md);
  atualizar **S2-NT na seção 3** e adicionar retorno na **seção 7**, com contagens,
  SHA/evidências, aceites locais/externos e dependências liberadas para o piloto.
- [ ] Preservar outros retornos e informar efeito sobre M1/etapas 2/4/5. Sem
  acesso à IaC, entregar resumo e manter **aguardando sincronização**. Concluído
  exige aceites e retorno efetivo; registrar parcial se existir ação transferida/aberta.
