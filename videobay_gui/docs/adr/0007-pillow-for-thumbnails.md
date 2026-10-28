# 0007. Pillow para decodificar miniaturas
- Status: aceita (aprovada pelo usuário na S-005)
- Data: 2026-10-27

## Contexto
As miniaturas vêm em JPEG/WebP, e o Tk só decodifica PNG e GIF. O `CTkImage` do CustomTkinter espera imagens do Pillow.

## Decisão
Adicionar `pillow>=11.0`. A decodificação fica só na view (`MediaInspectionPanelView`). Bytes inválidos viram placeholder (EC-14).

## Alternativas consideradas
- Sem miniatura na v1.
- Converter com o ffmpeg do sistema: lento e frágil.

## Consequências
O binário onefile foi de 13,5 MB para 26,5 MB, porque o Pillow embute ~15 MB de bibliotecas nativas (AVIF, WebP, freetype…).
**Dívida técnica:** excluir os codecs não usados no PyInstaller (`--exclude-module` / filtrar `pillow.libs`) para voltar a ~18 MB.
