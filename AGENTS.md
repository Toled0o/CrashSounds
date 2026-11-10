# Continuidade do EcoDeck

Projeto independente do painel de buffet. Código em `src/ecodeck`.
Leia `docs/PLAN.md` e `docs/STATUS.md`; confira `git status --short`.
Use `.venv/Scripts/python -m pytest` e `.venv/Scripts/ruff check .`.
Não capture microfone, reproduza nos dispositivos reais, instale driver ou
ative inicialização sem ação explícita do usuário. QA usa diretório temporário,
`QT_QPA_PLATFORM=offscreen` e dispositivos falsos.
Todo arquivo de código deve manter o cabeçalho de copyright solicitado.
Preserve privacidade, dados locais fora do Git e ausência de telemetria.
