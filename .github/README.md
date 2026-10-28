# VideoBay

[![videobay-gui-ci](https://github.com/luizmachado/videobay/actions/workflows/videobay-gui-ci.yml/badge.svg)](https://github.com/luizmachado/videobay/actions/workflows/videobay-gui-ci.yml)
[![videobay-upstream-sync](https://github.com/luizmachado/videobay/actions/workflows/videobay-upstream-sync.yml/badge.svg)](https://github.com/luizmachado/videobay/actions/workflows/videobay-upstream-sync.yml)

Interface gráfica leve e moderna para baixar vídeos e áudios com o
[yt-dlp](https://github.com/yt-dlp/yt-dlp), para Linux.

O VideoBay é um **fork do [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)**. Todo o trabalho de
download é feito pelo yt-dlp original; este fork só acrescenta uma GUI, numa pasta isolada, e
recebe as atualizações do upstream todos os dias, incluindo as correções de segurança e de sites.

> O VideoBay não é afiliado ao projeto yt-dlp. Problemas com a interface devem ser relatados
> [aqui](https://github.com/luizmachado/videobay/issues), nunca no repositório original.

## Recursos
- Cole a URL e veja título, canal, duração e miniatura antes de baixar.
- Escolha a qualidade (melhor disponível, até 1080p, 720p, 480p…) e a pasta de destino.
- Extraia só o áudio em **MP3** ou **M4A**.
- Fila de downloads com progresso, velocidade e tempo restante, dois ao mesmo tempo por padrão,
  com cancelar e tentar de novo.
- Playlists inteiras ou só os itens marcados, com seleção página a página.
- Legendas em português, inglês e espanhol, ou nos idiomas que o vídeo oferecer.
- Mensagens de erro claras para vídeo privado, site não suportado, rede fora do ar e extractor
  desatualizado.

## Instalação
Baixe o binário da [última release](https://github.com/luizmachado/videobay/releases/latest)
(Linux x86_64, um único arquivo, sem instalar Python):

```bash
chmod +x videobay-gui-linux-x86_64
./videobay-gui-linux-x86_64
```

Recomenda-se ter o `ffmpeg` instalado (`sudo apt install ffmpeg`). Sem ele, a extração de áudio
fica indisponível e os vídeos são baixados no melhor formato de arquivo único.
O runtime JavaScript que o YouTube exige (deno) já vem embutido no binário.

## Como o fork se mantém atualizado
- O código da GUI fica todo em [`videobay_gui/`](../videobay_gui/); nenhum arquivo do yt-dlp é
  alterado, então o merge do upstream nunca dá conflito.
- O workflow [`videobay-upstream-sync`](workflows/videobay-upstream-sync.yml) mescla o
  `yt-dlp/yt-dlp:master` todos os dias e só publica o resultado se os testes da GUI passarem.
- A GUI usa o yt-dlp apenas pela API pública `yt_dlp.YoutubeDL`.

A documentação do yt-dlp em si (opções da linha de comando, sites suportados etc.) continua no
[README original](../README.md), que este fork mantém intacto.

## Desenvolvimento
Requer [uv](https://docs.astral.sh/uv/) e, para os testes de interface e o binário, Podman
rootless.

```bash
cd videobay_gui
make run   # abre a GUI a partir do código
make ci    # lint, tipos e testes (a mesma verificação da CI)
```

Detalhes em [`videobay_gui/README.md`](../videobay_gui/README.md), na
[arquitetura](../videobay_gui/docs/ARCHITECTURE.md) e nas [ADRs](../videobay_gui/docs/adr/).

## Licença e créditos
O yt-dlp é software de domínio público, sob a [Unlicense](../LICENSE), mantido pelos
[desenvolvedores do yt-dlp](https://github.com/yt-dlp/yt-dlp/graphs/contributors).
