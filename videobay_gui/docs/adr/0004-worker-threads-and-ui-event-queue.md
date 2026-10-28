# 0004. Threads de worker e fila de eventos da UI
- Status: aceita
- Data: 2026-10-27

## Contexto
`YoutubeDL.download` bloqueia, e o Tkinter não é thread-safe.

## Decisão
Downloads e inspeções rodam em threads de worker (limite padrão: 2 downloads simultâneos). Os eventos vão para
uma `queue.Queue`, drenada na thread do Tk via `after(100ms)`. Nenhum widget é tocado fora da thread principal.
Para cancelar, o progress hook verifica uma flag por job e lança `yt_dlp.utils.DownloadCancelled`.

## Consequências
O core recebe um `BackgroundWorkerPoolPort`. Nos testes, `ManuallyDrainedBackgroundWorkerPoolFake` só executa as tarefas quando o teste chama
`drain_pending_background_tasks()`. Assim, corridas como "resultado antigo chega depois do novo" ficam determinísticas.
