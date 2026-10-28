# Glossário (linguagem ubíqua)

| Termo | Significado | Nome no código |
|---|---|---|
| URL de mídia | Endereço colado pelo usuário | `media_url` |
| Motivo de rejeição da URL | Por que a sintaxe da URL foi recusada | `MediaUrlRejectionReason` |
| Inspeção | Consulta de metadados sem baixar | `InspectedMediaSummary`, `InspectedPlaylistSummary` |
| Falha de inspeção | Categoria de erro ao ler metadados, com mensagem ao usuário | `MediaInspectionFailureKind`, `MediaInspectionFailedError` |
| Apresentador de inspeção | Liga a barra de URL ao extractor e à view | `MediaInspectionPresenter` |
| Miniatura | Imagem de capa da mídia; falha nunca é erro (EC-14) | `ThumbnailImageFetcherPort`, `ThumbnailImageFetchFailedError` |
| Apresentador de download | Pasta, ffmpeg, progresso coalescido, cancelar e tentar de novo de um download | `SingleMediaDownloadPresenter`, `SingleMediaDownloadPorts` |
| Escolha de qualidade | Altura máxima (None = melhor) ou só áudio | `MediaQualityChoice` |
| Faixa padrão de altura | 4320…144 px; alturas cortadas caem na faixa abaixo | `STANDARD_VIDEO_HEIGHT_TIERS` |
| Codec de áudio de saída | Formato da extração de áudio | `AudioOutputCodec` |
| Pedido de download | Tudo que o usuário escolheu para um download | `VideoDownloadRequest` |
| Job de download | Pedido na fila, com estado | `VideoDownloadJob`, `VideoDownloadJobStatus` |
| Fila de downloads | Jobs ordenados com limite de concorrência | `VideoDownloadJobQueue` |
| Instantâneo de progresso | Estado do progresso num momento; total pode ser estimado ou desconhecido (EC-08) | `DownloadProgressSnapshot`, `DownloadProgressViewModel` |
| Falha de download | Categoria de erro durante o download, com mensagem e regra de "tentar de novo" | `MediaDownloadFailureKind`, `MediaDownloadFailedError`, `MediaDownloadCancelledError` |
| Resultado do download | Arquivos gerados e se já existiam (EC-07) | `MediaDownloadOutcome` |
| Construtor de opções | Traduz o pedido para opções do yt-dlp (+ aviso de fallback) | `build_yt_dlp_download_options`, `YtDlpDownloadOptionsBuildResult` |
| Configurações | Preferências persistidas (pasta de destino, limite de downloads simultâneos) | `VideobayUserSettings` |
| Problema na pasta de destino | Pasta inexistente, arquivo no lugar ou sem permissão (EC-06) | `OutputDirectoryProblem` |
