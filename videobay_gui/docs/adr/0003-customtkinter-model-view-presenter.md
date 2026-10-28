# 0003. CustomTkinter com Model-View-Presenter
- Status: aceita
- Data: 2026-10-27

## Contexto
A GUI precisa ser leve e moderna, e a lógica de tela precisa ser testável sem display.

## Decisão
CustomTkinter para os widgets. Presenters e view-models ficam no core (sem importar tkinter) e recebem uma
interface de view (`Protocol`). As views CTk são finas: desenham e repassam eventos ao presenter.

## Alternativas consideradas
- PySide6: mais completo, mas o binário fica 4 a 6 vezes maior.
- pywebview: depende de GTK/WebKit no Linux.

## Consequências
100% de cobertura em presenters; as views ficam fora da métrica e são cobertas por smoke tests sob Xvfb.
