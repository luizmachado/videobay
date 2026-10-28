# 0008. Deno embutido + extras `default` do yt-dlp
- Status: aceita (aprovada pelo usuário no G3 da F-01, opção onefile)
- Data: 2026-10-27

## Contexto
- Sem um runtime JavaScript, o yt-dlp considera a extração do YouTube obsoleta e alguns formatos podem faltar.
- O deno sozinho não basta: o yt-dlp também precisa do pacote `yt-dlp-ejs` (os scripts JS que o deno executa).
  Esse pacote faz parte dos extras `default` do yt-dlp, que a GUI hoje **não** instala. Junto com ele faltam
  `certifi`, `requests`, `urllib3`, `websockets`, `brotli`, `mutagen` e `pycryptodomex`, todos recomendados pelo próprio yt-dlp.
- O usuário escolheu embutir o deno no binário (G3 da F-01).

## Decisão proposta
1. Depender de `yt-dlp[default]`, ainda pelo caminho editável do fork. Assim, o `yt-dlp-ejs` e os demais extras acompanham o upstream.
2. Fixar o **deno v2.9.8** (`deno-x86_64-unknown-linux-gnu.zip`) no `Makefile`. O build no container baixa o arquivo e
   **verifica o SHA-256** publicado antes de embutir (`--add-binary`).
3. O composition root resolve o caminho do deno: dentro do binário, `sys._MEIPASS/deno`; rodando do código-fonte,
   o deno do `PATH` (se houver). O caminho chega ao adapter como `js_runtimes={'deno': {'path': ...}}`.
4. Sem deno disponível (rodando do código-fonte, sem deno no PATH), a GUI continua funcionando com formatos reduzidos.

## Custos (medidos em 2026-10-27)
| Item | Hoje | Com deno + extras |
|---|---|---|
| Arquivo do binário | 26,5 MB | ~70 MB |
| Extraído em `/tmp` a cada execução (onefile) | ~60 MB | ~160 MB |
| Tempo extra de abertura (estimado) | — | +0,5 a 1 s |

No Debian 13 o `/tmp` é tmpfs, então os ~160 MB extraídos ocupam **RAM** enquanto o app está aberto.

### Medido após a implementação (S-024)
- Binário: **74,4 MB**. Extraído em `/tmp`: **149 MB**. Memória do processo com a janela aberta: **64 MB**.
- A listagem de formatos do YouTube saiu **igual com e sem deno** (até 2160p em `aqz-KE-bpKQ`). O ganho esperado
  aparece no download, onde as URLs dependem dos desafios resolvidos. A S-009 precisa confirmar isso.

## Alternativas consideradas
- Exigir o deno instalado no sistema: binário pequeno, mas exige um passo a mais do usuário.
- AppImage com o deno dentro: um único arquivo de tamanho parecido, montado via squashfs, **sem** extrair a cada execução.
  Exige `appimagetool` no build e FUSE (ou `--appimage-extract-and-run`) na máquina.

## Consequências
O build passa a depender de rede (download do deno) e de um checksum fixo, que precisa ser atualizado junto com a versão.
