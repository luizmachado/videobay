# 0001. Subprojeto isolado dentro do fork
- Status: aceita
- Data: 2026-10-27

## Contexto
O fork precisa receber as atualizações do yt-dlp sem conflitos de merge.

## Decisão
Todo o código da GUI fica em `videobay_gui/`, com `pyproject.toml`, `Makefile`, `.gitignore` e `docs/` próprios.
Fora dele, só entram arquivos novos com prefixo próprio: `CLAUDE.md` e `.github/workflows/videobay-*.yml`.
O yt-dlp é uma dependência de caminho editável (`yt-dlp = { path = "..", editable = true }`), então a GUI usa
o código do fork já sincronizado. A GUI consome apenas a API pública `yt_dlp.YoutubeDL`.

## Alternativas consideradas
- Alterar arquivos do upstream: gera conflitos a cada sync.
- Repositório separado com yt-dlp via pip: limpo, mas descarta o fork.

## Consequências
`git diff upstream/master --stat` deve listar só os caminhos acima. Esse é o critério verificável.
