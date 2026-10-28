# 0005. Binário PyInstaller e rollback por symlink
- Status: aceita
- Data: 2026-10-27

## Contexto
App desktop não é "deployado" em container, mas precisa de distribuição portátil e rollback instantâneo.

## Decisão
- PyInstaller onefile para Linux, compilado num container Podman rootless com base Debian bookworm
  (glibc antiga, o que deixa o binário mais portátil).
- Publicação em GitHub Releases por tag imutável `gui-vX.Y.Z`.
- `make install` copia o binário para `~/.local/share/videobay/<git-sha>/` e troca o symlink
  `~/.local/bin/videobay-gui` de forma atômica (symlink temporário + `mv -T`).
- `make rollback` aponta o symlink para o SHA anterior registrado.

## Consequências
As versões antigas ficam no disco até uma limpeza manual. O rollback não depende de rede.
