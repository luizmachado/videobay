# VideoBay (fork do yt-dlp com GUI)

Interface gráfica leve em CustomTkinter para o yt-dlp, mantida num fork que recebe o upstream sem conflitos.

## Regra do fork (obrigatório)
- **Nunca altere arquivos do upstream.** Todo trabalho fica em `videobay_gui/`, neste `CLAUDE.md` e em
  `.github/workflows/videobay-*.yml`. Verificação: `git diff upstream/master --stat`.
- A GUI usa o yt-dlp só pela API pública `yt_dlp.YoutubeDL` (dependência de caminho editável `..`).
- Nada deste projeto é enviado ao yt-dlp original: sem PRs, issues ou comentários no upstream.

## Papéis
O usuário é Product Manager, Tech Lead e QA. Claude é o par de programação: propõe, testa,
implementa em fatias pequenas e para nos gates.

## Mapa
- Arquitetura: `videobay_gui/docs/ARCHITECTURE.md` · Decisões: `videobay_gui/docs/adr/` · Glossário: `videobay_gui/docs/GLOSSARY.md`
- Backlog e progresso: `videobay_gui/docs/BACKLOG.md`. **Leia antes de retomar qualquer trabalho.**
- Core sem I/O: `videobay_gui/src/videobay_gui/core/` · Ports: `ports/` · Adapters: `adapters/` · Views: `views/`
- Composition root: `videobay_gui/src/videobay_gui/videobay_composition_root.py`

## Comandos (em `videobay_gui/`, ou `make -C videobay_gui <alvo>`)
- `make test`: testes headless (fakes, sem infra)
- `make ci`: lint + testes + cobertura (fonte da verdade, igual à CI)
- `make test-ui` / `make binary`: em container Podman rootless
- `make install` / `make rollback`

## Nomenclatura (obrigatório)
Todo nome de classe, variável, função, método, arquivo e módulo deve ser **altamente distintivo e
longo**, para que buscas com `grep`/`rg` retornem só o alvo, sem falsos positivos que poluam a
janela de contexto.
- Codifique domínio + papel + especificidade: `InvoiceTaxCalculatorForBrazilianNfe`,
  `pendingInvoiceRetryQueue`, `fetchUnpaidInvoicesOlderThanDays()`. Nunca `Calculator`, `queue`, `fetch()`.
- Proibidos sozinhos ou como sufixo genérico: `Manager, Service, Helper, Util(s), Handler,
  Processor, Data, Info, Item, Common, Misc, Base, Impl, temp, result, value, obj, x`.
- Teste de unicidade: antes de criar um nome, rode `rg -w <nome>`. Se já existir em outro
  contexto, escolha outro nome.
- Variáveis de laço curtas (`i`) só em escopos de até 3 linhas.
- Termos de domínio vêm de `docs/GLOSSARY.md`. Um termo novo entra no glossário no mesmo commit.

## TDD
- Nenhuma lógica sem um teste visto falhando antes (Red → Green → Refactor).
- Cobertura de 100% de linhas + branches em `core/`, aplicada pelo `make ci`. Nunca baixe o threshold.
- Todo I/O (rede, disco, relógio, env, aleatoriedade) passa por um port injetado no composition root.
  Nos testes, use fakes em memória em `tests/fakes/`.
- Tkinter só na thread principal. Workers falam com a UI por `queue.Queue` (ADR-0004).

## Estrutura do código
- Arquivo ≤ 300 linhas, função ≤ 40 linhas, aninhamento ≤ 2 níveis. Use early returns.
- Comentários `WHY:` / `HACK:` / `PROVENANCE:` **nunca são removidos** em refatorações. Só saem
  junto com o código que explicam, e isso fica registrado no commit (`Removed-Context:`).

## Commits e deploy
- Uma fatia por commit, Conventional Commits, `Refs: S-xxx`. Só commite com `make ci` verde.
- Commit é automático. `git push`, release e operações destrutivas sempre pedem autorização.
- Binário PyInstaller construído em Podman rootless, versionado pelo SHA do git, rollback com `make rollback`.

## Gates
Pare e pergunte: ao mudar a arquitetura (proponha uma ADR), ao adicionar dependência, quando um
requisito for ambíguo e ao terminar uma feature.
