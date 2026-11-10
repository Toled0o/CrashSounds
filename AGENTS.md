# Continuidade do CrashSounds

Projeto independente do painel de buffet. Código em `src/ecodeck`.
Leia `docs/PLAN.md` e `docs/STATUS.md`; confira `git status --short`.
Use `.venv/Scripts/python -m pytest` e `.venv/Scripts/ruff check .`.
Não capture microfone, reproduza nos dispositivos reais, instale driver ou
ative inicialização sem ação explícita do usuário. QA usa diretório temporário,
`QT_QPA_PLATFORM=offscreen` e dispositivos falsos.
Todo arquivo de código deve manter o cabeçalho de copyright solicitado.
Preserve privacidade, dados locais fora do Git e ausência de telemetria.

## Downloads

Prepare as ferramentas de mídia antes dos testes: python scripts/prepare_media_tools.py.
A rede no produto só inicia por ação explícita; não ler cookies/contas do navegador.
QA de download usa fixture sintética em HTTP loopback e porta efêmera, sem sites reais.
Worker/FFmpeg/Node devem ser encerrados juntos ao cancelar, sem matar outros apps.
