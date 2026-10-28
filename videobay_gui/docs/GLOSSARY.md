# Glossário (linguagem ubíqua)

| Termo | Significado | Nome no código |
|---|---|---|
| URL de mídia | Endereço colado pelo usuário | `media_url` |
| Motivo de rejeição da URL | Por que a sintaxe da URL foi recusada | `MediaUrlRejectionReason` |
| Inspeção | Consulta de metadados sem baixar | `InspectedMediaSummary`, `InspectedPlaylistSummary` |
| Escolha de qualidade | Resolução alvo ou só áudio | `MediaQualityChoice` |
| Codec de áudio de saída | Formato da extração de áudio | `AudioOutputCodec` |
| Pedido de download | Tudo que o usuário escolheu para um download | `VideoDownloadRequest` |
| Job de download | Pedido na fila, com estado | `VideoDownloadJob`, `VideoDownloadJobStatus` |
| Fila de downloads | Jobs ordenados com limite de concorrência | `VideoDownloadJobQueue` |
| Instantâneo de progresso | Estado do progresso num momento | `DownloadProgressSnapshot` |
| Construtor de opções | Traduz o pedido para `ydl_opts` | `YtDlpOptionsBuilder` |
| Configurações | Preferências persistidas (pasta, tema, limite) | `VideobayUserSettings` |
