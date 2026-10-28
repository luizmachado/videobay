# Arquitetura: VideoBay GUI

## Contexto
- **Problema:** o yt-dlp é só CLI. Queremos uma GUI leve e moderna, sem perder as atualizações de segurança do upstream.
- **Usuário:** o autor no Linux (i3/X11) e quem baixar o binário.
- **MVP:** URL → metadados e miniatura → qualidade e pasta; áudio MP3/M4A; fila com progresso,
  cancelar e tentar de novo; playlists (inteiras ou itens selecionados) e legendas.
- **Não-objetivos v1:** Windows/macOS, live streams, cookies/login, auto-update do binário, i18n,
  qualquer contribuição ao upstream (sem PRs, issues ou comentários no yt-dlp).
- **Restrições:** nenhum arquivo do upstream é alterado; Python ≥ 3.11; Podman rootless.
- **Stack:** Python 3.12 (uv), CustomTkinter, `yt_dlp.YoutubeDL` como biblioteca, pytest, ruff, pyright, PyInstaller.

## Visão de componentes (ports & adapters)

```
 [CTk views] ⇄ [Presenters + view-models]  ← core (sem I/O, sem tkinter, sem yt_dlp)
                       │ usa
        ┌──────────────┼──────────────────────────────┐
  MediaMetadataExtractorPort   MediaDownloadExecutorPort   VideobaySettingsStorePort
  ThumbnailImageFetcherPort    FfmpegAvailabilityProbePort  BackgroundWorkerPoolPort  ClockPort
        │ implementados por (adapters/)
  YtDlpMetadataExtractorAdapter · YtDlpDownloadExecutorAdapter · JsonFileVideobaySettingsStoreAdapter
  UrllibThumbnailImageFetcherAdapter · ShutilWhichFfmpegProbeAdapter · ThreadingBackgroundWorkerPoolAdapter
        ↑ instanciados só em src/videobay_gui/videobay_composition_root.py
```

| Componente | Camada | Responsabilidade | Depende de |
|---|---|---|---|
| `core/` | domínio | Entidades, regras, presenters, builder de opções | nada (só stdlib) |
| `ports/` | contrato | Protocolos de I/O | `core/` |
| `adapters/` | infraestrutura | yt-dlp, disco, rede, threads | `ports/`, libs externas |
| `views/` | UI | Widgets CustomTkinter finos | presenters |
| `videobay_composition_root.py` | entrada | Instancia adapters e injeta | tudo |

## Ports (limites de I/O)
| Port | Adapter real | Fake de teste | Contrato |
|---|---|---|---|
| `MediaMetadataExtractorPort` | `YtDlpMetadataExtractorAdapter` | `InMemoryMediaMetadataExtractorFake` | sim |
| `MediaDownloadExecutorPort` | `YtDlpDownloadExecutorAdapter` | `ScriptedMediaDownloadExecutorFake` | sim |
| `VideobaySettingsStorePort` | `JsonFileVideobaySettingsStoreAdapter` | `InMemoryVideobaySettingsStoreFake` | sim |
| `ThumbnailImageFetcherPort` | `UrllibThumbnailImageFetcherAdapter` | `StaticThumbnailImageFetcherFake` | sim |
| `FfmpegAvailabilityProbePort` | `ShutilWhichFfmpegProbeAdapter` | `FixedFfmpegAvailabilityProbeFake` | sim |
| `BackgroundWorkerPoolPort` | `ThreadingBackgroundWorkerPoolAdapter` | `ManuallyDrainedBackgroundWorkerPoolFake` | sim |
| `OutputDirectoryAccessProbePort` | `LocalOutputDirectoryAccessProbeAdapter` | (fake por teste) | não |
| `ClockPort` | `SystemMonotonicClockAdapter` | `ManualTickClockFake` | sim |

## Fluxo de dados (caminho principal)
1. O usuário cola a URL, e `validate_media_url_syntax` valida a sintaxe.
2. O worker chama `extract_info(download=False, extract_flat="in_playlist")`.
3. Os metadados viram `InspectedMediaSummary` (vídeo) ou `InspectedPlaylistSummary`.
4. O presenter monta as opções de qualidade, áudio e legendas.
5. "Baixar" monta um `VideoDownloadRequest`, que vira `VideoDownloadJob` (`queued`) na `VideoDownloadJobQueue`.
6. O worker livre executa: `build_yt_dlp_download_options` traduz o request em opções do yt-dlp.
7. Os progress hooks viram `DownloadProgressSnapshot` → `queue.Queue` → thread do Tk (`after(100ms)`) → presenter → view.
8. O job termina como `completed`, `failed` (com mensagem traduzida) ou `cancelled`.

## Modelo de domínio
- `VideoDownloadRequest`: url, `MediaQualityChoice` (best/1080/720/480/audio_only),
  `AudioOutputCodec` (mp3/m4a), output_directory, subtitle_languages, playlist_item_indices.
- `VideoDownloadJob`: `queued → running → completed | failed | cancelled`; `failed | cancelled → queued` (tentar de novo).
  Transição inválida lança `InvalidVideoDownloadJobTransitionError`.
- `DownloadProgressSnapshot`: downloaded_bytes, total_bytes (exato ou estimado), speed, eta, percentage ou `None`.
- `build_yt_dlp_download_options` (puro): request + capacidades (ffmpeg?) → opções do yt-dlp + aviso de fallback.

## Edge cases
| ID | Cenário | Comportamento esperado | Fatia |
|---|---|---|---|
| EC-01 | URL vazia/malformada | Botão desabilitado + mensagem inline | S-001 |
| EC-02 | Site não suportado / privado / geo-block / idade | Erro do yt-dlp traduzido para mensagem clara | S-002 |
| EC-03 | Rede caiu ou timeout na inspeção | Erro + "tentar de novo", sem travar a UI | S-002 |
| EC-04 | ffmpeg ausente + qualidade que exige merge | Fallback para arquivo único + aviso | S-006 |
| EC-05 | ffmpeg ausente + só áudio | Bloqueia com instrução de instalar ffmpeg | S-012 |
| EC-06 | Pasta de destino inexistente/sem permissão | Valida antes de enfileirar | S-007 |
| EC-07 | Arquivo já existe | `nooverwrites`; mostra "já baixado" | S-009 |
| EC-08 | Progresso sem total_bytes | total_bytes_estimate ou barra indeterminada | S-008 |
| EC-09 | Cancelar no meio | Job `cancelled`; `.part` removidos | S-009 |
| EC-10 | Mesma URL e opções já na fila | Rejeita a duplicata | S-016 |
| EC-11 | Playlist com itens indisponíveis | `ignoreerrors`; "N de M baixados" | S-020 |
| EC-12 | Playlist enorme | Listagem flat + seleção paginada | S-019 |
| EC-13 | Idioma de legenda indisponível | Ignora e avisa; continua | S-021 |
| EC-14 | Falha na miniatura | Placeholder, não fatal | S-005 |
| EC-15 | Settings corrompido | Padrões + backup `.bak` | S-007 |
| EC-16 | Fechar com downloads ativos | Confirma; cancela de forma limpa | S-018 |
| EC-17 | Live stream | Rejeitado na v1 com mensagem | S-002 |
| EC-18 | Extractor quebrado (site mudou) | Mensagem sugere sincronizar o fork | S-023 |

## Riscos e decisões em aberto
- O upstream pode criar arquivos com os mesmos nomes. O workflow de sync falha alto e não faz push.
- A política do upstream proíbe contribuições assistidas por IA. Este código fica só no fork e nunca é enviado ao yt-dlp.
- O CustomTkinter não tem drag & drop nativo. Fica fora da v1.
- Runtime JS do YouTube: resolvido na ADR-0008 (deno 2.9.8 embutido + `yt-dlp[default]`). A S-009 confirmou que sem deno o download do YouTube falha.
- A Vimeo passou a exigir login para a maioria dos vídeos. Hoje isso cai em EC-02 ("exige login").
