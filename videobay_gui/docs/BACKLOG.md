# Backlog

## F-00 Walking skeleton
- [x] S-000 Tooling, CI, Containerfile, binário "hello", install/rollback

## F-01 Inspeção de URL
- [x] S-001 Validação de sintaxe da URL
  - Aceite: URL http(s) com host é aceita; vazia, sem esquema ou com esquema não-http é rejeitada com motivo
  - Edge cases: EC-01
- [x] S-002 `MediaMetadataExtractorPort` + fake + `InspectedMediaSummary`
  - Aceite: o presenter mostra título, duração e autor; erros viram mensagens claras; live é rejeitado
  - Edge cases: EC-02, EC-03, EC-17
- [x] S-003 `YtDlpMetadataExtractorAdapter` + suíte de contrato
  - Aceite: o mesmo contrato passa contra o fake e (em integração) contra o yt-dlp real
- [x] S-004 Formatos disponíveis → opções de qualidade
  - Aceite: só oferece resoluções que existem; "melhor" e "só áudio" sempre presentes
- [x] S-005 View: barra de URL + card de mídia com miniatura
  - Edge cases: EC-14

## F-02 Download único
- [x] S-024 Deno embutido + `yt-dlp[default]` (ADR-0008)
  - Aceite: o binário contém deno e os scripts do yt-dlp-ejs; o adapter passa `js_runtimes` quando há deno; checksum errado aborta o build
- [x] S-006 `build_yt_dlp_download_options`: qualidade → format string, com fallback sem ffmpeg
  - Edge cases: EC-04
- [x] S-007 Settings store + pasta de destino
  - Edge cases: EC-06, EC-15
- [x] S-008 `MediaDownloadExecutorPort` + `DownloadProgressSnapshot`
  - Edge cases: EC-08
- [x] S-009 `YtDlpDownloadExecutorAdapter` + cancelamento
  - Edge cases: EC-07, EC-09
- [x] S-010 View de progresso

## F-03 Áudio
- [x] S-011 Pós-processador MP3/M4A
- [x] S-012 Bloqueio sem ffmpeg
  - Edge cases: EC-05

## F-04 Fila
- [x] S-013 Máquina de estados de `VideoDownloadJob`
- [x] S-014 `VideoDownloadJobQueue` com limite de concorrência
- [x] S-015 Cancelar e tentar de novo
- [x] S-016 Rejeitar duplicata
  - Edge cases: EC-10
- [x] S-017 View da fila
- [x] S-018 Fechar com jobs ativos
  - Edge cases: EC-16

## F-05 Playlists e legendas
- [x] S-019 Detecção de playlist + listagem flat
  - Edge cases: EC-12
- [x] S-020 Seleção de itens → `playlist_items`
  - Edge cases: EC-11
- [ ] S-021 Legendas
  - Edge cases: EC-13
- [ ] S-022 View de seleção de playlist e legendas
- [ ] S-023 Mensagem de extractor quebrado
  - Edge cases: EC-18
