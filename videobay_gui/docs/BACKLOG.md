# Backlog

## F-00 Walking skeleton
- [x] S-000 Tooling, CI, Containerfile, binário "hello", install/rollback

## F-01 Inspeção de URL
- [ ] S-001 Validação de sintaxe da URL
  - Aceite: URL http(s) com host é aceita; vazia, sem esquema ou com esquema não-http é rejeitada com motivo
  - Edge cases: EC-01
- [ ] S-002 `MediaMetadataExtractorPort` + fake + `InspectedMediaSummary`
  - Aceite: o presenter mostra título, duração e autor; erros viram mensagens claras; live é rejeitado
  - Edge cases: EC-02, EC-03, EC-17
- [ ] S-003 `YtDlpMetadataExtractorAdapter` + suíte de contrato
  - Aceite: o mesmo contrato passa contra o fake e (em integração) contra o yt-dlp real
- [ ] S-004 Formatos disponíveis → opções de qualidade
  - Aceite: só oferece resoluções que existem; "melhor" e "só áudio" sempre presentes
- [ ] S-005 View: barra de URL + card de mídia com miniatura
  - Edge cases: EC-14

## F-02 Download único
- [ ] S-006 `YtDlpOptionsBuilder`: qualidade → format string, com fallback sem ffmpeg
  - Edge cases: EC-04
- [ ] S-007 Settings store + pasta de destino
  - Edge cases: EC-06, EC-15
- [ ] S-008 `MediaDownloadExecutorPort` + `DownloadProgressSnapshot`
  - Edge cases: EC-08
- [ ] S-009 `YtDlpDownloadExecutorAdapter` + cancelamento
  - Edge cases: EC-07, EC-09
- [ ] S-010 View de progresso

## F-03 Áudio
- [ ] S-011 Pós-processador MP3/M4A
- [ ] S-012 Bloqueio sem ffmpeg
  - Edge cases: EC-05

## F-04 Fila
- [ ] S-013 Máquina de estados de `VideoDownloadJob`
- [ ] S-014 `VideoDownloadJobQueue` com limite de concorrência
- [ ] S-015 Cancelar e tentar de novo
- [ ] S-016 Rejeitar duplicata
  - Edge cases: EC-10
- [ ] S-017 View da fila
- [ ] S-018 Fechar com jobs ativos
  - Edge cases: EC-16

## F-05 Playlists e legendas
- [ ] S-019 Detecção de playlist + listagem flat
  - Edge cases: EC-12
- [ ] S-020 Seleção de itens → `playlist_items`
  - Edge cases: EC-11
- [ ] S-021 Legendas
  - Edge cases: EC-13
- [ ] S-022 View de seleção de playlist e legendas
- [ ] S-023 Mensagem de extractor quebrado
  - Edge cases: EC-18
