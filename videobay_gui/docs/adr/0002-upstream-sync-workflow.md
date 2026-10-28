# 0002. Sincronização com o upstream
- Status: aceita
- Data: 2026-10-27

## Contexto
As correções de extractors e de segurança chegam com frequência no yt-dlp.

## Decisão
- Remote `upstream` = `https://github.com/yt-dlp/yt-dlp`. O sync manual é `git fetch upstream && git merge upstream/master`.
- O workflow agendado `.github/workflows/videobay-upstream-sync.yml` (diário + manual) faz o merge, roda
  `make -C videobay_gui ci` e só faz push se ficar verde. Em caso de conflito ou CI vermelho, falha sem push.
- Os workflows do upstream (release, nightly etc.) são desativados pela UI do GitHub
  (Actions → workflow → Disable workflow), sem editar arquivos.

## Alternativas consideradas
- Só o botão "Sync fork" do GitHub: não roda a CI da GUI antes de integrar.

## Consequências
O push automático exige que o workflow tenha permissão `contents: write`.
