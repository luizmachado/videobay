# 0006. Camadas de teste headless
- Status: aceita
- Data: 2026-10-27

## Decisão
- `make test`: unit + contract com fakes, sem display e sem rede. Cobertura de 100% (linhas + branches) em `core/`.
- `make test-ui`: smoke tests das views sob `xvfb-run`, dentro do container Podman.
- `make test-integration`: adapters reais (yt-dlp com rede). Roda manualmente e no workflow agendado.

## Consequências
`make ci` = lint + typecheck + `make test`. É rápido e roda no terminal sem infraestrutura nenhuma.
